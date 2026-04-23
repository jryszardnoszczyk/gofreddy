#!/usr/bin/env python3
"""Generate v1 audit-agent rubric YAMLs from the locked lens catalog.

Source:
    docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md

Outputs (data/):
    rubrics_phase0_meta.yaml      — 9 meta-frames woven into all 4 agents
    rubrics_findability.yaml      — Area 1 + Area 11 MarTech subset
    rubrics_narrative.yaml        — Areas 2 + 9 + 4
    rubrics_acquisition.yaml      — Areas 3 + 5 + 10
    rubrics_experience.yaml       — Areas 6 + 7 + 8 + Area 11 Compliance subset

Per LHR design doc follow-up #2 Step A. Mechanical parse of the locked v2 catalog;
applies the 18 post-reduction deletions + merges documented in the "Lens count per
area (verified, post-2026-04-23 v2 reductions)" table. No judgment content added
in v1 (no severity rubrics, no scoring guidance) — those live with v2 judges.
"""
from __future__ import annotations

import re
import sys
from collections import OrderedDict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG = REPO_ROOT / "docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md"
OUT_DIR = REPO_ROOT / "data"

# ── v2 reductions ─────────────────────────────────────────────────────────
# Lens IDs to drop entirely (cut from catalog — no merge target).
CUT_IDS: set[int] = {135, 154, 155}

# Lens IDs to drop because merged into another lens. Target noted for traceability.
MERGED_INTO: dict[int, int] = {
    153: 95,    # A1 schema stacking — @graph folded into 3-4 @types
    25: 12,     # A2 template library → free tools
    43: 12,     # A2 lead-magnet format → free tools
    29: 22,     # A6 signup flow → form CRO
    142: 22,    # A6 progressive profiling → form CRO
    34: 45,     # A6 logo wall → trust signals
    140: 45,    # A6 refund/guarantee → trust signals
    106: 105,   # A7 help-center completeness → docs maturity
    112: 105,   # A7 product-tour → docs maturity
    130: 105,   # A7 onboarding checklist → docs maturity
    117: 47,    # A10 competitive battlecards → sales-enablement
    136: 50,    # A10 sales content library → (target noted)
    138: 150,   # A10 channel partner tier → (target noted)
    # #149 is listed in Area 11 MarTech's catalog table but the reduction ledger
    # attributes it to Area 10. We drop it wherever it appears (here: Area 11
    # MarTech) to hit the authoritative 149-total. Catalog per-area counts differ
    # by ±1 from the reduction ledger as a result; the total is load-bearing.
    149: 20,    # Self-reported attribution (in A11 MarTech table, A10 in reduction ledger)
    76: 20,     # A11 event-naming discipline → attribution maturity
}

# ── Area → Agent mapping (v1 LHR design) ─────────────────────────────────
# Areas 1/2/3/4/5/6/7/8/9/10. Area 11 splits between Findability (MarTech subset)
# and Experience (Compliance subset).
AGENT_AREAS: dict[str, list[int]] = {
    "findability": [1],          # + Area 11 MarTech (added after area-11 split)
    "narrative":   [2, 9, 4],
    "acquisition": [3, 5, 10],
    "experience":  [6, 7, 8],    # + Area 11 Compliance (added after area-11 split)
}

# Phase 0 meta-frames — bullet list, no numeric IDs (Phase 0 IDs 1-5, 31, 38, 44, 52
# come from ranking doc 006, not the catalog areas view).
PHASE0_RANKING_IDS: list[int] = [1, 2, 3, 4, 5, 31, 38, 44, 52]


def read_catalog() -> str:
    if not CATALOG.exists():
        sys.exit(f"catalog not found: {CATALOG}")
    return CATALOG.read_text(encoding="utf-8")


# ── Parsers ───────────────────────────────────────────────────────────────
AREA_HEADER = re.compile(r"^### Area (\d+) — ([^\(]+) \((\d+) lenses\)\s*$", re.M)
PHASE0_HEADER = re.compile(r"^### Phase 0 — Meta-Diagnostic Frames \(9 lenses\)\s*$", re.M)
SUBSECTION_HEADER = re.compile(r"^\*\*([^*]+)\*\*\s*$", re.M)
TABLE_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*$", re.M)
BULLET = re.compile(r"^- (.+)$", re.M)


