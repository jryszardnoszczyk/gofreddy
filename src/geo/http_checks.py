"""HTTP-based GEO factor detection (robots.txt, llms.txt).

Uses Freddy's url_validation for SSRF protection on all URLs.
Redirects are rejected (SSRF prevention — robots.txt/llms.txt should not redirect).
"""

import asyncio
import logging
from urllib.parse import urlparse

import httpx
from gpyrobotstxt.robots_cc import RobotsMatcher

from ..common.url_validation import resolve_and_validate
from .models import Finding, Severity

logger = logging.getLogger(__name__)

# AI bot user-agents to check
AI_BOT_USER_AGENTS = (
    "GPTBot",  # OpenAI
    "ChatGPT-User",  # OpenAI browsing
    "ClaudeBot",  # Anthropic
    "PerplexityBot",  # Perplexity
    "Google-Extended",  # Google AI
)

HTTP_TIMEOUT = 5.0
MAX_ROBOTS_BYTES = 524_288  # 512KB — robots.txt should be small


async def detect_http_factors(
    final_url: str,
    client: httpx.AsyncClient | None = None,
) -> list[Finding]:
    """Detect factors requiring HTTP requests (parallel)."""
    should_close_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)

    try:
        ai_bot_result, llms_result = await asyncio.gather(
            _check_ai_bot_access(final_url, client),
            _check_llms_txt(final_url, client),
            return_exceptions=True,
        )

        findings: list[Finding] = []

        if isinstance(ai_bot_result, Exception):
            findings.append(
                Finding(
                    factor_id="ai_bot_access",
                    factor_name="AI Bot Access (robots.txt)",
                    detected=None,
                    severity=Severity.CRITICAL,
                    details=f"Unable to check: {type(ai_bot_result).__name__}",
                )
            )
        else:
            findings.append(ai_bot_result)

        if isinstance(llms_result, Exception):
            findings.append(
                Finding(
                    factor_id="llms_txt",
                    factor_name="llms.txt Presence",
                    detected=None,
                    severity=Severity.OPTIONAL,
                    details=f"Unable to check: {type(llms_result).__name__}",
                )
            )
        else:
            findings.append(llms_result)

        return findings
    finally:
        if should_close_client:
            await client.aclose()


