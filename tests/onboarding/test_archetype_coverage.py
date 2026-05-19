"""D11 archetype-coverage CI assertion (Plan Success Criterion #1).

Per plan §172:
  > "Holdout fixtures green per archetype, with ≥1 real-client-content
  >   fixture per archetype"

And §87-88:
  > "The D11 archetype-level CI assertion (≥1 real_client fixture)
  >   applies only to onboarded archetypes; `stub_allowed: true`
  >   archetypes are excluded."

This test makes the assertion programmatic: for every onboarded client
(archetype_stub_allowed=False), at least one eval-suite fixture must
exist that names the client + carries data_provenance='real_client'.

This is a structural assertion — it does NOT run the fixtures; only
verifies the architectural invariant holds at the file-system level.
A new onboarded client added without at least one real_client fixture
fails this test loud at CI.

Stub clients (b2b_tech via _stub_b2b_tech) are intentionally excluded.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.clients.config import ClientConfig
from src.clients.loader import load_client_config


_REPO_ROOT = Path(__file__).resolve().parents[2]
_CLIENTS_DIR = _REPO_ROOT / "clients"
_EVAL_SUITES_DIR = _REPO_ROOT / "autoresearch" / "eval_suites"


def _discover_onboarded_clients() -> list[ClientConfig]:
    """Walk clients/ for non-stub client.yaml files and load each.

    Onboarded = archetype_stub_allowed=False. Stub clients (only
    _stub_b2b_tech in v1) are excluded per plan §87 carve-out.
    fixture-client is an integration-test scaffold and is also excluded.
    """
    configs: list[ClientConfig] = []
    for client_dir in sorted(_CLIENTS_DIR.iterdir()):
        if not client_dir.is_dir():
            continue
        yaml_path = client_dir / "client.yaml"
        if not yaml_path.is_file():
            continue
        # Skip the fixture client used by test infra (not a real
        # production onboarding).
        if client_dir.name == "fixture-client":
            continue
        config = load_client_config(client_dir.name)
        if not config.archetype_stub_allowed:
            configs.append(config)
    return configs


def _fixtures_referencing_client(slug: str) -> list[dict]:
    """Return all eval-suite fixtures (across every suite JSON) that
    name this client slug.

    Eval suites have two shapes:
      - Standalone: top-level {"suite_id", "fixtures": {<lane>: [...]}}
      - search-v1.json: top-level {"suite_id", "fixtures": {<lane>: [...]}}
        with potentially multiple lane keys.
    """
    matches: list[dict] = []
    for suite_path in sorted(_EVAL_SUITES_DIR.glob("*.json")):
        try:
            data = json.loads(suite_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        fixtures_block = data.get("fixtures")
        if not isinstance(fixtures_block, dict):
            continue
        for _lane, fixture_list in fixtures_block.items():
            if not isinstance(fixture_list, list):
                continue
            for fixture in fixture_list:
                if not isinstance(fixture, dict):
                    continue
                if fixture.get("client") == slug:
                    # Carry the suite-level data_provenance if the
                    # per-fixture doesn't override.
                    provenance = (
                        fixture.get("data_provenance")
                        or data.get("data_provenance")
                    )
                    matches.append({
                        "suite": suite_path.name,
                        "fixture_id": fixture.get("fixture_id"),
                        "data_provenance": provenance,
                    })
    return matches


def test_at_least_one_onboarded_client_exists() -> None:
    """v1 ships with ≥1 onboarded client (Klinika + DWF per
    §Generalization Justification). A run where the test loop
    finds zero onboarded clients indicates _CLIENTS_DIR drift."""
    configs = _discover_onboarded_clients()
    assert len(configs) >= 1, (
        f"No onboarded clients found under {_CLIENTS_DIR}. v1 expects "
        f"Klinika Melitus + DWF Poland as the first cohort."
    )


def test_each_onboarded_client_has_real_client_fixture() -> None:
    """D11 enforcement: every non-stub client.yaml must have ≥1
    eval-suite fixture with data_provenance='real_client' that names
    the client by slug. New onboarded clients added without a fixture
    fail loud here, not silently in production runs."""
    configs = _discover_onboarded_clients()
    failures: list[str] = []
    for config in configs:
        fixtures = _fixtures_referencing_client(config.slug)
        real_client_fixtures = [
            f for f in fixtures
            if f.get("data_provenance") == "real_client"
        ]
        if not real_client_fixtures:
            all_fixtures_summary = (
                ", ".join(f["fixture_id"] or "?" for f in fixtures)
                if fixtures else "(no fixtures of any kind)"
            )
            failures.append(
                f"{config.slug} (archetype={config.archetype}): "
                f"no real_client fixture found. Found fixtures: "
                f"{all_fixtures_summary}"
            )
    assert not failures, (
        f"D11 archetype-coverage assertion failed:\n  "
        + "\n  ".join(failures)
        + "\n\nFix: author at least one eval-suite fixture per onboarded "
          "client with `data_provenance: 'real_client'` + `client: "
          "<slug>`. Synthetic stubs do not count toward D11."
    )


def test_each_onboarded_archetype_has_real_client_fixture() -> None:
    """Mirror at the archetype level: every onboarded archetype must
    have ≥1 real_client fixture (via any onboarded client of that
    archetype). Adding a new onboarded archetype without a fixture
    fails this test."""
    configs = _discover_onboarded_clients()
    archetypes_with_fixture: set[str] = set()
    for config in configs:
        fixtures = _fixtures_referencing_client(config.slug)
        if any(f.get("data_provenance") == "real_client" for f in fixtures):
            archetypes_with_fixture.add(config.archetype)

    all_onboarded_archetypes = {c.archetype for c in configs}
    missing = all_onboarded_archetypes - archetypes_with_fixture
    assert not missing, (
        f"Onboarded archetypes without real_client fixture coverage: "
        f"{sorted(missing)}. Author at least one real_client fixture "
        f"per onboarded archetype before v1 SHIP gate."
    )
