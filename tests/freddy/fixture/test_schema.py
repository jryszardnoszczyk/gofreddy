import pytest

from cli.freddy.fixture.schema import (
    FixtureSpec,
    FixtureValidationError,
    SuiteManifest,
    assert_pool_matches,
    parse_fixture_spec,
    parse_suite_manifest,
)


def test_fixture_spec_requires_version():
    with pytest.raises(FixtureValidationError, match="version"):
        parse_fixture_spec({
            "fixture_id": "geo-test",
            "client": "test",
            "context": "https://example.com",
        })


def test_fixture_spec_accepts_semver_version():
    spec = parse_fixture_spec({
        "fixture_id": "geo-test",
        "client": "test",
        "context": "https://example.com",
        "version": "1.0",
    })
    assert spec.fixture_id == "geo-test"
    assert spec.version == "1.0"


def test_fixture_spec_accepts_three_part_semver():
    spec = parse_fixture_spec({
        "fixture_id": "geo-test",
        "client": "test",
        "context": "https://example.com",
        "version": "1.2.3",
    })
    assert spec.version == "1.2.3"


def test_fixture_spec_rejects_non_semver_version():
    with pytest.raises(FixtureValidationError, match="semver"):
        parse_fixture_spec({
            "fixture_id": "geo-test",
            "client": "test",
            "context": "https://example.com",
            "version": "v1",
        })


def test_fixture_spec_rejects_empty_required():
    with pytest.raises(FixtureValidationError, match="client"):
        parse_fixture_spec({
            "fixture_id": "geo-test",
            "client": "",
            "context": "https://example.com",
            "version": "1.0",
        })


def test_fixture_spec_env_must_be_dict():
    with pytest.raises(FixtureValidationError, match="env"):
        parse_fixture_spec({
            "fixture_id": "geo-test",
            "client": "test",
            "context": "https://example.com",
            "version": "1.0",
            "env": ["not", "a", "dict"],
        })


def test_suite_manifest_requires_version():
    with pytest.raises(FixtureValidationError, match="version"):
        parse_suite_manifest({
            "suite_id": "test-v1",
            "domains": {"geo": [{
                "fixture_id": "x", "client": "y", "context": "z", "version": "1.0"
            }]},
        })


def test_suite_manifest_parses_with_version():
    manifest = parse_suite_manifest({
        "suite_id": "test-v1",
        "version": "1.0",
        "domains": {"geo": [{
            "fixture_id": "x", "client": "y", "context": "z", "version": "1.0"
        }]},
    })
    assert manifest.suite_id == "test-v1"
    assert manifest.version == "1.0"
    assert len(manifest.fixtures["geo"]) == 1


def test_assert_pool_matches_rejects_mismatch():
    manifest = parse_suite_manifest({
        "suite_id": "search-v1",
        "version": "1.0",
        "domains": {"geo": []},
    })
    with pytest.raises(ValueError, match="cross-pool"):
        assert_pool_matches("holdout-v1", manifest)


def test_assert_pool_matches_accepts_match():
    manifest = parse_suite_manifest({
        "suite_id": "search-v1",
        "version": "1.0",
        "domains": {"geo": []},
    })
    assert_pool_matches("search-v1", manifest)  # does not raise


# --- env expansion (2026-04-24 fix; opt-in via expand_env=True) -----------


def test_expand_env_false_preserves_literal(monkeypatch):
    """Default (expand_env=False) — ``${VAR}`` stays literal. Used by
    ``freddy fixture envs`` to surface missing env-var references."""
    monkeypatch.delenv("TEST_CTX", raising=False)
    spec = parse_fixture_spec({
        "fixture_id": "geo-t", "client": "t",
        "context": "${TEST_CTX}", "version": "1.0",
    })
    assert spec.context == "${TEST_CTX}"


def test_expand_env_true_resolves_set_var(monkeypatch):
    """expand_env=True replaces ``${VAR}`` with os.environ[VAR]."""
    monkeypatch.setenv("TEST_MONITORING_UUID", "ef702c19-9849-59bd-a2e4-74a25dba81d1")
    spec = parse_fixture_spec(
        {"fixture_id": "mon-t", "client": "t",
         "context": "${TEST_MONITORING_UUID}", "version": "1.0"},
        expand_env=True,
    )
    assert spec.context == "ef702c19-9849-59bd-a2e4-74a25dba81d1"


def test_expand_env_true_raises_on_unset(monkeypatch):
    """Unset var with expand_env=True → loud validation error, not literal."""
    monkeypatch.delenv("TEST_UNSET_CONTEXT", raising=False)
    with pytest.raises(FixtureValidationError, match="TEST_UNSET_CONTEXT"):
        parse_fixture_spec(
            {"fixture_id": "mon-t", "client": "t",
             "context": "${TEST_UNSET_CONTEXT}", "version": "1.0"},
            expand_env=True,
        )


def test_expand_env_true_resolves_env_field_values(monkeypatch):
    """env field values are also expanded, not just context."""
    monkeypatch.setenv("TEST_PLATFORM", "youtube")
    spec = parse_fixture_spec(
        {"fixture_id": "story-t", "client": "t", "context": "youtube",
         "version": "1.0",
         "env": {"AUTORESEARCH_STORYBOARD_PLATFORM": "${TEST_PLATFORM}"}},
        expand_env=True,
    )
    assert spec.env["AUTORESEARCH_STORYBOARD_PLATFORM"] == "youtube"


def test_expand_env_true_preserves_plain_strings():
    """No regression: non-``${...}`` strings pass through unchanged."""
    spec = parse_fixture_spec(
        {"fixture_id": "geo-t", "client": "t",
         "context": "https://example.com", "version": "1.0"},
        expand_env=True,
    )
    assert spec.context == "https://example.com"


def test_expand_env_handles_mixed_content(monkeypatch):
    """``${VAR}`` can appear mid-string; surrounding text preserved."""
    monkeypatch.setenv("TEST_HOST", "example.com")
    spec = parse_fixture_spec(
        {"fixture_id": "geo-t", "client": "t",
         "context": "https://${TEST_HOST}/page", "version": "1.0"},
        expand_env=True,
    )
    assert spec.context == "https://example.com/page"


def test_parse_suite_manifest_propagates_expand_env(monkeypatch):
    """Suite-level expand_env flows through to every fixture."""
    monkeypatch.setenv("TEST_MANIFEST_CTX", "abc-123")
    payload = {
        "suite_id": "t-v1", "version": "1.0",
        "domains": {
            "monitoring": [{"fixture_id": "m-a", "client": "c",
                            "context": "${TEST_MANIFEST_CTX}", "version": "1.0"}],
        },
    }
    m = parse_suite_manifest(payload, expand_env=True)
    assert m.fixtures["monitoring"][0].context == "abc-123"

    # Default (expand_env=False) preserves literal
    m2 = parse_suite_manifest(payload)
    assert m2.fixtures["monitoring"][0].context == "${TEST_MANIFEST_CTX}"