def parse_phase0(body: str) -> list[dict]:
    """Phase 0 uses a bullet list of 9 meta-frame names."""
    m = PHASE0_HEADER.search(body)
    if not m:
        sys.exit("phase 0 header not found")
    # Next heading terminates the section.
    start = m.end()
    next_heading = re.search(r"^### ", body[start:], re.M)
    section = body[start : start + next_heading.start()] if next_heading else body[start:]
    names = [b.group(1).strip() for b in BULLET.finditer(section)]
    if len(names) != 9:
        sys.exit(f"phase 0 expected 9 bullets, got {len(names)}")
    return [
        {"id": rid, "name": name, "area": "phase0"}
        for rid, name in zip(PHASE0_RANKING_IDS, names)
    ]


def parse_area(body: str, area_no: int) -> list[dict]:
    """Parse one area's lens table. Returns list of {id, name, area}."""
    pattern = re.compile(
        rf"^### Area {area_no} — [^\n]+\n.+?(?=^### Area \d+ —|^## )",
        re.M | re.S,
    )
    m = pattern.search(body)
    if not m:
        sys.exit(f"area {area_no} not found")
    section = m.group(0)
    lenses = []
    for row in TABLE_ROW.finditer(section):
        rid = int(row.group(1))
        name = row.group(2).strip()
        lenses.append({"id": rid, "name": name, "area": area_no})
    return lenses


def parse_area_11(body: str) -> tuple[list[dict], list[dict]]:
    """Area 11 has two bolded sub-sections: MarTech (14) + Compliance (14).

    Returns (martech_lenses, compliance_lenses).
    """
    m = re.search(r"^### Area 11 — [^\n]+\n.+?(?=^### |^## )", body, re.M | re.S)
    if not m:
        sys.exit("area 11 not found")
    section = m.group(0)

    # Split on the two bolded sub-headers.
    subs = list(SUBSECTION_HEADER.finditer(section))
    if len(subs) < 2:
        sys.exit(f"area 11 sub-headers: got {len(subs)}, expected 2+")

    martech_start = subs[0].end()
    compliance_start = subs[1].end()
    martech_block = section[martech_start : subs[1].start()]
    compliance_block = section[compliance_start:]

    def _rows(block: str, area_tag: str) -> list[dict]:
        return [
            {"id": int(r.group(1)), "name": r.group(2).strip(), "area": area_tag}
            for r in TABLE_ROW.finditer(block)
        ]

    return _rows(martech_block, "11_martech"), _rows(compliance_block, "11_compliance")


def apply_reductions(lenses: list[dict]) -> list[dict]:
    """Drop cut IDs and merged-into sources. Target lenses (e.g. #12, #22, #45,
    #105, #20, #47, #50, #150, #95) stay in place; the catalog row is the survivor.
    """
    kept: list[dict] = []
    for lens in lenses:
        if lens["id"] in CUT_IDS:
            continue
        if lens["id"] in MERGED_INTO:
            continue
        kept.append(lens)
    return kept


# ── Bundle parsers ────────────────────────────────────────────────────────
# Triggers: first match wins — prefer the bolded form, fall back to plain.
TRIGGER_LINE = re.compile(r"^(?:\*\*Triggers on:\*\*|Triggers on:)\s*(.+?)\s*$", re.M)
BUNDLE_ENTRY = re.compile(r"^### (?:Vertical|Geo Bundle|Segment Bundle) (\d+):\s*([^\n]+)$", re.M)


def _slugify(name: str) -> str:
    """Short machine-friendly identifier from a bundle name."""
    # Keep the lead token; drop bracketed qualifiers.
    base = re.sub(r"\s*\([^)]*\)\s*", " ", name).strip()
    # First 1-2 meaningful words only.
    words = re.findall(r"[A-Za-z0-9]+", base.lower())
    stop = {"the", "a", "an", "and", "or", "of", "for", "to", "in", "on", "vs"}
    picked = [w for w in words if w not in stop][:2]
    return "_".join(picked) if picked else base.lower()


def _extract_bullets(block: str) -> list[str]:
    """Bullet lines that aren't meta — skip trigger lines + empty bullets."""
    out = []
    for line in block.splitlines():
        m = re.match(r"^-\s+(.+?)\s*$", line)
        if not m:
            continue
        text = m.group(1).strip()
        if not text or text.lower().startswith("triggers on"):
            continue
        out.append(text)
    return out


