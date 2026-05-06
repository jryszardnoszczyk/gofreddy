# x_engine — research-heavy tweet drafting pipeline

Pulls tweets from priority X creators + GitHub releases + RSS feeds, ranks by resonance, generates 5 daily drafts in JR's voice, writes them to `drafts/YYYY-MM-DD.md` for manual posting on x.com.

**No automated posting. Manual only.** This pipeline reads — JR posts.

## Setup

```bash
cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy
uv sync                                # ensures deps + installs `xeng` CLI
```

Required env (already in `gofreddy/.env`):
- `TWITTERAPI_IO_KEY` — twitterapi.io read access

Required CLI (already installed):
- `codex` — Codex CLI, gpt-5.5 via JR's ChatGPT subscription. **No paid API.** $0/run.
- `xeng` — auto-installed by `uv sync`. Tool surface for the agentic master + ad-hoc inspection.

Optional env tuning:
- `X_ENGINE_REASONING_EFFORT` — `low` (default), `medium`, `high`. Higher = quality, slower.
- `X_ENGINE_TIMEOUT_S` — per-call timeout, default 180s.
- `X_ENGINE_CODEX_BIN` — path override if `codex` not on PATH.
- `X_ENGINE_AGENTIC_TIMEOUT_S` — master codex session timeout, default 900s.

## Two modes

### Mode A — Deterministic (default; fast, predictable)

```bash
./x_engine/run.sh
```

Python orchestrates. 4 phases run in order: pull → rank → topic_pick → draft → write. Each LLM call (topic_pick, writer, critic) goes to codex via subprocess with strict JSON Schema. **~80s end-to-end, $0/run.**

When to use: every day. Predictable, repeatable, fast.

### Mode B — Agentic (master codex orchestrates)

```bash
uv run python -m x_engine.agentic --effort medium
```

A master codex session reads voice + sources, decides which angles to draft, spawns parallel `xeng draft-angle` subagents, can adaptively reroll angles that don't pass, writes outputs. **~3-4 min, $0/run.**

When to use: when you want emergent behavior — e.g. master can decide-don't-ship-this-angle and pick a replacement, or front-load a specific theme via `--extra-instructions "today emphasize harness"`.

Tradeoff: 3× slower than deterministic, but flexible. Same final-quality guarantees (drafting goes through the same `xeng draft-angle` → deterministic 1-5 critic).

## Daily schedule (launchd)

```bash
./x_engine/install_schedule.sh                     # symlinks plist + loads it
launchctl start com.jryszardnoszczyk.x-engine      # run NOW (skip the 06:30 wait)
launchctl list | grep x-engine                     # status
launchctl unload ~/Library/LaunchAgents/com.jryszardnoszczyk.x-engine.plist  # disable
```

Logs land in `x_engine/logs/run-YYYY-MM-DD.log` (gitignored, append-mode).

## Structure

```
voice/        # READ-ONLY voice files (about-me, profile, hooks, anti-ai, exemplars, no-go)
prompts/      # writer, critic, topic_picker, slop_check, agentic_master
schemas/      # JSON Schemas for codex --output-schema (topic_picker, writer, critic)
pipeline/     # db, pull, rank, llm, topic_pick, draft, slop_gate, compose
cli.py        # `xeng` CLI (typer entry point)
agentic.py    # master codex entrypoint
sources.yaml  # priority users + search queries + GitHub repos + RSS feeds
vault/        # generated daily evidence (gitignored)
drafts/       # generated daily drafts (gitignored)
state.db      # SQLite local state (gitignored)
logs/         # daily run logs (gitignored)
run.sh        # deterministic-mode entrypoint (used by launchd)
install_schedule.sh    # one-shot launchd installer
com.jryszardnoszczyk.x-engine.plist   # launchd schedule
bootstrap_from_cache.py    # dev-only: hydrate state.db from /tmp/x-recon/
```

## Sources covered

- **8 priority X creators** (curated 2026-05-06, all in AI / agent / agency space): `@AlfieJCarter @gkisokay @jack_9947 @helloitsaustin @MichLieben @ecomchigga @rubenhassid @N01ennn`
- **26 search queries** spanning JR's content pillars: AI search/SEO/GEO, paid media, CRO, lifecycle, PLG, brand positioning, content strategy, attribution, MarTech analytics, plus AI marketing meta. (See `sources.yaml` for full list.)
- **9 GitHub repos** for release watching: anthropics/claude-code, openai/openai-agents-python, langchain-ai/langgraph, etc.
- **4 RSS feeds**: openai news, langchain changelog, GTM Engineer substack, Latent.Space.

Edit `sources.yaml` to add/remove. Changes propagate immediately.

## `xeng` CLI — direct tool surface

Independent of compose modes. Use for ad-hoc inspection or scripting:

```bash
xeng info                                 # state.db stats + paths
xeng top-tweets --hours 48 --min-likes 30 # ranked top from DB (JSON)
xeng top-releases --days 7
xeng pull-search 'AI marketing within_time:48h min_faves:50' --label adhoc
xeng slop-check "Most people don't realize how powerful AI is"
xeng list-shipped --days 14               # texts JR already posted
xeng voice                                # full concatenated voice substrate
xeng pillars                              # JR's content pillars
xeng write-vault                          # regenerate vault file from today's angles
xeng write-drafts --limit 5               # regenerate drafts file (pillar-deduped)
```

## Architecture

See `docs/research/2026-05-06-x-content-engine.md` for full research + decisions.

**v1 (current):** Static voice files. No RAG. Hand-curated `voice/exemplars.md` with 20-30 niche posts substitutes for retrieval over personal corpus.

**v2 (planned):** Add RAG over JR's X archive once ≥100 organic tweets exist. ~200 LOC + ingest module.

## Cost

~$3-10/mo operating: ~$0.30/day twitterapi.io reads + **$0/day** LLM (codex/ChatGPT subscription).

Performance progression today (2026-05-06):

| Stage | Cost/run | Wall time |
|---|---|---|
| Initial OpenAI gpt-4.1 | $0.42 | 108s (cached) |
| Stricter prompts + mini critic | $0.24 | 97s |
| Codex CLI refactor | $0.00 | 109s |
| + Outer 5-parallel | $0.00 | 121s (live full) |
| + Inner critic-parallel | $0.00 | 78s (cached) |
| + Parallel pulls | **$0.00** | **82s (live full)** |
| Agentic mode | $0.00 | ~220s (live full) |

## Quality guarantees

Every draft that ships through either mode passes:
1. **Writer prompt** — voice substrate + angle + 3 hook strategies (observation / contradiction / lived-experience)
2. **Critic** with JSON Schema scoring (voice / factual / hook / slop, all integers 1-5)
3. **Factual veto** — any invented number, name, quote, or date NOT in source_text → caps factual_specificity at 1, blocks ship
4. **Slop gate** — deterministic regex against ~50 banned phrases + em-dashes + parallel-structure formulas + 5-gram dedup vs `voice/exemplars.md`
5. **Pillar diversity** — top-5 ship list prefers distinct content pillars before doubling up
6. **Ship gate** — `score_avg >= 4` AND `voice_match >= 4` AND `factual_veto = false`

## Tests

```bash
uv run pytest x_engine/tests/         # 37 passing
```
