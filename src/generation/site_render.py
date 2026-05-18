"""Playwright-based site section renderer (U7b).

Consumed by `site_engine` (U15b) for SE-1/SE-5/SE-8 visual scoring +
SE-6/SE-7 hand-grading. Renders a section's HTML+CSS+JS inside a
host page sandbox that:

- Blocks all network egress except `data:` URIs (no SSRF, no external
  font CDN exfil, no metadata-endpoint pull).
- Disables WebRTC (no ICE-candidate leak channel).
- Waits for `document.fonts.ready` + 300ms settle so screenshots include
  brand-token fonts.
- Captures screenshot + DOM snapshot + console messages with source
  classification (lane-html / lane-css / lane-js / external / unknown).
- Refuses to launch unsandboxed on macOS without an explicit env
  escape hatch (`GOFREDDY_U7B_ALLOW_UNSANDBOXED=1`).

Playwright is a Python optional dep (already in the `[audit]` extra);
this module imports it lazily so callers that don't actually render
a section can still import the module (e.g., for type-checking, for
documenting the contract).

Per Pass-5 audit: U7c (axe-core + Lighthouse audit) was cut for v1.
SE-6/SE-7 are operator hand-graded against the screenshot + console
output captured here. Re-introduce U7c only if real a11y regressions
or perf budget drift surface.
"""

from __future__ import annotations

import logging
import os
import platform
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


ViewportSpec = tuple[str, int, int]  # (name, width, height)

DEFAULT_VIEWPORTS: tuple[ViewportSpec, ...] = (
    ("desktop", 1440, 900),
    ("mobile", 375, 812),
)


ConsoleSeverity = Literal["error", "warning", "info"]
ConsoleSource = Literal["lane-html", "lane-css", "lane-js", "external", "unknown"]


@dataclass(frozen=True)
class ConsoleMessage:
    """One captured browser console message."""

    severity: ConsoleSeverity
    text: str
    source: ConsoleSource


@dataclass(frozen=True)
class BlockedRequest:
    """One captured network request that the host-page filter blocked."""

    url: str
    reason: str  # "external_domain" | "rfc1918" | "metadata_endpoint" | ...


@dataclass(frozen=True)
class RenderResult:
    """Captured output from one section render across configured viewports."""

    screenshot_paths: dict[str, Path] = field(default_factory=dict)  # viewport name → path
    dom_snapshot: str = ""
    console_errors: list[ConsoleMessage] = field(default_factory=list)
    network_blocked: list[BlockedRequest] = field(default_factory=list)
    render_time_ms: int = 0
    degraded: bool = False
    degraded_reason: str | None = None


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class UnsafeRenderEnvironmentError(RuntimeError):
    """Raised when the host platform lacks the sandboxing posture v1 requires.

    Specifically: on non-Linux without `GOFREDDY_U7B_ALLOW_UNSANDBOXED=1`,
    SiteRenderer refuses to launch — Chromium without seccomp + user
    namespace + the network-block flags is an exploitation surface a
    hostile section HTML could weaponise.
    """


class PlaywrightNotInstalledError(RuntimeError):
    """Raised when `import playwright` fails — operator must
    `pip install playwright` + `playwright install chromium`."""


# ---------------------------------------------------------------------------
# Network classification helpers
# ---------------------------------------------------------------------------


# Cloud-metadata hostnames (resolve via DNS at provider — separate from IP-range check below).
_METADATA_HOSTS: frozenset[str] = frozenset({
    "metadata.google.internal",
    "metadata.google.com",
    "metadata.azure.com",
    "metadata.tencentyun.com",
    "metadata",  # AWS IMDSv1 single-label
})


def _classify_blocked_request(url: str) -> str:
    """Return a short reason tag for a blocked request URL.

    Per the 4-agent review (adv-2 T1-E + sec-3): use the ipaddress
    module to classify the URL's host so integer-encoded IPv4
    (http://2130706433/ = 127.0.0.1), bracketed IPv6 ([::1], [fd00::1]),
    IPv4-mapped IPv6 ([::ffff:169.254.169.254]), and 0.0.0.0 are all
    recognised. Plain hostname patterns (metadata.google.internal,
    metadata.azure.com) are also matched. Replaces the prior regex
    set which missed every IPv6 surface beyond fe80/fd00 and every
    integer-IP form.
    """
    from urllib.parse import urlparse
    import ipaddress

    if url.startswith(("data:", "blob:", "about:")):
        return "internal_scheme"

    try:
        parsed = urlparse(url)
    except ValueError:
        return "external_domain"

    host = (parsed.hostname or "").lower()
    if not host:
        return "external_domain"

    # Cloud-metadata hostname check (DNS-resolved at provider).
    if host in _METADATA_HOSTS:
        return "metadata_endpoint"

    # IP-form classification via the ipaddress module.
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # Not an IP — could be hostname like localhost.attacker.com which
        # is intentionally external_domain (DNS resolution to whatever).
        if host == "localhost":
            return "rfc1918"
        return "external_domain"

    # AWS / GCP / Azure metadata endpoint range.
    if ip in ipaddress.ip_network("169.254.169.254/32"):
        return "metadata_endpoint"
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        mapped = ip.ipv4_mapped
        if mapped in ipaddress.ip_network("169.254.169.254/32"):
            return "metadata_endpoint"
        if mapped.is_link_local or mapped.is_loopback or mapped.is_private:
            return "rfc1918"
    if ip.is_link_local or ip.is_loopback or ip.is_private or ip.is_unspecified:
        # is_unspecified covers 0.0.0.0 / ::
        return "rfc1918"
    return "external_domain"


