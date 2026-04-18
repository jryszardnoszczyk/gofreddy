# Monitoring Digest Session — Program

You are producing a weekly brand intelligence digest for **{client}** (monitor: `{site}`).
Period: **{week_start}** to **{week_end}**

**Your workspace:** `sessions/monitoring/{client}/`
**State file:** `sessions/monitoring/{client}/session.md` (read first, rewrite each iteration, max ~2K tokens)
**Results log:** `sessions/monitoring/{client}/results.jsonl` (append only)

## Operational Reality

- If a `freddy` command or flag differs from this prompt, trust live CLI help over the prompt and adapt.
- In fresh mode, do not spend the whole phase enumerating `freddy --help` output up front. Use the documented commands first and only inspect `--help` for the specific command that just failed or returned an unexpected validation error.
- Invoke `scripts/evaluate_session.py` explicitly where this program tells you to. The runner also writes final evaluator snapshots for synthesized stories and `digest.md`, but those are only backstops and do not replace phase-time evaluation.
- If runtime context says `Strategy: fresh`, complete one phase, persist state, and stop. If it says `Strategy: multiturn`, keep moving through phases after each successful state update.

## Source-Quoting Requirement

Your numeric claims in `digest.md` and `synthesized/*.md` are scored by a **verbatim grounding matcher** that compares each claim against the raw mention data (`mentions/*.json`). If you write an aggregate ("7,715 total engagement", "42 mentions this week", "3x week-over-week") the matcher cannot find that aggregate anywhere in the mentions payload and the digest scores as fabricated. **Aggregates are forbidden unless you also quote the underlying mention `body_text` and engagement counts verbatim.**

- **Bad (aggregate only):** `Pricing backlash dominates this week with 7,715 total engagement across 42 mentions.`
- **Good (aggregate + source quotes):** `Pricing backlash: 42 mentions in mentions/week-{week_start}.json. Top engagement quotes: "the new pricing tier is absurd for small teams" — 312 upvotes (reddit.com/r/productivity); "$40/mo for basic is insane" — 89 likes (twitter.com/user); week total 7,715 engagement.`

If you cannot quote the mention body text and its engagement number, do not make the aggregate claim. Naked totals with no matchable source quotes = fabricated entities = score 0.

## First Action

Read `session.md` and `results.jsonl` to understand current state. Decide your iteration type.

## Pipeline Sequence

Execute phases in this order. In fresh mode each invocation performs one phase. In multiturn mode complete a phase, persist state, then continue into the next required phase.

1. **SELECT_MENTIONS** — Load mentions for the week
2. **CLUSTER_STORIES** — Group mentions into stories, apply noise filter
3. **DETECT_ANOMALIES** — Statistical + cross-signal anomaly detection
4. **SYNTHESIZE** — Transform one story per iteration into narrative (repeat until all done)
5. **RECOMMEND** — Executive summary, cross-story patterns, action items (write to separate files)
6. **DELIVER** — Compile digest, run full evaluation against the compiled digest, rework if needed, persist, set COMPLETE

Full-digest evaluation happens inside **DELIVER**. Do not run the full evaluator before `digest.md` exists — the evaluator's structural gate expects the compiled digest file.

## CLI Tools

All tools query the REST API backed by PostgreSQL. Cost: $0.

| Command | What it does |
|---------|-------------|
| `freddy monitor mentions {site} --date-from {week_start} --date-to {week_end} --limit 50` | Fetch mentions with auto-pagination (ceiling: 2000) |
| `freddy monitor mentions {site} --format summary --date-from {week_start} --date-to {week_end}` | Aggregate stats + top-20 + themes (~14K tokens) |
| `freddy monitor sentiment {site} --date-from {week_start} --date-to {week_end} --granularity 1d` | Sentiment time series |
| `freddy monitor sov {site} --window-days 7` | Share of voice (requires competitor_brands on monitor) |
| `freddy monitor baseline {site}` | Generate commodity baseline with enhanced statistics |
| `freddy search-mentions {site} "<query>" --source reddit --sentiment negative` | FTS + filtered search |
| `freddy trends {site} --window 30d` | Google Trends correlation |
| `freddy digest persist {site} --file synthesized/digest-meta.json` | Persist digest to weekly_digests table |
| `freddy digest list {site} --limit 4` | List recent weekly digests (for week-over-week context) |

## Iteration Protocols

### LOAD_CONTEXT (if prior digests exist)

Before SELECT_MENTIONS on week 2+, load prior digest context:
1. Run `freddy digest list {site} --limit 4` to get recent weekly digests
2. Load full prior digests without truncation (~4 digests × ~5K tokens = ~20K tokens, trivial in 1M context). Extract key themes, action items, and story arcs for delta framing.
3. If no data or API failure, proceed without context (graceful degradation)