def parse_bundle_group(body: str, group_header: str) -> list[dict]:
    """Extract bundles under a `## <group_header>` section.

    group_header examples: "Vertical Bundles", "Geo-Conditional Bundles",
    "Segment-Conditional Bundles (added 2026-04-22 v2)" — match on prefix.
    """
    # Find the group section (between its ## heading and the next ## heading).
    m = re.search(rf"^## {re.escape(group_header)}[^\n]*\n(.+?)(?=^## |\Z)", body, re.M | re.S)
    if not m:
        sys.exit(f"bundle group not found: {group_header}")
    section = m.group(1)

    # Split into per-bundle blocks.
    entries = list(BUNDLE_ENTRY.finditer(section))
    bundles = []
    for i, entry in enumerate(entries):
        start = entry.end()
        end = entries[i + 1].start() if i + 1 < len(entries) else len(section)
        block = section[start:end]

        number = int(entry.group(1))
        title = entry.group(2).strip()

        trigger_match = TRIGGER_LINE.search(block)
        trigger = trigger_match.group(1).strip() if trigger_match else ""
        # If the trigger is on a line starting with `-`, strip the bullet marker.
        trigger = re.sub(r"^-\s+", "", trigger)

        lenses = _extract_bullets(block)

        bundles.append({
            "id": f"{_slugify(title)}",
            "number": number,
            "name": title,
            "trigger": trigger,
            "lens_count": len(lenses),
            "lenses": lenses,
        })
    return bundles


def write_bundles(path: Path, bundle_type: str, bundles: list[dict], description: str) -> None:
    doc = OrderedDict([
        ("bundle_type", bundle_type),
        ("bundle_count", len(bundles)),
        ("total_lens_count", sum(b["lens_count"] for b in bundles)),
        ("description", description),
        ("source", "docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md"),
        ("bundles", [
            OrderedDict([
                ("id", b["id"]),
                ("number", b["number"]),
                ("name", b["name"]),
                ("trigger", b["trigger"]),
                ("lens_count", b["lens_count"]),
                ("lenses", b["lenses"]),
            ])
            for b in bundles
        ]),
    ])
    path.write_text(_yaml_dump(doc), encoding="utf-8")


# ── Preflight (Stage-1a deterministic checks) ─────────────────────────────
# The catalog lists ~25 deterministic checks in one paragraph under Stage-1a.
# Parser extracts the ` · ` (middle-dot) separated list.
PREFLIGHT_LIST = re.compile(
    r"Lenses to move:\s*(.+?)(?=- Saves|\Z)",
    re.S,
)


def parse_preflight(body: str) -> list[dict]:
    m = PREFLIGHT_LIST.search(body)
    if not m:
        sys.exit("preflight lens list not found")
    raw = m.group(1).strip()
    # Split on middle-dot ` · ` (U+00B7) surrounded by spaces.
    parts = [p.strip().rstrip(".") for p in re.split(r"\s*·\s*", raw) if p.strip()]
    return [{"id": f"preflight_{i+1:02d}", "name": p} for i, p in enumerate(parts)]


def write_preflight(path: Path, checks: list[dict]) -> None:
    doc = OrderedDict([
        ("stage", "1a"),
        ("check_count", len(checks)),
        ("description", (
            "Deterministic Python checks (DNS probes, well-known file fetches, "
            "JSON-LD parsing, header inspection, badge regex) that don't need LLM "
            "judgment. Output becomes context keys downstream agents read; saves "
            "~$10/audit vs routing through Sonnet."
        )),
        ("source", "docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md (Stage-1a pre-pass section)"),
        ("checks", [
            OrderedDict([("id", c["id"]), ("name", c["name"])])
            for c in checks
        ]),
    ])
    path.write_text(_yaml_dump(doc), encoding="utf-8")


# ── Emitters ──────────────────────────────────────────────────────────────
def _yaml_dump(obj) -> str:
    """Stable, readable YAML output: preserve key order via OrderedDict handler."""
    def repr_od(dumper, data):
        return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())
    yaml.add_representer(OrderedDict, repr_od, Dumper=yaml.SafeDumper)
    return yaml.dump(obj, Dumper=yaml.SafeDumper, sort_keys=False, width=100, allow_unicode=True)


def write_rubric(path: Path, agent: str, areas: list, lenses: list[dict], description: str) -> None:
    doc = OrderedDict([
        ("agent", agent),
        ("areas", areas),
        ("lens_count", len(lenses)),
        ("description", description),
        ("source", "docs/plans/2026-04-22-005-marketing-audit-lens-catalog.md"),
        ("lenses", [
            OrderedDict([("id", l["id"]), ("area", l["area"]), ("name", l["name"])])
            for l in sorted(lenses, key=lambda x: x["id"])
        ]),
    ])
    path.write_text(_yaml_dump(doc), encoding="utf-8")


