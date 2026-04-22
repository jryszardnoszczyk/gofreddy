---
title: Evaluation + competitive second-pass — F-E.1..12 (judges, structural gates, rubrics, ad-domain filter)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-005-pipeline-overengineering-second-pass.md
---

# Deep-Research Follow-Up — Evaluation, Competitive, Monitoring Adapter

**Scope:** `src/evaluation/`, `src/competitive/service.py`, `src/competitive/markdown.py` (brief rendering — `brief.py` does not exist; `markdown.py` is the closest analog), `src/monitoring/adapters/news.py`.

**Note on missing file:** `src/competitive/brief.py` does not exist in the repo. The async fan-out + synthesis pattern the user asked about lives partially in `src/competitive/service.py` (parallel Foreplay+Adyntel fan-out) and the deterministic "synthesis" into markdown lives in `src/competitive/markdown.py`. Findings cover both; the "Opus-synthesis" step referenced in context is presumed to be the audit-pipeline port target, not present in competitive today.

## Exec Summary

Audited 4 targets looking for deterministic work that would be better done by an agent. Results:

- **`src/monitoring/adapters/news.py`:** NO agentification candidates. It's a correctly deterministic provider-shape-normalization adapter. It passes `source_priority`, `ai_tags`, `sentiment_label` through as-is (no classification in code) — exactly right for an adapter layer. This is the design the other 11 adapters should match; `news.py` is the positive exemplar, not a problem.
- **`src/evaluation/judges/` + `service.py`:** 2 HIGH, 1 MEDIUM. The evidence-verification fuzzy-match (F-E.1), the gradient evidence-gate ("cap at 3 if <2 evidence" — F-E.2), and the length-normalization formula (F-E.4) all encode content-judgment in frozen Python.
- **`src/evaluation/structural.py`:** 3 HIGH, 1 MEDIUM. F5.2 (prior audit) understated the scope. The 500-char brief threshold, the "3 headers" gate, the "no_excessive_rework" >3 attempts cap, the digest-hallucination regex guard, and the "synth_matches_stories ≥50%" ratio are all qualitative calls dressed as shape checks.
- **`src/evaluation/rubrics.py`:** 1 HIGH, 1 MEDIUM. The domain→word-range table (`_WORD_RANGES`), the domain→primary-deliverable table (`_JUDGE_PRIMARY_DELIVERABLE`), and the 32 frozen rubric prompts are lookup tables where an agent could pick context-appropriate scoring targets.
- **`src/competitive/service.py`:** 1 HIGH, 1 MEDIUM. The `_ad_domain_matches` filter is brittle string-matching that silently drops legitimate ads; the `data_quality` tier classification (`"rich" / "metadata_only" / "entity_only"`) is hardcoded based on shape only.
- **`src/competitive/markdown.py`:** 1 MEDIUM. The `_format_list_content` dispatch table (if title contains "share of voice" → SoV table, else → generic) is string-match dispatch that breaks on any agent-generated title variation.

**Pattern across findings:** The evaluation layer — supposedly the "fixed outer loop" — has more content-judgment-in-code than we admit. Every one of these Python-encoded heuristics is a thing an agent used to decide in prose and we calcified for reproducibility. That tradeoff was intentional (F5.2 documents the reasoning), but the footprint has grown past where it should stop.

