"""Phase 2 Unit 1 — sitemap SSRF guard splits DNS-failure from blocked-IP.

Background: the v009 GEO run failed-closed with `invalid_url` on every URL
because the sandboxed environment had no DNS, and the freddy CLI's local
SSRF guard collapsed `socket.gaierror` and "IP in blocked CIDR" both to
`ValueError`, then mapped any `ValueError` to `invalid_url`. The fix:

- `resolve_and_validate` raises `DNSResolutionFailed` (subclass of
  ValueError) when DNS lookup itself fails (transient / sandboxed),
- `resolve_and_validate` raises `BlockedIPRange` (subclass of ValueError)
  when DNS resolved but the IP is in a blocked CIDR,
- `sitemap_command` catches BlockedIPRange and emits `invalid_url`, but
  catches DNSResolutionFailed and falls through to `SitemapParser.parse`,
  which has its own httpx error handling.

Backward compat: both new classes still subclass ValueError, so existing
callers that catch the broad ValueError keep working unchanged.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

_repo_root = Path(__file__).resolve().parents[2]
for _p in (_repo_root, _repo_root / "cli"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from cli.freddy.commands import sitemap as sitemap_mod  # noqa: E402
from src.common.url_validation import (  # noqa: E402
    BlockedIPRange,
    DNSResolutionFailed,
)


# ---------------------------------------------------------------------------
# url_validation: distinguish DNS failure from blocked CIDR
# ---------------------------------------------------------------------------


def test_url_validation_distinguishes_dns_vs_blocked_ip():
    """Both classes must be importable and not collapsed to one another.

    They both subclass ValueError so legacy callers keep working, but each
    is a distinct type so new code can branch on intent.
    """
    # Distinct classes, neither is the other.
    assert DNSResolutionFailed is not BlockedIPRange
    assert not issubclass(DNSResolutionFailed, BlockedIPRange)
    assert not issubclass(BlockedIPRange, DNSResolutionFailed)

    # Backward compat: both inherit from ValueError.
    assert issubclass(DNSResolutionFailed, ValueError)
    assert issubclass(BlockedIPRange, ValueError)

    # Instances behave like ValueError for legacy `except ValueError:` paths.
    try:
        raise DNSResolutionFailed("no DNS")
    except ValueError as exc:
        assert isinstance(exc, DNSResolutionFailed)
        assert not isinstance(exc, BlockedIPRange)

    try:
        raise BlockedIPRange("blocked CIDR")
    except ValueError as exc:
        assert isinstance(exc, BlockedIPRange)
        assert not isinstance(exc, DNSResolutionFailed)


# ---------------------------------------------------------------------------
# sitemap_command behavior: fail-open on DNS, fail-closed on blocked CIDR
# ---------------------------------------------------------------------------


def _capture_emitted_error(captured_stderr: str) -> dict | None:
    """Pull a {"error": {"code": ..., "message": ...}} JSON record off stderr.

    `emit_error` writes one JSON object per line to stderr; the last line is
    typically the latest error.
    """
    last_obj = None
    for line in captured_stderr.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (ValueError, json.JSONDecodeError):
            continue
        if isinstance(obj, dict) and "error" in obj:
            last_obj = obj
    return last_obj


def test_sitemap_blocked_ip_emits_invalid_url(monkeypatch, capsys):
    """When resolve_and_validate raises BlockedIPRange, sitemap_command
    must emit `invalid_url` (preserves the SSRF guard's intent)."""
    monkeypatch.setattr(
        sitemap_mod,
        "resolve_and_validate",
        AsyncMock(side_effect=BlockedIPRange("blocked CIDR")),
    )
    # Make sure SitemapParser doesn't get called — and if it does, the test
    # blows up loudly so we know.
    monkeypatch.setattr(
        sitemap_mod,
        "SitemapParser",
        lambda *a, **k: pytest.fail(
            "SitemapParser should not be reached when guard rejects the URL"
        ),
    )

    with pytest.raises(SystemExit) as excinfo:
        sitemap_mod.sitemap_command(url="https://attacker.example.com", max_urls=10)

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    err = _capture_emitted_error(captured.err)
    assert err is not None, f"no JSON error record on stderr; stderr was: {captured.err!r}"
    assert err["error"]["code"] == "invalid_url"


def test_sitemap_dns_failure_does_not_emit_invalid_url(monkeypatch, capsys):
    """When resolve_and_validate raises DNSResolutionFailed (no-DNS sandbox),
    sitemap_command must NOT emit `invalid_url`. It should fall through to
    SitemapParser; if SitemapParser also fails, the error code must be
    distinct from `invalid_url`.
    """
    monkeypatch.setattr(
        sitemap_mod,
        "resolve_and_validate",
        AsyncMock(side_effect=DNSResolutionFailed("no DNS")),
    )

    # Provide a fake SitemapParser whose .parse() returns an empty inventory,
    # so we can observe that control flowed past the SSRF guard cleanly. This
    # is the "fall-through and SitemapParser handles it" success case.
    class _FakeInventory:
        entries: list = []
        sitemaps_parsed: list = []
        errors: list = []

    class _FakeParser:
        async def parse(self, url):
            return _FakeInventory()

    monkeypatch.setattr(sitemap_mod, "SitemapParser", lambda *a, **k: _FakeParser())

    # Should NOT raise SystemExit (no error emitted): the command runs to
    # completion and prints the normal JSON output to stdout.
    sitemap_mod.sitemap_command(url="https://reachable.example.com", max_urls=10)

    captured = capsys.readouterr()
    err = _capture_emitted_error(captured.err)
    # Either: no error at all (fall-through happy path), or — if a future
    # variant routes the SitemapParser failure through emit_error — the
    # code must not be `invalid_url`.
    if err is not None:
        assert err["error"]["code"] != "invalid_url", (
            f"DNS failure must not collapse to invalid_url; got {err!r}"
        )

    # The stdout should contain the normal sitemap JSON envelope (urls_found,
    # urls_returned, ...), proving we reached SitemapParser.
    assert "urls_found" in captured.out