def main() -> None:
    body = read_catalog()
    OUT_DIR.mkdir(exist_ok=True)

    # Phase 0
    phase0 = parse_phase0(body)
    write_rubric(
        OUT_DIR / "rubrics_phase0_meta.yaml",
        agent="all",
        areas=["phase0"],
        lenses=phase0,
        description=(
            "Meta-diagnostic frames woven into every agent prompt. "
            "Interpret findings, don't generate them — sit above tactical lenses."
        ),
    )

    # Areas 1-10 (Area 11 handled separately).
    area_lenses: dict[int, list[dict]] = {}
    for n in list(range(1, 11)):
        area_lenses[n] = parse_area(body, n)
    area_11_martech, area_11_compliance = parse_area_11(body)

    # Apply reductions.
    for n in area_lenses:
        area_lenses[n] = apply_reductions(area_lenses[n])
    area_11_martech = apply_reductions(area_11_martech)
    area_11_compliance = apply_reductions(area_11_compliance)

    # Assemble per-agent lens lists.
    agents = {
        "findability": (
            [1, "11_martech"],
            area_lenses[1] + area_11_martech,
            "Discoverability + Organic Search + MarTech/measurement stack. SEO + GEO report sections.",
        ),
        "narrative": (
            [2, 9, 4],
            area_lenses[2] + area_lenses[9] + area_lenses[4],
            "Content assets + Brand & Authority + Earned media. Brand/Narrative + part of Competitive sections.",
        ),
        "acquisition": (
            [3, 5, 10],
            area_lenses[3] + area_lenses[5] + area_lenses[10],
            "Paid media + Distribution/community + Sales/GTM. Distribution + Monitoring + part of Competitive sections.",
        ),
        "experience": (
            [6, 7, 8, "11_compliance"],
            area_lenses[6] + area_lenses[7] + area_lenses[8] + area_11_compliance,
            "Conversion + Activation + Lifecycle + Compliance/regulatory. Conversion + Lifecycle + MarTech-Attribution sections.",
        ),
    }

    counts = {}
    for agent, (areas, lenses, desc) in agents.items():
        write_rubric(OUT_DIR / f"rubrics_{agent}.yaml", agent, areas, lenses, desc)
        counts[agent] = len(lenses)

    total = sum(counts.values()) + len(phase0)
    print("Rubric YAMLs generated:")
    print(f"  data/rubrics_phase0_meta.yaml — {len(phase0)} meta-frames")
    for agent, n in counts.items():
        print(f"  data/rubrics_{agent}.yaml — {n} lenses")
    print(f"Total always-on: {total} (target 149)")
    if total != 149:
        print(f"  WARNING: total mismatch — expected 149, got {total}")
        sys.exit(2)

    # Bundle YAMLs — vertical / geo / segment
    vertical = parse_bundle_group(body, "Vertical Bundles")
    geo = parse_bundle_group(body, "Geo-Conditional Bundles")
    segment = parse_bundle_group(body, "Segment-Conditional Bundles")

    write_bundles(
        OUT_DIR / "bundles_vertical.yaml",
        "vertical",
        vertical,
        "Detection-gated: fires when prospect's vertical is detected via signals "
        "(Shopify fingerprint → e-com; HIPAA disclaimer → healthcare; etc.). "
        "Additive on top of always-on.",
    )
    write_bundles(
        OUT_DIR / "bundles_geo.yaml",
        "geo",
        geo,
        "Detection-gated: fires when prospect has presence in that geography "
        "via hreflang / ccTLD / currency / jurisdiction mentions. Each bundle "
        "contains mandatory regulatory lenses for operating there.",
    )
    write_bundles(
        OUT_DIR / "bundles_segment.yaml",
        "segment",
        segment,
        "Detection-gated: fires when prospect's customer-segment is detected "
        "via pricing-page structure, CTA language, signup flow, jobs-page role "
        "mix, enterprise-pricing language.",
    )

    # Preflight YAML
    preflight = parse_preflight(body)
    write_preflight(OUT_DIR / "preflight_lenses.yaml", preflight)

    print("Bundle YAMLs generated:")
    print(f"  data/bundles_vertical.yaml — {len(vertical)} bundles, "
          f"{sum(b['lens_count'] for b in vertical)} lenses")
    print(f"  data/bundles_geo.yaml — {len(geo)} bundles, "
          f"{sum(b['lens_count'] for b in geo)} lenses")
    print(f"  data/bundles_segment.yaml — {len(segment)} bundles, "
          f"{sum(b['lens_count'] for b in segment)} lenses")
    print(f"  data/preflight_lenses.yaml — {len(preflight)} deterministic checks")


if __name__ == "__main__":
    main()
