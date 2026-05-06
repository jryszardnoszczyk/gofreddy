"""Drafter — writer + critic + revise. Writes drafts to drafts/YYYY-MM-DD.md."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from .db import connect
from .llm import LLM, DEFAULT_CRITIC_MODEL, DEFAULT_WRITER_MODEL
from .slop_gate import check_full

VOICE_DIR = Path(__file__).parent.parent / "voice"
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
DRAFTS_DIR = Path(__file__).parent.parent / "drafts"
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


def _load_schema(name: str) -> dict:
    import json as _json
    return _json.loads((SCHEMAS_DIR / f"{name}.json").read_text())

VOICE_FILES = [
    "about-me.md",
    "profile.md",
    "hooks.md",
    "anti-ai-writing-style.md",
    "exemplars.md",
]


def load_voice_block() -> str:
    """Concat all voice/*.md into a single system-prompt block."""
    parts: list[str] = []
    for name in VOICE_FILES:
        path = VOICE_DIR / name
        if path.exists():
            parts.append(f"\n\n=== {name} ===\n\n")
            parts.append(path.read_text())
    return "".join(parts)


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text()


def write_variants(
    llm: LLM,
    angle: dict[str, Any],
    *,
    voice_block: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Generate 3 variants for one angle. Returns (variants, stats)."""
    writer_prompt = load_prompt("writer.md")
    system = writer_prompt + "\n\n=== VOICE SUBSTRATE ===\n\n" + voice_block
    user = json.dumps(
        {
            "angle": {
                "headline": angle.get("headline", ""),
                "claim": angle.get("claim", ""),
                "source_url": angle.get("source_url", ""),
                "suggested_format": angle.get("suggested_format", "single"),
                "voice_pillar": angle.get("voice_pillar", ""),
                "why_it_matters": angle.get("why_it_matters", ""),
            }
        },
        indent=2,
    )
    parsed, resp = llm.call_json(
        system=system,
        user=user,
        model=DEFAULT_WRITER_MODEL,
        max_output_tokens=2000,
        temperature=0.85,
        schema=_load_schema("writer"),
    )
    variants = parsed.get("variants", [])
    return variants, {
        "input_tokens": resp.input_tokens,
        "output_tokens": resp.output_tokens,
        "cost_usd": resp.cost_usd,
    }


def lookup_source_text(source_url: str) -> str:
    """Pull the original source text from state.db by URL.

    Searches across tweets, releases, rss_items. Empty if not found in any.
    """
    if not source_url:
        return ""
    with connect() as conn:
        # tweets
        row = conn.execute(
            "SELECT text FROM tweets WHERE source_url = ? LIMIT 1", (source_url,)
        ).fetchone()
        if row:
            return row["text"] or ""
        # github releases (url column)
        row = conn.execute(
            "SELECT name, body FROM releases WHERE url = ? LIMIT 1", (source_url,)
        ).fetchone()
        if row:
            name = row["name"] or ""
            body = (row["body"] or "")[:2000]
            return f"{name}\n\n{body}".strip()
        # RSS items (url column)
        row = conn.execute(
            "SELECT title, summary FROM rss_items WHERE url = ? LIMIT 1", (source_url,)
        ).fetchone()
        if row:
            title = row["title"] or ""
            summary = (row["summary"] or "")[:2000]
            return f"{title}\n\n{summary}".strip()
    return ""


def critique_variant(
    llm: LLM,
    variant: dict[str, Any],
    angle: dict[str, Any],
    *,
    voice_signals: str,
    source_text: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Score one variant. Returns (critic_dict, stats)."""
    critic_prompt = load_prompt("critic.md")
    if not source_text:
        source_text = lookup_source_text(angle.get("source_url", ""))
    user = json.dumps(
        {
            "variant": variant,
            "angle": angle,
            "source_text": source_text,
            "voice_signals": voice_signals,
        },
        indent=2,
    )
    parsed, resp = llm.call_json(
        system=critic_prompt,
        user=user,
        model=DEFAULT_CRITIC_MODEL,
        max_output_tokens=600,
        temperature=0.2,
        schema=_load_schema("critic"),
    )
    return parsed, {
        "input_tokens": resp.input_tokens,
        "output_tokens": resp.output_tokens,
        "cost_usd": resp.cost_usd,
    }


def get_voice_signals_for_pillar(pillar: str, max_chars: int = 4000) -> str:
    """Extract relevant exemplars from exemplars.md based on pillar keywords."""
    path = VOICE_DIR / "exemplars.md"
    if not path.exists():
        return ""
    text = path.read_text()
    # For v1: just return first N chars. v2: filter by pillar keywords or topic similarity.
    return text[:max_chars]


def revise_variant(
    llm: LLM,
    variant: dict[str, Any],
    critic: dict[str, Any],
    angle: dict[str, Any],
    *,
    voice_block: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Single revision pass. Returns (revised_variant, stats)."""
    writer_prompt = load_prompt("writer.md")
    system = writer_prompt + "\n\n=== VOICE SUBSTRATE ===\n\n" + voice_block
    user = json.dumps(
        {
            "angle": angle,
            "previous_variant": variant,
            "critic_concerns": critic.get("concerns", []),
            "critic_revise_suggestion": critic.get("revise_suggestion", ""),
            "instruction": "Return ONE revised variant in the same JSON shape as before, addressing the critic's concern. Set id=99 to indicate revision.",
        },
        indent=2,
    )
    parsed, resp = llm.call_json(
        system=system,
        user=user,
        model=DEFAULT_WRITER_MODEL,
        max_output_tokens=800,
        temperature=0.6,
        schema=_load_schema("writer"),
    )
    variants = parsed.get("variants", [])
    revised = variants[0] if variants else variant
    return revised, {
        "input_tokens": resp.input_tokens,
        "output_tokens": resp.output_tokens,
        "cost_usd": resp.cost_usd,
    }


def save_draft_to_db(
    angle_id: int,
    variant: dict[str, Any],
    critic: dict[str, Any],
    *,
    revised: bool = False,
    slop_result: dict | None = None,
) -> int:
    now = dt.datetime.now(dt.UTC).isoformat()
    scores = critic.get("scores", {})
    avg = critic.get("avg") or sum(scores.values()) / max(len(scores), 1)
    slop_blocked = (slop_result or {}).get("ngram_blocked", False) or bool(
        (slop_result or {}).get("phrase_flags")
    )
    slop_flags_text = ",".join((slop_result or {}).get("phrase_flags", []))
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO drafts
              (angle_id, variant_id, format, hook, text, rationale,
               score_voice, score_factual, score_hook, score_slop, score_avg,
               ship, factual_veto, revised, slop_blocked, slop_flags, critic_concerns,
               created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                angle_id,
                variant.get("id", 0),
                variant.get("format", "single"),
                variant.get("hook", "")[:200],
                variant.get("text", ""),
                variant.get("rationale", "")[:500],
                scores.get("voice_match", 0),
                scores.get("factual_specificity", 0),
                scores.get("hook_strength", 0),
                scores.get("slop_freeness", 0),
                avg,
                1 if (critic.get("ship") and not slop_blocked) else 0,
                1 if critic.get("factual_veto") else 0,
                1 if revised else 0,
                1 if slop_blocked else 0,
                slop_flags_text[:500],
                "; ".join(critic.get("concerns", []))[:1000],
                now,
            ),
        )
        return cur.lastrowid


def _process_variant(
    llm: LLM,
    v: dict[str, Any],
    angle_row: dict[str, Any],
    *,
    voice_block: str,
    voice_signals: str,
    exemplars_path: Path,
) -> dict[str, Any]:
    """Slop-check + critic + optional revise+re-critic for ONE variant.

    Designed to run concurrently with sibling variants (3-wide pool inside
    draft_for_angle). Returns dict with variant, critic, slop_result, revised, cost.
    """
    cost = 0.0
    slop_result = check_full(v.get("text", ""), exemplars_path=exemplars_path)
    critic, c_stats = critique_variant(llm, v, angle_row, voice_signals=voice_signals)
    cost += c_stats["cost_usd"]

    revised = False
    if not critic.get("ship") and not critic.get("factual_veto"):
        revised_var, r_stats = revise_variant(llm, v, critic, angle_row, voice_block=voice_block)
        cost += r_stats["cost_usd"]
        slop_result_rev = check_full(revised_var.get("text", ""), exemplars_path=exemplars_path)
        critic_rev, c2_stats = critique_variant(
            llm, revised_var, angle_row, voice_signals=voice_signals
        )
        cost += c2_stats["cost_usd"]
        if critic_rev.get("ship"):
            v = revised_var
            critic = critic_rev
            slop_result = slop_result_rev
            revised = True

    return {
        "variant": v,
        "critic": critic,
        "slop_result": slop_result,
        "revised": revised,
        "cost_usd": cost,
    }


def draft_for_angle(
    llm: LLM,
    angle_row: dict[str, Any],
    *,
    voice_block: str,
    inner_workers: int = 3,
) -> dict[str, Any]:
    """Run full draft pipeline for one angle. Returns dict with variants + scoring + costs.

    Inner parallelism: the 3 critic+revise loops run concurrently in a thread pool.
    Each codex subprocess is independent, so this is safe.
    """
    import concurrent.futures

    pillar = angle_row.get("voice_pillar", "")
    voice_signals = get_voice_signals_for_pillar(pillar)
    exemplars_path = VOICE_DIR / "exemplars.md"

    total_cost = 0.0
    variants, stats = write_variants(llm, angle_row, voice_block=voice_block)
    total_cost += stats["cost_usd"]

    # Each thread gets its own LLM (codex subprocesses are stateless; this just keeps
    # the API symmetric and avoids any potential subprocess-shared-state surprises)
    def _run(v):
        thread_llm = LLM()
        return _process_variant(
            thread_llm, v, angle_row,
            voice_block=voice_block,
            voice_signals=voice_signals,
            exemplars_path=exemplars_path,
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=inner_workers) as ex:
        processed = list(ex.map(_run, variants))

    results = []
    for r in processed:
        total_cost += r["cost_usd"]
        draft_id = save_draft_to_db(
            angle_row["angle_id"], r["variant"], r["critic"],
            revised=r["revised"], slop_result=r["slop_result"],
        )
        results.append(
            {
                "draft_id": draft_id,
                "variant": r["variant"],
                "critic": r["critic"],
                "slop_result": r["slop_result"],
                "revised": r["revised"],
            }
        )

    return {"angle_id": angle_row["angle_id"], "results": results, "cost_usd": total_cost}


def pick_top_drafts_for_today(limit: int = 5) -> list[dict[str, Any]]:
    """Top drafts with two-level diversity: pillar-first, then angle.

    Pass 1: pick highest-scoring draft per ANGLE, tiebreak by hook
    Pass 2: across those, prefer DISTINCT PILLARS (one draft per pillar) until
            all pillars represented, then fill remaining slots by score.

    This avoids the daily queue collapsing to 2-3 pillars even when 6+ angles
    were drafted across more pillars.
    """
    today = dt.date.today().isoformat()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT d.*, a.headline, a.source_url, a.source_handle, a.why_it_matters,
                   a.voice_pillar, a.suggested_format
            FROM drafts d
            JOIN angles a ON d.angle_id = a.angle_id
            WHERE a.run_date = ? AND d.ship = 1
            ORDER BY d.score_avg DESC, d.score_hook DESC
            """,
            (today,),
        ).fetchall()
    # Pass 1: dedup by angle_id (already what we did before)
    seen_angles: set[int] = set()
    by_angle: list[dict[str, Any]] = []
    for r in rows:
        if r["angle_id"] in seen_angles:
            continue
        seen_angles.add(r["angle_id"])
        by_angle.append(dict(r))

    # Pass 2: pillar diversity — first take the top-scoring draft per pillar
    seen_pillars: set[str] = set()
    out: list[dict[str, Any]] = []
    leftovers: list[dict[str, Any]] = []
    for d in by_angle:
        pillar = d.get("voice_pillar") or "_unknown"
        if pillar in seen_pillars:
            leftovers.append(d)
            continue
        seen_pillars.add(pillar)
        out.append(d)
        if len(out) >= limit:
            return out
    # Fill remaining slots from leftovers (already sorted by score)
    for d in leftovers:
        if len(out) >= limit:
            break
        out.append(d)
    return out


def write_drafts_file(drafts: list[dict[str, Any]], date_str: str | None = None) -> Path:
    """Write the daily drafts/YYYY-MM-DD.md file."""
    date_str = date_str or dt.date.today().isoformat()
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    path = DRAFTS_DIR / f"{date_str}.md"

    lines = [f"# Drafts — {date_str}", ""]
    lines.append(f"**{len(drafts)} drafts ready.** Pick, optionally edit, post manually on x.com.")
    lines.append("")
    if not drafts:
        lines.append("> No drafts shipped today. Check `vault/{date}.md` for angles, "
                     "and `state.db` `drafts` table for blocked variants.")
    for i, d in enumerate(drafts, 1):
        lines.append(
            f"## Draft {i} — voice {d['score_voice']:.1f} / "
            f"fact {d['score_factual']:.1f} / hook {d['score_hook']:.1f} / "
            f"slop {d['score_slop']:.1f} — avg **{d['score_avg']:.2f}**"
        )
        lines.append("")
        lines.append("```")
        lines.append(d["text"])
        lines.append("```")
        lines.append("")
        lines.append(f"**Angle:** {d['headline']}")
        lines.append(f"**Source:** {d['source_url']} ({d['source_handle']})")
        lines.append(f"**Pillar:** {d['voice_pillar']}")
        lines.append(f"**Format:** {d['format']}{' (revised)' if d['revised'] else ''}")
        if d["critic_concerns"]:
            lines.append(f"**Critic notes:** {d['critic_concerns']}")
        lines.append("**Variant rationale:** " + (d["rationale"] or ""))
        lines.append("")
        lines.append("---")
        lines.append("")
    path.write_text("\n".join(lines))
    return path
