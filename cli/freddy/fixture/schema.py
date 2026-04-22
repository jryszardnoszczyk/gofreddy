"""Fixture schema (structural + type validation); qualitative checks live in dryrun.py."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping


class FixtureValidationError(ValueError):
    """Raised when a fixture payload fails structural validation."""


_SEMVER_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")


@dataclass(frozen=True)
class FixtureSpec:
    fixture_id: str
    client: str
    context: str
    version: str
    max_iter: int = 3
    timeout: int = 300
    anchor: bool = False
    env: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SuiteManifest:
    suite_id: str
    version: str
    fixtures: Mapping[str, tuple[FixtureSpec, ...]]


def parse_fixture_spec(payload: Mapping[str, Any]) -> FixtureSpec:
    for required in ("fixture_id", "client", "context", "version"):
        value = payload.get(required)
        if not isinstance(value, str) or not value.strip():
            raise FixtureValidationError(
                f"fixture spec missing required string field: {required!r}"
            )
    version = str(payload["version"]).strip()
    if not _SEMVER_RE.match(version):
        raise FixtureValidationError(
            f"fixture version {version!r} must be semver (e.g. '1.0', '1.2.3')"
        )
    env_raw = payload.get("env", {})
    if not isinstance(env_raw, dict):
        raise FixtureValidationError("fixture 'env' must be a dict")
    return FixtureSpec(
        fixture_id=str(payload["fixture_id"]).strip(),
        client=str(payload["client"]).strip(),
        context=str(payload["context"]).strip(),
        version=version,
        max_iter=int(payload.get("max_iter", 3)),
        timeout=int(payload.get("timeout", 300)),
        anchor=bool(payload.get("anchor", False)),
        env={str(k): str(v) for k, v in env_raw.items()},
    )


def parse_suite_manifest(payload: Mapping[str, Any]) -> SuiteManifest:
    suite_id = payload.get("suite_id")
    if not isinstance(suite_id, str) or not suite_id.strip():
        raise FixtureValidationError("suite_id is required and must be a string")
    suite_version = payload.get("version")
    if not isinstance(suite_version, str) or not _SEMVER_RE.match(suite_version):
        raise FixtureValidationError(
            f"suite {suite_id!r} version {suite_version!r} must be semver"
        )
    domains_payload = payload.get("domains")
    if not isinstance(domains_payload, dict):
        raise FixtureValidationError("suite 'domains' must be a dict")
    fixtures: dict[str, tuple[FixtureSpec, ...]] = {}
    for domain, items in domains_payload.items():
        if not isinstance(items, list):
            raise FixtureValidationError(f"domain {domain!r} must be a list")
        fixtures[domain] = tuple(parse_fixture_spec(item) for item in items)
    return SuiteManifest(
        suite_id=suite_id.strip(),
        version=suite_version.strip(),
        fixtures=fixtures,
    )


def assert_pool_matches(pool: str, manifest: SuiteManifest) -> None:
    """Raise ValueError if --pool does not match manifest.suite_id.

    Shared guard used by refresh / refresh_all / dry-run / discriminate — all
    of which must reject cross-pool cache contamination before any cache I/O.
    """
    if pool != manifest.suite_id:
        raise ValueError(
            f"--pool {pool!r} does not match manifest.suite_id "
            f"{manifest.suite_id!r}. Pool and suite_id must agree to prevent "
            f"cross-pool cache contamination."
        )
