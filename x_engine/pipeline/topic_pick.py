"""Topic picker — turns ranked feed into structured angles in vault/."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from .db import connect
from .llm import LLM, DEFAULT_TOPIC_MODEL
from .rank import recent_releases, recent_rss, top_n_ranked

VAULT_DIR = Path(__file__).parent.parent / "vault"
DRAFTS_DIR = Path(__file__).parent.parent / "drafts"
VOICE_DIR = Path(__file__).parent.parent / "voice"
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text()


def get_recent_drafts_text(days: int = 14, limit: int = 30) -> list[str]:
    """Pull text of recently-shipped drafts (ship=1) to avoid repetition."""
    cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).isoformat()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT text FROM drafts
            WHERE ship = 1 AND created_at >= ?
            ORDER BY created_at DESC LIMIT ?
            """,
            (cutoff, limit),
        ).fetchall()
    return [r["text"] for r in rows]


def get_no_go_topics() -> str:
    path = VOICE_DIR / "no-go-topics.md"
    return path.read_text() if path.exists() else ""


def get_voice_pillars() -> str:
    """Extract just the pillars section from profile.md (token efficiency)."""
    path = VOICE_DIR / "profile.md"
    if not path.exists():
        return ""
    text = path.read_text()
    # Grab the "Content pillars" section
    if "## Content pillars" in text:
        section = text.split("## Content pillars", 1)[1].split("\n## ", 1)[0]
        return section
    return text[:2000]


def build_evidence_payload(
    *,
    top_n: int = 50,
    min_likes: int = 20,
    freshness_hours: int = 36,
    rss_days: int = 7,
    release_days: int = 7,
) -> list[dict[str, Any]]:
    """Compose ranked evidence: tweets + releases + RSS as a unified list."""
    items: list[dict[str, Any]] = []

    for t in top_n_ranked(n=top_n, min_likes=min_likes, freshness_hours=freshness_hours):
        items.append(
            {
                "kind": "tweet",
                "id": t["tweet_id"],
                "source_url": t["source_url"],
                "source_handle": "@" + (t["source_handle"] or ""),
                "text": (t["text"] or "")[:600],
                "likes": t["likes"],
                "retweets": t["retweets"],
                "replies": t["replies"],
                "views": t["views"],
                "created_at": t["created_at"],
                "resonance_score": round(t["resonance_score"] or 0.0, 4),
            }
        )

    for r in recent_releases(days=release_days):
        items.append(
            {
                "kind": "github_release",
                "id": r["release_id"],
                "source_url": r["url"],
                "source_handle": r["repo"],
                "text": f"{r['name']}: {(r['body'] or '')[:500]}",
                "created_at": r["published_at"],
            }
        )

    for r in recent_rss(days=rss_days):
        items.append(
            {
                "kind": "rss",
                "id": r["rss_id"],
                "source_url": r["url"],
                "source_handle": r["source_label"],
                "text": f"{r['title']}: {(r['summary'] or '')[:500]}",
                "created_at": r["published_at"],
            }
        )

    return items


def pick_angles(
    llm: LLM,
    *,
    angles_count: int = 7,
    top_n: int = 50,
    min_likes: int = 20,
    freshness_hours: int = 36,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run topic picker. Returns (angles, llm_stats)."""
    system = load_prompt("topic_picker.md").replace("{N}", str(angles_count))
    evidence = build_evidence_payload(
        top_n=top_n, min_likes=min_likes, freshness_hours=freshness_hours
    )
    user = json.dumps(
        {
            "recent_drafts": get_recent_drafts_text(),
            "no_go_topics": get_no_go_topics(),
            "voice_pillars": get_voice_pillars(),
            "evidence": evidence,
        },
        indent=2,
    )
    parsed, resp = llm.call_json(
        system=system,
        user=user,
        model=DEFAULT_TOPIC_MODEL,
        max_output_tokens=4000,
        temperature=0.4,
    )
    angles = parsed.get("angles", [])
    return angles, {
        "input_tokens": resp.input_tokens,
        "output_tokens": resp.output_tokens,
        "cost_usd": resp.cost_usd,
        "evidence_count": len(evidence),
    }


def save_angles_to_db(angles: list[dict[str, Any]]) -> list[int]:
    """Insert angles into DB. Returns list of inserted angle_ids."""
    now = dt.datetime.now(dt.UTC).isoformat()
    today = dt.date.today().isoformat()
    ids: list[int] = []
    with connect() as conn:
        for a in angles:
            cur = conn.execute(
                """
                INSERT INTO angles
                  (run_date, headline, claim, source_url, source_handle, why_it_matters,
                   suggested_format, voice_pillar, confidence, picked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    today,
                    a.get("headline", ""),
                    a.get("claim", ""),
                    a.get("source_url", ""),
                    a.get("source_handle", ""),
                    a.get("why_it_matters", ""),
                    a.get("suggested_format", "single"),
                    a.get("voice_pillar", ""),
                    a.get("confidence", "medium"),
                    now,
                ),
            )
            ids.append(cur.lastrowid)
    return ids


def write_vault_file(angles: list[dict[str, Any]], date_str: str | None = None) -> Path:
    """Write today's angles to vault/YYYY-MM-DD.md as structured markdown."""
    date_str = date_str or dt.date.today().isoformat()
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    path = VAULT_DIR / f"{date_str}.md"

    lines = [f"# Vault — {date_str}", ""]
    lines.append(f"**{len(angles)} angles picked.** Source: `pipeline/topic_pick.py`.")
    lines.append("")
    for i, a in enumerate(angles, 1):
        lines.append(f"## Angle {i}: {a.get('headline', '?')}")
        lines.append("")
        lines.append(f"- **Claim:** {a.get('claim', '?')}")
        lines.append(f"- **Source:** {a.get('source_url', '?')} ({a.get('source_handle', '')})")
        lines.append(f"- **Why it matters:** {a.get('why_it_matters', '?')}")
        lines.append(f"- **Suggested format:** {a.get('suggested_format', 'single')}")
        lines.append(f"- **Voice pillar:** {a.get('voice_pillar', '?')}")
        lines.append(f"- **Confidence:** {a.get('confidence', 'medium')}")
        lines.append("")

    path.write_text("\n".join(lines))
    return path
