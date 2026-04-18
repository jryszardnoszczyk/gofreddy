from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def load_json_optional(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


def competitive_raw_competitor_names(raw_dir: Path) -> list[str]:
    names: set[str] = set()
    pattern = re.compile(r"^(?P<name>.+?)_(ads|detect|visibility|scrape(?:_home|_pricing)?)_raw$")
    for path in raw_dir.glob("*_raw.json"):
        stem = path.stem
        if stem.startswith("_client_baseline"):
            continue
        match = pattern.match(stem)
        if match:
            names.add(match.group("name"))
    return sorted(names)


def competitive_bundle_score(bundle: dict) -> int:
    score = 0
    if bundle.get("ads"):
        score += 3
    if bundle.get("visibility_results"):
        score += 2
    if bundle.get("detect"):
        score += 2
    if bundle.get("scrape_pages"):
        score += 1
    return score


def competitive_domain_from_bundle(name: str, bundle: dict) -> str:
    ads_payload = bundle.get("ads_payload")
    if isinstance(ads_payload, dict):
        domain = str(ads_payload.get("domain", "")).strip()
        if domain:
            return domain

    for page in bundle.get("scrape_pages", []):
        if isinstance(page, dict):
            for key in ("final_url", "url"):
                raw = str(page.get(key, "")).strip()
                if raw:
                    parsed = urlparse(raw)
                    if parsed.netloc:
                        return parsed.netloc.removeprefix("www.")

    detect_payload = bundle.get("detect")
    if isinstance(detect_payload, dict):
        for key in ("final_url", "url"):
            raw = str(detect_payload.get(key, "")).strip()
            if raw:
                parsed = urlparse(raw)
                if parsed.netloc:
                    return parsed.netloc.removeprefix("www.")

    fallback = name.strip().lower()
    return fallback if "." in fallback else f"{fallback}.com"


def competitive_display_name(name: str, bundle: dict) -> str:
    visibility_payload = bundle.get("visibility_payload")
    if isinstance(visibility_payload, dict):
        brand = str(visibility_payload.get("brand", "")).strip()
        if brand:
            return brand
    return name.replace("-", " ").replace("_", " ").title()


def competitive_data_tier(bundle: dict) -> str:
    has_ads = bool(bundle.get("ads"))
    has_detect = bool(bundle.get("detect"))
    has_visibility = bool(bundle.get("visibility_results"))
    has_scrape = bool(bundle.get("scrape_pages"))

    if has_ads and has_detect and has_visibility:
        return "full"
    if has_ads or (has_visibility and has_scrape) or (has_detect and has_scrape) or (has_visibility and has_detect):
        return "partial"
    if has_scrape:
        return "scrape_only"
    if has_detect:
        return "detect_only"
    return "partial"


def rewrite_competitive_session_state(session_dir: Path, client: str, context: str, selected: list[dict]) -> None:
    total = len(selected)
    queue_lines = []
    for index, item in enumerate(selected, start=1):
        queue_lines.append(f"{index}. {item['display_name']} — {item['data_tier']} — 0/3 attempts")
    queue = "\n".join(queue_lines) if queue_lines else "(gather incomplete)"
    dead_ends = []
    for item in selected:
        if item["data_tier"] != "full":
            dead_ends.append(
                f"- {item['display_name']}: partial first-pass gather accepted in fresh mode ({item['data_tier']})."
            )
    dead_end_text = "\n".join(dead_ends) if dead_ends else "(none yet)"
    session_md = session_dir / "session.md"
    session_md.write_text(
        "\n".join(
            [
                f"# Session: {client}",
                f"Context: {context}",
                "",
                "## Current State",
                f"Competitors: {total} total | Data gathered: {total} | Analyzed: 0 | Synthesized: no",
                "",
                "## Priority Queue",
                queue,
                "",
                "## Cross-Competitor Insights (max 800 tokens)",
                "(waiting for ANALYZE phase — no cross-competitor synthesis yet)",
                "",
                "## Open Questions (max 500 tokens)",
                "- Which competitor shows the strongest observed ad deployment cadence once deployment dates are normalized?",
                "- Which observed gaps are real whitespace versus simple data-availability artifacts?",
                "",
                "## Dead Ends (max 300 tokens)",
                dead_end_text,
                "",
                "## Learnings",
                "- Fresh-mode competitive gather is complete once three usable competitor bundles are normalized; deeper source completion can happen in later phases.",
                "",
                "## Status: RUNNING",
                "",
            ]
        ),
        encoding="utf-8",
    )


def salvage_competitive_gather(session_dir: Path, client: str, context: str, iteration: int) -> bool:
    raw_dir = session_dir / "competitors"
    baseline = raw_dir / "_client_baseline.json"
    if not baseline.exists():
        return False

    names = competitive_raw_competitor_names(raw_dir)
    if not names:
        return False

    bundles = []
    for name in names:
        ads_payload = load_json_optional(raw_dir / f"{name}_ads_raw.json")
        detect_payload = load_json_optional(raw_dir / f"{name}_detect_raw.json")
        visibility_payload = load_json_optional(raw_dir / f"{name}_visibility_raw.json")

        scrape_pages = []
        for suffix in ("scrape_raw.json", "scrape_home_raw.json", "scrape_pricing_raw.json"):
            payload = load_json_optional(raw_dir / f"{name}_{suffix}")
            if payload is not None:
                scrape_pages.append(payload)

        bundle = {
            "name": name,
            "ads_payload": ads_payload,
            "ads": ads_payload.get("ads", []) if isinstance(ads_payload, dict) else [],
            "detect": detect_payload if isinstance(detect_payload, dict) else {},
            "visibility_payload": visibility_payload,
            "visibility_results": visibility_payload.get("results", []) if isinstance(visibility_payload, dict) else [],
            "scrape_pages": scrape_pages,
        }
        if competitive_bundle_score(bundle) > 0:
            bundles.append(bundle)

    if len(bundles) < 3:
        return False

    bundles.sort(key=competitive_bundle_score, reverse=True)
    selected = bundles[:3]
    counts = {"full": 0, "partial": 0, "scrape_only": 0, "detect_only": 0}

    for bundle in selected:
        tier = competitive_data_tier(bundle)
        display_name = competitive_display_name(bundle["name"], bundle)
        domain = competitive_domain_from_bundle(bundle["name"], bundle)
        counts[tier] += 1
        normalized = {
            "name": display_name,
            "domain": domain,
            "data_tier": tier,
            "ads": bundle.get("ads", []),
            "visibility": {
                "queries": (
                    bundle["visibility_payload"].get("keywords", [])
                    if isinstance(bundle.get("visibility_payload"), dict)
                    else []
                ),
                "results": bundle.get("visibility_results", []),
            },
            "detect": bundle.get("detect", {}),
            "scrape": {"pages": bundle.get("scrape_pages", [])},
            "content": {"creators": [], "videos": []},
            "collected_at": datetime.now().astimezone().isoformat(),
        }
        bundle["data_tier"] = tier
        bundle["display_name"] = display_name
        (raw_dir / f"{bundle['name']}.json").write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")

    rewrite_competitive_session_state(session_dir, client, context, selected)

    result_entry = {
        "iteration": iteration,
        "type": "gather",
        "competitors": len(selected),
        "data_tiers": counts,
        "status": "done",
        "salvaged": True,
    }
    results_file = session_dir / "results.jsonl"
    with open(results_file, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(result_entry) + "\n")
    return True
