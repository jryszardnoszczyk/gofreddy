"""xeng — CLI tool surface for the X + LinkedIn lane agents.

Each subcommand is a small operation the lane agent (claude/codex/opencode
subprocess driven by `programs/<lane>-session.md`) composes. JSON output
on stdout for machine parsing. Side effects (DB writes, files) are intentional —
the agent uses these tools to do real work.

Per master plan v13 §3.1, the v1 X-engine `compose`, `draft-angle`,
`write-vault`, `write-drafts`, `topic-pick`, `save-angle` commands are
DROPPED — the per-lane agent prompts collapse those operations.

Usage:
  # Pull lane (X — twitterapi.io)
  xeng pull-user @AlfieJCarter            # fetch + upsert
  xeng pull-search 'AI marketing min_faves:50 within_time:48h'
  xeng pull-github anthropics/claude-code
  xeng pull-rss https://www.latent.space/feed latentspace

  # Pull lane (LinkedIn — Apify-backed; per D11)
  xeng pull-linkedin-search 'ai marketing'
  xeng pull-linkedin-user https://linkedin.com/in/<handle>
  xeng pull-linkedin-all-search           # iterate sources_linkedin.yaml keywords
  xeng pull-linkedin-all-users            # iterate sources_linkedin.yaml profiles
  xeng pull-linkedin-brightdata           # feature-flagged off (R5 fallback)

  # Read lane (engagement-ranked surfaces for the agent)
  xeng top-tweets --n 50 --min-likes 30 --hours 48
  xeng top-linkedin --days 14             # decay-weighted formula
  xeng top-releases --days 7
  xeng top-rss --days 7
  xeng list-shipped --days 14

  # Voice substrate access (read-only)
  xeng voice                              # concat voice/*.md (X-side)
  xeng exemplars                          # voice/exemplars.md
  xeng pillars                            # extract content pillars from profile.md
  xeng no-go                              # no-go-topics.md

  # Quality gate
  xeng slop-check '<text>' --platform x|linkedin

  # Angle access (both lanes' agents at session start; per D13)
  xeng angle-show <id>
  xeng angle-list --days 30

  # Decision tracking + holdout export (L1 critical-path)
  xeng mark-posted <id> --platform x|linkedin --tweet-url URL
  xeng skip-draft <id> --platform x|linkedin --reason <enum>
  xeng holdout-export [--output PATH]

  # Diagnostics
  xeng info
  xeng posted --days 30
  xeng sync-engagement --days 7
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv

# Load .env from gofreddy root (one level up from x_engine/)
load_dotenv(Path(__file__).parent.parent / ".env")

from x_engine.pipeline import linkedin as linkedin_mod
from x_engine.pipeline import pull as pull_mod
from x_engine.pipeline import rank as rank_mod
from x_engine.pipeline import slop_gate as slop_mod
from x_engine.pipeline.db import connect, init_db

app = typer.Typer(no_args_is_help=True, add_completion=False)

# Per plan §5.2: structured skip_reason enum (`no_time` is operator-noise that
# `holdout-export` filters before partitioning). The DB CHECK constraint on
# `draft_decisions.skip_reason` enforces the same set; this list keeps the CLI
# error message in lock-step with the schema so a typo surfaces here, not via a
# raw `sqlite3.IntegrityError`.
_SKIP_REASONS: tuple[str, ...] = (
    "voice_off",
    "factual_unverifiable",
    "off_pillar",
    "duplicate",
    "no_time",
    "other",
)
_PLATFORMS: tuple[str, ...] = ("x", "linkedin")


def _key() -> str:
    k = os.environ.get("TWITTERAPI_IO_KEY")
    if not k:
        typer.echo("ERROR: TWITTERAPI_IO_KEY not set", err=True)
        raise typer.Exit(2)
    return k


def _print_json(obj) -> None:
    typer.echo(json.dumps(obj, indent=2, default=str))


def _validate_platform(platform: str) -> None:
    if platform not in _PLATFORMS:
        typer.echo(
            f"ERROR: --platform must be one of {sorted(_PLATFORMS)}, got {platform!r}",
            err=True,
        )
        raise typer.Exit(2)


def _lookup_draft(conn, draft_id: int) -> dict | None:
    """Return draft text + angle_id + pillar from `drafts` or `hand_drafts`.

    Cold-start flow (Round-6 P0 #4): JR hand-writes 5 ship + 5 skip LinkedIn
    drafts during the L1 X-dogfood window; those rows live in `hand_drafts`,
    not `drafts`. `mark-posted` and `skip-draft` must accept either.
    """
    row = conn.execute(
        "SELECT d.text AS body, d.angle_id, a.voice_pillar FROM drafts d "
        "LEFT JOIN angles a ON d.angle_id = a.angle_id WHERE d.draft_id=?",
        (draft_id,),
    ).fetchone()
    if row is not None:
        return {"body": row["body"], "angle_id": row["angle_id"],
                "pillar": row["voice_pillar"], "source": "drafts"}
    row = conn.execute(
        "SELECT h.body, h.angle_id, a.voice_pillar FROM hand_drafts h "
        "LEFT JOIN angles a ON h.angle_id = a.angle_id WHERE h.draft_id=?",
        (draft_id,),
    ).fetchone()
    if row is not None:
        return {"body": row["body"], "angle_id": row["angle_id"],
                "pillar": row["voice_pillar"], "source": "hand_drafts"}
    return None


# ---------- Pull lane ----------

@app.command("pull-user")
def pull_user(username: str, max_tweets: int = 30, freshness_hours: int = 48):
    """Pull last-N tweets from a user, dedup-insert into state.db."""
    init_db()
    username = username.lstrip("@")
    tweets = pull_mod.pull_user_timeline(
        username, api_key=_key(), max_tweets=max_tweets, freshness_hours=freshness_hours
    )
    inserted = pull_mod.upsert_tweets(tweets, username)
    _print_json({"username": username, "fresh": len(tweets), "inserted": inserted})


@app.command("pull-search")
def pull_search(query: str, label: str = "search", max_tweets: int = 30):
    """Run advanced_search query. Use within_time:Nh in query for freshness."""
    init_db()
    tweets = pull_mod.pull_search_query(query, api_key=_key(), max_tweets=max_tweets)
    inserted = pull_mod.upsert_search_tweets(tweets, label)
    _print_json({"query": query[:80], "label": label, "fresh": len(tweets), "inserted": inserted})


@app.command("pull-github")
def pull_github(repo: str, days: int = 7):
    """Pull GitHub releases (last N days) for org/repo."""
    init_db()
    releases = pull_mod.pull_github_releases(repo, days=days)
    inserted = pull_mod.upsert_releases(releases, repo)
    _print_json({"repo": repo, "fresh": len(releases), "inserted": inserted})


@app.command("pull-rss")
def pull_rss(url: str, label: str = "rss", days: int = 7):
    """Pull RSS feed items (last N days)."""
    init_db()
    items = pull_mod.pull_rss(url, label, days=days)
    inserted = pull_mod.upsert_rss(items)
    _print_json({"label": label, "fresh": len(items), "inserted": inserted})


# ---------- Pull lane (LinkedIn — Apify-backed; per master plan v13 §3.4) ----------

@app.command("pull-linkedin-search")
def pull_linkedin_search(keyword: str, limit: int = 50, max_cu: float = 50.0):
    """Pull LinkedIn posts matching a keyword via apimaestro actor.

    Cost-cap: `--max-cu 50` default. Runs that exceed the cap are aborted
    in flight; the command exits with code 3 (not 0) so daily totals stay
    bounded by `&&`-chained pipelines.
    """
    try:
        result = linkedin_mod.pull_linkedin_search(
            keyword, limit=limit, max_cu=max_cu
        )
    except linkedin_mod.ApifyCostCapExceeded as exc:
        typer.echo(f"ERROR: cost-cap exceeded: {exc}", err=True)
        raise typer.Exit(3)
    except linkedin_mod.ApifyError as exc:
        typer.echo(f"ERROR: apify: {exc}", err=True)
        raise typer.Exit(2)
    _print_json(result)


@app.command("pull-linkedin-user")
def pull_linkedin_user(profile_url: str, limit: int = 30, max_cu: float = 200.0):
    """Pull recent posts from a LinkedIn profile via harvestapi actor.

    Cost-cap: `--max-cu 200` default. Same exit-code policy as
    pull-linkedin-search.
    """
    try:
        result = linkedin_mod.pull_linkedin_user(
            profile_url, limit=limit, max_cu=max_cu
        )
    except linkedin_mod.ApifyCostCapExceeded as exc:
        typer.echo(f"ERROR: cost-cap exceeded: {exc}", err=True)
        raise typer.Exit(3)
    except linkedin_mod.ApifyError as exc:
        typer.echo(f"ERROR: apify: {exc}", err=True)
        raise typer.Exit(2)
    _print_json(result)


@app.command("pull-linkedin-all-search")
def pull_linkedin_all_search(
    sources: str = "",
    limit: int = 50,
    max_cu: float = 50.0,
):
    """Iterate `linkedin_keywords` from sources_linkedin.yaml and pull each.

    Default `--sources` resolves to `x_engine/sources_linkedin.yaml`. Each
    keyword is pulled with `--max-cu` so daily totals stay bounded; per-call
    failure does not abort the batch. Wired by the
    com.jryszardnoszczyk.linkedin-pull-search LaunchAgent (daily 06:35).
    """
    sources_path = Path(sources) if sources else (Path(__file__).parent / "sources_linkedin.yaml")
    if not sources_path.exists():
        typer.echo(f"ERROR: sources_linkedin.yaml not found at {sources_path}", err=True)
        raise typer.Exit(2)
    import yaml as _yaml  # local import — yaml already a x_engine dep
    cfg = _yaml.safe_load(sources_path.read_text()) or {}
    keywords = list(cfg.get("linkedin_keywords") or [])
    if not keywords:
        typer.echo("WARN: no linkedin_keywords in sources file; nothing to do", err=True)
        _print_json({"keywords": 0, "results": []})
        return
    results = []
    failed = 0
    for kw in keywords:
        try:
            res = linkedin_mod.pull_linkedin_search(kw, limit=limit, max_cu=max_cu)
            results.append({"keyword": kw, **res})
        except linkedin_mod.ApifyError as exc:
            results.append({"keyword": kw, "error": str(exc)})
            failed += 1
    _print_json({
        "keywords": len(keywords),
        "succeeded": len(keywords) - failed,
        "failed": failed,
        "results": results,
    })
    # Exit 1 when ANY keyword failed (resilient over the loop, but the
    # cron + monitoring need a non-zero signal). Exit 2 only when ALL
    # failed (full-batch failure) so monitoring can distinguish.
    if failed == len(keywords) and keywords:
        raise typer.Exit(2)
    if failed:
        raise typer.Exit(1)


@app.command("pull-linkedin-all-users")
def pull_linkedin_all_users(
    sources: str = "",
    limit: int = 30,
    max_cu: float = 200.0,
):
    """Iterate `linkedin_users` from sources_linkedin.yaml and pull each.

    Default `--sources` resolves to `x_engine/sources_linkedin.yaml`. Wired
    by the com.jryszardnoszczyk.linkedin-pull-user LaunchAgent (weekly
    Sun 07:00 — per-creator content updates slowly so weekly is cost-controlled).
    """
    sources_path = Path(sources) if sources else (Path(__file__).parent / "sources_linkedin.yaml")
    if not sources_path.exists():
        typer.echo(f"ERROR: sources_linkedin.yaml not found at {sources_path}", err=True)
        raise typer.Exit(2)
    import yaml as _yaml
    cfg = _yaml.safe_load(sources_path.read_text()) or {}
    users = list(cfg.get("linkedin_users") or [])
    if not users:
        typer.echo("WARN: no linkedin_users in sources file; nothing to do", err=True)
        _print_json({"users": 0, "results": []})
        return
    results = []
    failed = 0
    for profile_url in users:
        try:
            res = linkedin_mod.pull_linkedin_user(
                profile_url, limit=limit, max_cu=max_cu
            )
            results.append({"profile_url": profile_url, **res})
        except linkedin_mod.ApifyError as exc:
            results.append({"profile_url": profile_url, "error": str(exc)})
            failed += 1
    _print_json({
        "users": len(users),
        "succeeded": len(users) - failed,
        "failed": failed,
        "results": results,
    })
    if failed == len(users) and users:
        raise typer.Exit(2)
    if failed:
        raise typer.Exit(1)


@app.command("pull-linkedin-brightdata")
def pull_linkedin_brightdata(keyword: str, limit: int = 50):
    """Bright Data fallback (pre-positioned, feature-flagged OFF in v1).

    Activate per plan §7.6 R5: set LINKEDIN_USE_BRIGHTDATA=1 +
    BRIGHTDATA_TOKEN. Default invocation surfaces a clear "disabled"
    error so it's safe to run accidentally.
    """
    try:
        result = linkedin_mod.pull_linkedin_brightdata(keyword, limit=limit)
    except linkedin_mod.BrightDataDisabledError as exc:
        typer.echo(f"ERROR: brightdata disabled: {exc}", err=True)
        raise typer.Exit(2)
    _print_json(result)


# ---------- Read lane ----------

@app.command("top-tweets")
def top_tweets(n: int = 50, min_likes: int = 20, hours: int = 48):
    """Rank-update + return top-N tweets by resonance from state.db (JSON list)."""
    rank_mod.update_scores()
    rows = rank_mod.top_n_ranked(n=n, min_likes=min_likes, freshness_hours=hours)
    _print_json(rows)


@app.command("top-releases")
def top_releases(days: int = 7, limit: int = 20):
    """Recent GitHub releases from state.db."""
    _print_json(rank_mod.recent_releases(days=days, limit=limit))


@app.command("top-rss")
def top_rss(days: int = 7, limit: int = 30):
    """Recent RSS items from state.db."""
    _print_json(rank_mod.recent_rss(days=days, limit=limit))


@app.command("top-linkedin")
def top_linkedin(days: int = 14, limit: int = 50):
    """Top LinkedIn posts by engagement score (decay-weighted).

    Per master plan v13 §3.4 (Round-7 Gap B):
        score = (reactions × 1.0 + comments × 3.0 + shares × 5.0)
                × exp(-days_since_posted / 14)

    Per-platform engagement scoring is per-command — `top-tweets` keeps
    X-engagement weights from rank.py; this command applies the LinkedIn
    formula. No shared cross-platform normalization.
    """
    _print_json(linkedin_mod.top_linkedin(days=days, limit=limit))


@app.command("list-shipped")
def list_shipped(days: int = 14, limit: int = 30):
    """Texts of drafts marked ship=1 in last N days. Use to avoid repetition."""
    cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).isoformat()
    with connect() as conn:
        rows = conn.execute(
            "SELECT text, created_at FROM drafts WHERE ship=1 AND created_at >= ? "
            "ORDER BY created_at DESC LIMIT ?",
            (cutoff, limit),
        ).fetchall()
    _print_json([dict(r) for r in rows])


# ---------- Voice substrate ----------

VOICE_DIR = Path(__file__).parent / "voice"

# Voice file load order — matches the v1 substrate concat. Used by `xeng voice`
# (X-side legacy reader). The lane port substrate at
# archive/<seed>/programs/references/voice.md is read directly by
# SessionEvalSpec.load_source_data; this CLI command is for ad-hoc inspection.
_VOICE_FILES: tuple[str, ...] = (
    "about-me.md",
    "profile.md",
    "hooks.md",
    "anti-ai-writing-style.md",
    "exemplars.md",
    "no-go-topics.md",
)


@app.command("voice")
def voice():
    """Print concatenated voice files (about-me, profile, hooks, anti-ai,
    exemplars, no-go). Read-only; agent uses the substrate at
    archive/<seed>/programs/references/voice.md, not this command."""
    parts: list[str] = []
    for name in _VOICE_FILES:
        p = VOICE_DIR / name
        if p.exists():
            parts.append(f"# {name}\n\n{p.read_text()}")
    typer.echo("\n\n---\n\n".join(parts))


@app.command("exemplars")
def exemplars():
    """Print voice/exemplars.md content only."""
    p = VOICE_DIR / "exemplars.md"
    if p.exists():
        typer.echo(p.read_text())


@app.command("pillars")
def pillars():
    """Extract content pillars from voice/profile.md.

    Pillars are declared as ``## NN. <Pillar Name>`` headers under the
    ``## Content pillars`` H2. Inline-implemented (formerly in
    pipeline/topic_pick.py, dropped per master plan v13 §3.1)."""
    profile = VOICE_DIR / "profile.md"
    if not profile.exists():
        typer.echo("ERROR: voice/profile.md not found", err=True)
        raise typer.Exit(2)
    text = profile.read_text()
    # Extract `## N. Name` headers (where N is a digit) — the pillar list.
    pillars_list = [
        m.group(1).strip()
        for m in re.finditer(r"^##\s+\d+\.\s+(.+?)\s*$", text, re.MULTILINE)
    ]
    typer.echo("\n".join(pillars_list))


@app.command("no-go")
def no_go():
    """Print no-go-topics.md content."""
    p = VOICE_DIR / "no-go-topics.md"
    if p.exists():
        typer.echo(p.read_text())


# ---------- Quality gate ----------

@app.command("slop-check")
def slop_check(text: str, platform: str = "x"):
    """Run banned-phrase + n-gram check on candidate text. Returns JSON.

    `--platform x` (default) keeps the v1 floor: shared banned phrases,
    em-dash check, parallel-structure formulas, and exemplar n-gram overlap.

    `--platform linkedin` drops the em-dash check (LinkedIn audiences
    accept dashes), adds LinkedIn-specific tells (`Thoughts? 👇`,
    `Agree? 🤔`, `Here's what I learned.` close, etc.), and gates
    whitespace inflation. Used by `linkedin_engine` lane's structural
    gate per master plan v13 §4.4.
    """
    _validate_platform(platform)
    exemplars_path = VOICE_DIR / "exemplars.md"
    result = slop_mod.check_full(
        text, exemplars_path=exemplars_path, platform=platform
    )
    _print_json(result)


# ---------- Angle access (lane-port shared; both lanes' agents call these) ----------

@app.command("angle-show")
def angle_show(angle_id: int):
    """Print one angle row as JSON. Used by both lanes' agents at session start.

    Returns: angle_id, headline, claim, source_url, source_handle,
    source_text (nullable per §5.2 — agent must tolerate null and fall back
    to source_url + headline for grounding), why_it_matters, suggested_format,
    voice_pillar, confidence, run_date, picked_at.
    """
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT angle_id, run_date, headline, claim, source_url, "
            "source_handle, why_it_matters, suggested_format, voice_pillar, "
            "confidence, picked_at, source_text FROM angles WHERE angle_id=?",
            (angle_id,),
        ).fetchone()
    if row is None:
        typer.echo(f"ERROR: angle {angle_id} not found", err=True)
        raise typer.Exit(2)
    _print_json(dict(row))


@app.command("angle-list")
def angle_list(days: int = 30, limit: int = 50):
    """List angles ordered by picked_at DESC, optionally trailing N days."""
    cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).isoformat()
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT angle_id, run_date, headline, voice_pillar, picked_at "
            "FROM angles WHERE picked_at >= ? "
            "ORDER BY picked_at DESC LIMIT ?",
            (cutoff, limit),
        ).fetchall()
    _print_json([dict(r) for r in rows])


# ---------- Holdout export (L1 dogfood → eval_suites/holdout-v1.json) ----------

@app.command("holdout-export")
def holdout_export(output: str = ""):
    """Emit holdout entries for BOTH lanes from `draft_decisions`.

    Per master plan v13 §5.3:
    - Filters `no_time` skip rows (operator-noise; not a quality signal).
    - Partitions remaining rows by `platform` into `domains.x_engine[]` and
      `domains.linkedin_engine[]`.
    - Each entry: {fixture_id, client="jr", context=str(angle_id),
      version="1.0", max_iter=1, timeout=600, anchor=true,
      env={JR_GROUND_TRUTH, SKIP_REASON, PLATFORM}}.
    - Operator atomically merges this into `~/.config/gofreddy/holdouts/holdout-v1.json`
      via jq per §7.9; this command does not touch the live holdout file.

    With `--output PATH`: writes JSON to PATH at mode 0o600.
    Without:               prints to stdout.
    """
    init_db()
    with connect() as conn:
        # Two valid row shapes:
        #   outcome='ship' AND skip_reason IS NULL    -> shipped draft
        #   outcome='skip' AND skip_reason IS NOT NULL -> skipped with reason
        # Anything else is a corrupt row (e.g., outcome='ship' with a
        # skip_reason). Filter `no_time` skip rows (operator-noise per §5.3)
        # AND any logically-contradictory rows.
        rows = conn.execute(
            "SELECT draft_id, angle_id, platform, outcome, skip_reason, "
            "created_at FROM draft_decisions "
            "WHERE ((outcome = 'ship' AND skip_reason IS NULL) "
            "       OR (outcome = 'skip' AND skip_reason IS NOT NULL "
            "           AND skip_reason != 'no_time')) "
            "ORDER BY created_at ASC"
        ).fetchall()

    domains: dict[str, list[dict]] = {"x_engine": [], "linkedin_engine": []}
    domain_for_platform = {"x": "x_engine", "linkedin": "linkedin_engine"}
    for row in rows:
        platform = row["platform"]
        domain = domain_for_platform.get(platform)
        if domain is None:  # defense-in-depth; CHECK constraint should already block
            continue
        decision_date = (row["created_at"] or "")[:10] or "unknown"
        fixture_id = f"jr-{decision_date}-{platform}-d{row['draft_id']}"
        domains[domain].append({
            "fixture_id": fixture_id,
            "client": "jr",
            "context": str(row["angle_id"]) if row["angle_id"] is not None else "",
            "version": "1.0",
            "max_iter": 1,
            "timeout": 600,
            "anchor": True,
            "env": {
                "JR_GROUND_TRUTH": row["outcome"],
                "SKIP_REASON": row["skip_reason"] or "",
                "PLATFORM": platform,
            },
        })

    payload = {"domains": domains}

    if output:
        out_path = Path(output).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2) + "\n")
        out_path.chmod(0o600)
        _print_json({
            "output": str(out_path),
            "x_engine": len(domains["x_engine"]),
            "linkedin_engine": len(domains["linkedin_engine"]),
        })
    else:
        _print_json(payload)


# ---------- Discovery ----------

@app.command("mark-posted")
def mark_posted(draft_id: int, platform: str = "x", tweet_url: str = ""):
    """Mark a draft as posted. Dual-writes to draft_decisions (both lanes) and,
    for X only, recent_posted (engagement-sync path; LinkedIn engagement-sync
    deferred to v2 per plan §5.2). Accepts draft_ids from either `drafts` or
    `hand_drafts` to support the L1 cold-start flow.

    Usage:
      xeng mark-posted 174                                      # X (default)
      xeng mark-posted 174 --tweet-url https://x.com/jr/status/12345
      xeng mark-posted 9001 --platform linkedin
    """
    _validate_platform(platform)
    init_db()
    with connect() as conn:
        draft = _lookup_draft(conn, draft_id)
        if draft is None:
            typer.echo(
                f"ERROR: draft {draft_id} not found in drafts or hand_drafts",
                err=True,
            )
            raise typer.Exit(2)
        now = dt.datetime.now(dt.UTC).isoformat()
        # Wrap both writes in a single BEGIN/COMMIT so a failure on the second
        # INSERT (recent_posted) rolls back the first (draft_decisions). Without
        # this, a constraint violation or disk-full mid-call leaves the
        # decision recorded but engagement-sync state lost — and a retry
        # would dual-insert into draft_decisions (no UNIQUE constraint).
        # The connect() context manager auto-commits on clean exit and
        # auto-rolls-back on exception (sqlite3 default). The explicit BEGIN
        # makes the boundary visible.
        conn.execute("BEGIN")
        try:
            conn.execute(
                "INSERT OR IGNORE INTO draft_decisions "
                "(draft_id, angle_id, platform, outcome, skip_reason, created_at) "
                "VALUES (?, ?, ?, 'ship', NULL, ?)",
                (draft_id, draft["angle_id"], platform, now),
            )
            if platform == "x":
                conn.execute(
                    "INSERT INTO recent_posted "
                    "(text, posted_at, draft_id, angle_id, pillar, tweet_url) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (draft["body"], now, draft_id, draft["angle_id"],
                     draft["pillar"], tweet_url),
                )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    _print_json({
        "draft_id": draft_id,
        "platform": platform,
        "outcome": "ship",
        "marked_at": now,
        "tweet_url": tweet_url,
        "source": draft["source"],
    })


@app.command("skip-draft")
def skip_draft(draft_id: int, reason: str = "", platform: str = "x"):
    """Skip a draft with a structured reason. Writes draft_decisions only.

    `--reason` must be one of: voice_off, factual_unverifiable, off_pillar,
    duplicate, no_time, other. `holdout-export` filters `no_time` rows
    (operator-noise) before partitioning by platform.

    Usage:
      xeng skip-draft 174 --reason voice_off
      xeng skip-draft 9001 --platform linkedin --reason off_pillar
    """
    _validate_platform(platform)
    if not reason:
        typer.echo(
            f"ERROR: --reason is required (one of {list(_SKIP_REASONS)})",
            err=True,
        )
        raise typer.Exit(2)
    if reason not in _SKIP_REASONS:
        typer.echo(
            f"ERROR: --reason must be one of {list(_SKIP_REASONS)}, got {reason!r}",
            err=True,
        )
        raise typer.Exit(2)
    init_db()
    with connect() as conn:
        draft = _lookup_draft(conn, draft_id)
        if draft is None:
            typer.echo(
                f"ERROR: draft {draft_id} not found in drafts or hand_drafts",
                err=True,
            )
            raise typer.Exit(2)
        now = dt.datetime.now(dt.UTC).isoformat()
        conn.execute(
            "INSERT OR IGNORE INTO draft_decisions "
            "(draft_id, angle_id, platform, outcome, skip_reason, created_at) "
            "VALUES (?, ?, ?, 'skip', ?, ?)",
            (draft_id, draft["angle_id"], platform, reason, now),
        )
    _print_json({
        "draft_id": draft_id,
        "platform": platform,
        "outcome": "skip",
        "skip_reason": reason,
        "marked_at": now,
        "source": draft["source"],
    })


@app.command("posted")
def posted(days: int = 30, limit: int = 50):
    """List drafts JR has marked as posted, with engagement if synced."""
    cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).isoformat()
    with connect() as conn:
        rows = conn.execute(
            "SELECT posted_id, posted_at, draft_id, pillar, tweet_url, likes, "
            "retweets, replies, views, substr(text, 1, 120) as snippet "
            "FROM recent_posted WHERE posted_at >= ? "
            "ORDER BY posted_at DESC LIMIT ?",
            (cutoff, limit),
        ).fetchall()
    _print_json([dict(r) for r in rows])


@app.command("sync-engagement")
def sync_engagement(days: int = 7):
    """Fetch fresh engagement counts for posted tweets via twitterapi.io.

    Looks up each posted draft by tweet_url, pulls latest likes/RT/replies/views,
    updates recent_posted. Run weekly to feed real-world engagement signal back
    into voice/exemplars curation.
    """
    init_db()
    cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).isoformat()
    with connect() as conn:
        rows = conn.execute(
            "SELECT posted_id, tweet_url FROM recent_posted "
            "WHERE posted_at >= ? AND tweet_url != ''",
            (cutoff,),
        ).fetchall()

    if not rows:
        _print_json({"synced": 0, "reason": "no posted drafts with tweet_url"})
        return

    # Extract tweet IDs from URLs (format: https://x.com/user/status/<id>)
    import re
    api_key = _key()
    synced = 0
    failed = 0
    for r in rows:
        m = re.search(r"/status/(\d+)", r["tweet_url"] or "")
        if not m:
            failed += 1
            continue
        tid = m.group(1)
        try:
            data = pull_mod._twitterapi_get(
                "/twitter/tweets", {"tweet_ids": tid}, api_key
            )
            tweets = data.get("tweets") or []
            if not tweets:
                failed += 1
                continue
            t = tweets[0]
            with connect() as conn:
                conn.execute(
                    "UPDATE recent_posted SET likes=?, retweets=?, replies=?, "
                    "views=?, last_synced_at=? WHERE posted_id=?",
                    (
                        int(t.get("likeCount") or 0),
                        int(t.get("retweetCount") or 0),
                        int(t.get("replyCount") or 0),
                        int(t.get("viewCount") or 0),
                        dt.datetime.now(dt.UTC).isoformat(),
                        r["posted_id"],
                    ),
                )
            synced += 1
        except Exception:
            failed += 1
    _print_json({"synced": synced, "failed": failed, "total": len(rows)})


@app.command("info")
def info():
    """Print path map + state stats so master agent can orient."""
    today = dt.date.today().isoformat()
    with connect() as conn:
        n_tweets = conn.execute("SELECT COUNT(*) FROM tweets").fetchone()[0]
        n_rel = conn.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
        n_rss = conn.execute("SELECT COUNT(*) FROM rss_items").fetchone()[0]
        n_angles = conn.execute("SELECT COUNT(*) FROM angles WHERE run_date=?", (today,)).fetchone()[0]
        n_drafts = conn.execute(
            "SELECT COUNT(*) FROM drafts WHERE angle_id IN (SELECT angle_id FROM angles WHERE run_date=?)",
            (today,)
        ).fetchone()[0]
    _print_json({
        "today": today,
        "state_db": str(Path(__file__).parent / "state.db"),
        "voice_dir": str(VOICE_DIR),
        "vault_dir": str(Path(__file__).parent / "vault"),
        "drafts_dir": str(Path(__file__).parent / "drafts"),
        "sources_yaml": str(Path(__file__).parent / "sources.yaml"),
        "stats": {
            "tweets_total": n_tweets,
            "releases_total": n_rel,
            "rss_items_total": n_rss,
            "angles_today": n_angles,
            "drafts_today": n_drafts,
        },
    })


if __name__ == "__main__":
    app()
