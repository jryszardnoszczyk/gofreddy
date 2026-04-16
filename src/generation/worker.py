"""Cloud Tasks generation worker — processes video generation jobs."""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any
from uuid import UUID

from ..common.shutdown import is_shutdown_requested
from .composition import CompositionService
from .config import GenerationSettings
from .exceptions import (
    GenerationError,
    GenerationTimeoutError,
    ModerationBlockedError,
    ProviderUnavailableError,
)
from .models import CompositionSpec
from .repository import PostgresGenerationRepository
from .storage import R2GenerationStorage

logger = logging.getLogger(__name__)


class GenerationWorker:
    """Processes generation jobs dispatched by Cloud Tasks."""

    def __init__(
        self,
        repository: PostgresGenerationRepository,
        storage: R2GenerationStorage,
        client: Any,  # GenerationProvider — use Any to avoid circular import
        composition_service: CompositionService,
        credit_service: Any,  # CreditService — avoid circular import
        settings: GenerationSettings,
    ) -> None:
        self._repo = repository
        self._storage = storage
        self._client = client
        self._composition = composition_service
        self._credit_service = credit_service
        self._settings = settings

    async def process_job(self, job_id: UUID) -> None:
        """Process a generation job: claim, generate cadres, compose, upload."""
        # 1. ATOMIC CLAIM with stale recovery (21 min threshold >= 1200s deadline + buffer)
        async with self._repo._acquire_connection() as conn:
            job_row = await conn.fetchrow(
                """UPDATE generation_jobs
                   SET status = 'generating', claimed_at = NOW()
                   WHERE id = $1
                     AND (status = 'pending'
                          OR (status = 'generating'
                              AND claimed_at < NOW() - INTERVAL '21 minutes'))
                   RETURNING *""",
                job_id,
            )
            if not job_row:
                logger.info("Job %s already claimed or completed, skipping", job_id)
                return

            cadre_rows = await conn.fetch(
                "SELECT * FROM generation_cadres WHERE job_id = $1 ORDER BY cadre_index",
                job_id,
            )

            # Reset any stale 'generating' cadres back to pending for resumption
            for cr in cadre_rows:
                if cr["status"] == "generating":
                    await conn.execute(
                        "UPDATE generation_cadres SET status = 'pending' WHERE id = $1",
                        cr["id"],
                    )

        try:
            job = dict(job_row)
            cadres = [dict(r) for r in cadre_rows]
            user_id = job["user_id"]
            spec_data = job["composition_spec"]
            if isinstance(spec_data, str):
                spec_data = json.loads(spec_data)
            spec = CompositionSpec(**spec_data)
        except Exception as e:
            logger.exception("Worker initialization failed for job %s", job_id)
            await self._repo.update_job_status(
                job_id, "failed", error=f"init_error: {str(e)[:200]}"
            )
            return

        # 2. SET DEADLINE
        deadline = time.monotonic() + self._settings.max_generation_deadline_seconds

        # 3. RESET CIRCUIT BREAKER
        self._client.reset_circuit_breaker()

        # 4. Cost per second
        if spec.resolution == "480p":
            cost_per_sec = self._settings.cost_per_second_cents_480p
        elif spec.resolution == "1080p":
            cost_per_sec = self._settings.cost_per_second_cents_1080p
        else:
            cost_per_sec = self._settings.cost_per_second_cents_720p

        # 5. PROCESS CADRES
        # When all cadres have seed images (approved scene previews), they are
        # independent and can run concurrently — ~6x speedup.
        pending = [c for c in cadres if c["status"] != "completed"]
        all_have_seeds = all(c.get("seed_image_storage_key") for c in pending) if pending else False
        if all_have_seeds and len(pending) > 1:
            logger.info("Job %s: %d cadres have seed images — parallel processing", job_id, len(pending))
            await self._process_cadres_parallel(
                job_id=job_id, user_id=user_id, cadres=cadres, spec=spec,
                cost_per_sec=cost_per_sec, deadline=deadline,
            )
            return

        # Sequential fallback (legacy jobs without seed images)
        completed_cadres: list[dict] = []
        failed = False
        partial = False

        for cadre in cadres:
            cadre_id = cadre["id"]
            cadre_index = cadre["cadre_index"]

            # Skip completed cadres (idempotent resumption)
            if cadre["status"] == "completed":
                completed_cadres.append(cadre)
                continue

            # Check cancellation
            if await self._repo.check_cancellation(job_id):
                logger.info("Job %s cancelled, voiding remaining", job_id)
                await self._repo.update_job_status(job_id, "cancelled")
                return

            # Check SIGTERM
            if is_shutdown_requested():
                logger.warning("SIGTERM checkpoint at cadre %d for job %s", cadre_index, job_id)
                return  # Cloud Tasks will redeliver

            # Check deadline
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                await self._mark_remaining_cadres_failed(
                    cadres, cadre_index
                )
                partial = bool(completed_cadres)
                failed = not partial
                break

            # Reserve credits
            cadre_duration = cadre["duration_seconds"]
            cost_estimate = cadre_duration * cost_per_sec
            reservation = None

            try:
                from ..billing.credits.exceptions import InsufficientCredits
                reservation = await self._credit_service.authorize_usage(
                    user_id=user_id,
                    units=cost_estimate,
                    source_type="video_generation",
                    source_id=f"gen:{job_id}:{cadre_index}",
                    ttl_minutes=self._settings.reservation_ttl_seconds // 60,
                )
            except Exception as e:
                # Import at function scope to avoid circular
                from ..billing.credits.exceptions import InsufficientCredits
                if isinstance(e, InsufficientCredits):
                    # Short-circuit ALL remaining cadres
                    logger.warning(
                        "InsufficientCredits at cadre %d for job %s", cadre_index, job_id
                    )
                    await self._mark_remaining_cadres_failed(
                        cadres, cadre_index
                    )
                    partial = bool(completed_cadres)
                    failed = not partial
                    break
                raise

            # Update cadre status to generating
            await self._repo.update_cadre_status(
                cadre_id, "generating", error=None, reservation_id=reservation.id
            )

            # Generate clip
            temp_path = Path(f"/tmp/gen-{job_id}-cadre-{cadre_index}.mp4")
            frame_path = Path(f"/tmp/gen-{job_id}-frame-{cadre_index}.png")
            try:
                # Project-linked renders prefer approved scene previews as seeds.
                # Legacy/non-project jobs fall back to the previous cadre's final frame.
                image_url = await self._resolve_seed_image_url(
                    cadre=cadre,
                    cadre_index=cadre_index,
                    user_id=user_id,
                    job_id=job_id,
                )

                clip_result = await self._generate_cadre_clip(
                    cadre=cadre,
                    duration=cadre_duration,
                    resolution=spec.resolution,
                    aspect_ratio=spec.aspect_ratio,
                    image_url=image_url,
                    job_id=job_id,
                )

                # Download + validate + extract frame + upload
                await self._client.download_video(clip_result.url, temp_path)
                await self._composition.validate_output(temp_path)

                # Extract final frame BEFORE cleanup (fixes lifecycle gap)
                await self._composition.extract_final_frame(temp_path, frame_path)
                frame_data = frame_path.read_bytes()
                frame_r2_key = await self._storage.upload_video(
                    user_id, job_id, f"frame_{cadre_index}.png", frame_data
                )

                # Upload cadre video
                video_data = temp_path.read_bytes()
                r2_key = await self._storage.upload_video(
                    user_id, job_id, f"cadre_{cadre_index}.mp4", video_data
                )

                # Capture credits
                try:
                    await self._credit_service.capture_usage(
                        reservation.id,
                        units_captured=cost_estimate,
                        unit_type="video_generation",
                    )
                except Exception:
                    logger.warning(
                        "Reservation %s capture failed (may be voided by TTL)", reservation.id
                    )

                # Mark cadre completed
                await self._repo.update_cadre_status(
                    cadre_id,
                    "completed",
                    grok_request_id=clip_result.request_id,
                    r2_key=r2_key,
                    error=None,
                    frame_r2_key=frame_r2_key,
                    cost_cents=cost_estimate,
                    reservation_id=reservation.id,
                )
                cadre["status"] = "completed"
                cadre["r2_key"] = r2_key
                cadre["frame_r2_key"] = frame_r2_key
                completed_cadres.append(cadre)
                self._client.reset_circuit_breaker()

            except ModerationBlockedError:
                logger.warning("Moderation block on cadre %d of job %s", cadre_index, job_id)
                if reservation:
                    await self._safe_void(reservation.id)
                await self._repo.update_cadre_status(
                    cadre_id,
                    "moderation_blocked",
                    error="blocked by content moderation",
                )
                await self._repo.update_job_status(
                    job_id, "failed", error="moderation_blocked"
                )
                return

            except ProviderUnavailableError:
                logger.error("Circuit breaker tripped for job %s", job_id)
                if reservation:
                    await self._safe_void(reservation.id)
                await self._repo.update_cadre_status(
                    cadre_id,
                    "failed",
                    error="video generation API unavailable",
                )
                # Void ALL remaining reservations
                await self._mark_remaining_cadres_failed(
                    cadres, cadre_index + 1, error="job cancelled after API outage"
                )
                await self._repo.update_job_status(
                    job_id, "failed", error="api_unavailable"
                )
                return

            except (GenerationError, GenerationTimeoutError) as e:
                logger.error(
                    "Cadre %d failed for job %s: %s", cadre_index, job_id, str(e)[:200]
                )
                if reservation:
                    await self._safe_void(reservation.id)
                await self._repo.update_cadre_status(
                    cadre_id,
                    "failed",
                    error=str(e)[:500],
                )
                partial = True

            except Exception as e:
                logger.exception("Unexpected error on cadre %d of job %s", cadre_index, job_id)
                if reservation:
                    await self._safe_void(reservation.id)
                await self._repo.update_cadre_status(
                    cadre_id,
                    "failed",
                    error=str(e)[:500],
                )
                partial = True

            finally:
                temp_path.unlink(missing_ok=True)
                frame_path.unlink(missing_ok=True)

        # 6. COMPOSITION (if all cadres completed)
        if failed:
            await self._repo.update_job_status(job_id, "failed", error="cadre_failures")
            return

        if partial or len(completed_cadres) < len(cadres):
            status = "partial" if completed_cadres else "failed"
            await self._repo.update_job_status(
                job_id, status, error="some_cadres_failed"
            )
            return

        # All cadres completed — compose
        await self._compose_and_upload(job_id, user_id, completed_cadres, spec)

    async def _compose_and_upload(
        self,
        job_id: UUID,
        user_id: UUID,
        completed_cadres: list[dict],
        spec: CompositionSpec,
        *,
        narration_path: Path | None = None,
        music_path: Path | None = None,
    ) -> None:
        """Download cadres from R2, compose, upload final video."""
        await self._repo.update_job_status(job_id, "composing")

        cadre_temp_paths: list[Path] = []
        output_path = Path(f"/tmp/gen-{job_id}-final.mp4")

        try:
            # Download cadres from R2 (Semaphore(3) for concurrency control)
            sem = asyncio.Semaphore(3)

            async def download_cadre(cadre: dict, idx: int) -> Path:
                async with sem:
                    r2_key = cadre["r2_key"]
                    dest = Path(f"/tmp/gen-{job_id}-dl-{idx}.mp4")
                    s3_client = await self._storage._video_storage._get_client()
                    response = await s3_client.get_object(
                        Bucket=self._storage._settings.bucket_name,
                        Key=r2_key,
                    )
                    body = await response["Body"].read()
                    dest.write_bytes(body)
                    return dest

            tasks = [download_cadre(c, i) for i, c in enumerate(completed_cadres)]
            cadre_temp_paths = await asyncio.gather(*tasks)

            # Compose
            await self._composition.compose(
                cadre_temp_paths, spec, output_path,
                narration_path=narration_path, music_path=music_path,
            )

            # Validate output
            duration = await self._composition.validate_output(output_path)
            logger.info("Composed video for job %s: %.1fs", job_id, duration)

            # Upload final video
            final_data = output_path.read_bytes()
            r2_key = await self._storage.upload_video(
                user_id, job_id, "final.mp4", final_data
            )

            # Update job as completed
            await self._repo.update_job_status(
                job_id, "completed", r2_key=r2_key
            )

        except (GenerationError, GenerationTimeoutError) as e:
            logger.error("Composition failed for job %s: %s", job_id, str(e)[:200])
            await self._repo.update_job_status(
                job_id, "partial", error="composition_failed"
            )
        except Exception:
            logger.exception("Unexpected composition error for job %s", job_id)
            await self._repo.update_job_status(
                job_id, "partial", error="composition_failed"
            )
        finally:
            for p in cadre_temp_paths:
                if isinstance(p, Path):
                    p.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
            if narration_path:
                narration_path.unlink(missing_ok=True)
            if music_path:
                music_path.unlink(missing_ok=True)

    async def _process_cadres_parallel(
        self,
        *,
        job_id: UUID,
        user_id: UUID,
        cadres: list[dict],
        spec: CompositionSpec,
        cost_per_sec: int,
        deadline: float,
    ) -> None:
        """Process cadres concurrently when all have seed images.

        Uses a semaphore to limit concurrent Grok API calls (avoid rate limits).
        Each cadre is independent — uses its own approved preview as I2V seed.
        """
        sem = asyncio.Semaphore(3)  # Max 3 concurrent Grok calls
        completed_cadres: list[dict] = []
        any_failed = False

        async def _process_one(cadre: dict) -> None:
            nonlocal any_failed
            if cadre["status"] == "completed":
                completed_cadres.append(cadre)
                return

            cadre_id = cadre["id"]
            cadre_index = cadre["cadre_index"]
            cadre_duration = cadre["duration_seconds"]
            cost_estimate = cadre_duration * cost_per_sec

            # Check deadline
            if time.monotonic() > deadline:
                await self._repo.update_cadre_status(cadre_id, "failed", error="deadline_exceeded")
                any_failed = True
                return

            # Reserve credits
            reservation = None
            try:
                reservation = await self._credit_service.authorize_usage(
                    user_id=user_id,
                    units=cost_estimate,
                    source_type="video_generation",
                    source_id=f"gen:{job_id}:{cadre_index}",
                    ttl_minutes=self._settings.reservation_ttl_seconds // 60,
                )
            except Exception:
                await self._repo.update_cadre_status(cadre_id, "failed", error="credit_reservation_failed")
                any_failed = True
                return

            await self._repo.update_cadre_status(
                cadre_id, "generating", error=None, reservation_id=reservation.id
            )

            temp_path = Path(f"/tmp/gen-{job_id}-cadre-{cadre_index}.mp4")
            frame_path = Path(f"/tmp/gen-{job_id}-frame-{cadre_index}.png")
            try:
                image_url = await self._resolve_seed_image_url(
                    cadre=cadre, cadre_index=cadre_index,
                    user_id=user_id, job_id=job_id,
                )

                async with sem:
                    clip_result = await self._generate_cadre_clip(
                        cadre=cadre, duration=cadre_duration,
                        resolution=spec.resolution, aspect_ratio=spec.aspect_ratio,
                        image_url=image_url, job_id=job_id,
                    )

                await self._client.download_video(clip_result.url, temp_path)
                await self._composition.validate_output(temp_path)
                await self._composition.extract_final_frame(temp_path, frame_path)

                frame_data = frame_path.read_bytes()
                frame_r2_key = await self._storage.upload_video(
                    user_id, job_id, f"frame_{cadre_index}.png", frame_data
                )
                video_data = temp_path.read_bytes()
                r2_key = await self._storage.upload_video(
                    user_id, job_id, f"cadre_{cadre_index}.mp4", video_data
                )

                try:
                    await self._credit_service.capture_usage(
                        reservation.id, units_captured=cost_estimate,
                        unit_type="video_generation",
                    )
                except Exception:
                    logger.warning("Reservation %s capture failed", reservation.id)

                await self._repo.update_cadre_status(
                    cadre_id, "completed",
                    grok_request_id=clip_result.request_id,
                    r2_key=r2_key, error=None,
                    frame_r2_key=frame_r2_key,
                    cost_cents=cost_estimate,
                    reservation_id=reservation.id,
                )
                cadre["status"] = "completed"
                cadre["r2_key"] = r2_key
                cadre["frame_r2_key"] = frame_r2_key
                completed_cadres.append(cadre)
                self._client.reset_circuit_breaker()
                logger.info("Cadre %d completed for job %s (parallel)", cadre_index, job_id)

            except ModerationBlockedError:
                logger.warning("Moderation block on cadre %d of job %s", cadre_index, job_id)
                if reservation:
                    await self._safe_void(reservation.id)
                await self._repo.update_cadre_status(
                    cadre_id, "moderation_blocked", error="blocked by content moderation",
                )
                any_failed = True

            except ProviderUnavailableError:
                logger.error("API unavailable for cadre %d of job %s", cadre_index, job_id)
                if reservation:
                    await self._safe_void(reservation.id)
                await self._repo.update_cadre_status(
                    cadre_id, "failed", error="video generation API unavailable",
                )
                any_failed = True

            except (GenerationError, GenerationTimeoutError) as e:
                logger.error("Cadre %d failed for job %s: %s", cadre_index, job_id, str(e)[:200])
                if reservation:
                    await self._safe_void(reservation.id)
                await self._repo.update_cadre_status(cadre_id, "failed", error=str(e)[:500])
                any_failed = True

            except Exception as e:
                logger.exception("Unexpected error on cadre %d of job %s", cadre_index, job_id)
                if reservation:
                    await self._safe_void(reservation.id)
                await self._repo.update_cadre_status(cadre_id, "failed", error=str(e)[:500])
                any_failed = True

            finally:
                temp_path.unlink(missing_ok=True)
                frame_path.unlink(missing_ok=True)

        # Run all cadres concurrently
        await asyncio.gather(*[_process_one(c) for c in cadres], return_exceptions=True)

        # Check for moderation block (fail entire job)
        moderation_blocked = any(
            c.get("status") == "moderation_blocked"
            for c in cadres if c.get("status") != "completed"
        )
        if moderation_blocked:
            await self._repo.update_job_status(job_id, "failed", error="moderation_blocked")
            return

        # Compose or mark partial/failed
        if len(completed_cadres) == len(cadres):
            completed_cadres.sort(key=lambda c: c["cadre_index"])
            await self._compose_and_upload(job_id, user_id, completed_cadres, spec)
        elif completed_cadres:
            await self._repo.update_job_status(job_id, "partial", error="some_cadres_failed")
        else:
            await self._repo.update_job_status(job_id, "failed", error="all_cadres_failed")

    async def _mark_remaining_cadres_failed(
        self,
        cadres: list[dict],
        from_index: int,
        *,
        error: str | None = None,
    ) -> None:
        """Mark all cadres from from_index onward as failed."""
        for cadre in cadres:
            if cadre["cadre_index"] >= from_index and cadre.get("status") != "completed":
                await self._repo.update_cadre_status(
                    cadre["id"],
                    "failed",
                    error=error,
                )

    async def _resolve_seed_image_url(
        self,
        *,
        cadre: dict,
        cadre_index: int,
        user_id: UUID,
        job_id: UUID,
    ) -> str | None:
        seed_key = cadre.get("seed_image_storage_key")
        if seed_key:
            try:
                return await self._storage.get_preview_url(seed_key, expiry=1800)
            except Exception:
                logger.warning(
                    "Failed to load preview seed for cadre %d of job %s; falling back",
                    cadre_index,
                    job_id,
                    exc_info=True,
                )

        if cadre_index <= 0:
            return None

        frame_key = self._storage._generation_key(
            user_id, job_id, f"frame_{cadre_index - 1}.png"
        )
        return await self._storage.get_presigned_url(
            frame_key, expiry=1800  # 30 min
        )

    def _build_video_prompt(self, scene_prompt: str, has_seed_image: bool) -> str:
        """Adapt scene prompt for video generation context."""
        if has_seed_image:
            # I2V: image defines the scene — animate with cinematic motion
            return (
                "Animate this scene from the reference image with fluid, cinematic motion. "
                "Maintain visual continuity with the reference while adding natural movement, "
                "atmospheric shifts, and emotional progression:\n"
                f"{scene_prompt}"
            )
        # T2V: use full cinematic prompt as-is
        return scene_prompt

    async def _generate_cadre_clip(
        self,
        *,
        cadre: dict,
        duration: int,
        resolution: str,
        aspect_ratio: str = "auto",
        image_url: str | None,
        job_id: UUID,
    ) -> Any:
        """Generate a cadre clip with bounded timeout retry and continuation fallback."""
        timeout_retried = False
        current_image_url = image_url

        while True:
            try:
                prompt = self._build_video_prompt(cadre["prompt"], current_image_url is not None)
                return await self._client.generate_clip(
                    prompt=prompt,
                    duration=duration,
                    resolution=resolution,
                    aspect_ratio=aspect_ratio,
                    image_url=current_image_url,
                )
            except (ModerationBlockedError, ProviderUnavailableError):
                raise
            except GenerationTimeoutError:
                if timeout_retried:
                    raise
                timeout_retried = True
                logger.warning(
                    "Cadre %d timed out for job %s, retrying once",
                    cadre["cadre_index"],
                    job_id,
                )
            except GenerationError:
                if current_image_url is not None:
                    logger.warning(
                        "Cadre %d failed with continuation image, retrying without: %s",
                        cadre["cadre_index"],
                        job_id,
                    )
                    current_image_url = None
                    continue
                raise

    async def _safe_void(self, reservation_id: UUID) -> None:
        """Void a credit reservation, ignoring errors."""
        try:
            await self._credit_service.void_usage(reservation_id)
        except Exception:
            logger.warning("Failed to void reservation %s", reservation_id)
