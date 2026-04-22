---
title: CLI + cross-pipeline implementation research (4 items)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-006-pipeline-overengineering-implementation-research.md
---

# Implementation research — 2 cross-pipeline consolidations + 2 pass-2 CLI agentifications

Date: 2026-04-22. Sibling to `2026-04-22-004-research-cluster-6-convergence.md` and `2026-04-22-005-research-cluster-9-providers-cli.md`. Scope: concrete implementation shape for items #16 (reporting library), #18 (named safety tiers), #39 (monitor summarizer agent), #40 (evaluate scope schema).

---

## #16 — Promote `autoresearch/report_base.py` to `src/reporting/` shared library

**Summary:** `autoresearch/report_base.py` (577 LOC) is already 80% a reporting library — the docstring literally says "Shared report generation infrastructure." Promote it to `src/reporting/`, split into 7 focused modules, adopt harness's secret-scrub regex set, add a Jinja2 entry point so the audit plan's Stage 5 can build atop it natively. Harness `review.py` deletes ~70 LOC by composing from the new package.

**Current state:** `autoresearch/report_base.py` — 577 LOC, one file, 14 public names (listed in the docstring). Consumers: `configs/{seo,competitive,monitoring,storyboard}/scripts/generate_report.py` (4 identical-shape imports). Parallel code in `harness/review.py` (`_SECRET_PATTERNS` at L10-18 — **stronger regex set than autoresearch has**; `_scrub` at L32-35; `compose` + `pr_body` at L38-79 — markdown-only, no HTML). Audit plan `U7` (plan L1096-1252) plans a separate Jinja2 + WeasyPrint stack + 9 partials + print CSS — ~300 LOC of net-new rendering code that overlaps 70% with what `report_base.py` does today.

**Target state:** One package at `src/reporting/` publishing stable API; `harness/review.py` composes from it; the audit plan's Stage 5 uses it natively (never writes its own rendering primitives); `autoresearch/report_base.py` becomes a 5-line re-export shim for backwards compat with existing `generate_report.py` scripts.

**Implementation approach:**

- **Option A (one-file promotion):** Move the whole 577 LOC to `src/reporting/__init__.py`. Cheapest physical migration. Rejected — the file already does five different jobs (parsing, rendering, scaffolding, PDF, argparse) and will keep growing once the audit plan adopts it.
- **Option B (split into 7 modules):** Recommended below.

**Recommended: Option B — split into 7 modules.**

**Justification:** The current file cleanly decomposes along its existing section-comment boundaries. Splitting now lets the audit plan add Jinja2 partials without bloating one file, lets harness import only `scrub` (without dragging mistune / Chrome detection into test paths), and makes future single-responsibility changes non-conflicting. The split costs nothing beyond 30 min of filename edits + a re-export shim.

**Module structure:**

```
src/reporting/
  __init__.py      # public re-exports — the 14 names from the docstring
  parsers.py       # load_json, load_jsonl, load_markdown, parse_findings
  renderers.py     # render_findings, render_session_log, render_logs_appendix,
                   # render_session_summary, render_report_md, unavailable_banner
  scaffold.py      # build_html_document, BASE_CSS, BADGE_COLORS, esc, truncate, md_to_html
  scrub.py         # _SECRET_PATTERNS (harness's set), scrub(), scrub_findings()
  pdf.py           # find_chrome, html_to_pdf, CHROME_CANDIDATES
  jinja.py         # render_template(template_path, context) — for audit plan U7 partials
  cli.py           # common_argparse
```

**Public API (keep it flat at package root for existing consumers):**

```python
# src/reporting/__init__.py
from .parsers import load_json, load_jsonl, load_markdown, parse_findings
from .renderers import (render_findings, render_session_log, render_logs_appendix,
                        render_session_summary, render_report_md, unavailable_banner)
from .scaffold import build_html_document, BASE_CSS, BADGE_COLORS, esc, truncate, md_to_html
from .scrub import scrub, SECRET_PATTERNS
from .pdf import find_chrome, html_to_pdf
from .jinja import render_template  # new — for audit plan
from .cli import common_argparse
```

**`scrub.py` details:** lift harness's 7 regex patterns verbatim from `harness/review.py:10-18` (JWT, GitHub tokens, AWS keys, Stripe keys, DB URLs-with-creds, high-entropy base64, `api_key=...` patterns). Rename `_SECRET_PATTERNS` → `SECRET_PATTERNS` (public). Keep `_scrub` as `scrub(text) -> text` (public). Add `scrub_findings(findings: list[dict]) -> list[dict]` for structured data.

**`jinja.py` (net-new, ~30 LOC):**

```python
from pathlib import Path
import jinja2

def render_template(template_path: Path, context: dict) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path.parent),
        autoescape=jinja2.select_autoescape(["html", "j2"]),
        undefined=jinja2.StrictUndefined,  # fail loud on missing keys
    )
    return env.get_template(template_path.name).render(**context)
```

**Pipeline adoption:**

