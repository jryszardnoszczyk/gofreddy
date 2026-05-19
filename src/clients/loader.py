"""Loader + run-manifest snapshot + drift detection for ClientConfig.

Three primary entry points:

  load_client_config(slug)
      Read `clients/<slug>/client.yaml`, validate against the
      `ClientConfig` schema, return a frozen instance.

  snapshot_client_config(config, snapshot_path)
      Write a deterministic YAML snapshot to the lane's run manifest dir
      (typically `autoresearch/archive_<lane>/v<NNN>/client-config.snapshot.yaml`).
      Snapshot is the source of truth at finalize time.

  check_config_drift(snapshot_path, current_config)
      Compare a snapshot to the current config-on-disk. Returns a
      ConfigDriftReport listing lineage-affecting diffs (which must fail
      finalize per D7) and reviewer-routing diffs (logged but tolerated).

Snapshot format intentionally matches the source YAML shape so a `diff`
between snapshot and source is human-readable. Per D7, lineage-affecting
fields fail loud; reviewer-routing carve-outs are logged + accepted.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from src.clients.config import (
    LINEAGE_AFFECTING_FIELDS,
    REVIEWER_ROUTING_CARVE_OUT_FIELDS,
    ClientConfig,
)

logger = logging.getLogger(__name__)


# Repo root resolution: `src/clients/loader.py` → `<repo>/src/clients/loader.py`,
# so two `.parent` calls land on `<repo>`. This module never runs from inside
# an installed wheel so the repo-relative resolution is fine.
_REPO_ROOT = Path(__file__).resolve().parents[2]


class ClientConfigNotFoundError(FileNotFoundError):
    """Raised when `clients/<slug>/client.yaml` does not exist."""


def _client_yaml_path(slug: str) -> Path:
    return _REPO_ROOT / "clients" / slug / "client.yaml"


def load_client_config(slug: str) -> ClientConfig:
    """Load + validate `clients/<slug>/client.yaml` into a frozen
    ClientConfig.

    Raises:
        ClientConfigNotFoundError: when the YAML file is missing.
        pydantic.ValidationError: when the YAML fails schema validation.
        yaml.YAMLError: when the YAML is malformed.
    """
    yaml_path = _client_yaml_path(slug)
    if not yaml_path.is_file():
        raise ClientConfigNotFoundError(
            f"clients/{slug}/client.yaml not found at {yaml_path}. "
            f"Verify the slug spelling or run the onboarding flow."
        )

    raw = yaml.safe_load(yaml_path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(
            f"clients/{slug}/client.yaml must contain a mapping at the top "
            f"level (got {type(raw).__name__}). Check for a stray list or scalar."
        )

    return ClientConfig.model_validate(raw)


def snapshot_client_config(config: ClientConfig, snapshot_path: Path) -> Path:
    """Write a deterministic YAML snapshot of `config` to `snapshot_path`.

    The snapshot directory is created if missing. Path-typed fields are
    serialized as strings so the snapshot survives YAML round-trips. The
    output is sort_keys-stable so byte-identical configs produce
    byte-identical snapshots (useful for diff + commit tracking).
    """
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    payload = config.model_dump(mode="json")
    snapshot_path.write_text(
        yaml.safe_dump(payload, sort_keys=True, default_flow_style=False)
    )
    return snapshot_path


@dataclass(frozen=True)
class FieldDrift:
    """A single field whose snapshot value diverges from the current value."""

    field_path: str
    snapshot_value: Any
    current_value: Any


@dataclass(frozen=True)
class ConfigDriftReport:
    """Result of comparing a snapshot ClientConfig to the current one.

    Per D7: `lineage_affecting` diffs must fail the lane's finalize step;
    `reviewer_routing` diffs are logged but tolerated (vacation /
    illness / departure should not destroy a multi-hour evolution run).
    Any drift outside both sets falls into `other` — the lane defaults
    to fail-loud (CLAUDE.md Rule 12) but the caller can choose to
    downgrade specific paths if needed.
    """

    lineage_affecting: list[FieldDrift] = field(default_factory=list)
    reviewer_routing: list[FieldDrift] = field(default_factory=list)
    other: list[FieldDrift] = field(default_factory=list)

    @property
    def has_lineage_drift(self) -> bool:
        return bool(self.lineage_affecting)

    @property
    def has_any_drift(self) -> bool:
        return bool(self.lineage_affecting or self.reviewer_routing or self.other)

    def fail_finalize_reason(self) -> str | None:
        """Returns the operator-readable reason a lane should fail finalize,
        or None if all drift is tolerated."""
        if not self.lineage_affecting and not self.other:
            return None
        diffs = self.lineage_affecting + self.other
        lines = [
            f"  - {d.field_path}: snapshot={d.snapshot_value!r} → current={d.current_value!r}"
            for d in diffs
        ]
        return (
            "Client config drift on lineage-affecting fields between run-start "
            "snapshot and finalize-time YAML:\n" + "\n".join(lines)
        )


def check_config_drift(
    snapshot_path: Path, current_config: ClientConfig
) -> ConfigDriftReport:
    """Compare a previously-written snapshot YAML to the current
    ClientConfig (typically reloaded at finalize time).

    Returns a `ConfigDriftReport` partitioning per-field diffs into
    lineage-affecting + reviewer-routing + other buckets per D7.
    """
    if not snapshot_path.is_file():
        raise FileNotFoundError(
            f"snapshot not found at {snapshot_path}; cannot compare drift."
        )

    snapshot_raw = yaml.safe_load(snapshot_path.read_text()) or {}
    current_raw = current_config.model_dump(mode="json")

    report = ConfigDriftReport()
    for field_name in sorted(set(snapshot_raw) | set(current_raw)):
        snap_value = snapshot_raw.get(field_name)
        curr_value = current_raw.get(field_name)
        if snap_value == curr_value:
            continue
        diff = FieldDrift(
            field_path=field_name,
            snapshot_value=snap_value,
            current_value=curr_value,
        )
        if field_name in LINEAGE_AFFECTING_FIELDS:
            report.lineage_affecting.append(diff)
        elif field_name in REVIEWER_ROUTING_CARVE_OUT_FIELDS:
            report.reviewer_routing.append(diff)
            logger.info(
                "client-config drift on reviewer-routing field %s "
                "(carve-out per D7; finalize continues): %r → %r",
                field_name, snap_value, curr_value,
            )
        else:
            report.other.append(diff)
    return report


__all__ = [
    "ClientConfigNotFoundError",
    "ConfigDriftReport",
    "FieldDrift",
    "check_config_drift",
    "load_client_config",
    "snapshot_client_config",
]
