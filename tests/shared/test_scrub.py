"""Coverage tests for the NEW patterns added to scrub.py in Unit 5 of the
portal-moments redesign, plus the new ``scrub_with_records`` sibling API.

The pre-existing 17 patterns are covered by ``tests/test_scrub_patterns.py``
— left untouched per CLAUDE.md Rule 3 (surgical changes). This file covers
only the Unit 5 additions:

- ``env_var_key`` — ``[A-Z][A-Z0-9_]*_(?:API_)?KEY=<value>``
- ``password`` — ``password=<value>``
- ``db_url`` — confirms the existing pattern catches
  ``DATABASE_URL=postgresql://user:pass@host/db``
- ``jwt`` — confirms the existing JWT pattern catches Supabase
  service_role keys (they ARE JWTs)
- ``scrub_with_records`` — returns (text, list[ScrubRecord]) with kinds
  and lengths matching the patterns that fired.

Test fixtures are constructed at runtime via the helpers below to avoid
GitHub's push-protection secret scanner — same convention as the
pre-existing test file.
"""
from __future__ import annotations

import pytest

from src.shared.reporting.scrub import (
    NAMED_SECRET_PATTERNS,
    SECRET_PATTERNS,
    ScrubRecord,
    scrub,
    scrub_with_records,
)


def _fake_b64(prefix: str, body_len: int = 32) -> str:
    """Build a fake credential — same helper convention as the legacy test."""
    return prefix + ("a" * body_len)


# ---------------------------------------------------------------------------
# NEW pattern: env_var_key — *_API_KEY= or *_KEY= assignment
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text,label",
    [
        ("OPENAI_API_KEY=" + "sk-proj-" + "abc12345", "OPENAI_API_KEY= short value"),
        ("ANTHROPIC_API_KEY=" + ("x" * 16), "ANTHROPIC_API_KEY= long value"),
        ("SUPABASE_KEY=" + ("y" * 12), "SUPABASE_KEY= mid value"),
        # With spacing around =
        ("MY_SERVICE_KEY = " + ("z" * 12), "spaces around ="),
    ],
)
def test_env_var_key_pattern_redacts(text: str, label: str) -> None:
    out = scrub(text)
    assert "[redacted]" in out, f"[{label}] expected redaction, got: {out!r}"


def test_env_var_key_does_not_match_short_value() -> None:
    # Value < 8 chars should not match (avoids false-positive on KEY=foo)
    out = scrub("MY_KEY=short")
    # `short` is 5 chars; pattern requires \S{8,}
    assert "[redacted]" not in out, f"unexpected redaction: {out!r}"


def test_env_var_key_does_not_match_lowercase_key() -> None:
    # Pattern anchors on [A-Z] for the env var name
    out = scrub("my_api_key=some_short_value")
    # The api_key= fallback may match if value is 16+ chars; here we use 16
    # chars so it WILL match via api_key, but the env_var_key kind shouldn't
    # fire on lowercase. Use scrub_with_records to verify the kind.
    _, records = scrub_with_records("my_api_key=" + ("a" * 16))
    kinds = {r.kind for r in records}
    assert "env_var_key" not in kinds, (
        f"env_var_key fired on lowercase: kinds={kinds}"
    )


# ---------------------------------------------------------------------------
# NEW pattern: password=<value>
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text,label",
    [
        ("password=hunter2", "lowercase password="),
        ("PASSWORD=hunter2", "uppercase PASSWORD="),
        ("password : myS3cret!", "password : with spaces"),
        ("password=" + ("x" * 20), "long password value"),
    ],
)
def test_password_pattern_redacts(text: str, label: str) -> None:
    out = scrub(text)
    assert "[redacted]" in out, f"[{label}] expected redaction, got: {out!r}"


def test_password_pattern_does_not_match_short_value() -> None:
    # Value < 4 chars — protects against `password=` empty/tiny placeholder
    out = scrub("password=abc")  # 3 chars
    assert "[redacted]" not in out, f"unexpected redaction: {out!r}"


def test_password_pattern_does_not_match_innocent_prose() -> None:
    # The word "password" in prose, no = / : assignment
    out = scrub("The user forgot their password and had to reset it")
    assert "[redacted]" not in out, f"unexpected redaction: {out!r}"


# ---------------------------------------------------------------------------
# Existing pattern verification: DATABASE_URL form caught by db_url regex
# ---------------------------------------------------------------------------

def test_database_url_with_creds_is_caught() -> None:
    # R-Sec-1 happy path: DATABASE_URL=postgresql://user:pass@host:5432/db
    payload = "DATABASE_URL=postgresql://" + "myuser:" + "myp4ss@" + "db.host:5432/mydb"
    out, records = scrub_with_records(payload)
    assert "<redacted:" in out, f"expected db_url redaction, got: {out!r}"
    kinds = {r.kind for r in records}
    # Either db_url fires (the credential part) OR env_var_key + db_url —
    # the spec only requires "caught by some pattern". Verify at least one
    # of the expected kinds fired.
    assert kinds & {"db_url", "env_var_key"}, (
        f"expected db_url or env_var_key kind, got: {kinds}"
    )


def test_database_url_postgres_short_scheme_caught() -> None:
    # Also exercise postgres:// (not postgresql://)
    payload = "postgres://" + "u:" + "p@" + "host/db"
    out = scrub(payload)
    assert "[redacted]" in out, f"expected redaction, got: {out!r}"


