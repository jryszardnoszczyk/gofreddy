# X Content Engine — Research & Implementation Plan

**Date:** 2026-05-06
**Goal:** Research-heavy automated tweet-drafting pipeline. Pull niche tweets, surface what's resonating, draft in JR's voice, output ~5 drafts/day. Manual posting initially.
**Operator:** JR (jryszardnoszczyk)
**Status:** Research complete. Decisions locked 2026-05-06. Ready for Unit 0.

## Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-05-06 | **Niche: AI-native marketing agency / AI / coding agents** | gofreddy is an AI marketing agency product; JR's professional context |
| 2026-05-06 | **Repo location: `gofreddy/x-engine/`** | Folded into existing repo, shares `.env` |
| 2026-05-06 | **v1 = no RAG** (static voice files only) | JR's X account is fresh/empty — no personal corpus to retrieve from |
| 2026-05-06 | **v2 = add RAG when JR has ≥100 organic tweets** | Bolt RAG on once corpus is meaningful |
| 2026-05-06 | **Archive request in parallel** | JR requesting now even though small; sets up v2 infra |
| 2026-05-06 | **AlfieJCarter playbook: engage** | Free, ~5 min, gets reference `profile.md` + `hooks.md` schema |
| 2026-05-06 | Tonal anchors: deferred | Defaults to creators surfaced in research (§2). Can refine in Unit 0. |

---

## TL;DR

**Build, don't fork.** ~500 LOC Python for v1 (no RAG), 2 days, ~$15/month operating cost. Add RAG (~200 LOC) in v2 once corpus exists.

**Why not fork:** Each candidate is wrong-shaped (clio = LinkedIn + no license + Slack/ClickUp wired in; last30days = research-only no remix; social-media-agent = heavy LangGraph; n8n template = voice-only no discovery layer). Adapting any of them = ~3-5 days and you carry their wrong assumptions forward.

**Why no RAG in v1:** JR's X account is fresh — no personal corpus to retrieve from. Voice cloning needs ~200+ tweets minimum for retrieval to outperform a static style guide. We start with static voice files (Hassid + AlfieJCarter pattern); RAG bolts on as a v2 unit once JR has organic posts.

**What to reuse as components:**
- `dorukardahan/twitterapi-io-skill` (already installed) — discovery primitive
- `enablement-ch/clio-ghostwriter` prompt patterns (factual-integrity veto, QAResult dataclass, 3-iteration max, two-phase propose/generate)
- `@rubenhassid`'s `anti-ai-writing-style.md` template (ban-list approach, free download)
- `@AlfieJCarter`'s `profile.md` + `hooks.md` schema (positive voice file structure)
- `@gkisokay`'s structured-evidence vault format (research → typed records, never raw scrape)
- Hand-curated `voice/exemplars.md` of 20-30 high-quality posts from the niche (replaces RAG for v1)

**Architecture in one paragraph (v1):** A nightly research agent pulls tweets from priority X lists + GitHub releases + AI/marketing newsletters, normalizes them into a structured evidence vault (gkisokay pattern), ranks by resonance, picks 5-10 candidate angles. A morning drafter loads static voice files + 20-30 hand-curated exemplars, generates 3 variants per angle, runs a critic-revise loop with a factual veto, gates against banned phrases, writes top 5 to `drafts/YYYY-MM-DD.md` for manual posting.

---

## Table of Contents

