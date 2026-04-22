---
title: Providers + CLI second-pass — F-P.1..6 (cloro position weight, monitor summary, evaluate file patterns)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-005-pipeline-overengineering-second-pass.md
---

# Over-Engineering Audit — Providers & CLI Commands (2026-04-22)

## Executive Summary

**Files audited (7):**

- `src/seo/providers/dataforseo.py` — 325 LOC — **correctly deterministic.** Pure API wrapper + schema normalization. One borderline case called out as LOW.
- `src/geo/providers/cloro.py` — 346 LOC — **1 finding.** The `_position_weight` function bakes a linear decay formula (1.0/0.8/0.6/0.4) into code that should probably be a per-platform/per-query-type agent call, because position importance varies by platform.
- `src/fetcher/instagram.py` — 593 LOC — **correctly deterministic.** Apify shape normalization. Hashtag/mention regex (L166-167) is a genuine floor extraction, not judgment.
- `cli/freddy/commands/monitor.py` — 250 LOC — **2 findings, 1 HIGH.** `_build_summary` (L120-170) bakes top-20-by-engagement, length-based theme extraction, and 3-per-source recency sampling — the three things that most need context awareness when a caller asks for a "summary."
- `cli/freddy/commands/evaluate.py` — 401 LOC — **2 findings, 1 HIGH.** `_DOMAIN_FILE_PATTERNS` (L58-88) is a hardcoded dispatch table whose inline comments literally admit the decisions are judgment calls that were hand-tuned in response to bugs.
- `cli/freddy/commands/iteration.py` — 139 LOC — **correctly deterministic.** Pure API POST plumbing, non-fatal wrapper. No judgment.
- `cli/freddy/commands/auto_draft.py` — 114 LOC — **1 LOW finding.** YAML-config-driven dispatch; the judgment is in the YAML config, not the code.

**Priority counts:** 2 HIGH, 2 MEDIUM, 2 LOW. Total: 6 findings.

**Patterns seen:**

