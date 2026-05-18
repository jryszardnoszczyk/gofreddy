"""ClientConfig schema + loader + drift detection (U2)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from src.clients.config import (
    LINEAGE_AFFECTING_FIELDS,
    REVIEWER_ROUTING_CARVE_OUT_FIELDS,
    BrandAssetsConfig,
    ClientConfig,
    LocaleConfig,
    PrePublishReviewerConfig,
    PrePublishReviewerSecondaryConfig,
    SiteEngineConfig,
)
from src.clients.loader import (
    ClientConfigNotFoundError,
    check_config_drift,
    load_client_config,
    snapshot_client_config,
)


# ---------------------------------------------------------------------------
# Helpers — minimal valid config payloads for schema-level tests
# ---------------------------------------------------------------------------


def _minimal_valid_config_dict(**overrides) -> dict:
    """Return a minimal valid ClientConfig payload as a plain dict."""
    base = {
        "slug": "fixture-client",
        "display_name": "Fixture Client",
        "archetype": "b2b_saas",
        "voice_persona_ref": "fixture_persona",
        "reviewer_assist_checklists": ["gdpr_eu"],
        "enabled_channels": ["article_engine"],
        "pre_publish_reviewer": {
            "email": "reviewer@example.com",
            "display_name": "Fixture Reviewer",
            "sla": "48h_business_us",
        },
        "weekly_publish_target": 5,
        "brand_assets": {
            "style_guide": "fixture/brand/style-guide.md",
            "logo": "fixture/brand/logo.svg",
            "palette": "fixture/brand/palette.json",
        },
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Schema: ClientConfig — required fields, validators, model_validators
# ---------------------------------------------------------------------------


def test_minimal_valid_config_constructs() -> None:
    """A minimal payload (required fields only) constructs a valid model."""
    config = ClientConfig.model_validate(_minimal_valid_config_dict())
    assert config.slug == "fixture-client"
    assert config.archetype == "b2b_saas"
    # Defaults applied
    assert config.brand_strictness == "strict"
    assert config.locale.gl == "en"
    assert config.brief_consumption.top_k_per_run == 3
    assert config.pre_publish_reviewer_secondary is None
    assert config.site_engine is None
    assert config.archetype_stub_allowed is False


def test_voice_corpus_consent_defaults_from_archetype() -> None:
    """Per TD-33: b2c_aesthetics + b2b_regulated default True; b2b_saas + b2b_tech default False."""
    saas = ClientConfig.model_validate(_minimal_valid_config_dict(archetype="b2b_saas"))
    aesthetics = ClientConfig.model_validate(_minimal_valid_config_dict(archetype="b2c_aesthetics"))
    regulated = ClientConfig.model_validate(_minimal_valid_config_dict(archetype="b2b_regulated"))

    assert saas.voice_corpus_consent_required is False
    assert aesthetics.voice_corpus_consent_required is True
    assert regulated.voice_corpus_consent_required is True


def test_voice_corpus_consent_explicit_value_overrides_archetype_default() -> None:
    """An explicit YAML value beats the archetype-derived default."""
    config = ClientConfig.model_validate(_minimal_valid_config_dict(
        archetype="b2c_aesthetics",
        voice_corpus_consent_required=False,
    ))
    assert config.voice_corpus_consent_required is False


def test_archetype_must_be_one_of_four_v1_values() -> None:
    """Per TD-56: archetype Literal narrows to 4 values in v1."""
    with pytest.raises(ValidationError) as exc:
        ClientConfig.model_validate(_minimal_valid_config_dict(archetype="b2c_ecommerce"))
    assert "archetype" in str(exc.value)


def test_slug_must_be_non_whitespace() -> None:
    with pytest.raises(ValidationError):
        ClientConfig.model_validate(_minimal_valid_config_dict(slug="bad slug"))
    with pytest.raises(ValidationError):
        ClientConfig.model_validate(_minimal_valid_config_dict(slug=""))


def test_slug_rejects_path_traversal_components() -> None:
    """Per the 4-agent review (adv-5 T2-D): slug becomes part of paths
    like clients/<slug>/audit/events.jsonl — `..`, `/`, and other path
    components are rejected at schema-validation time."""
    for bad_slug in [
        "..",
        "../etc",
        "foo/bar",
        "/etc/passwd",
        "foo\x00bar",  # null byte
        "FOO",         # uppercase (regex requires lowercase)
        "-leading-hyphen",  # confused-for-CLI-flag
        "a" * 64,      # exceeds 63 chars
    ]:
        with pytest.raises(ValidationError) as exc:
            ClientConfig.model_validate(_minimal_valid_config_dict(slug=bad_slug))
        assert "slug" in str(exc.value).lower()


def test_slug_accepts_kebab_and_snake_case() -> None:
    for ok_slug in [
        "klinika-melitus",
        "dwf-poland",
        "_stub_b2b_tech",
        "a",
        "client_1",
        "client-2-prefix",
    ]:
        config = ClientConfig.model_validate(_minimal_valid_config_dict(slug=ok_slug))
        assert config.slug == ok_slug


def test_missing_required_field_raises_validation_error() -> None:
    """Per the plan U2 verification: missing required field → ValidationError
    with a field-specific message."""
    payload = _minimal_valid_config_dict()
    del payload["slug"]
    with pytest.raises(ValidationError) as exc:
        ClientConfig.model_validate(payload)
    assert "slug" in str(exc.value)


def test_reviewer_assist_checklists_must_be_length_one_in_v1() -> None:
    """Per D6 revised + TD-18: v1 supports a single rule_set per client."""
    # Empty
    with pytest.raises(ValidationError) as exc:
        ClientConfig.model_validate(_minimal_valid_config_dict(reviewer_assist_checklists=[]))
    assert "exactly 1 entry" in str(exc.value)

    # >1
    with pytest.raises(ValidationError) as exc:
        ClientConfig.model_validate(_minimal_valid_config_dict(
            reviewer_assist_checklists=["gdpr_eu", "medical_pl"],
        ))
    assert "exactly 1 entry" in str(exc.value)


def test_site_engine_required_when_channel_enabled() -> None:
    """site_engine in enabled_channels but no site_engine sub-config → ValidationError."""
    with pytest.raises(ValidationError) as exc:
        ClientConfig.model_validate(_minimal_valid_config_dict(
            enabled_channels=["article_engine", "site_engine"],
            # No site_engine sub-config
        ))
    assert "site_engine" in str(exc.value)


def test_site_engine_subconfig_constructs_when_channel_enabled() -> None:
    config = ClientConfig.model_validate(_minimal_valid_config_dict(
        enabled_channels=["site_engine"],
        site_engine={
            "target_url": "https://example.com",
            "sections_in_scope": ["hero", "value_prop"],
            "brand_tokens": "clients/fixture-client/brand/tokens.json",
            "codex_fallback": True,
            "weekly_section_target": 2,
        },
    ))
    assert config.site_engine is not None
    assert config.site_engine.target_url == "https://example.com"
    assert config.site_engine.sections_in_scope == ["hero", "value_prop"]


def test_archetype_stub_allowed_only_for_b2b_tech_in_v1() -> None:
    """Per the onboarded-vs-demonstrated distinction: v1 stub flag is reserved
    for b2b_tech only."""
    with pytest.raises(ValidationError) as exc:
        ClientConfig.model_validate(_minimal_valid_config_dict(
            archetype="b2b_saas",
            archetype_stub_allowed=True,
        ))
    assert "b2b_tech" in str(exc.value)

    # b2b_tech + stub_allowed=True is fine
    ClientConfig.model_validate(_minimal_valid_config_dict(
        archetype="b2b_tech",
        archetype_stub_allowed=True,
    ))


def test_model_is_frozen() -> None:
    """Per the plan U2: ClientConfig is frozen at load. Mutation must raise."""
    config = ClientConfig.model_validate(_minimal_valid_config_dict())
    with pytest.raises(ValidationError):
        config.archetype = "b2b_regulated"  # type: ignore[misc]


def test_secondary_reviewer_optional() -> None:
    """Per the plan U2 verification: missing pre_publish_reviewer_secondary → loader accepts."""
    config = ClientConfig.model_validate(_minimal_valid_config_dict())
    assert config.pre_publish_reviewer_secondary is None

    config = ClientConfig.model_validate(_minimal_valid_config_dict(
        pre_publish_reviewer_secondary={
            "email": "deputy@example.com",
            "display_name": "Deputy",
            "escalate_at_pct_sla": 50,
        },
    ))
    assert config.pre_publish_reviewer_secondary is not None
    assert config.pre_publish_reviewer_secondary.email == "deputy@example.com"


# ---------------------------------------------------------------------------
# Loader: load_client_config reads real client.yaml files
# ---------------------------------------------------------------------------


def test_load_klinika_melitus() -> None:
    """Per the plan U2 verification:
    python -c 'from src.clients.loader import load_client_config; c = load_client_config(...)'
    → c.archetype == 'b2c_aesthetics'"""
    config = load_client_config("klinika-melitus")
    assert config.slug == "klinika-melitus"
    assert config.archetype == "b2c_aesthetics"
    assert config.voice_persona_ref == "dr_maria"
    assert config.locale.gl == "pl"
    assert config.locale.requires_diacritic_normalization is True
    assert "medical_pl" in config.reviewer_assist_checklists
    assert "site_engine" in config.enabled_channels
    assert config.site_engine is not None
    assert "clinical_visuals" in config.content_denylist
    assert config.voice_corpus_consent_required is True  # derived from archetype
    assert config.brand_strictness == "permissive"


def test_load_dwf_poland() -> None:
    config = load_client_config("dwf-poland")
    assert config.slug == "dwf-poland"
    assert config.archetype == "b2b_regulated"
    assert config.voice_persona_ref == "partner_jamka"
    assert "legal_pl" in config.reviewer_assist_checklists
    assert config.weekly_publish_target == 3
    assert config.brand_strictness == "strict"
    assert config.voice_corpus_consent_required is True  # derived from archetype


def test_load_stub_b2b_tech() -> None:
    config = load_client_config("_stub_b2b_tech")
    assert config.archetype == "b2b_tech"
    assert config.archetype_stub_allowed is True
    assert config.weekly_publish_target == 0  # stub never publishes
    assert config.voice_corpus_consent_required is False  # explicit override


def test_load_unknown_slug_raises_client_config_not_found() -> None:
    with pytest.raises(ClientConfigNotFoundError) as exc:
        load_client_config("does-not-exist-anywhere")
    assert "client.yaml" in str(exc.value)
    assert "does-not-exist-anywhere" in str(exc.value)


def test_two_clients_share_voice_persona_ref_allowed() -> None:
    """Per the plan U2 verification: two clients referencing same persona_ref
    is allowed; provenance metadata is logged but no error."""
    # Build two configs that share a persona ref
    c1 = ClientConfig.model_validate(_minimal_valid_config_dict(
        slug="client-a", voice_persona_ref="shared_persona",
    ))
    c2 = ClientConfig.model_validate(_minimal_valid_config_dict(
        slug="client-b", voice_persona_ref="shared_persona",
    ))
    assert c1.voice_persona_ref == c2.voice_persona_ref == "shared_persona"


# ---------------------------------------------------------------------------
# Snapshot + drift detection — D7
# ---------------------------------------------------------------------------


def test_snapshot_writes_yaml_and_round_trips(tmp_path: Path) -> None:
    """snapshot_client_config writes a YAML file at the requested path; the
    file round-trips via yaml.safe_load to the same content shape."""
    config = ClientConfig.model_validate(_minimal_valid_config_dict())
    snap_path = tmp_path / "archive_article_engine" / "v042" / "client-config.snapshot.yaml"

    snapshot_client_config(config, snap_path)

    assert snap_path.is_file()
    loaded = yaml.safe_load(snap_path.read_text())
    assert loaded["slug"] == "fixture-client"
    assert loaded["archetype"] == "b2b_saas"


def test_snapshot_is_deterministic_for_identical_configs(tmp_path: Path) -> None:
    """Byte-identical snapshots for byte-identical configs (sort_keys=True)."""
    config = ClientConfig.model_validate(_minimal_valid_config_dict())
    p1 = tmp_path / "snap1.yaml"
    p2 = tmp_path / "snap2.yaml"
    snapshot_client_config(config, p1)
    snapshot_client_config(config, p2)
    assert p1.read_bytes() == p2.read_bytes()


def test_check_drift_no_change(tmp_path: Path) -> None:
    """Snapshot matches current → empty drift report."""
    config = ClientConfig.model_validate(_minimal_valid_config_dict())
    snap_path = tmp_path / "snapshot.yaml"
    snapshot_client_config(config, snap_path)

    report = check_config_drift(snap_path, config)
    assert report.has_any_drift is False
    assert report.fail_finalize_reason() is None


def test_check_drift_lineage_affecting_field_fails(tmp_path: Path) -> None:
    """Per D7: archetype is lineage-affecting. Drift → fail finalize."""
    original = ClientConfig.model_validate(_minimal_valid_config_dict(archetype="b2b_saas"))
    snap_path = tmp_path / "snapshot.yaml"
    snapshot_client_config(original, snap_path)

    drifted = ClientConfig.model_validate(_minimal_valid_config_dict(archetype="b2c_aesthetics"))
    report = check_config_drift(snap_path, drifted)

    assert report.has_lineage_drift is True
    assert any(d.field_path == "archetype" for d in report.lineage_affecting)
    reason = report.fail_finalize_reason()
    assert reason is not None and "archetype" in reason


def test_check_drift_reviewer_routing_carve_out_does_not_fail(tmp_path: Path) -> None:
    """Per D7: reviewer email change is a carve-out (vacation / illness /
    departure); drift logged but finalize continues."""
    original = ClientConfig.model_validate(_minimal_valid_config_dict())
    snap_path = tmp_path / "snapshot.yaml"
    snapshot_client_config(original, snap_path)

    drifted_payload = _minimal_valid_config_dict()
    drifted_payload["pre_publish_reviewer"]["email"] = "different@example.com"
    drifted = ClientConfig.model_validate(drifted_payload)

    report = check_config_drift(snap_path, drifted)
    assert report.has_lineage_drift is False  # carve-out, not lineage
    assert any(d.field_path == "pre_publish_reviewer" for d in report.reviewer_routing)
    assert report.fail_finalize_reason() is None  # carve-out does not fail


def test_check_drift_weekly_publish_target_is_carve_out(tmp_path: Path) -> None:
    """weekly_publish_target is reviewer-routing per D7."""
    original = ClientConfig.model_validate(_minimal_valid_config_dict(weekly_publish_target=5))
    snap_path = tmp_path / "snapshot.yaml"
    snapshot_client_config(original, snap_path)

    drifted = ClientConfig.model_validate(_minimal_valid_config_dict(weekly_publish_target=3))
    report = check_config_drift(snap_path, drifted)

    assert report.has_lineage_drift is False
    assert any(d.field_path == "weekly_publish_target" for d in report.reviewer_routing)


def test_check_drift_missing_snapshot_raises(tmp_path: Path) -> None:
    config = ClientConfig.model_validate(_minimal_valid_config_dict())
    with pytest.raises(FileNotFoundError):
        check_config_drift(tmp_path / "absent.yaml", config)


# ---------------------------------------------------------------------------
# D7 invariant — lineage + reviewer-routing field sets are disjoint
# ---------------------------------------------------------------------------


def test_d7_field_partitions_are_disjoint() -> None:
    """Lineage-affecting and reviewer-routing carve-out sets must not overlap —
    every field is either one or the other, never both. Catches the case
    where someone adds a field to both sets and the drift behavior is
    ambiguous."""
    overlap = LINEAGE_AFFECTING_FIELDS & REVIEWER_ROUTING_CARVE_OUT_FIELDS
    assert not overlap, f"D7 partitions overlap on: {sorted(overlap)}"
