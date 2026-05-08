"""MarTech fingerprinting via wappalyzer-next.

Master plan §4.4 — Tier-3 local detection. Used by Stage 1a
``stage_1_warmup`` to seed ``cache/martech_<hash>.json``; ~14 Area-11
MarTech lenses depend on this output, and 70+ lenses across Areas
6/7/8/10/11 + most vertical/segment bundles read it indirectly through the
Stage 2 Experience agent's reading guide.

Public surface
--------------

    fingerprint_martech_stack(url, *, scan_type="fast", timeout=20) -> dict

Returns a dict with keys:

    {
      "url": str,
      "fetched_at": iso-8601 utc,
      "scan_type": "fast" | "balanced" | "full",
      "raw_technologies": {tech_name: {confidence, version, categories, groups}},
      "groupings": {
          "analytics": [tech_names...],
          "cmp": [tech_names...],
          ...
      },
      "tech_count": int,
      "degraded": bool,            # True if scan failed or lib unavailable
      "degraded_reason": str | "",
    }

The ``groupings`` block applies ``data/martech_rules.yaml`` to the raw
wappalyzer detections — Stage 2 agents never see the underlying ~2500
wappalyzer entries; they reason about the marketing-meaningful groupings.

Day-1 spike outcome (2026-05-06)
--------------------------------
``wappalyzer-next`` v2.0.0 installed cleanly; ``analyze('https://shopify.com',
scan_type='fast')`` returned ``Shopify`` with confidence 100, plus 12 other
techs. ``analyze('https://hubspot.com')`` returned ``HubSpot`` with
confidence 100. Port path is the thin-wrapper plan, NOT the
fork-or-subprocess fallback paths discussed in §4.4 + A9.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_RULES_PATH = Path(__file__).resolve().parents[3] / "data" / "martech_rules.yaml"
_rules_cache: dict[str, Any] | None = None


def _load_rules() -> dict[str, Any]:
    global _rules_cache
    if _rules_cache is not None:
        return _rules_cache
    try:
        import yaml
    except ImportError as e:
        logger.warning("PyYAML missing — martech groupings disabled: %s", e)
        _rules_cache = {"groupings": {}, "overrides": {}}
        return _rules_cache
    if not _RULES_PATH.exists():
        logger.warning("martech_rules.yaml not found at %s", _RULES_PATH)
        _rules_cache = {"groupings": {}, "overrides": {}}
        return _rules_cache
    with _RULES_PATH.open("r", encoding="utf-8") as fh:
        _rules_cache = yaml.safe_load(fh) or {"groupings": {}, "overrides": {}}
    return _rules_cache


def _apply_groupings(
    technologies: dict[str, dict[str, Any]],
    rules: dict[str, Any],
) -> dict[str, list[str]]:
    """Roll wappalyzer detections into marketing-relevant groupings.

    A tech matches a group if EITHER its name OR any of its categories
    appears in the group's match list. A tech can land in multiple groups
    (Mixpanel is both ``analytics`` and ``product_analytics`` — that's
    intentional; agents downstream filter by group, not by tech).
    """
    groupings: dict[str, list[str]] = {}
    grouping_rules = rules.get("groupings", {}) or {}
    for group_name, match_list in grouping_rules.items():
        match_set = {m.lower() for m in match_list}
        hits: list[str] = []
        for tech_name, meta in technologies.items():
            tech_lower = tech_name.lower()
            cat_lowers = {c.lower() for c in meta.get("categories", [])}
            if tech_lower in match_set or cat_lowers & match_set:
                hits.append(tech_name)
        if hits:
            groupings[group_name] = sorted(hits)
    return groupings


def _apply_domain_overrides(
    url: str,
    groupings: dict[str, list[str]],
    rules: dict[str, Any],
) -> dict[str, list[str]]:
    """Apply per-domain forcing rules.

    Each override entry: ``"example.com": {"add": {"crm": ["X"]}, "remove": {"cmp": ["Y"]}}``
    """
    overrides = rules.get("overrides", {}) or {}
    if not overrides:
        return groupings
    host = (urlparse(url).hostname or "").lower()
    for pattern, ops in overrides.items():
        # Simple suffix match — sufficient for v1.
        if not host.endswith(pattern.lower().lstrip("*").lstrip(".")):
            continue
        for group, techs in (ops.get("add") or {}).items():
            groupings.setdefault(group, []).extend(techs)
            groupings[group] = sorted(set(groupings[group]))
        for group, techs in (ops.get("remove") or {}).items():
            if group in groupings:
                groupings[group] = sorted(t for t in groupings[group] if t not in techs)
                if not groupings[group]:
                    del groupings[group]
    return groupings


def _normalize_wappalyzer_output(raw: Any, url: str) -> dict[str, dict[str, Any]]:
    """Coerce ``wappalyzer.analyze`` output into ``{tech_name: meta}``.

    ``analyze()`` returns ``{url: {tech: meta}}``. We unwrap the outer URL key
    (which may be the redirected URL, not the input) and return the flat tech
    map. If the structure is unrecognized, return ``{}``.
    """
    if not isinstance(raw, dict):
        return {}
    if not raw:
        return {}
    # Single-URL form: {actual_url: {tech: meta}}.
    first_value = next(iter(raw.values()))
    if isinstance(first_value, dict) and any(
        isinstance(v, dict) and "confidence" in v for v in first_value.values()
    ):
        return first_value
    # Already-flat form: {tech: meta}.
    if any(isinstance(v, dict) and "confidence" in v for v in raw.values()):
        return raw
    return {}


def fingerprint_martech_stack(
    url: str,
    *,
    scan_type: str = "fast",
    timeout: int = 20,
) -> dict[str, Any]:
    """Detect web technologies + roll into marketing groupings.

    Parameters
    ----------
    url
        Target URL (typically the prospect's homepage).
    scan_type
        ``"fast"`` (HTTP GET only — default), ``"balanced"`` (adds 1 JS-rendered
        fallback), ``"full"`` (all pages walked). Stage 1a uses ``"fast"`` for
        homepage seed; future deeper scans can opt into ``"balanced"``.
    timeout
        Per-request timeout in seconds. wappalyzer-next's default is 30; we
        use 20 to keep Stage 1a wall-clock predictable.

    Behavior on failure: returns ``degraded=True`` with empty
    ``raw_technologies`` + ``groupings``. Never raises — Stage 1a fan-out
    treats the result as a partial signal alongside ~16 other adapters.
    """
    fetched_at = datetime.now(timezone.utc).isoformat()
    base = {
        "url": url,
        "fetched_at": fetched_at,
        "scan_type": scan_type,
        "raw_technologies": {},
        "groupings": {},
        "tech_count": 0,
        "degraded": False,
        "degraded_reason": "",
    }

    try:
        from wappalyzer import analyze
    except ImportError as e:
        logger.warning("wappalyzer-next not installed: %s", e)
        base["degraded"] = True
        base["degraded_reason"] = f"wappalyzer-next not installed: {e}"
        return base

    try:
        raw = analyze(url, scan_type=scan_type, timeout=timeout)
    except Exception as e:  # noqa: BLE001 — Stage 1a must never crash the run
        logger.warning("wappalyzer.analyze failed for %s: %s", url, e)
        base["degraded"] = True
        base["degraded_reason"] = f"analyze() raised: {type(e).__name__}: {e}"
        return base

    technologies = _normalize_wappalyzer_output(raw, url)
    if not technologies:
        base["degraded"] = True
        base["degraded_reason"] = "analyze() returned no technologies"
        return base

    rules = _load_rules()
    groupings = _apply_groupings(technologies, rules)
    groupings = _apply_domain_overrides(url, groupings, rules)

    base["raw_technologies"] = technologies
    base["groupings"] = groupings
    base["tech_count"] = len(technologies)
    return base


__all__ = ["fingerprint_martech_stack"]
