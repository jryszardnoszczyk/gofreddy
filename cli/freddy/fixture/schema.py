"""Fixture schema (structural + type validation); qualitative checks live in dryrun.py."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Mapping


class FixtureValidationError(ValueError):
    """Raised when a fixture payload fails structural validation."""


_SEMVER_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")
_ENV_REF_RE = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")


def _expand_env(value: str) -> str:
    """Expand ``${VAR}`` references in ``value`` against ``os.environ``.

    Mirrors the env-expansion that
    ``autoresearch.evaluate_variant._normalize_suite_manifest`` performs at
    load time, so fixtures loaded via the CLI refresh path (which bypasses
    that normalizer) behave identically.

    Missing env vars raise ``FixtureValidationError`` — silent fallback to
    the literal ``${...}`` sends malformed input to downstream APIs (the
    root cause of the 2026-04-24 monitoring priming run, where shopify/
    lululemon/notion fixtures sent ``${VAR}`` strings to xpoz and got
    validation_error back).
    """
    missing: list[str] = []

    def _sub(m: re.Match[str]) -> str:
        var = m.group(1)
        if var in os.environ and os.environ[var]:
            return os.environ[var]
        missing.append(var)
        return m.group(0)

    expanded = _ENV_REF_RE.sub(_sub, value)
    if missing:
        raise FixtureValidationError(
            f"fixture context references unset env var(s): "
            f"{', '.join(sorted(set(missing)))}"
        )
    return expanded


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


def parse_fixture_spec(
    payload: Mapping[str, Any], *, expand_env: bool = False,
) -> FixtureSpec:
    """Parse a fixture payload dict into a FixtureSpec.

    ``expand_env=True`` resolves ``${VAR}`` references in ``context`` and
    ``env`` values against os.environ — used by the refresh + session paths
    where fixture data hits real backends.

    ``expand_env=False`` (default) preserves literal ``${VAR}`` strings —
    used by ``freddy fixture {list, envs, validate}`` which deliberately
    surface missing env-var references (the `envs` command's whole job).
    """
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

    context = str(payload["context"]).strip()
    env_values = {str(k): str(v) for k, v in env_raw.items()}
    if expand_env:
        context = _expand_env(context)
        env_values = {k: _expand_env(v) for k, v in env_values.items()}

    return FixtureSpec(
        fixture_id=str(payload["fixture_id"]).strip(),
        client=str(payload["client"]).strip(),
        context=context,
        version=version,
        max_iter=int(payload.get("max_iter", 3)),
        timeout=int(payload.get("timeout", 300)),
        anchor=bool(payload.get("anchor", False)),
        env=env_values,
    )


def expand_fixture_env(spec: FixtureSpec) -> FixtureSpec:
    """Return a new FixtureSpec with ``${VAR}`` refs expanded against os.environ.

    Used by the refresh path to defer env-expansion until the target fixture
    is identified — so unset vars in *other* fixtures in the manifest don't
    block a refresh of a fixture whose own vars are all set.
    """
    new_context = _expand_env(spec.context)
    new_env = {k: _expand_env(v) for k, v in spec.env.items()}
    return FixtureSpec(
        fixture_id=spec.fixture_id,
        client=spec.client,
        context=new_context,
        version=spec.version,
        max_iter=spec.max_iter,
        timeout=spec.timeout,
        anchor=spec.anchor,
        env=new_env,
    )


def parse_suite_manifest(
    payload: Mapping[str, Any], *, expand_env: bool = False,
) -> SuiteManifest:
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
        fixtures[domain] = tuple(
            parse_fixture_spec(item, expand_env=expand_env) for item in items
        )
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