1. **Heuristic summarization inside CLI commands.** When a command has to collapse large result sets for a human or a downstream agent (monitor summary, baseline), the collapsing logic is currently ad-hoc (word-frequency themes, length-gates, arbitrary top-N thresholds). This is the single strongest pattern across the CLI files — the qualitative work happens between the raw API call and the emit().
2. **Dispatch tables whose entries encode judgment, not mechanism.** `_DOMAIN_FILE_PATTERNS` and the `issue_map` in DataForSEO are both `dict[key, policy]`. The DataForSEO one is fine (it's mapping schema fields to a severity taxonomy). The evaluate.py one encodes the judgment "what counts as an output vs. source for this domain" and has been hand-patched after bugs (the storyboard comment explicitly says so).
3. **Providers themselves are clean.** DataForSEO and Cloro wrappers correctly stop at API shape normalization and don't try to classify toxic backlinks, rank keywords, or judge citations. Instagram similarly stops at shape. The confident pattern here is: this codebase's providers are disciplined about the fetch/parse boundary; the qualitative creep happens further downstream in CLI commands.

**Note on scope overlap with prior audit:** Two of these findings (F-P.1, F-P.3) intersect with the existing 26 recommendations in nature (heuristic scoring / hardcoded dispatch), but the specific code sites are new — these are additional instances of patterns JR's audit already flagged.

---

## Findings

### [F-P.1] — Cloro position-weight formula (`word_pos_score`)

- **File:line:** `src/geo/providers/cloro.py:42-46`, `src/geo/providers/cloro.py:307-346`
- **Today:** `_position_weight(position)` applies a hardcoded linear decay (1st=1.0, 2nd=0.8, 3rd=0.6, 4th+=0.4 floor) and multiplies it by full-response word count to produce `word_pos_score`, a "prominence" metric attached to every citation from ChatGPT/Perplexity/Gemini/Grok/Copilot/Google-AI-Mode/Claude.
- **Why it's qualitative:** The value of being the Nth citation is platform-dependent and query-type-dependent. On Perplexity, citation 1 and citation 5 may carry near-equal weight because Perplexity surfaces all sources in a visible list. On ChatGPT, the 1st in-line citation dominates because later ones often aren't clicked. For shopping queries, the top 3 are commercial-intent ranked; for informational queries, the top 10 are all "supporting." Baking a single decay curve into Python applies the same weighting to all seven platforms and all query types.
- **Agentic redesign:** The Cloro provider should continue to emit the raw citation list with `position` and `word_count`. The scoring itself should move to an LLM judge that sees (a) the platform, (b) the query text, (c) the response text, and (d) the full citation list, and assigns a prominence score per citation. Or, cheaper: platform-specific weight tables chosen by an agent at session start based on the query-type taxonomy, rather than one formula baked in.
- **Why agent wins:** Removes a silent bias that propagates into every AI-visibility metric downstream (this score likely flows into ranking client brands vs. competitors). Makes platform-specific research possible — we can ask "does Gemini weight position 2 like position 1?" without editing code.
- **New risks:** Noisier per-citation scores (LLM variance). Per-query LLM cost unless weights are cached per platform/query-type. Existing dashboards that assume the linear decay will need to be revalidated; old snapshots won't be directly comparable.
- **Priority:** MEDIUM — this is foundational scoring that downstream analytics trust, so it's worth a careful migration; the current code is "wrong but consistent" (same bias everywhere) which is why it's not HIGH. Short-term alternative: make the weights configurable per platform in config, even without an agent.

---

### [F-P.2] — Monitor summary: themes + top-20 + recency sampling

- **File:line:** `cli/freddy/commands/monitor.py:120-170` (`_build_summary`)
- **Today:** When `format=summary` is requested on `freddy monitor mentions`, the CLI computes: (a) top 20 mentions by engagement (`likes + shares + comments` falling back to `engagement_total`); (b) "themes" via lowercase word-frequency count keeping words > 4 characters; (c) 3 most-recent per source. Each of these is baked into the function with no knobs.
- **Why it's qualitative:** All three are judgment-heavy. (a) "Engagement" sums likes+shares+comments equally — but a share from a 200K-follower account on X is not equal to a share on Reddit is not equal to a comment on a long-form blog. (b) "Word length > 4" as a theme signal is the crudest possible approximation of topical clustering; it will surface common English words like "freddy," "brand," "today" and miss two-word phrases ("price hike") entirely. (c) "3 per source" is arbitrary — a brand with 50 mentions on TikTok and 2 on LinkedIn gets the same 3-sample treatment per source, hiding the distribution.
- **Agentic redesign:** When a summary is requested, have the CLI send the raw mention list to a summarizer agent with explicit instructions about what the caller is trying to learn. The agent returns: (a) top-N mentions by relevance (not raw engagement), weighted per-source and per-context; (b) semantic themes (topics/phrases, not single long words), with representative quotes; (c) a source-mix summary that adapts sample counts to source volume. The function still computes the cheap aggregates (source counts, language counts) deterministically — those are correct counters. The judgment parts get swapped for an LLM call.
- **Why agent wins:** (a) Themes become meaningful (topics vs word-length artifacts). (b) Engagement ranking gets platform-aware, so a single viral TikTok doesn't drown out serious reviewer coverage on a B2B blog. (c) Sampling matches source volume instead of a flat 3. And the caller of `--format=summary` is typically an agent or a human looking for a briefing — both audiences are better served by an LLM-generated briefing than a word-frequency table.
- **New risks:** Non-deterministic output (same mentions produce different summaries across runs). Latency spike: CLI summary goes from ~5ms to 5-20s. Cost: every `--format=summary` call becomes a paid LLM call. Mitigation: cache by mention-set-hash; keep the deterministic stats section as a raw floor under the agent narrative.
- **Priority:** HIGH — this function is specifically the "summarize for a downstream consumer" code path, and it's doing exactly the wrong thing with deterministic code. Also: "themes via word-frequency where word length > 4" is almost certainly producing junk output today that nobody has audited.

---

### [F-P.3] — evaluate.py `_DOMAIN_FILE_PATTERNS` + underscore-carveout

- **File:line:** `cli/freddy/commands/evaluate.py:58-88` (the dispatch table), `cli/freddy/commands/evaluate.py:91-116` (the reader + carveout), `cli/freddy/commands/evaluate.py:299-309` (consumer)
- **Today:** `freddy evaluate variant <domain> <session_dir>` looks up the domain in `_DOMAIN_FILE_PATTERNS` (hardcoded dict for geo/competitive/monitoring/storyboard) to decide which glob patterns count as "outputs" (the thing being evaluated) and which count as "source_data" (reference inputs for the judge). `_read_files` additionally implements a `competitors/_*.json` skip rule with a carveout for `_client_baseline.json`.
- **Why it's qualitative:** The inline comments are a confession. The storyboard entry comment literally says "both must be visible to the variant-level scorer, otherwise a successful IDEATE phase writes artifacts the scorer silently ignores (this was the run #6 I.14 invisibility bug)." The competitive entry's comment says "competitors/*.json are agent-generated (written from tool outputs), not external inputs. Classify as outputs so the structural gate can verify they exist + parse." The underscore-carveout is the smoking gun: `_client_baseline.json` starts with an underscore (by convention "scratch") but is semantically real input, so it needed a hardcoded exception. Every time a new artifact type lands, someone has to update this dict or get a silent scoring bug. The pattern table is encoding domain knowledge about artifact semantics — which is exactly what an agent should judge.
- **Agentic redesign:** Replace the dict with a small classifier agent call at the start of `variant_command`: list the files in the session directory, let the agent classify each as (output | source_data | transient | ignore) based on the file's path and a peek at its content. Cache the classification per domain and invalidate when new artifact types appear. For a simpler step that preserves determinism: move the patterns out to a per-domain YAML config so the agent writing the variant can declare what it emitted, rather than the CLI guessing.
- **Why agent wins:** New session artifacts stop causing silent-ignore bugs. The `_*.json` convention is enforced by meaning, not by path-prefix. When the competitive domain evolves and adds (say) `competitors/_ads_scratch.json`, the classifier picks up the "scratch" semantics without code edits. The comments documenting past bugs become unnecessary.
- **New risks:** Classifier mistakes. Mitigate with a known-artifact allowlist fallback (the current dict becomes a prior, not the final word) and a verbose mode that shows the classification decision. Latency: single extra LLM call per evaluate invocation (small compared to the 5-minute judge call that follows).
- **Priority:** HIGH — the comments themselves prove this has caused real bugs ("run #6 I.14 invisibility bug"). The current code is known-fragile by its own documentation. Even if full agentification is too much, pushing the classification into per-domain YAML (owned by the producing agent) resolves most of the pain.

---

### [F-P.4] — Engagement scoring formula in `_eng()`

- **File:line:** `cli/freddy/commands/monitor.py:126-130` (nested inside `_build_summary`)
- **Today:** `_eng(m)` returns `m["engagement_total"]` if present, else `likes + shares + comments` with equal weights. This single number drives top-20 ranking.
- **Why it's qualitative:** Equal weighting of likes, shares, and comments is a judgment call. Shares propagate reach; comments signal engagement depth; likes are often ambient. A mention with 100 likes + 0 shares is not equivalent to one with 10 likes + 90 shares, but this formula treats them identically. Also: no platform normalization — TikTok like-counts are orders of magnitude higher than LinkedIn like-counts.
- **Agentic redesign:** Either (a) keep the raw components (`likes`, `shares`, `comments`) and let the agent that consumes the CLI output apply weights appropriate to its task, or (b) push the scoring into an agent that also sees the source platform and applies platform-calibrated weights. Option (a) is cheaper and composes better: the CLI becomes dumber, the downstream consumer smarter.
- **Why agent wins:** Removes a silent cross-platform bias. Makes it possible to rank mentions by (e.g.) "most impactful for our risk posture" rather than "highest arithmetic sum."
- **New risks:** Breaking change for existing consumers that depend on a single engagement scalar. Mitigate by keeping `_eng()` as-is but also emitting the component breakdown, letting consumers choose.
- **Priority:** MEDIUM — smaller scope than F-P.2 and tangled with it. If F-P.2 is adopted, the summarizer agent subsumes this judgment. Worth a note but don't double-count.

---

### [F-P.5] — DataForSEO `issue_map` severity classification

- **File:line:** `src/seo/providers/dataforseo.py:233-247`
- **Today:** Maps DataForSEO check flags (no_title, no_description, no_h1_tag, is_noindex, is_redirect, no_favicon, has_render_blocking_resources, no_content_encoding) to a `(category, severity, description)` tuple. `is_noindex` is hardcoded "critical"; `no_favicon` is hardcoded "info"; etc.
- **Why it's qualitative-but-borderline:** Severity assignment is context-dependent. `is_noindex` on a thank-you page is correct behavior (not a critical issue); `is_noindex` on the homepage is catastrophic. `no_h1_tag` on a login page is fine; on a blog post it's a real warning. The severities baked here apply the same label regardless of page role.
- **Agentic redesign:** Keep the check-to-category mapping (that's schema normalization and is fine). Move severity out of the mapping and into the downstream SEO-audit agent that has the page's role/intent context. Or: add a second dimension (page_role) and parameterize the dict.
- **Why agent wins:** Severity becomes useful for prioritization rather than noise. Users stop being told the homepage's 200-status OK page has a "warning" because it lacks an H1 in a layout where the H1 is on the background hero image.
- **New risks:** Harder to A/B compare issue counts across pages if severity is dynamic. Low real-world blast radius; currently this just feeds UI color coding.
- **Priority:** LOW — the provider layer is fundamentally right to normalize shape. This is a correctly-placed-but-slightly-too-opinionated field. Leave it unless the SEO audit pipeline explicitly needs page-role-aware severity.

---

### [F-P.6] — `auto_draft._check_trigger` dispatch table

- **File:line:** `cli/freddy/commands/auto_draft.py:16-34`
- **Today:** Three hardcoded trigger types (`digest_available`, `brief_available`, `cron`) each with its own file-existence check. New trigger types require code edits.
- **Why it's qualitative-but-debatable:** "Is this draft worth generating right now?" is genuinely a judgment question (has enough new data arrived since last draft? is the monitor in a quiet period?). But the current code doesn't try to answer that judgment question — it only checks "does a named file exist," which is mechanical. The qualitative work in auto-draft lives in the YAML config (what triggers map to what actions) and in the downstream agents that the triggered commands invoke.
- **Agentic redesign:** Replace the if-ladder with a dynamic registry: triggers are defined as named modules (or lambdas), looked up by name. For a real upgrade: add a `type: judgment` trigger that passes the base_dir and trigger config to a small agent that answers "is there enough signal to draft?" — for a VoC digest, "has mention volume doubled since last draft?" is judgment, not file-existence.
- **Why agent wins:** Opens the door to substantive triggers like "draft when sentiment drops 20%" or "draft when a new competitor appears" without rebuilding the worker.
- **New risks:** Triggering complexity moves into an agent that can mis-fire. Budget per agent-evaluated trigger.
- **Priority:** LOW — the existing code isn't broken; it's a small extension point. Worth noting because the pattern (if-ladder on a string type) tends to accumulate entries over time; fixing it now is cheap.

---

## Files with NO agentification candidates

- `src/seo/providers/dataforseo.py` — the one borderline call (F-P.5) is LOW and arguably correct as-is. The file is otherwise a clean async wrapper: HTTP calls, cost recording, Pydantic-shaped response normalization, fixed API pagination limits. No classification heuristics, no toxic-link logic, no "related keywords" selection. Correctly deterministic.
- `src/fetcher/instagram.py` — 593 LOC of Apify shape normalization, retry machinery, sanitization of search input (regex at L436 is stripping chars the Apify actor rejects — an API constraint, not judgment), and timestamp parsing. The caption hashtag/mention regex (L166-167) is a genuine floor extraction, not classification. Correctly deterministic.
- `cli/freddy/commands/iteration.py` — pure API plumbing, non-fatal wrapper around a POST to `/v1/sessions/{id}/iterations`. Reads state files, truncates to size caps, fires the request. Zero judgment. Correctly deterministic.

## Closing notes

The providers in this codebase (DataForSEO, Cloro, Instagram) are disciplined — they stop at the shape-normalization boundary and resist the temptation to classify. That's the right pattern. The qualitative creep in this sample lives **downstream** in the CLI commands, specifically in code paths that try to collapse raw API data into a human/agent-readable summary (`_build_summary`, `_DOMAIN_FILE_PATTERNS`). Those are the highest-leverage agentification points in this batch.

If JR is building a priority list from the full 26+6 findings, F-P.2 (monitor summary) and F-P.3 (domain file patterns) are the two where the current code is both (a) doing qualitative work and (b) demonstrably producing brittle or incorrect outputs today. F-P.1 (Cloro position weight) is a silent-bias issue — worth fixing but not urgent. The remaining three are minor.
