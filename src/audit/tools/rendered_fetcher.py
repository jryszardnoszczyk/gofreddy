"""Playwright Chromium headless wrapper — rendered DOM + screenshots + console + network.

Master plan §4.4 — Tier-3 local detection. Required for ~25 lenses across
Areas 1, 6, 9 (paywall UX, popup CRO, demo-flow probes, accessibility scans,
AI-chat handoff timing, signup-flow CRO). Used by Stage 1a homepage seed +
Stage 2 Experience agent's per-page checks.

Public surface
--------------

    async with RenderedFetcher() as fetcher:
        result = await fetcher.fetch("https://example.com")
        # result.html, result.screenshot_path, result.console_errors,
        # result.network_log, result.degraded, result.degraded_reason

A single ``RenderedFetcher`` instance shares one Chromium browser context
across all ``fetch()`` calls in a Stage 1a or Stage 2 invocation — keeps
per-page wall-clock low (no relaunch per URL) while isolating per-page state
through ``new_page()`` per call.

Fail-soft: any exception (Playwright not installed, browser launch failure,
page nav failure) returns ``RenderResult(degraded=True, ...)`` instead of
raising. Stage 1a fan-out treats degraded results as partial signal.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class NetworkRequest:
    """One row of the network log (request → response pairing)."""

    url: str
    method: str
    status: int | None
    resource_type: str
    request_headers: dict[str, str] = field(default_factory=dict)
    response_headers: dict[str, str] = field(default_factory=dict)
    started_at: str = ""
    ended_at: str = ""
    failure: str | None = None


@dataclass
class RenderResult:
    """Output of a single ``fetch()`` call.

    ``html`` is the rendered DOM after JS execution + network-idle settle.
    ``screenshot_path`` is the on-disk PNG (only set if ``screenshot_dir``
    was passed to ``fetch()``).
    """

    url: str
    final_url: str = ""
    fetched_at: str = ""
    status: int | None = None
    html: str = ""
    title: str = ""
    screenshot_path: Path | None = None
    console_errors: list[str] = field(default_factory=list)
    console_warnings: list[str] = field(default_factory=list)
    network_log: list[NetworkRequest] = field(default_factory=list)
    timing_ms: dict[str, float] = field(default_factory=dict)
    degraded: bool = False
    degraded_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Stable JSON-serializable form (used by cache layer)."""
        return {
            "url": self.url,
            "final_url": self.final_url,
            "fetched_at": self.fetched_at,
            "status": self.status,
            "html": self.html,
            "title": self.title,
            "screenshot_path": str(self.screenshot_path) if self.screenshot_path else None,
            "console_errors": self.console_errors,
            "console_warnings": self.console_warnings,
            "network_log": [
                {
                    "url": r.url, "method": r.method, "status": r.status,
                    "resource_type": r.resource_type,
                    "request_headers": r.request_headers,
                    "response_headers": r.response_headers,
                    "started_at": r.started_at, "ended_at": r.ended_at,
                    "failure": r.failure,
                } for r in self.network_log
            ],
            "timing_ms": self.timing_ms,
            "degraded": self.degraded,
            "degraded_reason": self.degraded_reason,
        }