def _classify_console_source(text: str, host_origin: str) -> ConsoleSource:
    """Best-effort source classification per the U7b contract.

    Lane-authored content is distinguished from external (blocked CDN
    font, broken `<link>`) via host-origin URL matching in the message
    body / stack source. False positives on classification widen
    `external` (safe default — won't trip the structural gate); the
    structural gate consumes `severity == 'error' AND source.startswith('lane-')`.
    """
    lowered = text.lower()
    if host_origin in text:
        if ".js" in lowered or "script" in lowered:
            return "lane-js"
        if ".css" in lowered or "style" in lowered:
            return "lane-css"
        return "lane-html"
    # Heuristic: external font / cdn references
    if any(s in lowered for s in ("cdn", "fonts.googleapis", "use.typekit")):
        return "external"
    return "unknown"


# ---------------------------------------------------------------------------
# SiteRenderer
# ---------------------------------------------------------------------------


def _host_page(brand_tokens_css: str, section_html: str, section_css: str, section_js: str) -> str:
    """Build the host page HTML that wraps the section under test.

    No analytics, no third-party scripts, no external font CDNs (per
    Threat Model). Brand tokens injected as a `<style>` block; the
    section's CSS comes after so it can override token values.
    """
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Section render</title>
  <style>{brand_tokens_css}</style>
  <style>{section_css}</style>
</head>
<body>
  <main>{section_html}</main>
  <script>{section_js}</script>
