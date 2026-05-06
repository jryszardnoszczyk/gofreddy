# x_engine — research-heavy tweet drafting pipeline

Pulls tweets from priority X creators + GitHub releases + RSS feeds, ranks by resonance, generates 5 daily drafts in JR's voice, writes them to `drafts/YYYY-MM-DD.md` for manual posting on x.com.

**No automated posting. Manual only.** This pipeline reads — JR posts.

## Setup

```bash
cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy
uv sync                                # ensures deps in top-level pyproject
```

Required env (already in `gofreddy/.env`):
- `TWITTERAPI_IO_KEY` — twitterapi.io read access

Required CLI (already installed):
- `codex` (Codex CLI, gpt-5.5 via JR's ChatGPT subscription) — used for all writer/critic/topic-picker calls. **No paid API.** $0/run.

Optional env tuning:
- `X_ENGINE_REASONING_EFFORT` — `low` (default), `medium`, `high`. Higher = better quality, slower.
- `X_ENGINE_TIMEOUT_S` — per-call timeout, default 180s.
- `X_ENGINE_CODEX_BIN` — path override if `codex` not on PATH.

## Daily run

```bash
cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy
./x_engine/run.sh
```

This will:
1. Pull last-24h tweets from `x_engine/sources.yaml` priority users
2. Rank by resonance, dedupe
3. Pick 5-10 candidate angles → `x_engine/vault/YYYY-MM-DD.md`
4. Generate 3 variants per angle, critic-rated, slop-gated
5. Write top 5 → `x_engine/drafts/YYYY-MM-DD.md`

## Structure

```
voice/      # READ-ONLY voice files (about-me, profile, hooks, anti-ai, exemplars, no-go-topics)
prompts/    # writer, critic, topic_picker, slop_check
pipeline/   # db, pull, rank, llm, topic_pick, draft, slop_gate, compose
sources.yaml # priority users + GitHub repos + RSS feeds
vault/      # generated daily evidence (gitignored)
drafts/     # generated daily drafts (gitignored)
state.db    # SQLite local state (gitignored)
```

## Architecture

See `docs/research/2026-05-06-x-content-engine.md` for full research + decisions.

**v1 (current):** Static voice files only — no RAG. Hand-curated `voice/exemplars.md` with 20-30 niche posts substitutes for retrieval over personal corpus.

**v2 (planned):** Add RAG over JR's X archive once ≥100 organic tweets exist. ~200 LOC + ingest module.

## Cost

~$3-10/mo operating: ~$0.30/day twitterapi.io reads + **$0/day** for LLM (Codex CLI uses JR's ChatGPT subscription).
Original v1 used OpenAI gpt-4.1 direct API at ~$0.24/day; codex backend (May 2026 refactor) drops that to zero.