1. [Validated Patterns from X (May 2026)](#1-validated-patterns)
2. [Creator-by-Creator Deep Dive](#2-creators)
3. [Existing Implementations Audit](#3-existing-implementations)
4. [Component Inventory](#4-components)
5. [Build vs Reuse Decision Matrix](#5-build-vs-reuse)
6. [Final Recommendation + Architecture](#6-final-recommendation)
7. [Implementation Plan](#7-implementation-plan)
8. [Cost Model](#8-cost-model)
9. [Risks + Failure Modes](#9-risks)
10. [Sources](#10-sources)

---

<a id="1-validated-patterns"></a>
## 1. Validated Patterns from X (May 2026)

Five architectural patterns appear *independently* across creators, with engagement metrics that confirm they're not theoretical:

### Pattern 1: Voice files as static `.md`, not prompts

Both **@rubenhassid (78k followers, 1109 likes on the canonical thread)** and **@AlfieJCarter (16k, 618 likes)** converged on the same recipe: voice lives in 2-4 markdown files in a Claude Cowork / `.claude/skills/` folder, read on every session. Hassid uses `about-me.md` + `anti-ai-writing-style.md` (the ban list) + `my-company.md`. AlfieJCarter uses `profile.md` (identity + stories + voice rules) + `hooks.md` (proven formats + no-go openers).

Hassid's 35-word universal prompt (319 likes):
> "I want to [TASK] for [SUCCESS CRITERIA]. Read my anti-AI writing style file first. It contains every known pattern of AI writing I want to avoid. Apply these as rules to everything you write for me."

The ban-list approach (~1,168 lines of "don't write like this") consistently outperforms positive style prompts. Hassid's view: **80% of voice cloning is exclusion, not imitation.**

### Pattern 2: Upstream research agent, structured evidence vault

**@gkisokay (25k followers, 1,160 likes on the canonical thread)** is the clearest articulation:
> "raw scraping the web is not research. If the information is not structured, your other agents can't use it. Every agent in my setup reads from the research vault first."

His research agent watches:
- Own X posts/replies
- Priority X lists
- GitHub releases + repo activity
- arXiv
- Hugging Face
- Blogs/RSS
- Targeted domain/news searches
- Browser enrichment on selected items
- Package momentum
- Community sources

It writes structured evidence: links + dates + summaries + claims + why-it-matters. **Never raw text.** Every downstream agent reads from this vault.

Quote with 327 likes:
> "Memory contamination is what kills multi-agent setups. The fix is not better prompts. It is forcing every agent to read structured evidence before doing anything and to write structured evidence."

### Pattern 3: 3-draft generation, not 1

**@AlfieJCarter, @jack_9947 (2,090 likes!), @MichLieben** all converge on generating multiple variants per topic. The reasoning:
- Singular drafts trigger sunk-cost editing — you ship the one you got
- 3-5 variants force selection — you compare and pick
- Variants reveal which hook actually fits before you commit

Format consistently: "3 options per post" matched to topic + audience tone.

### Pattern 4: Engagement-ranked-feed for topic discovery

**@enablement-ch/clio-ghostwriter** (the only OSS reference for this exact pattern, ~1,200 LOC) sorts scraped competitor posts by `engagement_rate` and shows the top-40 to a topic-picker LLM. The LLM identifies themes, deliberately avoids topics the user already covered recently, returns weekly topics with rationale.

This is the bridge between Pattern 2 (research) and the writer: the research agent surfaces what's hot; the topic-picker decides what's hot for **you specifically**.

### Pattern 5: Critic-revise loop with factual veto

Every well-built pipeline (clio, social-media-agent, ColdIQ skills, AlfieJCarter playbook) has a critic step. The strongest version is clio's `qa_agent.py`:
- Multi-criterion rubric (voice/factuality/hook/specificity 1-10)
- Hard veto: any invented number, name, or quote → score capped at 5.0
- Max 3 revisions, threshold 7.0/10
- Factual specificity is the single best signal of "actually-shippable" vs "AI slop"

@rubenhassid's two-step variant (181 likes): always run a final pass with prompt *"Audit your text using the anti-ai-writing-style.md file from your folder."*

---

<a id="2-creators"></a>
## 2. Creator-by-Creator Deep Dive

### @AlfieJCarter — 16,423 followers, Conigma founder

The most-developed publicly-shared playbook. Files described:

- `profile.md` — personal stories, professional context, voice rules
- `hooks.md` — proven formats + no-go openers
- 3-draft generation per topic
- Photo matching by filename (no vision API needed)
- Playwright MCP for publish (we drop this, manual posting)
- Sunday-morning batch fills full week

**Distributables (DM-gated by like + follow + comment):**
- "Claude Code GTM Engineering Playbook" — 8 sections
- "Claude Cowork Playbook for GTM Engineers" — 9 sections
- "Claude Code + Claude Design B2B GTM Scaling Playbook"
- "Marketing Playbook" with brand-extraction skill, multi-skill orchestration via CLAUDE.md, Notion auto-sync
- LinkedIn skill (the original 618-like thread) — comment "SKILL"
- Carousel variant — comment "CAROUSEL"

No public GitHub. **Action: like + follow + comment "SKILL" on https://x.com/AlfieJCarter/status/2048785952697463222 — get the actual files he ships, fork the schema for X.**

### @gkisokay (Graeme) — 25,055 followers, Amplifi founder

Hermes/OpenClaw multi-agent operator. Six-agent fan-out (May 6 tweet, 36 likes):
1. **Research** — only one allowed on open web
2. **Main** — strategy and decisions
3. **Coder** — implementation buildroom
4. **Content** — drafting
5. **Subconscious** — long-term memory
6. **QA** — verification

Each agent has its own `SOUL.md`, configs, jobs, goals. Communication via shared vault, never directly. Lanes = dedicated Discord channels.

Six-step build (1,160 likes):
1. Pick a domain
2. Give it sources
3. Define signal
4. Save evidence (links/dates/summaries/claims/why-it-matters)
5. Daily brief to Discord/Slack/Notion/Obsidian/markdown
6. Feedback loop ("more like this", "this source is noisy")

Said publicly there's "enough demand to share a complete research agent setup guide." **Not yet published — follow him for release.**

Stack: Hermes (Nous Research) + OpenClaw. Public site https://gkisokay.com.

**Action: follow @gkisokay; reply on his "setup guide" tweet asking for ETA; subscribe if Substack exists.**

### @rubenhassid — 78k followers

Voice-cloning canon. Three free `.md` files at https://how-to-ai.guide:
- `about-me.md` — built via 100-question "Taste Interviewer" interview, compressed
- `anti-ai-writing-style.md` — the ban list (~1,168 lines), 80% of contents = what to *avoid*
- `my-company.md`

The full system has 8 files (Substack note c-241161890):
1. about-me.md
2. voice-profile.md
3. anti-ai-writing-style.md
4. The Cowork Folder = ABOUT ME / PROJECTS / TEMPLATES / OUTPUTS
5. Global Instructions (Settings → Cowork)
6. The 35-word universal prompt
7. Connectors — Slack/Drive/Notion/Gmail/Figma
8. Plugins — domain skill bundles

The viral 2,174-like recipe (May 2):
> "1. Open Google Doc / 2. Paste prompt below / 3. Name it 'anti-ai-writing-style' / 4. Save .md / 5. Upload to Claude / 6. To download mine: https://t.co/psB7XxAv8w / 7. Subscribe free / 8. Open welcome email / 9. Hit auto-reply / 10. Notion link → download .md files."

Source method: copy Wikipedia "Signs of AI writing" → seed → expand into ban list.

Community port to Claude Skill format: https://github.com/conorbronsdon/avoid-ai-writing.

**Action: subscribe to https://how-to-ai.guide; download all `.md files`; lift `anti-ai-writing-style.md` verbatim into `voice/` folder.**

### @Av1dlive (Avid) — 11,045 followers, aggregator

Citing **@coreyganim** (46,933 followers, "Build With AI" classroom $799/yr). Av1d's 5-step recipe is a summary of Corey's:

1. Pick agent platform (MaxClaw/OpenClaw)
2. Build brand voice skill first using **X archives**
3. Add a "last 30 days" research skill
4. Build a quote-tweet skill/format
5. 30 min/day reviewing drafts, not writing them

His original work: https://github.com/codejunkie99/agentic-stack (harness-agnostic memory for AI agents).

**Action: archive the 5-step list as our high-level operator loop (matches our plan exactly). The "21M views/mo case study" lives behind Corey's paywall — skip.**

### @MichLieben (Michel Lieben, ColdIQ) — 9,131 followers

ColdIQ founder, $7M ARR GTM agency. Public 4-Layer GTM Stack:

1. **Signal** — PredictLeads, Common Room, Attention, RB2B
2. **Data** — Apify, Wiza, Prospeo, FullEnrich, Openmart, Apollo
3. **Action** — Instantly, lemlist, LinkedIn Ads
4. **Automation** — n8n + Claude API

5-pillar Claude Code skill library (~4,200 lines methodology, 7 master skills, 52 sub-skills):
- Cold Email — SPARK framework + 6 archetypes
- ICP Research — 5-dimension scoring + FITS qualification
- Signal Scoring — 4-category taxonomy + 12 trigger maps
- Campaign Analytics — 6-layer diagnostics
- Sales Intelligence — 7-layer transcript analysis

**Public repos:**
- https://github.com/sachacoldiq/ColdIQ-s-GTM-Skills (137 sales triggers, 34 templates, 11 GTM plays)
- https://github.com/kenny589/gtm-flywheel (head-of-GTM Kenny's starter kit, 154-lead working demo)
- https://coldiq.com/skills-directory

**Action: clone `sachacoldiq/ColdIQ-s-GTM-Skills` to study the master-skill + sub-skill file structure. Their GTM scope ≠ our scope, but the file/folder layout transfers.**

### @ecomchigga — 11,621 followers (the original spark)

Validated the use case verbatim:
> "i write 3 tweets a day across 4 accounts and i haven't actually typed a tweet myself in 5 months. claude writes them. i edit. i post. 12 minutes total."

> "nobody on x writes their own tweets anymore. every account doing real numbers is running claude with a system underneath."

No public files. The methodology is the methodology. **No action — confirmation only.**

### @jack_9947 — 1,907 followers, 2,090 likes on viral Claude marketing skill stack

Viral tweet describes a stack that "plans campaigns, writes social posts, designs carousels, and produces animated videos from a single brief every week." Files he distributes via Notion docs:
- "Opus 4.7 and ChatGPT 5.5 GTM Engineer's Playbook" — 7 modules
- "Claude Code + ChatGPT + Gemini Three-Brain GTM Setup" — 3 sections
- "Claude Co-work Live Artifacts playbook" — 2 sections
- "Claude Skills Playbook for GTM Engineers"

**Action: skim 1-2 of these for any structural insight not covered by AlfieJCarter; otherwise skip.**

### @selinaai_ — 6,473 followers, viral prompt threads (LinkedIn-focused)

7-prompt and 11-prompt threads for LinkedIn upgrade. Prompt-engineering content, not pipeline. **Action: ignore for our use case.**

---

<a id="3-existing-implementations"></a>
## 3. Existing Implementations Audit

| Repo | Stars | Pushed | Verdict | Reason |
|---|---|---|---|---|
| `mvanhorn/last30days-skill` | 24,874 | 2026-05-02 | **STUDY-AND-COMPOSE** | Best discovery skill on the planet. Pure research, no remix. Has cookie-auth fallback in `bird_x.py` if twitterapi.io fails. |
| `langchain-ai/social-media-agent` | 2,546 | 2026-05-06 | **STUDY** | Heavy LangGraph commitment. Lift the post-structure prompts (`prompts/index.ts`) and group-by-content pattern. Don't fork. |
| `enablement-ch/clio-ghostwriter` | 6 | 2026-03-09 | **FORK-PARTIAL (no license!)** | Closest pipeline shape. ~1,500 LOC of writer + QA + style guide is structurally lift-able BUT no LICENSE file = legally questionable. Use as reference only. |
| `dorukardahan/twitterapi-io-skill` | 6 | 2026-04-29 | **USE AS-IS** | Already installed. THE X tool layer. |
| `dorukardahan/twitterapi-io-mcp` | 5 | 2026-05-03 | **IGNORE** | Offline docs MCP. Not needed if skill is installed. |
| `Polsia-Inc/twitter-read-mcp` | 4 | 2026-01-30 | **IGNORE** | Wraps official Twitter API ($100+/mo). twitterapi.io is 30-60x cheaper. |
| `sachacoldiq/ColdIQ-s-GTM-Skills` | n/a | recent | **STUDY** | Master-skill + sub-skill file structure reference. GTM-shaped, our content-shaped — but the org pattern transfers. |
| `kenny589/gtm-flywheel` | n/a | recent | **STUDY** | Same. Real working starter kit. |
| `conorbronsdon/avoid-ai-writing` | n/a | recent | **MAYBE FORK** | Hassid's anti-ai-writing-style ported as a Skill. Could be the cleanest install path for that file. |
| n8n template 10672 (RAG voice) | n/a | 2 mo old | **STUDY** | Closest to voice-RAG architecture (Supabase pgvector, OpenAI gpt-4.1-mini). We swap pgvector → sqlite-vec for fewer moving parts. |

### Code-quality reads (the audit details)

**`mvanhorn/last30days-skill`:**
- 350+ KB of Python in `lib/`, modular per-source
- Real engineering: `evaluate_search_quality.py` harness, fixtures dir, plan docs in `docs/plans/`
- Recent commits = real bug fixes
- Lift-able: `bird_x.py` (X cookie auth + GraphQL) and `score.py`/`dedupe.py` patterns
- Skip: orchestrator, planner, fusion (overkill for our use case)

**`enablement-ch/clio-ghostwriter`:**
- 1,500-1,700 LOC across 8 modules (Python)
- Two-phase: PROPOSE (Mon: scrape → classify → topic_analyzer → Slack proposal) / GENERATE (Wed: read Slack feedback → write+QA loop → ClickUp tasks)
- Voice = style guide + ICP doc, NOT RAG (we upgrade this)
- Quality: tight, dataclasses, defensive try/except, factual-veto in QA grader
- **No LICENSE file** — strictly speaking can't fork. Lift patterns + structure as reference, write our own.

**`langchain-ai/social-media-agent`:**
- TypeScript + LangGraph
- Sub-graphs: `curate-data/`, `generate-post/`, `generate-thread/`, `repurposer/`, `find-and-generate-images/`, `reflection/`
- Hardcoded list ID, hardcoded few-shot examples (8.5 KB) — meant to be customized
- HITL via Slack ingest + Agent Inbox
- Production-grade but framework-heavy. Skip the framework, lift the prompts.

**n8n template 10672:**
- JSON workflow, self-hostable
- Ingest form (text + metadata) → Supabase pgvector → query form → Agent retrieves top-K → outputs `{post, quote, reply, image_prompt}`
- We replace pgvector with sqlite-vec (one less dependency, one fewer service)

---

<a id="4-components"></a>
## 4. Component Inventory

What we need, sourced from where:

| Component | Source | Status (v1) |
|---|---|---|
| **X API client** | `~/.claude/skills/twitterapi-io` | ✅ Installed |
| **API key** | `gofreddy/.env: TWITTERAPI_IO_KEY` | ✅ Saved + verified |
| **Discovery: search by query** | `/twitter/tweet/advanced_search` (with `within_time:`, not `since:`) | Documented in skill |
| **Discovery: user timelines** | `/twitter/user/last_tweets` | Documented in skill |
| **Discovery: list timelines** | `/twitter/list/tweets` (cheaper than per-user fan-out) | Documented in skill |
| **Voice files** | `voice/about-me.md`, `voice/profile.md`, `voice/hooks.md`, `voice/anti-ai-writing-style.md`, `voice/exemplars.md` | Build (Unit 0, manual) |
| **Static exemplars** | 20-30 hand-curated posts from niche creators (§2 surfaced 8 candidates) | Build (Unit 0) |
| **AlfieJCarter playbook** | DM-gated; like + follow + comment "SKILL" on his thread | JR action — yes |
| **Hassid voice files** | https://how-to-ai.guide → subscribe → email reply → Notion `.md files` | JR action |
| **X archive** | Twitter Settings → Your Twitter Data → Download (24-48h) | JR action — for v2 |
| **LLM writer** | Claude Sonnet 4.6 via Anthropic SDK | Already in `.env` (assumed) |
| **LLM critic** | Claude Sonnet 4.6 via Anthropic SDK | Same |
| **Critic prompt** | clio's QAResult dataclass + factual veto verbatim | Reference clio's `qa_agent.py` |
| **Slop gate** | banned-phrase regex + n-gram dedup vs voice/exemplars.md | Build (~40 LOC) |
| **Output queue** | `drafts/YYYY-MM-DD.md` (5 sections, paste-and-post) | Build |
| **Scheduler** | macOS launchd plist OR `cron` | Build |
| **State** | local SQLite (scraped_tweets, vault, drafts, feedback) | Build (~80 LOC schema) |
| **— v2 components (deferred) —** | | |
| Voice corpus DB | `corpus/archive.db` from X archive ZIP | Defer to v2 |
| Voice embeddings | OpenAI `text-embedding-3-small` | Defer to v2 |
| Vector store | sqlite-vec | Defer to v2 |
| Retrieve module | `pipeline/retrieve.py` (top-K voice exemplars) | Defer to v2 |

**No more open decisions for v1.** Tonal anchors default to the creators surfaced in §2 (AlfieJCarter, gkisokay, jack_9947, helloitsaustin, MichLieben). Refinable during Unit 0.

---

<a id="5-build-vs-reuse"></a>
## 5. Build vs Reuse Decision Matrix

| Approach | Effort | Quality | Lock-in | Verdict |
|---|---|---|---|---|
| Fork `clio-ghostwriter`, port LinkedIn → X | 3-5 days | Medium (vestigial Slack/ClickUp; no license; LinkedIn-shaped weekly cadence vs daily) | High (carry their architecture) | ❌ |
| Use `last30days-skill` as-is + write writer/critic | 2 days | High discovery / writer is custom anyway | Medium (depend on their orchestrator) | ❌ — discovery part is overkill (multi-source) and Twitter-only is simpler |
| Adopt `social-media-agent` (LangGraph) | 4-6 days | High infrastructure / no voice RAG | Very high (LangGraph framework) | ❌ |
| Self-host n8n template + add discovery | 2-3 days | Voice RAG good / discovery bolt-on weak | Medium (n8n + Supabase) | ❌ — two extra services |
| **Build from scratch in Python, ~700 LOC** | **2-3 days** | **High (custom-fit, no vestigial deps)** | **None (own all code)** | **✅** |

**Why "build" wins:** every fork candidate has the wrong shape and forces 2+ days of removal work before adding our value. From-scratch + reused patterns is the same effort with zero technical debt.

**Why this isn't NIH:** we're reusing the *prompts* from clio (which IS the hard part — anti-hallucination veto, multi-criterion rubric), the *file schema* from Hassid + AlfieJCarter (which solves voice cloning), and the *X tool layer* from twitterapi-io-skill (which IS the API surface). The custom code is the glue: pull → rank → retrieve → orchestrate → output. That glue is intentionally cheap.

---

<a id="6-final-recommendation"></a>
## 6. Final Recommendation + Architecture

### Repo location

**`gofreddy/x-engine/`** (locked 2026-05-06). Folded into the existing repo. Shares `.env` (already has `TWITTERAPI_IO_KEY`). Subdir, not a sibling — keeps it discoverable + tied to the product.

### Stack

- **Python 3.13** (matches gofreddy)
- **Anthropic SDK** for writer + critic (Sonnet 4.6 default; bump to Opus for one-off quality experiments)
- **OpenAI SDK** for embeddings (`text-embedding-3-small`, $0.02/1M tokens)
- **sqlite-vec** for vector search (single file, no server)
- **httpx** for twitterapi.io calls (sync; we don't need async)
- **pydantic** for typed records (signal, draft, evidence)
- **rich** for CLI output
- **pytest** for tests

### Folder structure (v1)

```
gofreddy/x-engine/
├── pyproject.toml               # x-engine deps (separate from gofreddy/Gemfile)
├── README.md
│
├── voice/                       # READ-ONLY voice files (hand-curated)
│   ├── about-me.md              # Who JR is, how he thinks (Hassid pattern, interview-derived)
│   ├── profile.md               # Identity + ICP + content pillars (AlfieJCarter pattern)
│   ├── hooks.md                 # Proven formats + no-go openers (AlfieJCarter pattern)
│   ├── anti-ai-writing-style.md # Ban list (Hassid verbatim, customized)
│   ├── exemplars.md             # 20-30 hand-curated niche posts (REPLACES RAG for v1)
│   └── no-go-topics.md          # Topics never to write about
│
├── sources.yaml                 # Niche seed config (locked: AI marketing / agents niche)
│   # x_lists: [...]              (build during Unit 0)
│   # x_users: [@AlfieJCarter, @gkisokay, @jack_9947, @helloitsaustin, @MichLieben, @ecomchigga, @rubenhassid, @N01ennn]
│   # github_repos: [anthropics/claude-code, langchain-ai/langgraph, openai/openai-agents-python, ...]
│   # rss: [https://www.anthropic.com/news/rss.xml, https://openai.com/blog/rss/, https://thegtmengineer.substack.com/feed, ...]
│
├── vault/                       # Structured evidence (gkisokay pattern)
│   └── 2026-05-06.md            # Today's evidence: links, dates, summaries, claims, why-it-matters
│
├── drafts/                      # Manual posting queue
│   └── 2026-05-06.md            # 5 sections: Draft 1-5 with rationale
│
├── prompts/
│   ├── topic_picker.md          # Given evidence + constraints, pick 5 angles
│   ├── writer.md                # Given angle + voice + exemplars, write 3 variants
│   ├── critic.md                # Score 1-5 voice/factuality/hook; factual veto
│   └── slop_check.md            # Final pass against anti-ai-writing-style.md
│
├── pipeline/
│   ├── __init__.py
│   ├── pull.py                  # twitterapi.io: search + list + user-timeline → SQLite
│   ├── rank.py                  # resonance score: (likes + 2*RT + 3*replies) / sqrt(views)
│   ├── topic_pick.py            # vault → 5-10 candidate angles
│   ├── draft.py                 # writer → critic → revise loop
│   ├── slop_gate.py             # banned phrases + n-gram dedup
│   ├── compose.py               # orchestrator (the only thing run.sh calls)
│   └── db.py                    # SQLite schema + helpers (state.db at repo root, gitignored)
│
├── tests/
│   ├── test_rank.py
│   ├── test_slop_gate.py
│   └── fixtures/sample_tweets.json
│
└── run.sh                       # Daily entrypoint: research + draft + write queue
```

**Files removed from v1 (deferred to v2):** `corpus/`, `pipeline/ingest_archive.py`, `pipeline/retrieve.py`, `tests/test_retrieve.py`. RAG bolts back on as a single new module + ingest script.

### Daily loop (sequenced, v1)

1. **Research phase** (`pipeline/pull.py` + `pipeline/rank.py` + topic_pick):
   - Pull last-24h tweets from priority X users (the 8 surfaced in §2 + niche-relevant adds)
   - Pull GitHub releases for watched repos (free GitHub API)
   - Optional: AI/marketing newsletter RSS
   - Score by resonance, dedupe by text similarity
   - Top-N (40-60) feed into topic-picker
   - Topic-picker outputs 5-10 candidate angles to `vault/YYYY-MM-DD.md` with structured fields (claim, source URL, why-it-matters)

2. **Drafting phase** (`pipeline/draft.py`):
   - Load all of `voice/*.md` (about-me + profile + hooks + anti-ai + exemplars) — single combined system prompt with prompt caching
   - Writer (Sonnet 4.6) generates 3 variants per angle, with hook variants split out
   - Critic (Sonnet 4.6) scores each (voice/factuality/hook 1-5)
   - If any score < 4 → revise once. If still < 4 → mark and ship lower-scored version with critic's note.
   - Slop gate: banned phrase regex + n-gram dedup vs `voice/exemplars.md` (so we don't accidentally clone exemplar phrases)
   - Top 5 (by avg score) → `drafts/YYYY-MM-DD.md` with critic notes + variant rationale

3. **Manual posting** (you):
   - Open `drafts/YYYY-MM-DD.md`
   - Pick 5 (or fewer) → copy to x.com
   - Optional: edit the variant slightly before posting
   - Mark posted in `state.db` for engagement tracking later

4. **Feedback loop** (weekly):
   - Pull engagement on posts you shipped vs drafts you skipped
   - Update `voice/profile.md` if patterns emerge
   - Refresh few-shot exemplar pool from last 30 days of your own tweets

### Voice file contents (templates)

All four files live in `voice/` and are read-only at runtime. Edit them by hand.

**`voice/about-me.md`** (Hassid pattern, ~150-300 lines):
- Identity, role, what you build
- How you think (mental models, hot takes you've defended)
- How you write (sentence length, punctuation habits, what triggers you)
- Domain knowledge & lived experience
- Audience (who reads, who you're not writing for)
- Off-limits (topics, accounts, opinions you don't share)

**`voice/profile.md`** (AlfieJCarter pattern, ~80-150 lines):
- ICP for posts (who's the reader)
- Goals per post type (educate, provoke, signal expertise, build network)
- Tonal anchors (3-5 example creators whose tone you respect; what you DO and DON'T copy from each)
- Content pillars (the 4-6 themes you own)

**`voice/hooks.md`** (AlfieJCarter pattern, ~100-200 lines):
- Section A: 20-30 hook formats that have worked for you historically (with examples)
- Section B: NO-GO openers (the ones that scream AI: "Most people don't realize", "Here's the thing", "Bookmark this", em-dashes, "It turns out", "Not X. Y." reversal, "Hot take:")
- Section C: structural patterns (single-sentence post, observation+contradiction, anecdote+lesson, list-as-thread, question-as-hook)

**`voice/anti-ai-writing-style.md`** (Hassid verbatim, customized):
- Download from how-to-ai.guide → Notion → `.md files`
- Customize: add JR-specific bans (your favored hedges, your specific tics, the slop patterns you most want to avoid)
- ~1,000-1,200 lines

### Why this beats the alternatives

- **Cleaner than fork-clio**: no LinkedIn vestiges, no Slack/ClickUp deps, no license ambiguity, daily cadence (vs weekly), our shape from line 1
- **Simpler than n8n template**: one Python script, no Supabase service, no n8n hosting, no JSON workflow editing
- **Lighter than social-media-agent**: no LangGraph framework, no TypeScript, no Slack ingest, no Arcade
- **More research-heavy than ecomchigga**: explicit research vault, structured evidence, ranked feed — not just "claude reads my notes"

---

<a id="7-implementation-plan"></a>
## 7. Implementation Plan

Sequenced units, each shippable independently.

### Unit 0: Voice files + niche seeds (2-3 hours, mostly manual)
- Create `gofreddy/x-engine/` directory + `pyproject.toml` + `.gitignore` for `state.db`/`drafts/`/`vault/`
- **JR actions in parallel:**
  - Subscribe to https://how-to-ai.guide → download all `.md files` from the email Notion link
  - Engage @AlfieJCarter's thread (https://x.com/AlfieJCarter/status/2048785952697463222): like + follow + comment "SKILL"
  - Request X archive at https://twitter.com/settings/your_twitter_data (parallel, for v2)
- Drop `anti-ai-writing-style.md` into `voice/` (verbatim from Hassid; light JR customization later)
- Hand-write `about-me.md` (Hassid 100-question interview, compressed; ~200 lines)
- Hand-write `profile.md` (AI-marketing-agency ICP + content pillars; ~80 lines)
- Hand-write `hooks.md` (proven formats — start with the formats observed in §2 creators; ~100 lines)
- Hand-curate `voice/exemplars.md`: 20-30 high-quality niche posts from @AlfieJCarter, @gkisokay, @jack_9947, @helloitsaustin, @MichLieben, @ecomchigga, @rubenhassid, @N01ennn (with explicit "study STRUCTURE not voice" note at top)
- Author `sources.yaml`: prefilled with the same 8 creators + the curated GitHub repos and RSS feeds
- **Output:** voice files done, sources locked, ready for code.

### Unit 1: REMOVED in v1
> Was: X archive ingest. v1 has no RAG, so no ingest needed. JR requests archive in Unit 0 anyway for v2.

### Unit 2: twitterapi.io pull layer (3-4 hours)
- `pipeline/pull.py`:
  - `pull_list(list_id)` → tweets from a list
  - `pull_user(username, since_hours=24)` → user timeline
  - `search(query, within_time="24h")` → advanced_search (respect degradation: hourly windows if needed)
  - All write to `state.db` with dedupe on `tweet_id`
- `pipeline/rank.py`:
  - `resonance_score(tweet)` = `(likes + 2*RT + 3*replies) / sqrt(max(views, 1))`
  - `dedupe(tweets, threshold=0.85)` via embedding similarity
- Test: `python -m pipeline.pull --niche-config sources.yaml`

### Unit 3: Vault + topic picker (2-3 hours)
- `pipeline/topic_pick.py`:
  - Reads ranked tweets + GitHub releases (if any)
  - Reads `voice/no-go-topics.md`
  - Reads recently-posted from `state.db` (avoid repetition)
  - Calls Sonnet 4.6 with `prompts/topic_picker.md` + top-50 ranked items
  - Writes structured records to `vault/YYYY-MM-DD.md`:
    ```
    ## Angle 1: [headline]
    **Source:** [tweet URL or repo URL]
    **Claim:** [the specific assertion]
    **Why it matters:** [one paragraph]
    **Suggested format:** [single-tweet | thread | quote-tweet]
    **Confidence:** [high|medium]
    ```

### Unit 4: Drafter + critic (3-4 hours)
- `pipeline/draft.py`:
  - Load all `voice/*.md` once at startup → single combined system prompt block (Anthropic prompt caching: ~9 cache hits per run, near-free)
  - For each angle:
    1. Writer call with `prompts/writer.md` + voice block + angle → 3 variants
    2. Critic call with `prompts/critic.md` + variant + exemplars → score JSON
    3. If avg < 4: revise (max 1 revision)
- `prompts/critic.md` (verbatim from clio's pattern):
  ```
  Score this draft on:
  - voice_match: 1-5 (does it sound like the user, given exemplars?)
  - factual_specificity: 1-5 (specific numbers, names, claims, vs vague gestures?)
  - hook_strength: 1-5 (would I read past the first line?)

  HARD VETO: if the draft contains an invented number, name, quote, or date that isn't grounded in the source URL, cap factual_specificity at 1 and revise.

  If avg score < 4, return REVISED draft. Else UNCHANGED.
  ```

### Unit 5: Slop gate + queue (1-2 hours)
- `pipeline/slop_gate.py`:
  - Regex: banned phrases from `voice/anti-ai-writing-style.md`
  - 5-gram check vs `corpus/archive.db` (kills self-plagiarism)
  - Em-dash check (Hassid's flag)
  - Returns (passed: bool, reasons: list[str])
- `pipeline/compose.py`:
  - Orchestrator: pull → rank → topic_pick → draft → slop_gate → write `drafts/YYYY-MM-DD.md`
- `drafts/YYYY-MM-DD.md` format:
  ```
  # X drafts — 2026-05-07

  ## Draft 1 — voice 4.5 / fact 5 / hook 4 — score 4.5
  [tweet text]

  **Angle:** [from vault]
  **Source:** [URL]
  **Critic notes:** [what's strong, any reservations]
  **Variants considered:** [variants 2 + 3 with score]

  ---

  ## Draft 2 — ...
  ```

### Unit 6: Schedule + dogfood (1 hour + 1 week)
- `run.sh`: bash entrypoint that calls `python -m pipeline.compose`
- launchd plist OR cron: daily 6am
- **Dogfood for 1 week** before declaring shippable. Track:
  - How many drafts are usable as-is (target: 2-3 of 5)
  - How many need light edits (target: 2-3 of 5)
  - How many are unusable (target: 0-1 of 5)
- Iterate `prompts/writer.md` and `voice/hooks.md` based on actual misses.

### Unit 7 (optional, week 2+): Engagement feedback loop
- Pull engagement metrics on shipped tweets (weekly)
- Compare to skipped variants
- Update `voice/hooks.md` (move winners to top, retire losers)
- Update `voice/exemplars.md` (replace weakest 3 with JR's own top 3 organic posts as the corpus grows)

### Unit 8 (v2, when JR has ≥100 organic tweets): Add RAG
- Implement `pipeline/ingest_archive.py` (parses `tweets.js` from X archive ZIP)
- Embed with `text-embedding-3-small` ($0.003 one-time)
- Store in `corpus/archive.db` via sqlite-vec
- Implement `pipeline/retrieve.py` (top-K voice exemplars by cosine similarity)
- Update `pipeline/draft.py`: replace `voice/exemplars.md` with retrieved-exemplars block
- Keep `voice/exemplars.md` as a fallback / cold-start mechanism
- Estimated effort: ~200 LOC, 3-4 hours

---

<a id="8-cost-model"></a>
## 8. Cost Model

### Setup costs (one-time)
- twitterapi.io: $0 (using $0.10 free credits for now)
- X archive embed: $0 in v1 (deferred to v2; ~$0.003 when v2 lands)
- LLM time during dev (testing prompts): ~$5 of LLM credits
- **Total: ~$5**

### Daily operating costs

**Research phase:**
- twitterapi.io: pull ~1,500 tweets/day (3 lists × 500 tweets) = ~22,500 credits = **$0.225**
- GitHub API: free
- arXiv: free
- Topic picker LLM call (Sonnet, ~30k input + 2k output): ~**$0.10**

**Drafting phase:**
- 5 angles × (writer + critic) = 10 LLM calls
- Each: ~5k input + 1k output
- 50k input × $3/M + 10k output × $15/M = **$0.30/day**

**Total daily: ~$0.65** (research $0.32 + drafting $0.30 + slop gate negligible)
**Total monthly: ~$20** (rounded up for retries, exploration)

### Cost scaling
- 10 drafts/day instead of 5: ~$1.30/day = $40/mo
- Switch writer to Opus 4.7 (Sonnet × 5 cost): ~$1.50/day = $45/mo
- Switch all LLM to DeepSeek V3.2: ~$0.10/day = $3/mo (quality risk)

**Recommended: Sonnet for both writer and critic, $20/mo. Negligible vs your time.**

### Bigger picture
- A SaaS like Drippi.ai costs $50-150/mo and doesn't do voice cloning over your archive.
- Tweet Hunter is $49/mo and gives you a swipe library, not a personalized engine.
- Your $20/mo bespoke pipeline = built to your voice, no vendor lock-in, owns the prompts.

---

<a id="9-risks"></a>
## 9. Risks + Failure Modes

| Risk | Likelihood | Mitigation |
|---|---|---|
| **twitterapi.io search degradation gets worse** | Medium (March 2026 already hit) | Use `within_time:` not `since:`. Use list endpoints + user timelines (unaffected). Vendor `bird_x.py` (cookie auth) as fallback. |
| **Voice drift over time** | High over months | Refresh few-shot pool from last 30 days weekly. Critic explicitly compares to recent exemplars. |
| **Hallucinated facts** | High without veto | Critic factual veto: any invented number/name/date caps score at 1. Web-search verifier for any post mentioning a person, number, or date. |
| **Slop bleeds through** | Medium | Banned-phrase regex + Hassid's anti-ai-writing-style audit pass + 5-gram dedup. |
| **Voice quality without RAG (v1)** | Medium — fresh archive means no retrieval | Static `voice/exemplars.md` (20-30 hand-curated niche posts) substitutes. Add RAG in Unit 8 once JR has ≥100 organic tweets. Target: 4 of 5 drafts usable raw — if not, more iteration on voice files before adding RAG. |
| **Daily drafts feel "off"** during dogfood week | High in week 1 | Iterate `voice/hooks.md` and writer prompt based on actual misses. Don't trust the pipeline until 4 of 5 drafts are usable raw. |
| **Cost overrun** | Low | Hard cap in `compose.py`: max 5 drafts × 2 LLM calls × max 1 revision. $0.65 ceiling enforced. |
| **JR loses interest after week 2** | Medium (any indie tool) | Build small, dogfood fast, declare done after 1 working week. Don't over-engineer. |
| **Twitter ToS / account risk** | Low (read-only via twitterapi.io, manual posting) | We don't auto-post, don't auto-engage. twitterapi.io's risk is theirs, not yours. |

---

<a id="10-sources"></a>
## 10. Sources

### Creator threads (X)
- @AlfieJCarter LinkedIn skill (618 likes): https://x.com/AlfieJCarter/status/2048785952697463222
- @AlfieJCarter Carousel + Higgsfield: https://x.com/AlfieJCarter/status/2051713136856650065
- @AlfieJCarter GTM Engineering Playbook: https://x.com/AlfieJCarter/status/2042653637306949677
- @AlfieJCarter Cowork Playbook: https://x.com/AlfieJCarter/status/2044091032942305627
- @gkisokay research agent (1,160 likes): https://x.com/gkisokay/status/2050026869274395020
- @gkisokay vault structure (327 likes): https://x.com/gkisokay/status/2051294697579249809
- @gkisokay 6-agent fan-out: https://x.com/gkisokay/status/2051836692009726401
- @gkisokay overnight 120-items: https://x.com/gkisokay/status/2051474784706560096
- @gkisokay components: https://x.com/gkisokay/status/2050400661595214030
- @rubenhassid voice-cloning (2,174 likes): https://x.com/rubenhassid/status/2050878032609530144
- @rubenhassid 3-files (1,109 likes): https://x.com/rubenhassid/status/2051255528056357165
- @rubenhassid duplicate-yourself (5,010 likes): https://x.com/rubenhassid/status/2050789469910093910
- @rubenhassid 35-word prompt (319 likes): https://x.com/rubenhassid/status/2049383362565988814
- @Av1dlive 5-step recipe: https://x.com/Av1dlive/status/2039993219329806526
- @MichLieben GTM 4-layer stack: https://x.com/MichLieben/status/2051286894206656782
- @ecomchigga 12-min system: https://x.com/ecomchigga (timeline-cited)
- @jack_9947 marketing skill stack (2,090 likes): https://x.com/jack_9947/status/2048786361201615038

### Repos
- https://github.com/dorukardahan/twitterapi-io-skill (installed at `~/.claude/skills/twitterapi-io`)
- https://github.com/dorukardahan/twitterapi-io-mcp
- https://github.com/mvanhorn/last30days-skill
- https://github.com/langchain-ai/social-media-agent
- https://github.com/enablement-ch/clio-ghostwriter (no license — reference only)
- https://github.com/sachacoldiq/ColdIQ-s-GTM-Skills
- https://github.com/kenny589/gtm-flywheel
- https://github.com/conorbronsdon/avoid-ai-writing
- https://github.com/codejunkie99/agentic-stack

### External resources
- https://how-to-ai.guide (Hassid's voice files distribution)
- https://twitterapi.io/dashboard (key + balance)
- https://docs.twitterapi.io (full API docs)
- https://n8n.io/workflows/10672-generate-twitter-content-in-personal-style-with-openai-and-supabase-rag/
- https://coldiq.com/skills-directory
- https://thegtmengineer.substack.com/p/li-content-tech-stacks-and-using

### Twitter platform notes
- twitterapi.io March 2026 search degradation: use `since_time:` (Unix), not `since:`; use hourly windows, pagination is broken
- X archive download: https://twitter.com/settings/your_twitter_data (24-48h delivery)

---

## Appendix A: Locked decisions (was: open questions)

All locked 2026-05-06. See Decision Log at top of doc.

1. ✅ **Niche** — AI-native marketing agency / AI / coding agents. Seeds the source list around §2 creators + Anthropic/OpenAI/LangChain orgs.
2. **Tonal anchors** — deferred to Unit 0; default is the 8 creators surfaced in §2.
3. **Embeddings** — N/A in v1 (no RAG). v2 starts with `text-embedding-3-small`.
4. ✅ **Repo location** — `gofreddy/x-engine/`.
5. ✅ **X archive** — request now even though small; sets up v2 infra.
6. ✅ **AlfieJCarter playbook** — engage thread.
7. **Daily run timing** — default 6am; refine after dogfood week 1.

## Appendix B: Concrete next-step actions for JR (in order)

1. **Now:** Engage AlfieJCarter — like + follow + comment "SKILL" on https://x.com/AlfieJCarter/status/2048785952697463222. Wait for DM.
2. **Now:** Subscribe at https://how-to-ai.guide → reply to welcome email → click Notion link → download all `.md files`.
3. **Now:** Request X archive at https://twitter.com/settings/your_twitter_data (24-48h delivery, for v2).
4. **When DM + Notion files arrive (≤24h):** drop `anti-ai-writing-style.md` into `voice/`; review AlfieJCarter's `profile.md`/`hooks.md` schema as reference.
5. **Then:** signal "go" and we start Unit 0 (voice files + niche seeds). Total time to working pipeline from "go": ~2 days.

