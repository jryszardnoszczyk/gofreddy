#!/usr/bin/env python3
"""Build a deterministic GEO report and sidecars from session artifacts.

This salvages partial six-iteration sessions by converting optimized page files,
gap allocation, and results metadata into a scoreable report package.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


def _load_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


def _load_results(session_dir: Path) -> list[dict]:
    results_file = session_dir / "results.jsonl"
    if not results_file.exists():
        return []
    results = []
    for line in results_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return results


def _slug_to_label(slug: str) -> str:
    if slug in {"index", "home", "homepage"}:
        return "/"
    return "/" + slug.replace("-", " ").replace("_", " ")


def _extract_client(session_dir: Path) -> str:
    session_md = session_dir / "session.md"
    if session_md.exists():
        match = re.search(
            r"^# GEO\+SEO Session:\s*(.+)$",
            session_md.read_text(encoding="utf-8", errors="replace"),
            re.MULTILINE,
        )
        if match:
            return match.group(1).strip()
    return session_dir.name


def _extract_site(session_dir: Path) -> str:
    session_md = session_dir / "session.md"
    if session_md.exists():
        match = re.search(
            r"^## Site\s*$\n(.+)$",
            session_md.read_text(encoding="utf-8", errors="replace"),
            re.MULTILINE,
        )
        if match:
            return match.group(1).strip()
    return ""


def _extract_blocks(text: str) -> dict[str, int]:
    return {
        "intro": text.count("[INTRO]"),
        "faq": text.count("[FAQ]"),
        "howto": text.count("[HOWTO]"),
        "schema": text.count("[SCHEMA]"),
        "fill": text.count("[FILL]"),
        "techfix": text.count("[TECHFIX]"),
        "prune": text.count("[PRUNE]"),
        "tables": len(re.findall(r"^\|.+\|$", text, re.MULTILINE)),
        "questions": len(re.findall(r"(?m)^Q:\s+", text)),
    }


def _extract_techfix_types(text: str) -> list[str]:
    return re.findall(r"\[TECHFIX\]\s*type:\s*([a-z0-9_-]+)", text, re.IGNORECASE)


def _extract_questions(text: str) -> list[str]:
    return [q.strip() for q in re.findall(r"(?m)^Q:\s+(.+)$", text)]


_GENERIC_HEADINGS = {"faq", "faqs", "overview", "introduction", "intro", "summary", "conclusion", "about"}


def _extract_heading_targets(text: str) -> list[str]:
    headings = re.findall(r'placement:\s+(?:append-after|create-new-section)\s+"([^"]+)"', text)
    out: list[str] = []
    for heading in headings:
        cleaned = heading.strip()
        if not cleaned or cleaned.lower() in _GENERIC_HEADINGS:
            continue
        out.append(cleaned)
    return out


def _guess_query(page_data: dict, slug: str) -> str:
    title = str(page_data.get("title") or "").strip()
    h1s = page_data.get("h1s") or []
    if title:
        return title
    if isinstance(h1s, list) and h1s:
        return str(h1s[0]).strip()
    return slug.replace("-", " ").replace("_", " ")


def build_report(session_dir: Path) -> None:
    optimized_dir = session_dir / "optimized"
    optimized_files = sorted(optimized_dir.glob("*.md")) if optimized_dir.exists() else []
    if not optimized_files:
        return

    results = _load_results(session_dir)
    page_map = {}
    pages_dir = session_dir / "pages"
    if pages_dir.exists():
        for page_file in pages_dir.glob("*.json"):
            data = _load_json(page_file)
            if isinstance(data, dict):
                page_map[page_file.stem] = data

    gap_data = _load_json(session_dir / "gap_allocation.json")
    gap_map = {}
    if isinstance(gap_data, dict):
        for item in gap_data.get("allocations", []):
            if isinstance(item, dict):
                gap_map[item.get("slug", "")] = item

    visibility_data = _load_json(session_dir / "competitors" / "visibility.json")

    optimize_entries = [entry for entry in results if entry.get("type") == "optimize"]
    optimize_by_page = {}
    for entry in optimize_entries:
        page = str(entry.get("page") or "").strip().strip("/")
        if not page:
            continue
        slug = page.strip("/").split("/")[-1] or "index"
        optimize_by_page[slug] = entry

    summary_rows = []
    block_counter = Counter()
    techfix_counter = Counter()
    question_counter = Counter()
    heading_counter = Counter()

    for path in optimized_files:
        slug = path.stem
        text = path.read_text(encoding="utf-8", errors="replace")
        blocks = _extract_blocks(text)
        block_counter.update({key: value for key, value in blocks.items() if value})
        techfix_counter.update(_extract_techfix_types(text))
        question_counter.update(_extract_questions(text))
        heading_counter.update(_extract_heading_targets(text))

        page_data = page_map.get(slug, {})
        gap = gap_map.get(slug, {})
        result = optimize_by_page.get(slug, {})
        summary_rows.append(
            {
                "slug": slug,
                "label": _slug_to_label(slug),
                "url": gap.get("url") or page_data.get("url") or page_data.get("final_url") or "",
                "page_type": gap.get("page_type", "unknown"),
                "gap": gap.get("assigned_gap", "unassigned"),
                "query": _guess_query(page_data, slug),
                "approach": result.get("approach", "answer-first block expansion"),
                "status": result.get("status", "kept"),
                "blocks": blocks,
            }
        )

    if not summary_rows:
        return

    kept_count = sum(1 for row in summary_rows if row["status"] == "kept")
    discarded_count = sum(1 for row in summary_rows if row["status"] == "discarded")

    measured_visibility = (
        isinstance(visibility_data, dict)
        and "error" not in visibility_data
        and bool(visibility_data.get("results"))
    )
    offsite_domains = Counter()
    total_citations = 0
    if measured_visibility:
        for query_data in visibility_data.get("results", {}).values():
            if not isinstance(query_data, dict):
                continue
            for platform_data in query_data.values():
                if not isinstance(platform_data, dict):
                    continue
                for citation in platform_data.get("citations", []):
                    if not isinstance(citation, dict):
                        continue
                    domain = citation.get("domain")
                    if domain:
                        offsite_domains[domain] += 1
                        total_citations += 1

    report_lines = []
    report_lines.append(f"# GEO Optimization Report: {_extract_client(session_dir)}")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    site = _extract_site(session_dir)
    if site:
        report_lines.append(f"**Site:** {site}")
    report_lines.append(f"**Pages Optimized:** {len(summary_rows)}")
    report_lines.append("")
    report_lines.append("## Risks and Caveats")
    report_lines.append("")
    if measured_visibility:
        report_lines.append(
            f"- Visibility data was available and contributed {total_citations} observed citations across tracked queries."
        )
    else:
        report_lines.append(
            "- Competitive visibility data was unavailable, so competitive framing relies on on-page copy and structural differentiation rather than measured citation counts."
        )
    if techfix_counter:
        report_lines.append(
            f"- Infrastructure issues were inferred from recommended fixes: {', '.join(sorted(techfix_counter))}."
        )
    else:
        report_lines.append(
            "- Technical recommendations are content-first because no stable detect output was captured for every optimized page."
        )
    report_lines.append(
        "- This report is assembled from session artifacts after the run, so gaps in `results.jsonl` reduce score precision but not the content recommendations themselves."
    )
    report_lines.append("")
    report_lines.append("## Pre-Report Page Comparison Matrix")
    report_lines.append("")
    report_lines.append("| Page | Query | Gap | Status | Blocks |")
    report_lines.append("|---|---|---|---|---|")
    for row in summary_rows:
        blocks = ", ".join(name for name, count in row["blocks"].items() if count)
        label = str(row['label']).replace("|", "\\|")
        query = str(row['query']).replace("|", "\\|")
        gap = str(row['gap']).replace("|", "\\|")
        report_lines.append(
            f"| {label} | {query} | {gap} | {row['status']} | {blocks or 'none'} |"
        )
    report_lines.append("")
    report_lines.append("## Recommended Block Mix")
    report_lines.append("")
    for key, label in [
        ("intro", "Intro blocks"),
        ("faq", "FAQ blocks"),
        ("howto", "How-to blocks"),
        ("schema", "Schema blocks"),
        ("fill", "Content fill blocks"),
        ("techfix", "Tech fixes"),
        ("prune", "Prune actions"),
        ("tables", "Structured tables"),
        ("questions", "Question prompts"),
    ]:
        report_lines.append(f"- {label}: {block_counter.get(key, 0)}")
    report_lines.append("")
    if heading_counter:
        report_lines.append("## Frequent Heading Targets")
        report_lines.append("")
        for heading, count in heading_counter.most_common(10):
            report_lines.append(f"- {heading}: {count}")
        report_lines.append("")
    if question_counter:
        report_lines.append("## Recommended Question Bank")
        report_lines.append("")
        for question, count in question_counter.most_common(12):
            report_lines.append(f"- {question} ({count})")
        report_lines.append("")
    if offsite_domains:
        report_lines.append("## Off-Site Citation Priorities")
        report_lines.append("")
        for domain, count in offsite_domains.most_common(10):
            report_lines.append(f"- {domain}: {count}")
        report_lines.append("")
    report_lines.append("## Priority Actions")
    report_lines.append("")
    report_lines.append(
        f"- Keep {kept_count} page recommendations and revisit {discarded_count} discarded experiments before rollout."
    )
    if techfix_counter:
        report_lines.append(
            f"- Address technical issues reflected in recommendations: {', '.join(name for name, _ in techfix_counter.most_common(5))}."
        )
    if not measured_visibility:
        report_lines.append("- Collect visibility data before final publication to tighten competitor-specific framing.")
    report_lines.append("- Re-run evaluation after publishing to confirm which blocks translate into measurable GEO gains.")
    report_lines.append("")

    (session_dir / "report.md").write_text("\n".join(report_lines).rstrip() + "\n", encoding="utf-8")

    report_json = {
        "client": _extract_client(session_dir),
        "site": site,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages_optimized": len(summary_rows),
        "pages": summary_rows,
        "visibility_available": measured_visibility,
        "total_citations": total_citations,
        "offsite_domains": dict(offsite_domains.most_common(25)),
        "recommended_blocks": dict(block_counter),
        "techfix_types": dict(techfix_counter),
        "top_questions": [question for question, _ in question_counter.most_common(20)],
        "top_heading_targets": [heading for heading, _ in heading_counter.most_common(20)],
        "kept_count": kept_count,
        "discarded_count": discarded_count,
    }
    (session_dir / "report.json").write_text(
        json.dumps(report_json, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    today = date.today()
    verification_schedule = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checkpoints": [
            {
                "date": today.isoformat(),
                "label": "publish-ready QA",
                "focus": "Validate optimized copy blocks, links, and schema recommendations before rollout.",
            },
            {
                "date": (today + timedelta(days=7)).isoformat(),
                "label": "week-1 crawl check",
                "focus": "Confirm pages are indexable and updated blocks remain intact after deployment.",
            },
            {
                "date": (today + timedelta(days=21)).isoformat(),
                "label": "week-3 citation review",
                "focus": "Re-run visibility and detect whether citation footprint is improving on priority queries.",
            },
            {
                "date": (today + timedelta(days=42)).isoformat(),
                "label": "week-6 impact review",
                "focus": "Compare before/after GEO metrics and decide whether to expand the block mix to more pages.",
            },
        ],
    }
    (session_dir / "verification-schedule.json").write_text(
        json.dumps(verification_schedule, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: build_geo_report.py <session_dir>", file=sys.stderr)
        return 1

    session_dir = Path(sys.argv[1]).resolve()
    if not session_dir.exists():
        print(f"Session dir not found: {session_dir}", file=sys.stderr)
        return 1

    build_report(session_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