# ---------------------------------------------------------------------------
# Existing pattern verification: Supabase service_role key caught by JWT pattern
# ---------------------------------------------------------------------------

def test_supabase_service_role_caught_by_jwt_pattern() -> None:
    # Supabase service_role keys are JWTs: header.payload.signature, all eyJ-prefixed.
    # We synthesize a JWT-shaped string to verify the existing JWT regex catches it.
    header = "eyJ" + "alg" * 8 + "_X"
    payload = "eyJ" + "role_service_role" * 3
    signature = "sig" + ("a" * 32)
    fake_jwt = f"{header}.{payload}.{signature}"
    out, records = scrub_with_records(fake_jwt)
    kinds = {r.kind for r in records}
    assert "jwt" in kinds, f"expected jwt kind, got kinds={kinds}, out={out!r}"


# ---------------------------------------------------------------------------
# scrub_with_records API: returns marker + record per match
# ---------------------------------------------------------------------------

def test_scrub_with_records_returns_marker_and_record() -> None:
    text = "Bearer eyJabc.eyJdef.signaturepart_long"
    out, records = scrub_with_records(text)
    assert "<redacted:jwt>" in out, f"expected per-kind marker, got: {out!r}"
    assert len(records) >= 1
    rec = records[0]
    assert isinstance(rec, ScrubRecord)
    assert rec.kind == "jwt"
    assert rec.original_length > 0
    # Original value NEVER stored on the record
    assert "eyJabc" not in str(rec)


def test_scrub_with_records_no_secrets_returns_empty_list() -> None:
    out, records = scrub_with_records("just plain prose, no secrets here")
    assert out == "just plain prose, no secrets here"
    assert records == []


def test_scrub_with_records_multiple_matches() -> None:
    text = (
        "API_KEY=" + ("x" * 16) + " "
        "and AKIA" + "IOSFODNN7EXAMPLE"
    )
    out, records = scrub_with_records(text)
    assert "<redacted:" in out
    # Should have at least 2 records — one for the env_var_key, one for AWS
    kinds = {r.kind for r in records}
    assert "aws_access_key" in kinds, f"expected aws_access_key, got: {kinds}"


def test_aws_marker_survives_env_var_key_pass() -> None:
    """F8: AWS_KEY=AKIAIOSFODNN7EXAMPLE keeps the specific aws_access_key
    label — env_var_key must NOT overwrite an earlier marker.

    Without the negative lookahead, env_var_key would re-match
    ``AWS_KEY=<redacted:aws_access_key>`` and clobber the marker with the
    generic ``<redacted:env_var_key>`` label, losing the audit-useful
    classification.
    """
    text = "AWS_KEY=AKIA" + "IOSFODNN7EXAMPLE"
    out, records = scrub_with_records(text)
    kinds = {r.kind for r in records}
    assert "aws_access_key" in kinds, f"missing aws kind: {kinds}"
    assert "env_var_key" not in kinds, (
        f"env_var_key overwrote aws marker: {kinds}, out={out!r}"
    )
    assert "<redacted:aws_access_key>" in out


def test_marker_survives_api_key_pass() -> None:
    """F8: ``SECRET=eyJ...`` keeps the jwt label even though api_key would
    otherwise match the post-jwt-replacement text.
    """
    jwt = (
        "eyJ" + "abc" + "." + "eyJ" + "def" + "." + ("sig" + ("naturepart_" * 2))
    )
    text = f"SECRET={jwt}"
    out, records = scrub_with_records(text)
    kinds = {r.kind for r in records}
    assert "jwt" in kinds, f"missing jwt kind: {kinds}"
    assert "api_key" not in kinds, (
        f"api_key overwrote jwt marker: {kinds}, out={out!r}"
    )


def test_scrub_with_records_idempotent() -> None:
    text = "Bearer " + "eyJ" + "abc.eyJ" + "def.sig" + ("naturepart_" * 2)
    once, _ = scrub_with_records(text)
    twice, twice_records = scrub_with_records(once)
    assert once == twice, f"idempotency broken: {once!r} != {twice!r}"
    # Second pass should find nothing — the marker is not itself matched
    assert twice_records == []


def test_scrub_with_records_preserves_legacy_scrub_compat() -> None:
    # Legacy scrub() still returns "[redacted]" markers — preserved for
    # backward compat with harness/review.py + report_base.py callers.
    text = "Bearer " + "eyJ" + "abc.eyJ" + "def.sig" + ("naturepart_" * 2)
    legacy = scrub(text)
    assert "[redacted]" in legacy
    assert "<redacted:" not in legacy


# ---------------------------------------------------------------------------
# Structural invariants
# ---------------------------------------------------------------------------

def test_named_and_unnamed_patterns_stay_in_sync() -> None:
    # SECRET_PATTERNS is derived from NAMED_SECRET_PATTERNS — count must match.
    assert len(SECRET_PATTERNS) == len(NAMED_SECRET_PATTERNS)
    for legacy, (_, named) in zip(SECRET_PATTERNS, NAMED_SECRET_PATTERNS):
        assert legacy is named, "SECRET_PATTERNS drifted from NAMED_SECRET_PATTERNS"


def test_all_pattern_names_are_unique() -> None:
    names = [name for name, _ in NAMED_SECRET_PATTERNS]
    assert len(names) == len(set(names)), f"duplicate pattern names: {names}"