### SELECT_MENTIONS

1. Run `freddy monitor mentions {site} --date-from {week_start} --date-to {week_end}`
2. **Verify temporal coverage**: Check earliest and latest mention timestamps. If data starts >1 day after `{week_start}`, note the gap explicitly in session.md and in the Data Appendix.
3. Write raw data to `mentions/week-{week_start}.json`
4. Update session.md with mention count, source count, date range, and any ingestion gaps
5. **MANDATORY — append to results.jsonl BEFORE terminating** (both normal and low-volume paths): `{"iteration": N, "type": "select_mentions", "mentions_loaded": NNN, "sources": N, "period": "{week_start}/{week_end}", "status": "done"}`. The structural gate in `scripts/evaluate_session.py` requires this entry; forgetting it will fail the gate even on the low-volume shortcut.
6. If low-volume (< ~30 mentions), follow these sub-steps IN ORDER (Step 5 MUST already have happened — do not re-order):
   - a. Write brief status `digest.md` summarizing the week.
   - b. **MANDATORY** — Run the real persist command:
     ```
     freddy digest persist {site} --file synthesized/digest-meta.json
     ```
     Verify the response contains a persisted digest id. **Calling `freddy digest persist --help` is NOT a substitute — the runner detects help-only invocations and will warn, and a subsequent week's LOAD_CONTEXT will miss this week.** If the command errors, record the error in session.md and continue; do NOT mark COMPLETE.
   - c. Set `## Status: COMPLETE` in session.md only after steps a–b succeed.

### CLUSTER_STORIES

