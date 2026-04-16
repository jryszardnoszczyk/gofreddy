"""ImagePreviewService — generate storyboard preview images."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import TYPE_CHECKING

from ..common.cost_recorder import cost_recorder as _cost_recorder, extract_gemini_usage
from .config import GenerationSettings
from .exceptions import PreviewError
from .models import PreviewResult, VerificationResult

if TYPE_CHECKING:
    from uuid import UUID

    from google import genai

    from .fal_client import FalPlatformClient
    from .grok_client import GrokImagineClient
    from .storage import R2GenerationStorage

logger = logging.getLogger(__name__)


class ImagePreviewService:
    """Generate still image previews for storyboard cadres.

    Supports multiple image generation backends:
    - "gemini" — Gemini image generation (default)
    - "grok" — Grok Imagine
    - "imagen" — Imagen 4
    - "fal" — FLUX.2 Pro via fal.ai
    """

    def __init__(
        self,
        client: genai.Client,
        storage: R2GenerationStorage,
        settings: GenerationSettings,
        grok_client: GrokImagineClient | None = None,
        fal_client: FalPlatformClient | None = None,
    ) -> None:
        self._client = client
        self._storage = storage
        self._settings = settings
        self._grok = grok_client
        self._fal = fal_client

    async def generate_preview(
        self,
        user_id: UUID,
        prompt: str,
        aspect_ratio: str = "9:16",
        style_ref_path: str | None = None,
        model: str = "gemini",
    ) -> PreviewResult:
        """Generate a single preview image for a cadre prompt.

        Args:
            user_id: Owner for R2 storage path.
            prompt: Cadre prompt describing the scene.
            aspect_ratio: Image aspect ratio (9:16, 16:9, 1:1).
            style_ref_path: Optional R2 key of a style reference image (cadre 0).
            model: "gemini" (Grok primary, Gemini fallback) or "imagen" (Imagen 3, cheaper).

        Returns:
            PreviewResult with image URL and optional QA score.

        Raises:
            PreviewError: On generation failure, safety block, or timeout.
        """
        model_used = model

        if model == "imagen":
            image_url, image_data = await self._generate_via_imagen(prompt, aspect_ratio)
        elif model == "grok":
            if self._grok is None:
                raise PreviewError("Grok Imagine is not configured. Use model='gemini' or 'imagen'.")
            style_ref_url = await self._resolve_style_ref_url(style_ref_path)
            image_url, image_data = await self._generate_via_grok(prompt, aspect_ratio, style_ref_url)
        elif model == "fal":
            if self._fal is None:
                raise PreviewError("fal.ai is not configured. Set FAL_KEY and GENERATION_PROVIDER=fal.")
            image_url, image_data = await self._generate_via_fal(prompt, aspect_ratio)
        elif model == "gemini":
            # Gemini path — with automatic fal.ai fallback on rate limit (429)
            try:
                image_url, image_data = await self._generate_via_gemini(prompt, aspect_ratio, style_ref_path)
            except PreviewError as e:
                error_str = str(e)
                if self._fal and ("Rate limited" in error_str or "429" in error_str or "RESOURCE_EXHAUSTED" in error_str):
                    logger.info("Gemini rate limited, falling back to fal.ai for preview generation")
                    image_url, image_data = await self._generate_via_fal(prompt, aspect_ratio)
                    model_used = "fal"
                else:
                    raise
        else:
            raise PreviewError(f"Unknown model: {model}. Use 'gemini', 'grok', 'fal', or 'imagen'.")

        # Upload to R2 if we got raw bytes (Gemini/Imagen path)
        if image_data:
            filename = f"{uuid.uuid4().hex}.png"
            r2_key = await self._storage.upload_preview(user_id, filename, image_data)
            image_url = await self._storage.get_preview_url(r2_key)
        elif image_url:
            # Grok returns a URL — download and re-upload to R2 for persistence
            r2_key = await self._reupload_to_r2(user_id, image_url)
            image_url = await self._storage.get_preview_url(r2_key)
        else:
            raise PreviewError("No image generated. Try a more descriptive prompt.")

        # Run QA score with style comparison when anchor exists
        qa_score, qa_feedback = await self._evaluate_qa(prompt, r2_key, style_ref_path)

        return PreviewResult(
            image_url=image_url,
            r2_key=r2_key,
            local_path="",
            qa_score=qa_score,
            qa_feedback=qa_feedback,
            model_used=model_used,
        )

    async def _resolve_style_ref_url(self, style_ref_path: str | None) -> str | None:
        """Resolve R2 key to presigned URL for Grok (which needs URLs, not bytes)."""
        if not style_ref_path:
            return None
        try:
            return await self._storage.get_preview_url(style_ref_path, expiry=600)
        except Exception:
            logger.warning("Failed to resolve style ref URL %s", style_ref_path)
            return None

    async def _generate_via_grok(
        self,
        prompt: str,
        aspect_ratio: str,
        style_ref_url: str | None,
    ) -> tuple[str | None, bytes | None]:
        """Generate image via Grok Imagine API. Raises on failure (caller handles fallback)."""
        from .grok_client import GrokModerationBlockedError

        assert self._grok is not None

        full_prompt = f"Generate a cinematic preview image for this video scene:\n{prompt}\nCinematic composition with depth of field, atmospheric lighting, and emotional resonance matching the scene direction."

        try:
            result = await asyncio.wait_for(
                self._grok.generate_image(
                    prompt=full_prompt,
                    aspect_ratio=aspect_ratio,
                    image_url=style_ref_url,
                ),
                timeout=30,
            )
            return result.url, None
        except GrokModerationBlockedError as e:
            raise PreviewError("Image blocked by safety filter. Try modifying the scene description.") from e
        except asyncio.TimeoutError as e:
            raise PreviewError("Preview generation timed out") from e

    async def _generate_via_fal(
        self,
        prompt: str,
        aspect_ratio: str,
    ) -> tuple[str | None, bytes | None]:
        """Generate image via fal.ai FLUX.2 Pro. Returns (url, None)."""
        from .exceptions import ModerationBlockedError

        assert self._fal is not None

        full_prompt = f"Generate a cinematic preview image for this video scene:\n{prompt}\nCinematic composition with depth of field, atmospheric lighting, and emotional resonance matching the scene direction."

        try:
            result = await asyncio.wait_for(
                self._fal.generate_image(
                    prompt=full_prompt,
                    aspect_ratio=aspect_ratio,
                ),
                timeout=60,
            )
            return result.url, None
        except ModerationBlockedError as e:
            raise PreviewError("Image blocked by safety filter. Try modifying the scene description.") from e
        except asyncio.TimeoutError as e:
            raise PreviewError("Preview generation timed out") from e
        except Exception as e:
            raise PreviewError(f"fal.ai image generation failed: {str(e)[:200]}") from e

    async def _generate_via_gemini(
        self,
        prompt: str,
        aspect_ratio: str,
        style_ref_path: str | None,
    ) -> tuple[str | None, bytes | None]:
        """Generate image via Gemini image gen with real image-based style conditioning."""
        from google.genai import types as genai_types

        contents: list[genai_types.Part] = []

        # Send actual anchor image bytes for style conditioning
        if style_ref_path:
            try:
                anchor_bytes = await self._storage.download_preview(style_ref_path)
                contents.append(genai_types.Part(
                    inline_data=genai_types.Blob(mime_type="image/png", data=anchor_bytes),
                ))
                contents.append(genai_types.Part(text=
                    "Above is the style reference image. Match its visual style, color palette, "
                    "lighting, and artistic treatment exactly.\n\n"
                ))
            except Exception:
                logger.warning("Failed to download style ref %s, generating without", style_ref_path)

        contents.append(genai_types.Part(text=
            f"Generate a cinematic preview image for this video scene:\n{prompt}\n"
            f"Aspect ratio: {aspect_ratio}. Cinematic composition with depth of field, atmospheric lighting, "
            f"and emotional resonance matching the scene direction."
        ))

        config = genai_types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        )

        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=self._settings.preview_model,
                    contents=contents,
                    config=config,
                ),
                timeout=30,
            )
        except asyncio.TimeoutError as e:
            raise PreviewError("Preview generation timed out") from e
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                raise PreviewError("Rate limited. Try again in a moment.") from e
            logger.exception("Preview generation failed")
            raise PreviewError("Preview generation failed") from e

        t_in, t_out, c = extract_gemini_usage(response, self._settings.preview_model)
        await _cost_recorder.record("gemini", "generate_preview", tokens_in=t_in, tokens_out=t_out, cost_usd=c, model=self._settings.preview_model)

        # Check finish reason
        if response.candidates and response.candidates[0].finish_reason not in (None, "STOP"):
            finish = response.candidates[0].finish_reason
            if finish == "SAFETY":
                raise PreviewError("Image blocked by safety filter. Try modifying the scene description.")
            raise PreviewError(f"Preview generation terminated: {finish}")

        # Extract image from response
        image_data = None
        if response.candidates:
            resp_content = response.candidates[0].content
            if resp_content and resp_content.parts:
                for part in resp_content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        image_data = part.inline_data.data
                        break

        if not image_data:
            raise PreviewError("No image generated. Try a more descriptive prompt.")

        return None, image_data

    async def _generate_via_imagen(
        self,
        prompt: str,
        aspect_ratio: str,
    ) -> tuple[str | None, bytes | None]:
        """Generate image via Imagen 3 (cheaper alternative, no image-input style conditioning)."""
        from google.genai import types as genai_types

        full_prompt = (
            f"Generate a cinematic preview image for this video scene:\n{prompt}\n"
            f"Aspect ratio: {aspect_ratio}. Cinematic composition with depth of field, atmospheric lighting, "
            f"and emotional resonance matching the scene direction."
        )

        config = genai_types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        )

        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=self._settings.preview_model_imagen,
                    contents=full_prompt,
                    config=config,
                ),
                timeout=30,
            )
        except asyncio.TimeoutError as e:
            raise PreviewError("Preview generation timed out") from e
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                raise PreviewError("Rate limited. Try again in a moment.") from e
            logger.exception("Imagen preview generation failed")
            raise PreviewError("Preview generation failed") from e

        t_in, t_out, c = extract_gemini_usage(response, self._settings.preview_model_imagen)
        await _cost_recorder.record("gemini", "generate_preview_imagen", tokens_in=t_in, tokens_out=t_out, cost_usd=c, model=self._settings.preview_model_imagen)

        if response.candidates and response.candidates[0].finish_reason not in (None, "STOP"):
            finish = response.candidates[0].finish_reason
            if finish == "SAFETY":
                raise PreviewError("Image blocked by safety filter. Try modifying the scene description.")
            raise PreviewError(f"Preview generation terminated: {finish}")

        image_data = None
        if response.candidates:
            resp_content = response.candidates[0].content
            if resp_content and resp_content.parts:
                for part in resp_content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        image_data = part.inline_data.data
                        break

        if not image_data:
            raise PreviewError("No image generated. Try a more descriptive prompt.")

        return None, image_data

    async def _reupload_to_r2(self, user_id: UUID, url: str) -> str:
        """Download image from Grok URL and re-upload to R2 for persistence."""
        import httpx

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as http:
            resp = await http.get(url)
            resp.raise_for_status()
            image_data = resp.content

        filename = f"{uuid.uuid4().hex}.png"
        return await self._storage.upload_preview(user_id, filename, image_data)

    async def generate_batch(
        self,
        user_id: UUID,
        prompts: list[str],
        style_ref_path: str,
        aspect_ratio: str = "9:16",
        model: str = "gemini",
    ) -> list[PreviewResult | None]:
        """Generate previews for multiple cadres in parallel.

        Uses cadre 0's image as style reference for visual consistency.
        Returns list matching input order; failed entries are None.
        """
        sem = asyncio.Semaphore(3)
        async def _limited(coro):
            async with sem:
                return await coro
        tasks = [
            _limited(self.generate_preview(user_id, p, aspect_ratio, style_ref_path, model=model))
            for p in prompts
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        output: list[PreviewResult | None] = []
        for i, raw in enumerate(raw_results):
            if isinstance(raw, BaseException):
                logger.warning("Preview generation failed for cadre %d: %s", i, raw)
                output.append(None)
            else:
                output.append(raw)
        return output

    async def verify_preview(
        self,
        prompt: str,
        generated_r2_key: str,
        style_ref_path: str | None = None,
    ) -> VerificationResult:
        """Structured verification: scene_score + style_score + improvement_suggestion.

        Downloads generated image and anchor image from R2, sends both to
        the lightweight verifier model for structured evaluation.
        """
        import json as _json
        from google.genai import types as genai_types

        verifier_model = self._settings.preview_verifier_model
        contents: list[genai_types.Part] = []

        # Include anchor image for style comparison
        if style_ref_path:
            try:
                anchor_bytes = await self._storage.download_preview(style_ref_path)
                contents.append(genai_types.Part(
                    inline_data=genai_types.Blob(mime_type="image/png", data=anchor_bytes),
                ))
                contents.append(genai_types.Part(text=
                    "Above is the STYLE REFERENCE image (frame 1 anchor). "
                    "The generated image below MUST match its visual style.\n\n"
                ))
            except Exception:
                logger.warning("Could not load anchor for structured verification")

        # Download and include generated image
        try:
            generated_bytes = await self._storage.download_preview(generated_r2_key)
            contents.append(genai_types.Part(
                inline_data=genai_types.Blob(mime_type="image/png", data=generated_bytes),
            ))
        except Exception as exc:
            raise PreviewError("Could not download generated image for verification") from exc

        has_style_ref = bool(style_ref_path and len(contents) >= 3)
        contents.append(genai_types.Part(text=(
            f"Above is the GENERATED image.\n\n"
            f"Scene description requirements: \"{prompt}\"\n\n"
            "You are a strict visual QA verifier. Score this generated image on TWO axes:\n"
            "1. SCENE_SCORE (1-10): Does it accurately depict the scene description? "
            "Check subjects, actions, setting, mood, and all specific details mentioned.\n"
            + (
                "2. STYLE_SCORE (1-10): Does it match the style reference image's color palette, "
                "lighting, artistic treatment, camera angle style, and overall visual identity?\n"
                if has_style_ref else
                "2. STYLE_SCORE (1-10): Rate the overall visual quality and coherence.\n"
            )
            + "\nThen provide:\n"
            "- FEEDBACK: One sentence describing the weakest aspect.\n"
            "- IMPROVEMENT_SUGGESTION: One actionable prompt refinement to improve the weakest aspect.\n\n"
            "Respond with ONLY a JSON object:\n"
            '{"scene_score": N, "style_score": N, "feedback": "...", "improvement_suggestion": "..."}'
        )))

        config = genai_types.GenerateContentConfig(temperature=0.1)

        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=verifier_model,
                    contents=contents,
                    config=config,
                ),
                timeout=20,
            )
            t_in, t_out, c = extract_gemini_usage(response, verifier_model)
            await _cost_recorder.record(
                "gemini", "verify_preview_structured",
                tokens_in=t_in, tokens_out=t_out, cost_usd=c, model=verifier_model,
            )

            text = (response.text or "").strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            data = _json.loads(text)
            scene_score = max(1, min(10, int(data.get("scene_score", 5))))
            style_score = max(1, min(10, int(data.get("style_score", scene_score))))
            feedback = str(data.get("feedback", ""))[:200]
            suggestion = str(data.get("improvement_suggestion", ""))[:500]
            return VerificationResult(
                scene_score=scene_score,
                style_score=style_score,
                overall_score=min(scene_score, style_score),
                feedback=feedback,
                improvement_suggestion=suggestion,
            )
        except PreviewError:
            raise
        except asyncio.TimeoutError as exc:
            raise PreviewError("Verification timed out") from exc
        except Exception as exc:
            logger.exception("Structured verification failed")
            raise PreviewError("Verification failed") from exc

    async def _evaluate_qa(
        self,
        prompt: str,
        generated_r2_key: str,
        style_ref_path: str | None = None,
    ) -> tuple[int | None, str | None]:
        """Evaluate generated image for prompt fidelity and style consistency.

        Uses a separate lightweight verifier model (gemini-3.1-flash-lite) to
        inspect the actual generated image bytes and compare against:
        1. The scene description (prompt fidelity)
        2. The style reference / anchor image (visual consistency)
        """
        from google.genai import types as genai_types

        verifier_model = self._settings.preview_verifier_model
        contents: list[genai_types.Part] = []

        # Include anchor image for style comparison when available
        if style_ref_path:
            try:
                anchor_bytes = await self._storage.download_preview(style_ref_path)
                contents.append(genai_types.Part(
                    inline_data=genai_types.Blob(mime_type="image/png", data=anchor_bytes),
                ))
                contents.append(genai_types.Part(text=
                    "Above is the STYLE REFERENCE image (frame 1 template). "
                    "The generated image below MUST match its visual style.\n\n"
                ))
            except Exception:
                logger.debug("Could not load anchor for QA comparison")

        # Download and include actual generated image bytes for evaluation
        try:
            generated_bytes = await self._storage.download_preview(generated_r2_key)
            contents.append(genai_types.Part(
                inline_data=genai_types.Blob(mime_type="image/png", data=generated_bytes),
            ))
        except Exception:
            logger.debug("Could not download generated image for QA, skipping")
            return None, None

        contents.append(genai_types.Part(text=
            f"Above is the GENERATED image.\n\n"
            f"Scene description requirements: \"{prompt}\"\n\n"
        ))

        if style_ref_path:
            contents.append(genai_types.Part(text=
                "You are a strict visual QA verifier. Evaluate this generated image on TWO criteria:\n"
                "1. SCENE ACCURACY: Does the image correctly depict everything described in the scene requirements? "
                "Check subjects, actions, setting, mood, and all specific details mentioned.\n"
                "2. STYLE CONSISTENCY: Does it match the style reference image's color palette, lighting, "
                "artistic treatment, camera angle style, and overall visual identity?\n\n"
                "Be strict — a score of 7+ means BOTH criteria are well met.\n"
                "Respond with ONLY a JSON object: {\"score\": <1-10>, \"feedback\": \"<one sentence explaining the weakest aspect>\"}"
            ))
        else:
            contents.append(genai_types.Part(text=
                "You are a strict visual QA verifier. Evaluate how accurately this generated image "
                "depicts the scene description requirements. Check all specific details: subjects, actions, "
                "setting, mood, composition, and any mentioned visual elements.\n\n"
                "Be strict — a score of 7+ means ALL requirements are clearly visible.\n"
                "Respond with ONLY a JSON object: {\"score\": <1-10>, \"feedback\": \"<one sentence explaining the weakest aspect>\"}"
            ))

        config = genai_types.GenerateContentConfig(
            temperature=0.1,
        )

        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=verifier_model,
                    contents=contents,
                    config=config,
                ),
                timeout=15,
            )
            t_in, t_out, c = extract_gemini_usage(response, verifier_model)
            await _cost_recorder.record("gemini", "verify_preview_quality", tokens_in=t_in, tokens_out=t_out, cost_usd=c, model=verifier_model)
            if response.text:
                import json
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                data = json.loads(text)
                score = int(data.get("score", 0))
                score = max(1, min(10, score))
                feedback = str(data.get("feedback", ""))[:200]
                return score, feedback
        except Exception:
            logger.debug("QA verification failed, skipping", exc_info=True)

        return None, None
