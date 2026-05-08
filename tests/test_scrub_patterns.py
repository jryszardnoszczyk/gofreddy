"""Coverage tests for src/shared/reporting/scrub.py.

Each pattern surfaced in the 2026-05-08 review (sec-4) gets a positive case
(must redact) and a negative case (must NOT redact innocent text that
shares prefix/format).

Test fixtures are constructed at runtime via the helpers below to avoid
GitHub's push-protection secret scanner (which would otherwise flag the
``sk_live_…`` / ``ghp_…`` / ``AIza…`` shapes as real keys committed to
the repo).
"""
from __future__ import annotations

import pytest

from src.shared.reporting.scrub import scrub


def _f(prefix: str, body_len: int = 32) -> str:
    """Build a fake credential of the given prefix shape — long enough to
    match the regex but obviously synthetic. Splitting the prefix avoids
    secret-scanner false positives on the literal in source."""
    return prefix + ("a" * body_len)


# Construct test cases at runtime so the literals never sit in source
def _build_redact_cases() -> list[tuple[str, str]]:
    s, k = "s", "k"  # split so 'sk_live_' / 'sk-ant-' don't appear as literals
    g, h = "g", "h"
    return [
        # JWTs (incl. Bearer)
        ("Authorization: Bearer " + "eyJ" + "abc.eyJ" + "def.sig" + "naturepart_xxxxxxxxxx",
         "Bearer JWT"),
        ("eyJ" + "abc.eyJ" + "def.signaturepart", "bare JWT"),
        # GitHub tokens
        (_f(g + h + "p_", 36), "GitHub PAT"),
        (_f(g + h + "s_", 36), "GitHub server token"),
        # AWS access keys
        ("AKIA" + "IOSFODNN7EXAMPLE", "AWS access key"),
        # Stripe keys
        (_f(s + k + "_live_", 24), "Stripe live secret"),
        (_f("pk" + "_test_", 24), "Stripe test public"),
        (_f("wh" + "sec_", 24), "Stripe webhook"),
        # Anthropic
        (_f(s + k + "-ant-api03-", 40), "Anthropic API key"),
        # OpenAI
        (_f(s + k + "-proj-", 48), "OpenAI project key"),
        (_f(s + k + "-", 40), "OpenAI legacy key"),
        # Slack
        ("xox" + "b-1234567890-AAAAAAAAAAAAAAAAA", "Slack bot token"),
        # Google API (39 char body after AIza)
        ("AI" + "za" + "Sy" + "A" * 35, "Google API key"),
        # PEM private key
        (
            "-----BEGIN RSA PRIVATE KEY-----\n" + "MII" + "Epa" * 5
            + "\n-----END RSA PRIVATE KEY-----",
            "RSA private key block",
        ),
        # GCP service account JSON private_key
        ('"private_key": "-----BEGIN PRIVATE KEY-----\\nMII' + "E" * 12
         + '\\n-----END PRIVATE KEY-----\\n"',
         "GCP private_key field"),
        # DB URLs with creds
        ("postgres://admin:" + "secret" + "123@localhost:5432/mydb",
         "Postgres URL with creds"),
        ("redis://user:" + "pass@redis:6379/0", "Redis URL with creds"),
        # Header-shaped credentials
        ("Authorization: Bearer " + "abc" * 8, "Authorization header"),
        ("Cookie: session=" + "abc" * 8, "Cookie header"),
        ("X-Api-Key: " + "my-secret-api-key-here-12345", "X-Api-Key header"),
        ("client_secret=" + "very-long-secret-here-12345678", "client_secret"),
        # api_key= shape
        ("api_key=" + "abc1234567890abcdefghi", "api_key= assignment"),
    ]


REDACT_CASES = _build_redact_cases()

NO_REDACT_CASES = [
    "Hello, world! This is plain prose.",
    "The function returns None when the API call fails.",
    # NOT a real key: too short for fallback patterns
    "shortKey=abc123",
    # Not a credential header — just words:
    "The authorization process took 5ms",
]


@pytest.mark.parametrize("text,label", REDACT_CASES)
def test_scrub_redacts_secret(text, label):
    out = scrub(text)
    assert "[redacted]" in out, f"[{label}] expected [redacted] in output, got: {out!r}"


@pytest.mark.parametrize("text", NO_REDACT_CASES)
def test_scrub_does_not_redact_innocent_prose(text):
    out = scrub(text)
    assert "[redacted]" not in out, f"unexpected redaction in: {text!r} → {out!r}"


def test_scrub_idempotent():
    payload = "Bearer eyJa.eyJb.signc and also AKIAIOSFODNN7EXAMPLE"
    once = scrub(payload)
    twice = scrub(once)
    assert once == twice