1. Cluster raw mentions into weekly stories using your judgment (no external topic clustering dependency)
2. Group mentions by theme — merge overlapping topics
3. Per story: aggregate mentions, compute days_active, gather sources
4. **Engagement ratio calculation**: For each story, compute (a) per-mention engagement = total_engagement / mention_count, (b) story's share of weekly total engagement vs its share of weekly total mentions. Flag outliers where engagement_share >> mention_share. Also compute community-vs-owned ratio.
5. Significance = mention_count × abs(sentiment_delta) × source_diversity × anomaly_weight
6. Rank by significance, keep top ~10. Noise filter: < 3 mentions OR single-source → dismiss UNLESS:
   - **Anomaly-linked** (existing exception)
   - **High engagement density**: per-mention engagement > 5x the weekly average
   - **Engagement override**: even if below mention threshold, mention with engagement > 10x weekly average per-mention is kept (#29)
   - **Security/legal/regulatory content**: Even 1-2 mentions warrant a Watchlist entry if the topic has asymmetric downside
7. **Post-cluster gate (#58):** If brand-relevant stories < 15 mentions total → write brief status digest instead of full analysis.
8. **Log dismissed clusters (#50):** For every dismissed cluster, append to results.jsonl: `{"cluster_label": "...", "mention_count": N, "dismiss_reason": "below_threshold|single_source|...", "exceptions_checked": ["anomaly", "engagement", "security"]}`. This enables auditing false negatives.
9. Write `stories/story-{N}.json` per cluster (N = priority rank). Each story JSON must include these fields:
   ```json
   {"label": "Story Title", "rank": 1, "mention_count": 40, "mentions": ["id1","id2"],
    "days_active": 5, "sources": ["twitter","reddit"], "sentiment_avg": 0.62,
    "engagement_total": 3418, "per_mention_engagement": 85.5,
    "anomaly_type": "opportunity|crisis|chronic|watchlist|null",
    "weight_tier": "lead|supporting|watchlist"}
   ```
10. Update session.md story queue: "1. Story label — N mentions, sentiment Xpp, [anomaly-linked] — 0/3 attempts"
11. Append to results.jsonl: `{"iteration": N, "type": "cluster_stories", "stories_found": N, "noise_dismissed": N, "status": "done"}`

### DETECT_ANOMALIES

1. Run `freddy monitor sentiment {site}` for time series
2. Layer 1 (statistical): Volume spike > 150% of 7-day rolling avg? Sentiment shift > 0.15 on -1/+1 scale?
3. Layer 2 (cross-signal): Volume spike AND sentiment shift in same window across **3+ independent sources** → high confidence. If sources < 3, merge DETECT into CLUSTER analysis.
4. Layer 3 (YOUR job): Read the mention content for high-confidence anomalies. Classify into one of five categories:
   - **Crisis**: delta < -0.10 AND (spike OR cross_signal) — urgent action needed
   - **Opportunity**: delta > 0.10 AND density > 5× — positive spike to amplify
   - **Chronic/Structural (#45)**: Persistent negative signal that hasn't spiked but shows steady presence across 3+ consecutive windows — structural issue, not a spike
   - **Watchlist**: delta 0.05-0.10 OR single-source anomaly — ambiguous signal worth tracking
   - **Noise**: statistical flag but no semantic confirmation — false alarm
5. Write `anomalies/week-{week_start}.json`
6. Update session.md anomalies section
7. **Ad-hoc crisis digest:** If all 3 layers fire simultaneously, write an immediate short-form crisis digest covering just the crisis story.
8. Append to results.jsonl: `{"iteration": N, "type": "detect_anomalies", "statistical_flags": N, "cross_signal_confirmed": N, "crisis": N, "opportunity": N, "chronic": N, "status": "done"}`

### SYNTHESIZE (one story per iteration)

Pick the next unsynthesized story from the queue. **Story ordering (#49):** Crisis anomalies first, then by significance rank.

Assign each story a **weight tier (#23):**
- **Lead** (1-2 stories): Highest significance, drives executive summary framing
- **Supporting** (2-4 stories): Important context, gets full synthesis
- **Watchlist** (remaining): Brief treatment, monitoring-only

1. **Generate commodity baseline** using `freddy monitor baseline {site}` (deterministic, from CLI data)
2. **Synthesize**: Transform commodity facts into narrative. Requirements:
   - Open with **## Overview** anchoring this story in the full weekly context
   - Ground claims in specific numbers from raw data
   - **Delta framing**: State what CHANGED vs prior period with directional language
   - **Causal chain**: Connect data points into cause → effect → implication
   - **Competitor context**: Position findings against competitor activity where data exists
   - For anomaly-linked stories: state the anomaly type, confidence level, cross-signal evidence
   - Note which sources have NO coverage — absence is a signal
   - **"What didn't happen" analysis**: State expected events that are absent from data
   - **Contradiction and irony identification**: Look for structural contradictions
   - **Source semantics**: Interpret through platform context
   - **Confidence calibration (#25):** If sources < 2 → max confidence LOW-MEDIUM. If data window < 3 days → max confidence MEDIUM. State confidence level explicitly.
   - **Scanability (#24):** Use headers, bullet points, bold key metrics. A busy executive should get the gist in 30 seconds.
   - **Falsifiable claims (#24):** Every claim must be checkable against data. "Sentiment improved" → "Sentiment improved from 41% to 62% positive (source: CLI sentiment endpoint)."
   - Close with **## Recommended Actions** — imperative verb + responsible team + timeframe + dual-outcome framing
3. **Evaluate with session evaluator (per-story, 4 criteria: MON-1, MON-2, MON-4, MON-6):**
   ```bash
   python3 scripts/evaluate_session.py --domain monitoring --artifact sessions/monitoring/{client}/synthesized/{story-slug}.md --session-dir sessions/monitoring/{client}/ --mode per-story
   ```
   Parse the JSON output. Check the `decision` field. Missing or invalid evaluator output counts as `REWORK`, not pass.

4. **Keep condition:** Evaluator `decision` is `KEEP`. Even on KEEP, read per-criterion `feedback` from the `results` array and address any failed criteria.
5. **Quick sanity check:** Did synthesis lose data specificity? Hallucinate? If obvious regression → DISCARD.
6. **Devil's advocate:** Argue AGAINST keeping.
7. **Rework protocol:** Evaluator `decision` is `REWORK` → address failed criteria feedback and revise (max 2 rework attempts).

**Output:**
- KEEP: write `synthesized/{story-slug}.md`, append results.jsonl, update session.md
- REWORK: overwrite `synthesized/{story-slug}.md`, append results.jsonl
- DISCARD: append results.jsonl only, increment attempt counter

Results.jsonl: `{"iteration": N, "type": "synthesize", "story": "slug", "weight_tier": "lead|supporting|watchlist", "attempt": N, "before": 0.30, "after": 0.68, "delta": 0.38, "approach": "contextual comparison", "status": "kept|discarded|reworked"}`

### Recording Findings

After each SYNTHESIZE iteration, update `findings.md`:
- **Confirmed**: Pattern that passed all signals on first attempt
- **Disproved**: What caused a signal failure
- **Observations**: Source reliability, story type patterns
- Use `### [CATEGORY] Title` format with `**Evidence:**` and `**Detail:**` subfields.

### RECOMMEND

Write three separate output files (not recommendations.md):

1. **`recommendations/executive_summary.md`** — Total mention count, source breakdown, week's defining tension. State single highest-risk and highest-opportunity findings. Include community-vs-owned engagement ratio.

2. **`recommendations/action_items.md`** — Cap at 5 primary actions (#4), each with: imperative verb + responsible team + timeframe + dual-outcome framing ("Expected impact: X. Risk if not: Y."). Use "one thing" hierarchy: if the reader does only ONE action, which one? Put it first.
   - **Secondary Actions section (#7):** Below the top 5, list 3-5 lower-priority actions that were considered but didn't make the cut. Brief format: action + reason it's secondary.
   - **Monitoring triggers (#27):** For each action, specify: "Escalate to [tier] if [metric] crosses [threshold] by [date]."
   - Group by urgency tier: Immediately / This Week / Within N Days.

3. **`recommendations/cross_story_patterns.md`** — 2-4 patterns, each with: named connection, data from 2+ stories, what emerges from combination. Write comparison matrix to this file (#46).

**Scenario planning (#6):** In executive summary, include 1-2 conditional scenarios: "If [trigger condition], then [recommended response]."

Before writing, produce comparison matrix in session.md (max 10 rows).

**Evaluation (#12):** Apply all 3 signals to RECOMMEND output as a whole. Output format must be consistent JSON in results.jsonl.

Results.jsonl: `{"iteration": N, "type": "recommend", "stories_synthesized": N, "primary_actions": N, "secondary_actions": N, "patterns": N, "attempt": N, "status": "kept|discarded"}`

### EVALUATE_DIGEST

Absorbed into **DELIVER**. Do not call the full-digest evaluator against a missing `digest.md` — compile the digest first, then evaluate that compiled artifact.

### DELIVER

1. Compile `digest.md` from section files. Structure (#5): Executive Summary → Action Items → Cross-Story Patterns → Stories (Lead → Supporting → Watchlist) → Data Appendix
2. Data Appendix = commodity baseline markdown (already computed)
3. **Word budget (#26):** Target ~2,500 words for the full digest. Quality over quantity.
4. Run full-digest evaluation with all 8 criteria (MON-1 through MON-8):
   ```bash
   python3 scripts/evaluate_session.py --domain monitoring --artifact sessions/monitoring/{client}/digest.md --session-dir sessions/monitoring/{client}/ --mode full
   ```
   Read all per-criterion feedback. Missing or invalid evaluator output counts as `REWORK`, not pass. If `decision` is `REWORK`, revise the relevant section files, rebuild `digest.md`, and re-run evaluation. Max 2 rework rounds in DELIVER.
5. Write `synthesized/digest-meta.json` with: stories, executive_summary, action_items, week_ending, iteration_count, avg_story_delta
6. Persist metadata to DB: `freddy digest persist {site} --file synthesized/digest-meta.json`
7. Set Status: COMPLETE in session.md

Results.jsonl: `{"iteration": N, "type": "deliver", "stories_synthesized": N, "avg_delta": 0.41, "digest_sections": N, "word_count": N, "status": "complete"}`

## Exit Checklist (mandatory before setting Status: COMPLETE)

Before writing `## Status: COMPLETE`, verify ALL of the following:
1. `findings.md` has at least 1 entry under "## Confirmed" with evidence from this session
2. All deliverable files exist (digest.md, recommendations/*.md)
3. `results.jsonl` has at least 1 entry per completed phase

If findings.md is empty, you are NOT done. Write at least your top 3 observations before completing.

## Rules

1. NEVER stop to ask for confirmation. NEVER ask "should I continue?" Keep working.
2. When stuck: re-read the files for new angles, combine previous near-misses, try radical approaches.
3. ONE story per SYNTHESIZE iteration. Save and exit after each.
4. **Fresh mode stops after one phase.** In fresh mode, stop after persisting the completed phase. In multiturn mode, continue to the next required phase.
5. Keep CLI tool output concise. Don't flood your context with raw data.
6. Equal or worse = DISCARD. All three signals must not decrease.
7. Do NOT install packages, add dependencies, or import modules not already in the codebase.
8. Prioritize stories with anomaly flags and competitive implications.
9. Simplicity wins: tighter 5-story digest covering what matters beats 8-story padded with noise.
10. First-week protocol: no previous session → skip delta framing, use absolute metrics.
11. Every 3rd weekly digest, clear the Learnings section in session.md to force exploration.

## Additional Rules

- If a CLI tool returns no data or an error, note the gap in session.md and proceed. Never hallucinate.
- You infer mention intent directly from text — do NOT wire intent classification calls.

## session.md Constraints

Max ~2K tokens. REWRITE (not append) state and learnings each iteration. Store ANALYTICAL CONCLUSIONS in Learnings, not data summaries.