class RenderedFetcher:
    """Headless Chromium wrapper with shared browser across fetches.

    Use as an async context manager::

        async with RenderedFetcher() as fetcher:
            result = await fetcher.fetch("https://example.com")

    Or driven manually for finer control::

        fetcher = RenderedFetcher()
        await fetcher.start()
        try:
            r = await fetcher.fetch(url)
        finally:
            await fetcher.stop()

    Construction options:
        viewport: (width, height); default 1440x900.
        user_agent: override UA; default Chromium's stock UA + GoFreddy tag.
        timeout_ms: per-page navigation timeout; default 25000.
        ignore_https_errors: True by default (audits prospect sites where TLS
            misconfigs are common signal).
    """

    DEFAULT_VIEWPORT = (1440, 900)
    DEFAULT_TIMEOUT_MS = 25_000
    UA_TAG = "GoFreddy-Audit/1.0"

    def __init__(
        self,
        *,
        viewport: tuple[int, int] = DEFAULT_VIEWPORT,
        user_agent: str | None = None,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        ignore_https_errors: bool = True,
    ) -> None:
        self._viewport = viewport
        self._user_agent_override = user_agent
        self._timeout_ms = timeout_ms
        self._ignore_https_errors = ignore_https_errors
        self._playwright = None  # type: ignore[assignment]
        self._browser = None  # type: ignore[assignment]
        self._context = None  # type: ignore[assignment]
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "RenderedFetcher":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()

    async def start(self) -> None:
        """Launch Chromium + open the shared context."""
        try:
            from playwright.async_api import async_playwright
        except ImportError as e:
            logger.warning("playwright not installed: %s", e)
            self._playwright = None
            self._browser = None
            self._context = None
            return

        self._playwright = await async_playwright().start()
        try:
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Chromium launch failed: %s", e)
            await self._playwright.stop()
            self._playwright = None
            self._browser = None
            return

        ua = self._user_agent_override or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 " + self.UA_TAG
        )
        self._context = await self._browser.new_context(
            viewport={"width": self._viewport[0], "height": self._viewport[1]},
            user_agent=ua,
            ignore_https_errors=self._ignore_https_errors,
            bypass_csp=False,
        )

    async def stop(self) -> None:
        try:
            if self._context is not None:
                await self._context.close()
        except Exception as e:  # noqa: BLE001
            logger.debug("context.close suppressed: %s", e)
        try:
            if self._browser is not None:
                await self._browser.close()
        except Exception as e:  # noqa: BLE001
            logger.debug("browser.close suppressed: %s", e)
        try:
            if self._playwright is not None:
                await self._playwright.stop()
        except Exception as e:  # noqa: BLE001
            logger.debug("playwright.stop suppressed: %s", e)
        self._context = None
        self._browser = None
        self._playwright = None

    async def fetch(
        self,
        url: str,
        *,
        wait_until: str = "networkidle",
        screenshot_dir: Path | str | None = None,
        wait_after_ms: int = 0,
    ) -> RenderResult:
        """Render ``url`` + collect DOM + screenshot + console + network.

        Parameters
        ----------
        wait_until
            Playwright load-state target: ``"load"``, ``"domcontentloaded"``,
            ``"networkidle"`` (default — best for SPA homepages where a
            Marketing-Audit lens cares about post-JS state).
        screenshot_dir
            If set, a PNG of the rendered page is written here as
            ``<sha-of-url>.png`` and the path is recorded on the result.
        wait_after_ms
            Extra delay after wait_until — useful for late-firing analytics
            beacons (Hotjar / Segment / consent banners).
        """
        result = RenderResult(
            url=url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )
        if self._context is None:
            result.degraded = True
            result.degraded_reason = (
                "playwright unavailable (lib not installed or Chromium launch failed)"
            )
            return result

        from playwright.async_api import (  # local import keeps lib optional
            ConsoleMessage,
            Error as PWError,
            Request,
            Response,
            TimeoutError as PWTimeoutError,
        )

        page = await self._context.new_page()
        page.set_default_navigation_timeout(self._timeout_ms)
        page.set_default_timeout(self._timeout_ms)

        # Wire console + network listeners ASAP (before navigation).
        net_index: dict[str, NetworkRequest] = {}

        def _on_console(msg: ConsoleMessage) -> None:
            text = msg.text
            if msg.type == "error":
                result.console_errors.append(text)
            elif msg.type == "warning":
                result.console_warnings.append(text)

        def _on_request(req: Request) -> None:
            net_index[req.url + "|" + req.method] = NetworkRequest(
                url=req.url,
                method=req.method,
                status=None,
                resource_type=req.resource_type,
                request_headers=dict(req.headers),
                started_at=datetime.now(timezone.utc).isoformat(),
            )

        def _on_response(resp: Response) -> None:
            key = resp.url + "|" + resp.request.method
            row = net_index.get(key)
            if row is None:
                return
            row.status = resp.status
            row.response_headers = dict(resp.headers)
            row.ended_at = datetime.now(timezone.utc).isoformat()

        def _on_request_failed(req: Request) -> None:
            key = req.url + "|" + req.method
            row = net_index.get(key)
            if row is None:
                return
            row.failure = req.failure or "request_failed"

        page.on("console", _on_console)
        page.on("request", _on_request)
        page.on("response", _on_response)
        page.on("requestfailed", _on_request_failed)

        nav_started = datetime.now(timezone.utc)
        try:
            response = await page.goto(url, wait_until=wait_until)
            result.status = response.status if response else None
            result.final_url = page.url
            if wait_after_ms > 0:
                await page.wait_for_timeout(wait_after_ms)
            result.html = await page.content()
            result.title = await page.title()
            if screenshot_dir is not None:
                screenshot_dir = Path(screenshot_dir)
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                slug = _hash_url(url)
                target = screenshot_dir / f"{slug}.png"
                await page.screenshot(path=str(target), full_page=True)
                result.screenshot_path = target
        except PWTimeoutError as e:
            result.degraded = True
            result.degraded_reason = f"timeout: {e}"
        except PWError as e:
            result.degraded = True
            result.degraded_reason = f"playwright error: {type(e).__name__}: {e}"
        except Exception as e:  # noqa: BLE001 — never crash Stage 1a
            result.degraded = True
            result.degraded_reason = f"{type(e).__name__}: {e}"
        finally:
            try:
                await page.close()
            except Exception:  # noqa: BLE001
                pass
            elapsed_ms = (datetime.now(timezone.utc) - nav_started).total_seconds() * 1000
            result.timing_ms["total"] = round(elapsed_ms, 2)
            result.network_log = list(net_index.values())

        return result


def _hash_url(url: str) -> str:
    """Stable short slug for screenshot filenames."""
    import hashlib
    host = (urlparse(url).hostname or "page").replace(":", "-")
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    return f"{host}_{digest}"


__all__ = ["RenderedFetcher", "RenderResult", "NetworkRequest"]