async def _check_ai_bot_access(page_url: str, client: httpx.AsyncClient) -> Finding:
    """Check robots.txt for AI bot access."""
    try:
        parsed = urlparse(page_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        try:
            await resolve_and_validate(robots_url)
        except ValueError as e:
            return Finding(
                factor_id="ai_bot_access",
                factor_name="AI Bot Access (robots.txt)",
                detected=None,
                severity=Severity.CRITICAL,
                details=f"URL validation failed: {e}",
            )

        # SECURITY: follow_redirects=False prevents SSRF via redirect to internal IPs
        response = await client.get(robots_url, follow_redirects=False)

        # Reject redirects — robots.txt should not redirect
        if response.status_code in (301, 302, 303, 307, 308):
            return Finding(
                factor_id="ai_bot_access",
                factor_name="AI Bot Access (robots.txt)",
                detected=None,
                severity=Severity.CRITICAL,
                details="robots.txt returned a redirect (skipped for security)",
            )

        if response.status_code == 404:
            return Finding(
                factor_id="ai_bot_access",
                factor_name="AI Bot Access (robots.txt)",
                detected=True,
                severity=Severity.CRITICAL,
                evidence=("No robots.txt found - all bots allowed",),
                details="AI bots can crawl this site",
            )

        if response.status_code != 200:
            return Finding(
                factor_id="ai_bot_access",
                factor_name="AI Bot Access (robots.txt)",
                detected=None,
                severity=Severity.CRITICAL,
                details=f"robots.txt returned {response.status_code}",
            )

        robots_content = response.text[:MAX_ROBOTS_BYTES]
        matcher = RobotsMatcher()

        blocked_bots: list[str] = []
        allowed_bots: list[str] = []

        for bot in AI_BOT_USER_AGENTS:
            can_fetch = matcher.one_agent_allowed_by_robots(robots_content, bot, page_url)
            if can_fetch:
                allowed_bots.append(bot)
            else:
                blocked_bots.append(bot)

        all_allowed = len(blocked_bots) == 0
        all_blocked = len(allowed_bots) == 0

        if all_allowed:
            return Finding(
                factor_id="ai_bot_access",
                factor_name="AI Bot Access (robots.txt)",
                detected=True,
                severity=Severity.CRITICAL,
                evidence=tuple(f"{bot}: allowed" for bot in allowed_bots[:5]),
                details="All major AI bots can crawl this page",
            )
        elif all_blocked:
            return Finding(
                factor_id="ai_bot_access",
                factor_name="AI Bot Access (robots.txt)",
                detected=False,
                severity=Severity.CRITICAL,
                count=len(blocked_bots),
                evidence=tuple(f"{bot}: BLOCKED" for bot in blocked_bots),
                details="ALL AI bots are blocked - content invisible to AI",
            )
        else:
            return Finding(
                factor_id="ai_bot_access",
                factor_name="AI Bot Access (robots.txt)",
                detected=False,
                severity=Severity.CRITICAL,
                count=len(blocked_bots),
                evidence=tuple(f"{bot}: BLOCKED" for bot in blocked_bots),
                details=f"Some AI bots blocked: {', '.join(blocked_bots)}",
            )

    except asyncio.TimeoutError:
        return Finding(
            factor_id="ai_bot_access",
            factor_name="AI Bot Access (robots.txt)",
            detected=None,
            severity=Severity.CRITICAL,
            details="robots.txt check timed out",
        )
    except Exception as e:
        logger.debug("ai_bot_access_check_error", exc_info=e)
        return Finding(
            factor_id="ai_bot_access",
            factor_name="AI Bot Access (robots.txt)",
            detected=None,
            severity=Severity.CRITICAL,
            details=f"Unable to check: {type(e).__name__}",
        )


async def _check_llms_txt(page_url: str, client: httpx.AsyncClient) -> Finding:
    """Check for llms.txt presence at domain root."""
    try:
        parsed = urlparse(page_url)
        llms_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"

        try:
            await resolve_and_validate(llms_url)
        except ValueError as e:
            return Finding(
                factor_id="llms_txt",
                factor_name="llms.txt Presence",
                detected=None,
                severity=Severity.OPTIONAL,
                details=f"URL validation failed: {e}",
            )

        # SECURITY: follow_redirects=False prevents SSRF via redirect
        response = await client.get(llms_url, follow_redirects=False)

        # Reject redirects
        if response.status_code in (301, 302, 303, 307, 308):
            return Finding(
                factor_id="llms_txt",
                factor_name="llms.txt Presence",
                detected=False,
                severity=Severity.OPTIONAL,
                details="llms.txt returned a redirect (skipped)",
            )

        if response.status_code == 200:
            content = response.text[:MAX_ROBOTS_BYTES]
            content_length = len(content)
            return Finding(
                factor_id="llms_txt",
                factor_name="llms.txt Presence",
                detected=True,
                severity=Severity.OPTIONAL,
                count=content_length,
                evidence=(f"Found llms.txt ({content_length} bytes)",),
                details="llms.txt present - AI-friendly documentation",
            )
        else:
            return Finding(
                factor_id="llms_txt",
                factor_name="llms.txt Presence",
                detected=False,
                severity=Severity.OPTIONAL,
                details="No llms.txt found (emerging standard)",
            )

    except asyncio.TimeoutError:
        return Finding(
            factor_id="llms_txt",
            factor_name="llms.txt Presence",
            detected=None,
            severity=Severity.OPTIONAL,
            details="llms.txt check timed out",
        )
    except Exception as e:
        logger.debug("llms_txt_check_error", exc_info=e)
        return Finding(
            factor_id="llms_txt",
            factor_name="llms.txt Presence",
            detected=None,
            severity=Severity.OPTIONAL,
            details=f"Unable to check: {type(e).__name__}",
        )