</body>
</html>
"""


class SiteRenderer:
    """Headless Chromium renderer with network egress fully blocked.

    Args:
        viewports: list of (name, width, height) to render. Defaults to
            desktop 1440×900 + mobile 375×812.
        timeout_ms: per-render timeout. Default 15s; Chromium launch
            failures contribute to the circuit breaker (3-fail → open).

    Raises:
        UnsafeRenderEnvironmentError: on non-Linux without the env escape.
        PlaywrightNotInstalledError: at render time when playwright is missing.
    """

    def __init__(
        self,
        viewports: list[ViewportSpec] | None = None,
        *,
        timeout_ms: int = 15_000,
        host_origin: str = "http://localhost",
    ) -> None:
        is_linux = platform.system() == "Linux"
        escape_set = os.environ.get("GOFREDDY_U7B_ALLOW_UNSANDBOXED") == "1"
        if not is_linux and not escape_set:
            raise UnsafeRenderEnvironmentError(
                f"SiteRenderer refuses to launch on {platform.system()}: "
                f"Chromium sandboxing requires Linux + seccomp + user "
                f"namespaces. For local dev, set "
                f"GOFREDDY_U7B_ALLOW_UNSANDBOXED=1 (logged warning) — "
                f"do NOT set this in production."
            )
        if not is_linux and escape_set:
            logger.warning(
                "SiteRenderer running on %s with sandboxing disabled "
                "(GOFREDDY_U7B_ALLOW_UNSANDBOXED=1) — DEV ONLY",
                platform.system(),
            )

        self.viewports = list(viewports) if viewports else list(DEFAULT_VIEWPORTS)
        self.timeout_ms = timeout_ms
        self.host_origin = host_origin
        self._launch_failures = 0
        self._breaker_open_until: float = 0.0

    # -----------------------------------------------------------------------
    # Public render entry point
    # -----------------------------------------------------------------------

    def render_section(
        self,
        section_html: str,
        section_css: str,
        section_js: str,
        brand_tokens_css: str,
        screenshot_dir: Path,
    ) -> RenderResult:
        """Render the section across configured viewports.

        Returns a RenderResult with screenshot paths + DOM snapshot +
        captured console errors + blocked-request log. `degraded=True`
        when an external request was blocked OR a non-fatal warning
        surfaced (e.g., font failed to load); the structural gate at
        the caller decides whether to fail the variant.

        Raises PlaywrightNotInstalledError when the playwright Python
        package is not importable.
        """
        if time.time() < self._breaker_open_until:
            raise RuntimeError(
                "SiteRenderer circuit breaker is OPEN (3+ recent Chromium "
                "launch failures). Wait for reset or fix the environment."
            )

        try:
            from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]
        except ImportError as exc:
            raise PlaywrightNotInstalledError(
                "playwright is not installed in this environment. Install "
                "via `uv sync --extra audit` (or pip install playwright) "
                "then run `playwright install chromium`."
            ) from exc

        screenshot_dir.mkdir(parents=True, exist_ok=True)
        host_html = _host_page(brand_tokens_css, section_html, section_css, section_js)
        screenshots: dict[str, Path] = {}
        console_errors: list[ConsoleMessage] = []
        network_blocked: list[BlockedRequest] = []
        dom_snapshot = ""
        degraded = False
        degraded_reason: str | None = None

        # Per the 4-agent review (adv-2 T1-E): pre-compute the allowed
        # (host, port) tuple so the route handler does an EXACT match
        # rather than a startswith prefix check that lets attacker
        # subdomains (localhost.attacker.com) bypass the audit.
        from urllib.parse import urlparse as _urlparse
        _host_parsed = _urlparse(self.host_origin)
        _allowed_host = (_host_parsed.hostname or "").lower()
        _allowed_port = _host_parsed.port

        start = time.time()
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    args=[
                        "--disable-features=NetworkService,DnsOverHttps,WebRTC,ServiceWorker",
                        "--disable-background-networking",
                        "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
                    ],
                )
                try:
                    for viewport_name, width, height in self.viewports:
                        ctx = browser.new_context(viewport={"width": width, "height": height})

                        # Per the 4-agent review (sec-4): route at the
                        # context level (NOT page level) so iframes,
                        # workers, and shared workers are captured by
                        # the audit. page.route only fires on the page.
                        def _route_handler(route, request, blocked=network_blocked):
                            url = request.url
                            if url.startswith(("data:", "blob:", "about:")):
                                route.continue_()
                                return
                            # Allow only our own host page — exact host
                            # + port match (no startswith bypass).
                            try:
                                u = _urlparse(url)
                                u_host = (u.hostname or "").lower()
                                u_port = u.port
                            except ValueError:
                                u_host = ""
                                u_port = None
                            if u_host == _allowed_host and u_port == _allowed_port:
                                route.continue_()
                                return
                            blocked.append(BlockedRequest(
                                url=url,
                                reason=_classify_blocked_request(url),
                            ))
                            route.abort()

                        ctx.route("**/*", _route_handler)
                        page = ctx.new_page()

                        # Console handler.
                        def _on_console(msg, errors=console_errors):
                            sev = msg.type
                            if sev not in ("error", "warning"):
                                return
                            source = _classify_console_source(msg.text, self.host_origin)
                            errors.append(ConsoleMessage(
                                severity=sev,  # type: ignore[arg-type]
                                text=msg.text,
                                source=source,
                            ))

                        page.on("console", _on_console)

                        page.set_content(host_html, timeout=self.timeout_ms)
                        try:
                            page.evaluate("document.fonts.ready")
                        except Exception:
                            logger.debug("document.fonts.ready failed; continuing")
                        page.wait_for_timeout(300)

                        out_path = screenshot_dir / f"{viewport_name}.png"
                        page.screenshot(path=str(out_path), full_page=False)
                        screenshots[viewport_name] = out_path

                        if not dom_snapshot:
                            dom_snapshot = page.content()

                        ctx.close()
                finally:
                    browser.close()

            self._launch_failures = 0
        except Exception as exc:
            self._launch_failures += 1
            if self._launch_failures >= 3:
                self._breaker_open_until = time.time() + 60
            raise

        if network_blocked:
            degraded = True
            degraded_reason = (
                f"{len(network_blocked)} external request(s) blocked; "
                f"first: {network_blocked[0].url}"
            )

        return RenderResult(
            screenshot_paths=screenshots,
            dom_snapshot=dom_snapshot,
            console_errors=console_errors,
            network_blocked=network_blocked,
            render_time_ms=int((time.time() - start) * 1000),
            degraded=degraded,
            degraded_reason=degraded_reason,
        )


__all__ = [
    "BlockedRequest",
    "ConsoleMessage",
    "DEFAULT_VIEWPORTS",
    "PlaywrightNotInstalledError",
    "RenderResult",
    "SiteRenderer",
    "UnsafeRenderEnvironmentError",
    "ViewportSpec",
    "_classify_blocked_request",
    "_classify_console_source",
]