1. **autoresearch:** `autoresearch/report_base.py` becomes a 5-line shim: `from src.reporting import *`. Existing `configs/*/scripts/generate_report.py` imports keep working unchanged. Zero migration cost.
2. **harness:** `harness/review.py` drops its own `_SECRET_PATTERNS` + `_scrub` (now in `src/reporting/scrub.py`). Imports `from src.reporting import scrub`. Net deletion: ~15 LOC. The rest of `review.py` (compose / pr_body / section helpers) stays markdown-only — harness doesn't need HTML today.
3. **audit plan:** Stage 5 (U7) uses `build_html_document` for the outer scaffold, `render_template` for per-section partials (the 9 `_partials/*.j2`), `parse_findings` for the finding envelope, `BASE_CSS` as a base + `audit_report.css` (Tailwind-compiled) as `css_extra=`, and the harness's secret regex set for final scrub before WeasyPrint. WeasyPrint replaces headless Chrome as the PDF engine for the audit plan specifically — `pdf.py` stays Chrome-based for autoresearch; audit plan gets its own `src/audit/pdf_weasy.py` (~20 LOC) because WeasyPrint has different CSS support than Chrome and the audit plan's print CSS is WeasyPrint-specific.

**Dependencies:** Zero blocking. Refactor is pure Python; no new dependencies (jinja2 is already in the audit plan's plan).

**Edge cases:**
1. `autoresearch/report_base.py` imports `mistune` at module-top — if `src/reporting/` does the same, every consumer pays the import cost even for scrub-only use. Mitigation: mistune import lives inside `renderers.py` (and inside `md_to_html` specifically), not in `__init__.py`.
2. Harness runs in worktrees that copy `autoresearch/` verbatim (see `harness/runs/20260422-143941/autoresearch/report_base.py`). The shim must exist at the old path or worktree-scoped generate_report scripts break mid-run. Keep the shim.
3. The existing `parse_findings` regex only recognizes `## Confirmed / ## Disproved / ## Observations` headers. Harness findings use YAML front-matter. Don't try to unify here — that's item #17 (`finding_lib`) which waits for audit plan U2.
4. Chrome-path detection (`find_chrome`) hardcodes macOS paths; if anyone ever runs in CI-Linux, audit plan's WeasyPrint path sidesteps it. Leave `pdf.py` as-is.
5. Jinja `StrictUndefined` will fail loud if a partial references a missing context key — **this is desired** (catches missing Finding.report_section coverage during render rather than shipping blank sections). Document in the module docstring.

**Test strategy:** Move `autoresearch`'s existing tests (any) to `tests/reporting/`. Add:
- `tests/reporting/test_scrub.py` — each of the 7 regex patterns × one positive + one negative per pattern.
- `tests/reporting/test_jinja.py` — StrictUndefined raises; template renders with full context.
- `tests/reporting/test_scaffold.py` — `build_html_document` skips empty sections; `esc(None)` returns empty.
- `tests/reporting/test_backcompat.py` — imports `from autoresearch.report_base import *` works (validates the shim).

**Rollout:** Hard cutover with shim. One PR: (a) create `src/reporting/` with the split; (b) replace `autoresearch/report_base.py` with a 5-line shim; (c) migrate `harness/review.py` scrub-only; (d) add tests. No parallel-path period needed because the shim preserves all existing import paths.

**Estimated effort:** 1 day (6-8 hrs): 2h split, 1h shim + tests, 2h harness migration, 1h jinja module + test, 2h backcompat test + polish.

**Open questions:**
1. Should the reporting package live at `src/reporting/` or `src/shared/reporting/`? Convergence doc uses both — `src/reporting/` is flatter and more discoverable; pick unless JR wants a `src/shared/` umbrella for future items (#18 does want one).
2. Should `scrub.py` include an allowlist for known-false-positives (e.g., `ghp_EXAMPLE_TOKEN_IN_DOCS`)? Punt — fix on first real false positive.
3. Audit plan's `audit_report.css` (Tailwind-compiled) replaces or stacks atop `BASE_CSS`? Probably replaces (Tailwind has its own reset). Decision can wait until U7 builds.

---

## #18 — Name 3 safety tiers explicitly (A read-only / B sandboxed-write / C repo-write+rollback)

**Summary:** Three pipelines already operate at three legitimately different safety tiers; convergence is naming + extracting shared primitives, not unifying behind one interface. Create `src/shared/safety/` publishing one sub-module per tier; each pipeline declares `safety_tier = "A"|"B"|"C"`; primitives move from per-pipeline locations to the shared package with zero behavior change.

**Current state:**
- **Tier A** (read-only / capability-restricted): audit plan `src/audit/scoped_tools.py` (not yet built; plan R4 at plan L275). `build_demo_flow_toolbelt()`, `build_welcome_email_toolbelt()`. Playwright observation-only / IMAP-read-only toolbelts passed to `ClaudeSDKClient`.
- **Tier B** (sandboxed-write): autoresearch `autoresearch/lane_paths.py` (86 LOC: `LANES`, `path_owned_by_lane`, per-lane prefixes) + `autoresearch/lane_runtime.py` (239 LOC: `ensure_materialized_runtime`, `_sync_filtered`, manifest management) + honor-system "Hard Rules" in `autoresearch/archive/*/programs/*-session.md` prompts.
- **Tier C** (repo-write + post-hoc): harness `harness/safety.py` (102 LOC: `SCOPE_ALLOWLIST` regex per track, `check_scope`, `check_no_leak`, `snapshot_dirty`, `working_tree_changes`) + `harness/review.py` secret scrub (moving to `src/reporting/scrub.py` in #16) + rollback logic in `harness/run.py:_process_finding`.

**Target state:** `src/shared/safety/` with three submodules publishing tier-specific primitives; each pipeline imports from exactly one submodule and declares its tier in config. Zero behavior change — this is a naming + move, not a rewrite.

**Implementation approach:**

- **Option A (one file per tier):** flat package.
- **Option B (tier-named submodules):** recommended.

**Recommended: Option B.**

**Justification:** Tier-named imports (`from src.shared.safety.tier_c import check_scope`) make the safety model **impossible to misread**. A new contributor opening any pipeline sees in one line which tier is in play and reads the right primitives for it. Cross-tier imports are a smell the naming surfaces; if harness ever wants `build_scoped_toolbelt`, the explicit `from src.shared.safety.tier_a import ...` signals a deliberate tier-change (harness's first read-only sub-agent).

**Package structure:**

```
src/shared/safety/
  __init__.py         # doc + SafetyTier = Literal["A","B","C"]; get_tier(name)
  README.md           # tier decision tree, picking guide, threat-model matrix
  tier_a.py           # read-only, capability-restricted
                      #   build_scoped_toolbelt(name, allowed_tools) -> toolbelt
                      #   per_action_confirm(prompt: str) -> bool  (human confirm)
  tier_b.py           # sandboxed-write
                      #   lane_ownership_check(path, lane) -> bool
                      #   sandbox_sync(source, target, *, lane) -> None
                      #   (ports lane_paths.path_owned_by_lane +
                      #    lane_runtime._sync_filtered)
  tier_c.py           # repo-write + post-hoc verification
                      #   snapshot_dirty(repo) -> set[str]
                      #   working_tree_changes(wt) -> list[str]
                      #   check_scope(wt, pre_sha, track, allowlist) -> list[str] | None
                      #   check_no_leak(pre_dirty, repo, reachable_re) -> list[str] | None
                      #   (ports harness/safety.py verbatim, parameterizing the
                      #    track-allowlist + fixer-reachable regex per-pipeline)
  tests/
    test_tier_a.py
    test_tier_b.py
    test_tier_c.py
```

**Pipeline-side declaration pattern:**

```python
# harness/config.py
SAFETY_TIER: Literal["A", "B", "C"] = "C"
SCOPE_ALLOWLIST = {  # harness-specific, passed to tier_c primitives
    "a": re.compile(r"^(cli/freddy/|pyproject\.toml$)"),
    "b": re.compile(r"^(src/|autoresearch/)"),
    "c": re.compile(r"^frontend/"),
}

# autoresearch/runtime_bootstrap.py
SAFETY_TIER: Literal["A", "B", "C"] = "B"
# lane_paths.py keeps its prefixes; calls tier_b.lane_ownership_check under the hood

# src/audit/config.py (audit plan)
SAFETY_TIER: Literal["A", "B", "C"] = "A"
# scoped_tools.py uses tier_a.build_scoped_toolbelt as the primitive
```

**Why each tier is right for its pipeline** (document this in `src/shared/safety/README.md`):

- **Harness fixer → Tier C.** Must mutate code — capability restriction impossible; the job is Write. Post-hoc scope check + leak check + rollback is the correct floor. The 3-of-5 plan-2 bugs (`771027f`, `128b43a`, `b6f3a61`) were rough edges on a 4-day-old greenfield implementation, not evidence the model is wrong.
- **Autoresearch evolver → Tier B.** Modifies variant prompts inside a sandboxed directory; harness owns git state. Lane-ownership filesystem check + honor-system prompt rules. Capability restriction would be overkill (the agent legitimately needs Write on its variant dir); Tier C would be too strict (no rollback needed — the whole variant dir is the rollback unit).
- **Audit-plan agent → Tier A.** Read + emit findings; never modifies prospect's site. Capability restriction is **strictly stronger** than allowlists because the destructive capability isn't in the toolbox. URL-blocklists were dropped because they're infinitely bypassable (plan L1438, R4 update).

**Migration steps (per convergence doc §F6.2, "zero migration cost because the pipelines already operate at the three tiers"):**

1. Create `src/shared/safety/` skeleton + README.
2. **tier_c:** port `harness/safety.py` verbatim; parameterize the per-track allowlist + fixer-reachable regex (currently hardcoded in `harness/safety.py:8-18`). Harness imports and passes its own allowlist. Tests move from `tests/harness/test_safety.py` → `tests/shared/safety/test_tier_c.py` (keep a 10-line harness-integration test that verifies the harness's allowlist against the real regexes).
3. **tier_b:** port `lane_paths.path_owned_by_lane` + `lane_runtime._sync_filtered` generically; autoresearch passes its own lane-prefix map. `lane_paths.py` becomes a 10-line shim holding the autoresearch-specific prefix dict + forwarding to `tier_b`.
4. **tier_a:** net-new when audit plan builds `scoped_tools.py`. Publish the `build_scoped_toolbelt(name, allowed_tools)` primitive + `per_action_confirm` helper; audit plan's `build_demo_flow_toolbelt` and `build_welcome_email_toolbelt` become thin wrappers that specify the tool list.
5. Each pipeline adds `SAFETY_TIER = "X"` to its config module. Grep-able for audits.

**Dependencies:** Depends on nothing. Does NOT block audit plan U2 (that's `finding_lib`, #17). Unblocks: harness's future read-only sub-agents (inventory agent, doc-drift-only agent) — they'd adopt Tier A cleanly.

**Edge cases:**
1. Someone adds a new pipeline with a 4th tier. Document in the README that tier proliferation = convergence-review gate; if you think you need Tier D, write down *why* and what distinguishes it from A/B/C. Likely you're at A with an extra constraint.
2. Harness-in-worktree copies `src/shared/safety/` into the worktree at run-start. Verify `engine.py` subprocess invocation picks up the worktree copy, not the main-repo copy (it should; sys.path is set per-worktree).
3. Audit plan's `per_action_confirm` needs a TTY. In a CI/scheduled context it'd block forever. Tier A's README must document that audit runs with `--readonly-mode true` or under a scheduler skip Tier-A-with-confirmation primitives entirely.
4. `tier_b.sandbox_sync` uses `shutil.copy2` today; on a crash mid-copy the target is half-synced. Autoresearch tolerates this (next run re-syncs). New Tier B users must either tolerate or wrap.
5. `tier_c.check_no_leak` uses a pre-snapshot vs post-snapshot diff; if the main repo is dirty in concurrent-dev-activity paths, the heuristic (`_FIXER_REACHABLE` regex) is what distinguishes them. That regex is harness-specific — Tier C consumers pass their own. Document clearly.

**Test strategy:** Move existing `tests/harness/test_safety.py` → `tests/shared/safety/test_tier_c.py` (rename only). Add `tests/shared/safety/test_tier_b.py` with lane-ownership unit tests lifted from `autoresearch/test_lane_ownership.py`. Net-new: `tests/shared/safety/test_tier_a.py` with a mock toolbelt verifying only whitelisted tool names are exposed. A top-level `test_tier_declaration.py` that imports each pipeline's config and asserts `SAFETY_TIER` is a valid value — prevents regression where someone adds a pipeline without declaring tier.

**Rollout:** Hard cutover with shim (like #16). `harness/safety.py` becomes a 10-line shim re-exporting from `tier_c` + holding harness-specific allowlist constants. `autoresearch/lane_paths.py` same shape. Tier A is net-new code; no migration needed.

**Estimated effort:** 1 day (6-8 hrs): 1h skeleton + README, 2h port tier_c + tests, 2h port tier_b + tests, 1h tier_a primitive (without audit-plan consumers), 1h shims + integration smoke, 1h doc polish.

**Open questions:**
1. Is `src/shared/` the right root, or should this be `src/safety/`? `src/shared/` makes sense if #16 also lives there (`src/shared/reporting/`) — pick one umbrella and be consistent. Recommend `src/shared/` for both.
2. Does `tier_a.per_action_confirm` live here, or in `src/audit/cli.py`? Debatable — it's a TTY prompt, not a safety primitive. Punt to audit plan U8 when the CLI command lands.
3. The README's threat-model matrix should include a "what if the agent goes rogue" row per tier. Probably a 30-min write-up by JR before this ships.

---

## #39 (F-P.2) — monitor.py `_build_summary` → summarizer agent

**Summary:** Replace `_build_summary`'s hardcoded top-20-by-engagement / word-length-theme / 3-per-source logic with a Sonnet summarizer agent that takes a caller-intent string and the raw mention list, returning relevance-ranked top-N, semantic themes with representative quotes, and volume-adaptive source-mix. Keep cheap deterministic aggregates (source counts, language counts) as a raw floor. Cache by mention-set hash + caller-intent hash to neutralize cost and latency on repeat calls.

**Current state:** `cli/freddy/commands/monitor.py:120-170` — `_build_summary(mentions, api_total)` does (a) top-20 by `engagement_likes + engagement_shares + engagement_comments` (equal weight, no source normalization — F-P.4 in cluster 9 research); (b) themes via `word_freq` where `len(word) > 4`, lowercased (will surface "freddy", "brand", "today" over real topics); (c) 3 most-recent per source (flat sample regardless of volume). Returned dict keys: `total`, `fetched`, `sources`, `languages`, `top_mentions`, `themes`, `recent_by_source`.

**Target state:** Same function signature, same top-level keys, but `top_mentions`, `themes`, `recent_by_source` are produced by an LLM call with caller-intent context; `sources`, `languages`, `total`, `fetched` stay deterministic. Add an `intent` parameter (CLI flag) that tells the agent whether the consumer is an agent-briefing, human-executive-read, or raw-analysis download.

**Implementation approach:**

- **Option A (always-agent):** every `--format=summary` call goes to the LLM. Simplest, but every dev-loop call costs money and 5-20s.
- **Option B (cached always-agent):** agent call with aggressive caching by `(monitor_id, mention_set_hash, intent, date_window)`.
- **Option C (opt-in agent):** `--format=summary` stays deterministic-but-fixed; new `--format=briefing` opts into LLM. Lets old consumers keep the deterministic shape.

**Recommended: Option B (cached always-agent) — but keep the deterministic shape reachable via `--format=summary-raw` for consumers who explicitly don't want LLM variance.**

**Justification:** The audit of this code said "themes via word-frequency where word length > 4 is almost certainly producing junk output today that nobody has audited" (F-P.2 cluster 9). The current deterministic output isn't *better* than LLM output — it's worse, just cheaper. Caching neutralizes the cost argument (most pipeline calls are deterministic repeats). Keeping `--format=summary-raw` reachable prevents breaking the one consumer (if any) that parsed the fixed top-20 list; the cutover path for them is `s/--format=summary/--format=summary-raw/`.

**Prompt design:**

```
System: You are a mention-stream summarizer for GoFreddy's brand monitoring
CLI. You receive (1) a list of raw mentions and (2) an intent string that
tells you what the consumer of this summary is trying to learn.

Your job: produce a structured JSON response with top mentions ranked by
relevance to the intent (not raw engagement), semantic themes with 1-2
representative quotes each, and a source-mix summary that adapts sample
counts to source volume.

Intent values:
- "agent-briefing": the caller is a downstream LLM agent. Prioritize signal
  density + entity/topic specificity. Shorter quotes, more mentions, more
  themes. Assume the agent will do its own analysis.
- "human-brief": the caller is a human reading a monitoring digest. Prioritize
  narrative clarity, surprising facts, sentiment range, action-relevance.
  Fewer but richer items.
- "raw-analysis": caller wants minimally-processed structured data. Rank by
  a weighted-engagement floor (shares*3 + comments*2 + likes) with platform
  normalization (tiktok_like_z, linkedin_like_z, ...), no semantic themes.
  This path exists mostly for tests.

Output JSON schema:
{
  "top_mentions": [{source, author, content (<=200ch), published_at,
                    engagement_breakdown: {likes, shares, comments},
                    relevance_score: float (0..1), relevance_reason: str}],
  "themes": [{theme: str (topic/phrase, not single word), quote: str (<=200ch),
              source_count: int, representative_mention_id: str}],
  "source_mix": {source: {count: int, sample: [{...mention fields...}]}}
                  // sample size adapts: 1 if count<5, 3 if 5-20, 5 if >20
}

User: {intent_string}

Here are the {N} mentions fetched from monitor {monitor_id} for
{date_from}..{date_to}:

{json.dumps(mentions, indent=2)[:180_000]}  # 180KB cap, see edge cases
```

**Model choice:** Claude Sonnet (not Opus, not Haiku). Opus is overkill for a 50-mention summary; Haiku tends to hallucinate author handles and miss themes. Sonnet hits the cost/quality sweet spot for structured-output tasks in the 10K-180K token range, which is where a 50-2000 mention payload lands. Temperature 0.2 (judgment task, but we want stable themes across calls).

**Caching strategy:**

Cache key: `sha256(monitor_id + "|" + mention_set_hash + "|" + intent + "|" + schema_version)`

Where `mention_set_hash = sha256(sorted([m["id"] for m in mentions]))` — order-insensitive, insensitive to pagination-order churn, stable across retries.

Cache location: `~/.freddy/cache/monitor_summary/<hash>.json` (default) or `$FREDDY_CACHE_DIR/monitor_summary/<hash>.json`. TTL: 24h (matches the existing audit cache pattern in the audit plan). `--no-cache` flag for dev.

Pseudo-code:

```python
def _build_summary(mentions, api_total, intent="agent-briefing", client=None):
    # Cheap deterministic floor (always computed)
    source_counts = Counter(m.get("source", "unknown") for m in mentions)
    lang_counts = Counter(m.get("language", "unknown") for m in mentions)
    floor = {
        "total": api_total,
        "fetched": len(mentions),
        "sources": dict(source_counts),
        "languages": dict(lang_counts.most_common(5)),
    }

    # Cache lookup
    key = _summary_cache_key(monitor_id, mentions, intent, SCHEMA_VERSION)
    cached = _cache_get(key)
    if cached:
        return {**floor, **cached}

    # Agent call (Sonnet)
    try:
        agent_part = _summarizer_agent(mentions, intent)
    except Exception:
        # Fall back to raw path — never fail the CLI on a summary call
        agent_part = _raw_summary_fallback(mentions)

    _cache_put(key, agent_part)
    return {**floor, **agent_part}
```

**Backwards compat for consumers expecting specific keys:**

The current return shape has these keys: `total`, `fetched`, `sources`, `languages`, `top_mentions`, `themes`, `recent_by_source`. The new shape:
- `total, fetched, sources, languages` — identical, unchanged.
- `top_mentions` — **same key, richer content** (now has `relevance_score`, `relevance_reason`, `engagement_breakdown`). Consumers reading `m["source"], m["content"], m["author"], m["engagement"]` still work (add `engagement` as a fallback scalar derived from the breakdown).
- `themes` — **shape change**: was `[{word, count}]`, now `[{theme, quote, source_count, representative_mention_id}]`. This is a genuine breaking change; document in the CLI help text + changelog. Deprecation path: `--format=summary-raw` keeps the word-frequency shape.
- `recent_by_source` — **renamed to `source_mix`** in the new shape. Keep `recent_by_source` as a duplicate key pointing at the same data for one release; then deprecate.

**CLI flag propagation for caller intent:**

```
freddy monitor mentions <monitor_id> --format=summary [--summary-intent=agent-briefing|human-brief|raw-analysis]
```

Default intent: `agent-briefing` (the most common caller today is the audit / autoresearch pipeline, which is an agent). Human monitoring CLI users can pass `--summary-intent=human-brief` for a digest-style output. The `raw-analysis` path is the determinism escape hatch.

**Dependencies:** Requires an Anthropic client. The codebase currently uses Gemini for `evaluate review` (cli/freddy/commands/evaluate.py:183). Add `anthropic` to pyproject.toml under an optional extra. Fallback to Gemini-Flash summarizer if `ANTHROPIC_API_KEY` is unset (cheaper, slightly worse — acceptable). Depends on `src/common/cost_recorder.py` for cost tracking.

**Edge cases:**
1. **Empty mentions.** Skip the agent call; return floor only with empty `top_mentions`, `themes`, `source_mix`.
2. **Very large mentions** (>2000 after pagination ceiling). Truncate to the top 500 by raw engagement before sending to Sonnet (180KB cap). Emit a `truncated_for_summary: true` flag in response. Also: use the existing `ceiling: 2000` in `mentions()` — no new truncation upstream.
3. **Non-deterministic output in tests.** Tests stub the agent call at the `_summarizer_agent` boundary (monkeypatch). The cache layer is also testable because `mention_set_hash` is content-addressed.
4. **Agent returns invalid JSON.** `parse_judge_response` pattern from `src/evaluation/judges/__init__.py` — one retry, then fall back to raw path. Log the bad output under `~/.freddy/cache/monitor_summary/failures/`.
5. **Cost spike from a CLI loop bug** (someone runs `freddy monitor mentions` in a while-loop). Cache hit on second call saves it; cost-recorder catches anomaly via the existing `extract_gemini_usage`/equivalent anthropic hook.

**Test strategy:** 
- Unit tests at `tests/cli/commands/test_monitor_summary.py`: (a) floor-only path when mentions empty; (b) agent called with correct intent + prompt shape (monkeypatch); (c) cache hit on second identical call (no agent invocation); (d) cache miss on different intent; (e) backwards-compat `recent_by_source` alias present; (f) agent-error fallback to raw path; (g) `--format=summary-raw` never calls agent.
- Integration test (manual): `freddy monitor mentions <test-uuid> --format=summary` on a fixture mention list → eyeball the output for quality.

**Rollout:**
1. Ship Option B behind a flag: `--format=summary` still hits `_build_summary_legacy` (renamed current), `--format=summary-v2` hits the new agent path. Internal testing for 1 week.
2. After 1 week: flip default — `--format=summary` → new path; `--format=summary-raw` preserves determinism for the one consumer that wants it. Legacy function deleted one release later.

**Estimated effort:** 2 days (12-14 hrs): 3h anthropic client + summarizer module, 3h prompt iteration + intent-specific quality tuning, 2h cache + hash layer, 2h CLI flag plumbing + backcompat aliases, 2h tests, 1h cost-recorder wiring.

**Open questions:**
1. Anthropic vs Gemini? Codebase currently has Gemini infra; adding a first Anthropic path means a new SDK dependency. JR's call — likely Anthropic because the audit plan is committing to Anthropic ClaudeSDKClient anyway.
2. Should `source_mix` be per-source or per-(source, language)? Linkedin-English vs Linkedin-Spanish are arguably different audiences. Punt; add if F-P.4 (engagement scoring) wants it.
3. `summary-intent=agent-briefing` is the default — should there be a secondary default that inspects the caller env (e.g., if `FREDDY_HUMAN_CALLER=1`, use `human-brief`)? Probably over-engineering.

---

## #40 (F-P.3) — evaluate.py `_DOMAIN_FILE_PATTERNS` → producer-owned YAML

**Summary:** Replace the hardcoded `_DOMAIN_FILE_PATTERNS` dict in `cli/freddy/commands/evaluate.py` with a per-domain YAML file owned by the producing agent (`autoresearch/archive/<v>/programs/<domain>/evaluation-scope.yaml`), loaded at `variant_command` start. When a domain gains new artifact types, the producing agent updates its YAML in the same PR; the CLI never guesses. Punt the classifier-agent option (Option B) as overkill for a fundamentally declarative problem.

**Current state:** `cli/freddy/commands/evaluate.py:58-88` — hardcoded `_DOMAIN_FILE_PATTERNS: dict[str, dict[str, list[str]]]` with four domains (geo, competitive, monitoring, storyboard). Each domain has `outputs` and `source_data` glob lists. Inline comments are a confession of judgment: `storyboard` entry says "this was the run #6 I.14 invisibility bug"; `competitive` entry explains the output-vs-source reclassification of agent-generated JSON. `_read_files` at L91-116 has a special-case carveout: `competitors/_*.json` is skipped **except** `_client_baseline.json`. `variant_command` at L299-309 is the sole consumer. Whenever a domain adds an artifact type, this file is hand-patched.

**Target state:** `_DOMAIN_FILE_PATTERNS` dict deleted. Per-domain `evaluation-scope.yaml` file colocated with the producing agent's session prompts. `variant_command` reads it at evaluation start via a shared loader. Adding a new artifact type = editing the producing agent's YAML (one file, same PR as the agent change).

**Implementation approach:**

- **Option A (producer-owned YAML):** schema below. Deterministic, cheap, audit-friendly. Agent owns what it emits; eval owns how it judges.
- **Option B (classifier agent at variant_command start):** agent sees the session dir, classifies each file as output|source_data|transient|ignore. Caches by domain. More "agentic" but adds a per-eval LLM call, latency, and a new failure mode (classifier mistake → scoring bug → harder to debug than a YAML edit).

**Recommended: Option A (producer-owned YAML).**

**Justification (honest evaluation):** The research doc (F-P.3 cluster 9) frames this as "producer-owned YAML is the cheaper fix; classifier agent is the agentic fix" and asks for an honest read. The honest read: **classifier agent is the wrong tool here.** The patterns table isn't encoding qualitative judgment that benefits from LLM reasoning — it's encoding **which files this agent produces** and **which files this agent reads as reference**. Those are declarative facts the producing agent already knows at write-time. An LLM classifier is strictly more expensive + less deterministic + less debuggable for the same information. The bugs this caused (run #6 I.14 invisibility) happened because the dict was maintained by the *wrong owner* (CLI code hand-patched after the fact); moving ownership to the producing agent's YAML fixes the root cause. The only scenario where a classifier wins is "new artifact type appears without anyone touching the producing agent" — which shouldn't happen if the producing agent emitted the artifact.

**YAML schema:**

```yaml
# autoresearch/archive/<v>/programs/<domain>/evaluation-scope.yaml
# Owned by the producing agent. When this agent emits a new artifact type,
# update this file in the same PR. The CLI does not guess.
#
# Schema version 1:

schema_version: 1
domain: storyboard  # must match the CLI --domain argument

outputs:
  # Files the agent produces as deliverables. These are what the variant-level
  # scorer judges. Order matters only for sorting in the judge prompt.
  - path: "stories/*.json"
    description: "PLAN_STORY phase output"
    required_count: ">=1"   # fails structural gate if glob returns 0
  - path: "storyboards/*.json"
    description: "IDEATE phase output (was silently ignored in run #6 I.14)"
    required_count: ">=1"

source_data:
  # Real external inputs the agent reads; fed to LLM judges as reference
  # context. NOT evaluated as outputs.
  - path: "patterns/*.json"
    description: "Client pattern library"
  - path: "session.md"
    description: "Session prompt + parameters"

transient:
  # Scratch files the evaluator should ignore. By convention these start with
  # an underscore, but state it explicitly here — the old "_* is transient"
  # rule had to be carved out for _client_baseline.json, so the convention
  # alone is unreliable.
  - path: "**/_*.json"
    except:
      - "competitors/_client_baseline.json"  # client Foreplay baseline IS real source

# Optional: explicit domain-wide carveouts, applied after the per-section rules
notes: |
  Storyboard-specific: both stories/ and storyboards/ must be visible to the
  variant-level scorer. The "run #6 I.14 invisibility bug" happened when the
  patterns table only listed stories/*.json; IDEATE phase output was silently
  dropped.
```

**Consumer change in `evaluate.py`:**

```python
# cli/freddy/commands/evaluate.py
import yaml

def _load_evaluation_scope(domain: str) -> dict:
    """Load the producing agent's evaluation-scope.yaml for this domain."""
    # Locate the current archive's active variant directory via the manifest
    from autoresearch import lane_runtime
    runtime_dir = lane_runtime.resolve_runtime_dir(_find_archive_dir())
    scope_path = runtime_dir / "programs" / domain / "evaluation-scope.yaml"
    if not scope_path.exists():
        typer.echo(json.dumps({
            "error": f"Missing evaluation-scope.yaml for domain={domain} at {scope_path}. "
                     f"The producing agent must declare its outputs/source_data."
        }))
        raise typer.Exit(1)
    scope = yaml.safe_load(scope_path.read_text())
    if scope.get("schema_version") != 1:
        typer.echo(json.dumps({"error": f"Unsupported schema_version in {scope_path}"}))
        raise typer.Exit(1)
    return scope

def _read_files_from_scope(session_dir: Path, entries: list[dict],
                           transient_rules: list[dict]) -> dict[str, str]:
    """Walk entries (outputs or source_data) and collect files, honoring
    transient skip rules with explicit except-carveouts."""
    result = {}
    skip_patterns = [e["path"] for e in transient_rules]
    except_paths = set()
    for rule in transient_rules:
        except_paths.update(rule.get("except", []))

    for entry in entries:
        pattern = entry["path"]
        if "*" in pattern:
            for fp in sorted(session_dir.glob(pattern)):
                if not fp.is_file():
                    continue
                rel = str(fp.relative_to(session_dir))
                # Transient skip, with per-file except-carveout
                if any(fnmatch(rel, pat) for pat in skip_patterns) and rel not in except_paths:
                    continue
                result[rel] = fp.read_text()
        else:
            fp = session_dir / pattern
            if fp.is_file():
                result[pattern] = fp.read_text()
    return result
```

**Migration path from current hardcoded dict:**

1. **PR 1 (compat shim):** Write `autoresearch/archive/current_runtime/programs/<domain>/evaluation-scope.yaml` for all four existing domains, one-to-one from the current `_DOMAIN_FILE_PATTERNS` dict. Add the `_load_evaluation_scope` loader. Fallback to hardcoded dict if YAML missing (logs WARNING).
2. **PR 2 (cutover):** Delete the hardcoded dict. Fallback path now errors. All four YAMLs must be present (they already are from PR 1).
3. **PR 3 (producer ownership):** Move each YAML from `current_runtime/programs/<domain>/` into the **variant-being-promoted's** programs dir. Future variant promotions carry forward their scope file. The producing-agent prompt template (`*-session.md`) gets a "When you add a new artifact type, update `evaluation-scope.yaml`" instruction block.

**How to handle new artifact types without code change:** the producing agent emits an artifact + updates its `evaluation-scope.yaml` in the same PR. The CLI never knows about the new type because it doesn't need to — it reads the YAML at runtime. Structural-gate verification uses `required_count` to assert the new artifact is present. No CLI edits for artifact-type adds, ever.

**Dependencies:** `pyyaml` (already in requirements.txt — autoresearch uses it). Requires `autoresearch/lane_runtime.resolve_runtime_dir` to find the active variant — already exists (`lane_runtime.py:66`).

**Edge cases:**
1. **YAML file missing for a new domain** (e.g., JR adds a 5th domain mid-migration). PR 2 onwards errors loud with clear message; PR 1 shim falls back. Either is acceptable; erroring loud is better once migration done.
2. **Schema version drift.** `schema_version: 1` check gates future fields. Adding `schema_version: 2` means either pipeline backcompat with v1 readers or bump and migrate all 4 YAMLs. Either is fine because YAMLs are co-owned with variant promotions.
3. **Glob collision across outputs + source_data.** A file matching both sections is ambiguous. Loader rule: outputs win (the more load-bearing classification). Document in the README.
4. **`except:` carveout for multiple skip patterns.** If two skip rules both match a path, both must `except:` it, or the first-listed rule wins. Pick first-listed-rule-wins and document.
5. **Variant re-materialization mid-evaluation** (autoresearch `_sync_filtered` runs during an eval). The YAML is read once at eval start — safe. If that becomes a race, snapshot the YAML into `session_dir` at session start.

**Test strategy:**
- Unit test `_load_evaluation_scope`: happy path, missing file, wrong schema_version, invalid YAML.
- Unit test `_read_files_from_scope`: glob matching, transient skip, except-carveout (both paths), outputs-vs-source precedence.
- Regression test for the run-#6-I.14 bug: a storyboard scope YAML with both `stories/*.json` and `storyboards/*.json` in outputs → both surfaces to the scorer.
- Migration test: a shim-mode test where YAML is absent verifies the fallback path matches current dict behavior exactly.

**Rollout:** Three-PR path (above). PR 1 ships shim + YAMLs; 1 week soak; PR 2 cutover; PR 3 moves ownership to variant dirs. The soak week catches missing-YAML cases in CI before cutover.

**Estimated effort:** 1 day (6-8 hrs): 2h YAML schema + loader + fnmatch logic, 2h write all 4 domain YAMLs (careful — it's a 1:1 port but the comments matter for future authors), 2h tests, 2h migration-PR plumbing + variant-dir-ownership wiring.

**Open questions:**
1. Should `evaluation-scope.yaml` live next to the agent's prompt (`programs/<domain>/`) or at the variant root (`<variant>/evaluation-scope.yaml`, one file with domain keys)? The per-domain-folder option wins because variant promotions are lane-scoped (the geo lane promotes its own scope file without touching storyboard's).
2. Do we need a `schema_version` field? Yes — cheap insurance; every CLI/agent tool that's been around >6 months regrets not having one.
3. Should `required_count` be an expression (`>=1`, `==3`, `0..10`)? Start with `>=N` literal int; expand if someone needs a range.
4. Is the classifier-agent option ever worth revisiting? Only if a domain emerges where the producing agent genuinely doesn't know what it will emit (e.g., a user-content analysis agent whose outputs depend on user input). In that case, the YAML could specify "dynamic" as a sentinel and trigger the classifier fallback. Not Day 1.
