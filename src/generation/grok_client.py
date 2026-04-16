"""Grok Imagine API client for video generation."""

import asyncio
import logging
import re
import time
from pathlib import Path
from typing import Self
from urllib.parse import urlparse
import httpx

from ..common.cost_recorder import cost_recorder as _cost_recorder
from .config import GenerationSettings
from .exceptions import (
    GenerationError,
    GenerationTimeoutError,
    ModerationBlockedError,
    ProviderUnavailableError,
)

# Re-export backward-compatible aliases for external importers
GrokModerationBlockedError = ModerationBlockedError
GrokAPIUnavailableError = ProviderUnavailableError
from .providers import ImageResult, VideoClip

logger = logging.getLogger(__name__)

# Backward-compatible alias — old code imports ClipResult from here
ClipResult = VideoClip


class GrokImagineClient:
    """Async context manager for Grok Imagine video generation API."""

    _ALLOWED_DOMAINS_RE = re.compile(r"^https://[a-zA-Z0-9.-]+\.x\.ai/")
    _MAX_CADRE_SIZE = 100 * 1024 * 1024  # 100MB

    def __init__(self, settings: GenerationSettings) -> None:
        self._settings = settings
        self._client = None  # xai_sdk.AsyncClient
        self._http: httpx.AsyncClient | None = None
        self._consecutive_failures = 0
        self._CIRCUIT_BREAKER_THRESHOLD = 3

    async def __aenter__(self) -> Self:
        import xai_sdk
        if not self._settings.xai_api_key:
            raise GenerationError("xai_api_key is required for GrokImagineClient")
        self._client = xai_sdk.AsyncClient(
            api_key=self._settings.xai_api_key.get_secret_value(),
        )
        await self._client.__aenter__()
        self._http = httpx.AsyncClient(
            follow_redirects=False,
            timeout=httpx.Timeout(30.0, read=120.0),
        )
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    async def close(self) -> None:
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None
        if self._http:
            await self._http.aclose()
            self._http = None

    def reset_circuit_breaker(self) -> None:
        self._consecutive_failures = 0

    def _check_circuit_breaker(self) -> None:
        if self._consecutive_failures >= self._CIRCUIT_BREAKER_THRESHOLD:
            raise GrokAPIUnavailableError(
                f"Circuit breaker open after {self._consecutive_failures} consecutive failures"
            )

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        image_url: str | None = None,
    ) -> ImageResult:
        """Generate a still image via Grok Imagine Image API."""
        self._check_circuit_breaker()
        assert self._client is not None, "Client not initialized — use async with"

        try:
            grok_image_model = self._settings.preview_model_grok
            response = await self._client.image.sample(
                prompt=prompt,
                model=grok_image_model,
                image_url=image_url,
                aspect_ratio=aspect_ratio,  # type: ignore[arg-type]  # SDK expects Literal but we pass str
                image_format="url",
            )

            if not response.respect_moderation:
                raise GrokModerationBlockedError("Image blocked by content moderation")

            self._consecutive_failures = 0
            usage = getattr(response, "usage", None)
            await _cost_recorder.record(
                "grok", "image_gen", model=grok_image_model,
                tokens_in=getattr(usage, "prompt_tokens", None) if usage else None,
                tokens_out=getattr(usage, "completion_tokens", None) if usage else None,
            )
            return ImageResult(url=response.url)

        except (GrokModerationBlockedError, GrokAPIUnavailableError):
            raise
        except GenerationError:
            raise
        except Exception as e:
            error_str = str(e)
            if "moderation" in error_str.lower():
                raise GrokModerationBlockedError(error_str) from e
            self._consecutive_failures += 1
            self._check_circuit_breaker()
            raise GenerationError(f"Grok image generation failed: {error_str[:200]}") from e

    async def generate_clip(
        self,
        prompt: str,
        duration: int,
        resolution: str,
        image_url: str | None = None,
    ) -> VideoClip:
        """Generate a video clip via Grok Imagine API with polling."""
        self._check_circuit_breaker()

        import grpc
        from xai_sdk.proto import deferred_pb2

        deadline = time.monotonic() + self._settings.poll_timeout_seconds

        assert self._client is not None, "Client not initialized — use async with"

        try:
            start_response = await self._client.video.start(
                prompt=prompt,
                model=self._settings.xai_video_model,
                duration=duration,
                resolution=resolution,  # type: ignore[arg-type]  # SDK expects Literal but we pass str
                image_url=image_url,
            )
            request_id = start_response.request_id
            logger.info("Grok video generation started: request_id=%s", request_id)

            while True:
                if time.monotonic() > deadline:
                    self._consecutive_failures += 1
                    raise GenerationTimeoutError(
                        f"Grok poll deadline exceeded ({self._settings.poll_timeout_seconds}s)"
                    )

                await asyncio.sleep(self._settings.poll_interval_seconds)

                poll_response = await self._client.video.get(request_id)

                if poll_response.status == deferred_pb2.DeferredStatus.DONE:
                    if not poll_response.HasField("response"):
                        self._consecutive_failures += 1
                        raise GenerationError("Deferred request completed but no response returned")

                    from xai_sdk.video import VideoResponse
                    video_resp = VideoResponse(poll_response.response)

                    if not video_resp.respect_moderation:
                        raise GrokModerationBlockedError("Video blocked by content moderation")

                    try:
                        url = video_resp.url
                    except ValueError as e:
                        if "moderation" in str(e).lower():
                            raise GrokModerationBlockedError(str(e)) from e
                        raise GenerationError(str(e)) from e

                    # Success — reset circuit breaker
                    self._consecutive_failures = 0
                    usage = getattr(video_resp, "usage", None)
                    await _cost_recorder.record(
                        "grok", "clip_gen", model="grok-imagine-video",
                        tokens_in=getattr(usage, "prompt_tokens", None) if usage else None,
                        tokens_out=getattr(usage, "completion_tokens", None) if usage else None,
                    )
                    return ClipResult(url=url, request_id=request_id)

                elif poll_response.status == deferred_pb2.DeferredStatus.EXPIRED:
                    self._consecutive_failures += 1
                    raise GenerationError("Deferred request expired")

                # PENDING — continue polling

        except (GrokModerationBlockedError, GrokAPIUnavailableError):
            # Don't increment circuit breaker for moderation blocks
            raise
        except GenerationError:
            raise
        except grpc.RpcError as e:
            code = e.code() if hasattr(e, 'code') else None
            details = e.details() if hasattr(e, 'details') else str(e)

            if code == grpc.StatusCode.UNAUTHENTICATED:
                raise GenerationError(f"Grok API authentication failed: {details}") from e
            elif code == grpc.StatusCode.NOT_FOUND:
                raise GenerationError(f"Grok model not found: {details}") from e
            elif code == grpc.StatusCode.RESOURCE_EXHAUSTED:
                # Rate limited — wait with exponential backoff before failing
                self._consecutive_failures += 1
                if self._consecutive_failures <= 2:
                    wait_secs = 30 * self._consecutive_failures  # 30s, 60s
                    logger.warning(
                        "Grok rate limited, waiting %ds before retry (attempt %d/3)",
                        wait_secs, self._consecutive_failures,
                    )
                    await asyncio.sleep(wait_secs)
                    # Don't raise — let the caller's retry loop handle it
                    raise GenerationError(f"Grok API rate limited (will retry after {wait_secs}s backoff)") from e
                raise GenerationError("Grok API rate limited (retries exhausted)") from e
            elif code in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED):
                self._consecutive_failures += 1
                self._check_circuit_breaker()
                raise GenerationError(f"Grok API unavailable: {details}") from e
            elif code == grpc.StatusCode.DATA_LOSS:
                raise GenerationError(f"Grok data loss (possible expired presigned URL): {details}") from e
            else:
                self._consecutive_failures += 1
                raise GenerationError(f"Grok API error: {details}") from e
        except Exception as e:
            if isinstance(e, (GenerationError, GenerationTimeoutError)):
                raise
            self._consecutive_failures += 1
            raise GenerationError(f"Unexpected error during generation: {str(e)[:200]}") from e

    async def download_video(self, url: str, dest: Path) -> None:
        """Download generated video with SSRF protection (4 layers).

        We pre-validate the resolved IP and prefer a pinned-IP request with the
        original Host header. If the CDN rejects that TLS handshake because SNI
        requires the hostname, we fall back to the validated hostname URL.
        """
        from ..common.url_validation import resolve_and_validate

        # Layer 1: Domain allowlist
        if not self._ALLOWED_DOMAINS_RE.match(url):
            raise GenerationError(f"URL domain not in allowlist: {url[:100]}")

        # Layer 2: IP validation
        try:
            validated_ip, hostname = await resolve_and_validate(url)
        except ValueError as e:
            raise GenerationError(f"SSRF validation failed: {e}") from e

        # Attempt DNS pinning by connecting to resolved IP with original Host.
        # Some CDNs require TLS SNI/hostname matching and may reject IP-based TLS.
        # In that case we fall back to hostname URL after pre-validation.
        parsed = urlparse(url)
        pinned_url = url.replace(f"://{parsed.hostname}", f"://{validated_ip}")
        assert self._http is not None, "Client not initialized — use async with"

        async def _download_stream(request_url: str, headers: dict[str, str] | None) -> int:
            async with self._http.stream("GET", request_url, headers=headers) as response:
                # Layer 3: No redirects
                if response.status_code >= 300:
                    raise GenerationError(f"Unexpected status: {response.status_code}")

                # Layer 4: Content-Type check
                ct = response.headers.get("content-type", "")
                if not ct.startswith("video/mp4"):
                    raise GenerationError(f"Unexpected content-type: {ct}")

                # Layer 5: Content-Length pre-check + streaming byte counter
                cl_str = response.headers.get("content-length", "0")
                try:
                    cl = int(cl_str)
                except ValueError:
                    cl = 0
                if cl > self._MAX_CADRE_SIZE:
                    raise GenerationError(f"Content-Length {cl} exceeds max {self._MAX_CADRE_SIZE}")

                downloaded = 0
                with open(dest, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        downloaded += len(chunk)
                        if downloaded > self._MAX_CADRE_SIZE:
                            raise GenerationError("Download exceeded max cadre size")
                        f.write(chunk)
                return downloaded

        try:
            downloaded = await _download_stream(pinned_url, headers={"Host": hostname})
        except httpx.ConnectError as exc:
            # DNS-pinned request can fail for multiple reasons (TLS SNI mismatch,
            # CDN rejecting IP-based connections, etc). Always fall back to hostname URL
            # since we already validated the IP.
            logger.warning(
                "grok_download_dns_pin_fallback: hostname=%s ip=%s reason=%s",
                hostname,
                validated_ip,
                str(exc)[:160],
            )
            downloaded = await _download_stream(url, headers=None)

        if downloaded == 0:
            dest.unlink(missing_ok=True)
            raise GenerationError("Downloaded zero bytes")
