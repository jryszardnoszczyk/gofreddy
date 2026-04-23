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