**HIGH-priority findings: 7.** **MEDIUM: 5.** **LOW: 0** (didn't include speculative; kept to defensible).

---

## Findings

### [F-E.1] — Evidence verification by token-set overlap is content-judgment in regex dress

- **File:** `src/evaluation/judges/__init__.py:71-85` (`fuzzy_match`)
- **Today:** Splits quote and text into lowercase word sets; passes if ≥50% of quote tokens appear in the text. Used to verify judge-cited evidence is grounded (not fabricated). Threshold was originally 0.8, now 0.5 because legitimate paraphrases failed.
- **Why it's qualitative:** "Did the judge cite real evidence from the text?" is exactly the kind of semantic equivalence task token-overlap cannot handle. A judge saying "the brief acknowledges competitor X's pricing advantage" could be perfectly grounded even if the brief wrote "Competitor X undercuts on price" — zero token overlap with "acknowledges" / "pricing advantage". The 0.5 threshold is a numeric compromise between false-positive paraphrases and false-negative hallucinations; neither end is satisfied.
- **Agentic redesign:** Replace `fuzzy_match` with a lightweight LLM call per evidence quote: "Does this quote paraphrase something actually stated in the following text? YES/NO plus the matching span." Batch all quotes for a criterion in one call to stay cheap. Run as a pre-aggregation step.
- **Why agent wins:** Semantic paraphrase is literally why LLMs exist. 0.5 vs 0.8 was a two-year-old argument we're still having (see comment: "0.8 flipped legitimate passes to fail (MON-4 diagnosis, 2026-04-17)"). The threshold-dance is the tell.
- **New risks:** Added latency + cost per criterion. Mitigation: batch all sub-question evidence into one call per judge-response; use a cheap model (Haiku/Flash). Also risks a judge-judging-judge loop — agent prompt must be narrow ("paraphrase check only, don't re-evaluate the criterion").
- **Priority:** HIGH.

### [F-E.2] — Gradient evidence-gate "cap at 3 if fewer than 2 verified quotes"

- **File:** `src/evaluation/judges/__init__.py:124-130` (`_parse_gradient`)
- **Today:** If `score > 3` and verified-evidence count `< 2`, cap the score at 3. Applies to every gradient criterion regardless of domain.
- **Why it's qualitative:** "A gradient score above 3 requires at least 2 pieces of evidence" is a rule about judgment, not shape. Some criteria (e.g. GEO-4 "voice consistency") are fundamentally holistic — asking for 2 quoted passages misreads the criterion. The threshold 2 is a universal pick; it's arbitrary. And it fires *after* `fuzzy_match` decides what counts — so F-E.1's deficiencies compound here.
- **Agentic redesign:** Let the judge self-assess confidence alongside the score and let the meta-aggregator (or a dedicated critique-judge) decide when low-confidence high scores should be tempered. Or: have an agent examine the (score, reasoning, quoted evidence) tuple and decide whether the reasoning is actually supported — a calibration judge rather than a token gate.
- **Why agent wins:** The calibration judge generalizes across criteria (some need evidence count, some need evidence quality, some need structural evidence). The `>3 → 3` cliff is mathematically ugly — a 5 with 1 evidence becomes a 3, but a 3 with 0 evidence stays 3.
- **New risks:** Calibration judge can be optimistic the same way the scoring judge was. Mitigation: calibration agent sees only the reasoning + evidence, not the score — blind re-assessment.
- **Priority:** HIGH.

### [F-E.3] — `_build_cross_item_text` concatenates with naïve slug extraction

- **File:** `src/evaluation/service.py:515-524`
- **Today:** For GEO-6 and SB-8 cross-item criteria, concatenates all outputs with `=== PAGE: {slug} ===` / `=== STORY: {slug} ===` delimiters, where slug is `filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]`.
- **Why it's qualitative:** The text format is a *prompt engineering* decision masquerading as a utility function. For GEO-6 (angle diversity across pages) the judge needs to see *what makes each page distinctive* — filename-slug plus raw content isn't the optimal shape. The concatenation order is alphabetical-by-filename, which may not match the narrative order. There's no per-page metadata (target query, attempt number) passed through despite those being central to "same angle vs different angle" judgment.
- **Agentic redesign:** Have a "cross-item framer" agent prepare the context: for each item, emit a structured mini-summary (target query, angle declared, distinguishing claim) and *then* concatenate those summaries for the cross-item judge. The framer is small, cheap, and lets the cross-item judge focus on similarity rather than parsing raw page HTML.
- **Why agent wins:** Cross-item judges currently see 5 pages × 2000 words = 10k words of raw content with minimal scaffolding. Framing dramatically improves signal-to-noise.
- **New risks:** Another failure mode layer; framer errors propagate to judge. Mitigation: framer output is purely additive scaffolding — raw content is still included.
- **Priority:** MEDIUM (real tradeoff: framer adds latency, and current approach is "working").

### [F-E.4] — Length-factor formula is a baked-in heuristic for domain quality

- **File:** `src/evaluation/service.py:77-114` + `_WORD_RANGES` at line 30
- **Today:** Per-domain word ranges `{"geo": (800,2000), "competitive": (2000,5000), "monitoring": (1500,4000), "storyboard": (300,800)}`. Outside the range, linear penalty with 0.3 floor, 1.5x upper buffer.
- **Why it's qualitative:** "How long should a competitive brief be?" depends on data richness, number of competitors, client context depth. The (2000, 5000) range is a guess that was correct for 2025's typical input; a brief about 1 competitor shouldn't be judged against the same range as one about 8. The linear penalty + floor is a scoring primitive dressed as infrastructure.
- **Agentic redesign:** Ask a calibration agent: "Given the input data (N competitors, K data-rich competitors, client stage), what's the expected word count range for a brief that's neither padded nor sparse?" Use that dynamic range in the formula. Alternatively, drop length-factor entirely and trust rubric MON-8 ("word count proportional to importance") + CI-8 ("does the brief recalibrate when data fails"), which already measure this qualitatively.
- **Why agent wins:** Current system double-penalizes: a sparse-data brief that's correctly short gets hit by length-factor *and* by the rubrics asking "did you acknowledge the gap." An agent sees the data-tier distribution and sets the expected range.
- **New risks:** Length-factor becomes non-deterministic across re-runs; cache key has to include the range. Mitigation: derive range from a deterministic function of input-data metadata (competitor count, data-tier counts) — not from model output.
- **Priority:** HIGH.

### [F-E.5] — Structural gate's `_validate_competitive` encodes "substantive" as 500 chars + 3 headers

- **File:** `src/evaluation/structural.py:101-108`
- **Today:** Rejects briefs `<500 chars` or with `<3` markdown headers. Docstring (line 84-89) explicitly acknowledges this is content-judgment trying to avoid content-judgment: "Bumping to 500 chars and requiring parseable competitor data blocks that failure mode without encoding content judgments in frozen code."
- **Why it's qualitative:** 500 chars is ~80 words — that's not "substantive," it's "exists". Most of the failure cases this was designed to catch (placeholder briefs with 3 fake headers) get past 500+3 trivially. A genuinely bad brief at 600 chars with 3 headers passes; a genuinely good low-data brief at 450 chars with 2 headers fails. Both outcomes are wrong.
- **Agentic redesign:** Drop the char/header gates entirely. The job of structural is "does the file exist and parse" — keep that. A 1-paragraph "no data available" brief is a valid low-volume output; CI-8 is the rubric that decides whether that's good or bad for the input it had.
- **Why agent wins:** We already have CI-1 (thesis clarity) and CI-8 (data-gap acknowledgment) as the rubrics for "is this brief substantive." The structural gate is duplicating their work with a worse heuristic and *pre-empting* their judgment — structural failure skips all 8 rubrics.
- **New risks:** Empty-string / 1-char briefs now reach judges and waste tokens. Mitigation: check for non-empty content (> 50 chars is a reasonable "did something actually render" floor), drop the 500+3 gate.
- **Priority:** HIGH.

### [F-E.6] — Structural gate `no_excessive_rework` and `synth_matches_stories ≥50%` thresholds

- **File:** `src/evaluation/structural.py:217-231` + `207-213`
- **Today:** DQS assertion 11 fails when `>3` synthesize attempts on any story. Assertion 10 fails when `<50%` of stories have a synthesized counterpart (with digest.md as escape hatch). Both are "structural" gates per the filename.
- **Why it's qualitative:** "Did the agent rework too much?" is a process-efficiency judgment. An agent that rewrote story 7 four times because the first three pushed back incorrectly on sentiment-scoring nuances is doing *better* work than one that accepted draft 1. The 3-attempt cap encodes "fast > thorough." Similarly, 50% synth coverage is arbitrary — a week with 12 stories where only 4 synthesized is arguably correct if 8 were noise.
- **Agentic redesign:** Move these into the monitoring rubric set as context signals for MON-2 (defensible severity classifications) and MON-8 (editorial restraint). Let the judge see attempts/stories/synth counts in the rubric prompt and judge whether restraint was exercised. Or convert to *monitoring metrics* that live in observability, not pass/fail gates.
- **Why agent wins:** Current design blocks the evaluation when the agent's process was "wrong" by a heuristic. We want to evaluate the *output*, and if process was messy but output was good, we should reward output. Conversely, if process was clean but output was thin, we should punish output.
- **New risks:** Losing visibility into "this agent is thrashing." Mitigation: keep the assertions as monitoring-only (the DQS score already tracks them), don't gate on them.
- **Priority:** HIGH.

### [F-E.7] — Digest-hallucination guard via `"Digest persisted" in session_md` string match

- **File:** `src/evaluation/structural.py:276-281`
- **Today:** If `session.md` contains the string "Digest persisted", require `synthesized/digest-meta.json` to exist; otherwise fail. Added to catch agents writing narrative claims about running a command they didn't run.
- **Why it's qualitative:** This is string-matching a specific hallucination pattern. The next hallucination pattern — "Successfully persisted digest" or "Digest saved" or "Ran `freddy digest persist`" — slips through unchanged. The commit history will show patch after patch adding more hallucination-phrase regexes.
- **Agentic redesign:** Have a small "claim-grounding checker" agent read session.md, extract any claims of side-effects ("ran X command", "persisted to Y", "wrote Z file"), and verify each against the actual outputs bundle. Broader coverage, one abstraction.
- **Why agent wins:** Claim extraction is paraphrase-invariant. Today's regex catches one phrasing out of thousands.
- **New risks:** Agent could itself hallucinate a claim; add evidence-span requirement ("quote the exact session.md passage making the claim"). Same pattern we already use for evidence gates.
- **Priority:** HIGH.

### [F-E.8] — `_JUDGE_PRIMARY_DELIVERABLE` lookup table encodes "what to grade"

- **File:** `src/evaluation/service.py:57-64`
- **Today:** Hardcoded `{"monitoring": ("digest.md",), "competitive": ("brief.md",)}`. For GEO and storyboard, *all* outputs are concatenated; for monitoring + CI, only the named file is sent to judges.
- **Why it's qualitative:** The decision of "what's the deliverable worth grading" is a product-shape call. If a monitoring run produces a good digest but the recommendations/ files are hollow, the judges never see the recommendations. If storyboard stories get an extra review pass that lands in `reviews/`, judges would include them — not necessarily desired. When a new domain or sub-deliverable lands, this table must be edited.
- **Agentic redesign:** Ask a "scoring-scope agent" per evaluation: "Given this outputs bundle, which file(s) constitute the primary deliverable the user would ship?" Default to all, but let the agent override. Record the scope decision in the evaluation record for traceability.
- **Why agent wins:** New domains / new sub-artifacts don't require a code change. The scope decision becomes explicit and auditable per-eval.
- **New risks:** Scope can drift across runs — cache invalidation. Mitigation: include scope-decision in the content-hash.
- **Priority:** MEDIUM (the table is small and stable today; wins are modest; real value emerges when domains proliferate).

### [F-E.9] — 32 frozen rubric prompts in `rubrics.py` with monolithic version hash

- **File:** `src/evaluation/rubrics.py` (entire file + `RUBRIC_VERSION` at line 994)
- **Today:** 32 criteria prompts as Python string constants, SHA256'd into a 12-char version hash that's used as the cache key for evaluation records.
- **Why it's qualitative:** The prompt *text* is the model's instruction set. Today, improving GEO-3 (competitor-honesty criterion) requires a code change, a version-hash roll, and invalidation of every cached GEO evaluation (32 criteria, all bumped together). Worse: the prompts treat all 4 domains as peers when some criteria probably need client-context-specific refinement (a fintech's "verifiable claims" bar differs from a consumer-app's).
- **Agentic redesign:** Store rubrics as data (db rows or markdown files), keyed per-criterion with its own hash. Let a rubric-curator agent propose per-client or per-domain-sub-variant refinements grounded in evaluation failure analysis — human still approves. Roll only the one criterion's hash when it changes.
- **Why agent wins:** Decouples rubric evolution from code deploys; enables A/B of criterion wording; avoids full-cache-flush for single-criterion tweaks.
- **New risks:** Rubric quality drift if agents are allowed to auto-roll. Mitigation: propose-only, human approval required; keep "baseline" rubric set in code as fallback.
- **Priority:** MEDIUM (infra change; payoff is long-horizon; no urgency).

### [F-E.10] — `_ad_domain_matches` silently drops ads on any non-exact host match

- **File:** `src/competitive/service.py:40-53`
- **Today:** Filters out ads where `link_url` hostname doesn't exactly match the queried domain (after www-stripping). Added as issue #11 (Foreplay substring-matching false positives for "sketch.com" → "mangasketch.com").
- **Why it's qualitative:** "Does this ad belong to the queried advertiser?" is a brand-identity judgment. Sketch Ltd runs ads that `link_url` to `getsketchapp.com` (a landing page subdomain). Those get dropped. Similarly, ad-rotation can point to affiliate shorteners (bit.ly, tracked URLs through ad-network redirects). Exact-host matching is a 90% solution that silently drops the other 10%.
- **Agentic redesign:** When link_url host ≠ queried domain, call a lightweight agent with (queried brand name, queried domain, ad copy, ad image URL, link_url, redirect chain if available) and ask "Is this ad from this advertiser? YES/NO/UNSURE." Batch per-search. Keep the fast-path (exact host match = keep, no agent call).
- **Why agent wins:** Recovers genuine ads currently dropped; handles multi-domain brands; handles tracked-URL redirects. Fast path (exact match) keeps the common case free.
- **New risks:** Extra latency + cost for ambiguous ads; agent could false-positive affiliate ads as brand ads. Mitigation: only call agent when drop rate is high (≥10%); persist agent decisions as training data.
- **Priority:** HIGH.

### [F-E.11] — `data_quality` tier classification is shape-check masquerading as richness judgment

- **File:** `src/competitive/service.py:187` + `203-205`
- **Today:** Foreplay ads always tagged `"rich"`; Adyntel ads tagged `"metadata_only"` if body content is non-empty, else `"entity_only"`. These tiers propagate into `data_tier` fields that rubrics CI-8 ("does the brief recalibrate confidence for detect-only competitors?") depend on.
- **Why it's qualitative:** Foreplay returning a record with empty transcription, blank persona, and missing emotional_drivers is not "rich" just because Foreplay is the provider. A thin Adyntel ad with one good variant body can be richer than a Foreplay ad with nothing but a headline. Tier should reflect *actual content present*, not provider brand.
- **Agentic redesign:** Compute data_tier from presence of rich fields: transcription exists → rich; body_text exists → standard; identity-only → minimal. Or, for per-ad granularity, have the synthesis-time agent assess richness itself. Either beats the current provider-based label.
- **Why agent wins:** Correctly penalizes thin Foreplay responses; correctly credits rich Adyntel ones; the CI-8 rubric (which consumes data_tier) becomes defensible.
- **New risks:** Changing tier semantics invalidates historical evaluations. Mitigation: version the tier schema, re-tier on read for old rows or simply accept the drift (tier isn't persisted in DB as primary signal).
- **Priority:** MEDIUM (real fix but per-ad granularity shifts downstream semantics; needs care).

### [F-E.12] — `markdown.py` `_format_list_content` uses substring-on-title dispatch

- **File:** `src/competitive/markdown.py:63-79`
- **Today:** Picks a renderer by string-matching section title: `"share of voice" in title_lower` → SoV table, `"sentiment" in title_lower` → sentiment table, etc.
- **Why it's qualitative:** Section titles come from agent output — an agent writing "Share-of-Voice Analysis" is fine, but "Voice-Share Breakdown" falls through to `_format_generic_table`. The rendering is keyed on a creative surface rather than on data shape. A new section type requires a code edit; a title rename by the agent silently degrades the brief.
- **Agentic redesign:** Two paths: (a) dispatch on *data shape* of `content` (has `mention_count` + `percentage` keys → SoV; has `avg_sentiment` → sentiment), not on title; or (b) render per section via a small "markdown-for-this-data" agent call, post-synthesis. Path (a) is cheaper; path (b) is more flexible for novel data shapes.
- **Why agent wins:** Decouples rendering from agent-chosen title wording; new section types work automatically if data keys are distinct.
- **New risks:** Shape-based dispatch can collide if two section types share keys (none do today, but could). Mitigation: explicit marker key (`_render_as: "sov_table"`) that the agent can set.
- **Priority:** MEDIUM (works for today's 4 section types; failure mode is cosmetic — generic table vs specialized table).

---

## Confirmed correctly-deterministic (NO findings)

- **`src/monitoring/adapters/news.py`:** `_map_article` is shape-normalization. `source_priority`, `ai_tags`, sentiment pass through raw — no classification in adapter code. `_compute_sentiment_score = pos - neg` is a provider's stated formula, not a judgment. Kept as positive exemplar. *(If anything, the finding-worthy concern is downstream: nothing in `src/monitoring/` consumes `source_priority`. Raw data is collected and thrown away. That's an agent-consumption gap, not a deterministic-overreach.)*
- **`service.py` TTL cache + retry:** correctly deterministic infra.
- **`structural.py` JSON parse checks for GEO / competitors / storyboards:** correctly deterministic (parse-or-fail is a shape test).
- **`structural.py` session.md presence check, results.jsonl presence:** correctly deterministic file-exists gates.
- **`judges/gemini.py` + `openai.py` retry + schema cleaning:** correctly deterministic.
- **`service.py` content_hash + cache lookup:** correctly deterministic.

---

## Summary table

| ID     | Area                              | Priority |
|--------|-----------------------------------|----------|
| F-E.1  | fuzzy_match evidence verification | HIGH     |
| F-E.2  | gradient evidence-gate cap-at-3   | HIGH     |
| F-E.3  | cross-item text concatenation     | MEDIUM   |
| F-E.4  | length-factor word ranges         | HIGH     |
| F-E.5  | competitive 500-char/3-header gate| HIGH     |
| F-E.6  | no_excessive_rework + synth ratio | HIGH     |
| F-E.7  | digest-hallucination regex guard  | HIGH     |
| F-E.8  | _JUDGE_PRIMARY_DELIVERABLE table  | MEDIUM   |
| F-E.9  | 32 frozen rubric prompts          | MEDIUM   |
| F-E.10 | ad-domain exact-host filter       | HIGH     |
| F-E.11 | data_quality tier by provider     | MEDIUM   |
| F-E.12 | markdown title-substring dispatch | MEDIUM   |

**7 HIGH, 5 MEDIUM, 0 LOW.** Most concentrated area: `src/evaluation/` (8 of 12). The pattern is consistent — "we gated the judge on a heuristic *because the judge used to hallucinate*, and the heuristic has now calcified into content-judgment-in-code." The audit's F5.2 was directionally right but understated the scope: it's not just structural.py — it's structural, service.py, judges/__init__.py, and rubrics.py all carrying qualitative-in-code load.
