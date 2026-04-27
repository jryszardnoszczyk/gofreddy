# Autoresearch Prompt Audit

**Date:** 2026-04-11
**Scope:** All 4 lane prompts (geo, competitive, monitoring, storyboard), render_prompt infrastructure, evaluator alignment
**Follows:** `2026-04-11-autoresearch-evaluation-infrastructure-audit.md` (ISSUE-11, ISSUE-20 expanded here)

## Prompt Size Inventory

| Lane | File | Lines | Bytes | ~Tokens | Phases |
|------|------|-------|-------|---------|--------|
| storyboard | `programs/storyboard-session.md` | 631 | 37,972 | ~9,500 | 6 (SELECT_VIDEOS → REPORT) |
| geo | `programs/geo-session.md` | 377 | 28,733 | ~7,200 | 5 (DISCOVER → REPORT) |
| competitive | `programs/competitive-session.md` | 366 | 27,528 | ~6,900 | 4 (GATHER → VERIFY) |
| monitoring | `programs/monitoring-session.md` | 247 | 18,893 | ~4,700 | 6 (SELECT_MENTIONS → DELIVER) |

Plus ~200 tokens appended per invocation by `config.py:render_prompt()`:
- Global findings file (`{domain}-findings.md`): ~70 tokens currently (6 lines each)
- Runtime Context block: ~125 tokens
- Fresh Session Override (fresh mode only): ~50 tokens

**Total prompt per fresh-mode invocation:** 4,900–9,700 tokens depending on lane.

---

## Issues

### PROMPT-1: Source-Quoting Requirement describes a removed evaluation mechanism

**Severity:** HIGH — actively misleading
**Files:** All 4 `programs/*-session.md` (~8-10 lines each, ~150 tokens each, ~600 total)
**Eval infra ref:** Relates to grounding gate removal documented in `src/evaluation/service.py:124-127`

**Problem:** All 4 prompts contain a Source-Quoting Requirement section that says:

> "Your numeric claims are scored by a **verbatim grounding matcher** that compares each claim against the raw source data"

This mechanism was **deliberately removed**. From `src/evaluation/service.py:124-127`:

```python
# The programmatic grounding gate was removed as a deliberate architectural
# decision — the regex-based claim extraction was flawed, flaky, and harmful
# (false failures on storyboard narrative, geo domain terminology, etc.).
# Factual accuracy is already covered proportionally by the LLM judge criteria.
```

The actual LLM judge criteria (CI-1→CI-8, GEO-1→GEO-8, MON-1→MON-8, SB-1→SB-8) do **not** require verbatim quoting. The closest are:
- CI-2: "Every claim traces to something observed" (evidence tracing, not verbatim matching)
- GEO-2: "Facts are specific, verifiable, and current" (specificity, not verbatim)
- MON-6: "Every number answers 'so what?'" (interpretation, not matching)

None enforce a mechanical verbatim matcher.

**Impact:**
- Agents over-optimize for verbatim quoting at the expense of synthesis quality and readability
- The monitoring prompt's "Bad/Good" example literally says to quote `body_text` and engagement counts verbatim — this produces bloated, quote-heavy output that the LLM judges don't reward
- The storyboard prompt warns against "synthesized narrative phrases" like "The Lost Cycle" — but SB-1 actually rewards creative authenticity, not source-quoting
- Each prompt spends ~150 tokens on a constraint that doesn't exist

**Evidence — the Good/Bad examples are actively counterproductive:**

Monitoring prompt example of "Good":
> `Pricing backlash: 42 mentions in mentions/week-{week_start}.json. Top engagement quotes: "the new pricing tier is absurd for small teams" — 312 upvotes (reddit.com/r/productivity); "$40/mo for basic is insane" — 89 likes (twitter.com/user); week total 7,715 engagement.`

This is bloated quote-heavy prose. MON-8 (the actual evaluator criterion) says: "Word count is proportional to importance... Editorial restraint is visible." The verbatim-quoting instruction fights the actual evaluator.

**Fix:** Rewrite Source-Quoting Requirement to match actual evaluation behavior. Keep the principle (ground claims in data) but remove the fiction (verbatim matcher, mechanical scoring). Reference what the LLM judges actually reward.

---

### PROMPT-2: Fresh-mode override buried at end of 9K+ token prompt

**Severity:** HIGH — prompt ordering degrades instruction following
**Files:** `runtime/config.py:168-179` (Fresh Session Override appended last), all 4 `programs/*-session.md`
**Eval infra ref:** ISSUE-11 from infrastructure audit

**Problem:** The fresh-mode constraint is the single most important behavioral directive for evolution runs, but it's the LAST thing in the prompt:

1. Lines 1-N: Full multi-phase workflow (4,700–9,500 tokens of "continue into next phase" instructions)
2. Lines N+1: Runtime Context block (~125 tokens)
3. Lines N+2: Fresh Session Override (4 lines, ~50 tokens)

The agent has already internalized thousands of tokens of multi-phase priming before it reads the override. This is backwards — the most critical constraint should be at the TOP, not buried after the entire workflow program.

**Fresh-mode instructions are scattered across 5 locations per prompt:**

| Location | Example text | Position in prompt |
|----------|-------------|-------------------|
| Operational Reality section | "If runtime context says Strategy: fresh, complete one phase and stop" | Lines 10-15 (early) |
| Each phase ending | "In fresh mode stop after this phase. In multiturn mode continue..." | Repeated 4-6× throughout |
| Rules section | "Fresh mode = one phase. Multiturn mode = continuous phases." | Near end of program |
| Runtime Context block | "Strategy: fresh" (metadata) | Appended by config.py |
| Fresh Session Override | "Complete exactly ONE phase, persist state to files, then stop" | **Very last section** |

The override at position 5 must overcome the priming from positions 1-4 which intermix fresh and multiturn instructions.

**Impact:** The agent is primed for multi-phase work and must overcome that priming to follow the fresh override. This is consistent with observed behavior where agents sometimes start a second phase before the harness kills them (wasting turns), or don't write the results.jsonl entry promptly because they're mentally "continuing."

**Fix:** Move the fresh-mode override to a prominent position BEFORE the phase protocols — or restructure the prompt to only include the current-phase protocol.

---

### PROMPT-3: Phase bloat — 50-70% of prompt irrelevant per fresh-mode invocation

**Severity:** HIGH — wastes 3,000-6,000 tokens per invocation
**Files:** All 4 `programs/*-session.md`
**Eval infra ref:** ISSUE-11 from infrastructure audit

**Problem:** Fresh mode runs ONE phase per invocation but every prompt loads ALL phases. Per-invocation waste:

| Lane | Total tokens | Relevant to any single phase | Waste per invocation |
|------|-------------|------------------------------|---------------------|
| storyboard | ~9,500 | ~3,000-4,000 | ~55-65% |
| geo | ~7,200 | ~3,000-3,500 | ~50-55% |
| competitive | ~6,900 | ~3,000-3,500 | ~50-55% |
| monitoring | ~4,700 | ~2,000-2,500 | ~47-53% |

**Specific waste by lane:**

**Storyboard (worst case):** Agent doing SELECT_VIDEOS receives:
- ANALYZE_PATTERNS protocol: 93 lines of batch curl submission and pattern extraction
- PLAN_STORY protocol: 91 lines of story bible synthesis and evaluator integration
- IDEATE protocol: 70 lines of storyboard creation with retry loops
- GENERATE_FRAMES protocol: 130 lines of anchor/scene generation, verification, approval
- REPORT protocol: 20 lines
- Total irrelevant: ~404 lines (~5,000 tokens)

**GEO:** Agent doing OPTIMIZE receives EFFICIENCY MODE iteration descriptions for DISCOVER+COMPETITIVE+SEO_BASELINE+REPORT. Agent doing DISCOVER receives full OPTIMIZE cycle + CQ-1→CQ-12 + Block Formats + Scoring Rubric + Report Specification.

**Competitive:** Agent doing GATHER receives ANALYZE (58 lines), SYNTHESIZE (40 lines), VERIFY (18 lines). Agent doing VERIFY receives the entire GATHER protocol with fallback cascades.

**Monitoring:** Agent doing SELECT_MENTIONS receives CLUSTER_STORIES, DETECT_ANOMALIES, SYNTHESIZE, RECOMMEND, DELIVER (~115 lines).

**Counter-argument:** Seeing the full pipeline may help agents make better phase-specific decisions (e.g., SELECT_VIDEOS knowing what ANALYZE_PATTERNS needs). Mitigation: include a 2-3 line summary of each downstream phase when stripping.

**Fix:** Phase-strip in `render_prompt()` — detect current phase from session.md state, include only the relevant phase protocol + brief summaries of adjacent phases + shared sections (tools, rules, source quoting).

---

### PROMPT-4: Inline bash code templates in storyboard (~1,500 tokens)

**Severity:** MEDIUM
**File:** `programs/storyboard-session.md` — multiple locations

**Problem:** The storyboard prompt contains ~126 lines of literal bash code templates (for loops, curl commands, JSON parsing):

| Section | Lines | Content |
|---------|-------|---------|
| ANALYZE_PATTERNS batch submission | 129-153 | Batched curl with parallel background jobs |
| Pattern fetch parallel | 157-164 | `for ANALYSIS_ID in ... &; done; wait` |
| IDEATE storyboard creation | 377-403 | Sequential curl with retry loop (27 lines) |
| GENERATE_FRAMES anchor generation | 455-477 | Parallel anchor curl (23 lines) |
| GENERATE_FRAMES scene generation | 480-494 | Scene preview curl (15 lines) |
| GENERATE_FRAMES verification | 508-521 | Verify curl loop with 5s spacing (14 lines) |
| GENERATE_FRAMES approval | 566-577 | Approval curl with revision re-read (12 lines) |

These are literal `for PID in ${PROJECT_IDS}; do ... done` scripts. The Claude agent can derive curl commands from API endpoint descriptions — it doesn't need the full bash loop scaffolding. The loops also embed specific implementation decisions (batch size 5, wait between calls, background jobs) that may be outdated or suboptimal.

**Impact:** ~1,500 tokens of copy-paste templates that crowd out analytical instructions. The agent often modifies these templates anyway (different variable names, error handling), so they're not saved verbatim.

**Fix:** Keep ONE example curl per endpoint pattern (showing URL, auth header, body shape). Remove for-loop scaffolding, batch orchestration, and retry loops — the agent can construct iteration logic from the endpoint description. Conservative savings: ~800 tokens.

**Risk:** Agent constructs slightly wrong curl commands → phase fails. Mitigated by keeping critical details (endpoint paths, required headers, body field names) and only removing bash scaffolding.

---

### PROMPT-5: Prompt-evaluator criteria alignment gaps

**Severity:** MEDIUM — missed optimization, causes unnecessary rework iterations
**Files:** All 4 `programs/*-session.md` vs `workflows/session_eval_*.py`

**Problem:** The prompts don't cover several key things the LLM judges actually evaluate. Agents generate content blind to these criteria, fail evaluation, get feedback, and rework — burning iterations. With tight max_iter budgets (6 for geo/competitive), every wasted rework is expensive.

**Verified blind spots (confirmed missing after re-inspection):**

| Criterion | What it actually evaluates | Prompt coverage |
|-----------|--------------------------|----------------|
| **CI-1** | Brief has a thesis organizing the entire document | **MISSING** — "open with most actionable finding" ≠ "thesis organizing entire document" |
| **GEO-3** | Honestly position client including where they lose | **MISSING** from CQ requirements — CQ-4 says "comparison table" but not "include where you lose" |
| **SB-4** | Turn recontextualizes the beginning | **MISSING** — no reframing/twist instruction |
| **SB-8** | Five genuinely different bets, not variations | **MISSING** — no diversity enforcement for story plans |

**Initially flagged but actually covered (false positives):**

| Criterion | Why it's actually covered |
|-----------|--------------------------|
| **CI-7** (prioritization) | SYNTHESIZE recommendations section already requires "3-5 specific" prioritized items |
| **GEO-7** (answer target queries) | Already in Scoring Rubric as "Answer directness" dimension |
| **MON-3** (one thing matters most) | RECOMMEND already says "State single highest-risk and highest-opportunity findings" |

**Partially covered (not worth adding — incremental gap):**

| Criterion | Evaluator focus | Prompt coverage gap |
|-----------|-----------------|-------------------|
| **CI-2** | Confidence explicit, conclusions proportional to evidence | Constitution covers evidence requirement but not proportionality |
| **GEO-6** | Cross-page coherence — pages reinforce, not cannibalize | CQ-9 says "different angle" but not "reinforce as a site" |
| **MON-8** | Editorial restraint — some data deliberately left out | Word budget (2,500) covers length but not editorial selection |
| **SB-6** | Scenes describable by current AI video models | Partially covered but no explicit "AI-producible" constraint |

**Impact:** On first attempt, agents miss the 4 verified blind spots. Each rework costs 1 iteration. With max_iter=6 for geo/competitive, losing even 1 iteration to avoidable rework is significant.

**Design tension:** Revealing the full rubric risks "teaching to the test" — agents might game criteria instead of producing genuinely good output. The evaluator is meant to be an independent quality check.

**Fix:** Add 1-2 lines per prompt for the 4 verified gaps only. Frame as quality principles, not checklist items:
- Competitive SYNTHESIZE: add "The brief should be organized around a single strategic thesis — every section serves that argument."
- GEO CQ requirements: add "Include where competitors genuinely win over the client — AI engines reward honest positioning."
- Storyboard PLAN_STORY: add "The turn should recontextualize the opening — by the end, the first scene means something different."
- Storyboard PLAN_STORY: add "Plans must be genuinely different bets — different premises, emotional registers, structural choices."

**Risk:** "Teaching to the test" → formulaic output. Mitigated by framing as principles, not checklist items.

---

### PROMPT-6: PLAN_STORY single-phase overload

**Severity:** MEDIUM — causes iteration waste when phase doesn't complete
**File:** `programs/storyboard-session.md` lines 209-357

**Problem:** PLAN_STORY asks the agent to do ALL of this in ONE fresh-mode invocation (100 turns):

1. Read all pattern files from `patterns/*.json` (15-20 files)
2. Synthesize a story bible (narrative, visual, audio analysis)
3. Generate 5 DETAILED story plans (each ~50-line JSON with 30+ fields including voice scripts, audio design, per-scene visual prompts)
4. Run `evaluate_session.py` on each of the 5 plans (5 subprocess calls, each invoking Gemini LLM judge)
5. Process evaluator feedback for each plan
6. Rework any failed plans (up to 3 attempts × 5 plans = 15 eval calls worst case)
7. Write 5 files to `stories/*.json`
8. Update session.md and results.jsonl

With 5+ evaluator subprocess invocations (each running 8 Gemini LLM judge criteria), extensive file I/O, and complex creative generation, this is the most compute-intensive single phase across all 4 lanes.

The phase event (`plan_story` in results.jsonl) is only written at the END. If the agent runs out of turns before finishing, no phase event is recorded, the harness times out, and the entire iteration is wasted.

**Impact:** The v004 Gossip.Goblin session took 10 iterations total but only 6 were needed for the 6 phases — 4 iterations were wasted on incomplete phases or rework. PLAN_STORY is the most likely phase to cause this waste.

**Fix options considered:**
- (a) Split PLAN_STORY into "PLAN_STORY_BIBLE" (synthesize bible) + per-story "PLAN_STORY_N" iterations — more phases but each is completable
- (b) Write partial results.jsonl entries as plans are created (not just at end) so the harness sees progress
- (c) Reduce from 5 to 3 story plans to fit within turn budget

**WITHDRAWN from fix plan:** Option (c) conflicts with evaluator criterion SB-8 which says "The **five** plans are genuinely different bets." Reducing to 3 would lower scores. Options (a) and (b) require harness changes (new phase types in TRACKED_PHASE_TYPES, or changes to phase detection logic). v004 Gossip.Goblin completed PLAN_STORY successfully — the overload concern is theoretical, not demonstrated in practice.

---

### PROMPT-7: Global findings file grows unboundedly

**Severity:** MEDIUM — latent, worsens over generations
**File:** `runtime/config.py:145-147`
**Eval infra ref:** ISSUE-20 from infrastructure audit

**Problem:** `render_prompt()` appends the entire `{domain}-findings.md` to every prompt without truncation:

```python
findings_path = script_dir / f"{domain}-findings.md"
if findings_path.exists():
    text += f"\n## Global Findings (from prior sessions)\n{findings_path.read_text()}"
```

The evolution loop promotes confirmed findings from session-level `findings.md` to global `{domain}-findings.md` via `FindingsPromotionConfig` (threshold: 2-3 confirmations). Over many generations, this file grows.

**Current state:** ~280 bytes each (empty templates, 6 lines). After 20+ generations with 3 fixtures each, could reach 5-10K tokens.

**Impact:** Progressive prompt bloat that degrades agent performance over time. Unlike the other prompt issues which are static, this one gets worse as evolution succeeds.

**Fix:** Truncate to a budget (e.g., last 2K tokens or top-N findings by recency). Alternatively, cap the findings file itself during promotion.

---

### PROMPT-8: Triple-redundant fresh/multiturn instructions

**Severity:** LOW-MEDIUM — wasted tokens + competing signals
**Files:** All 4 `programs/*-session.md`, `runtime/config.py`

**Problem:** Every prompt says the same fresh/multiturn constraint 4-5 ways:

1. **Operational Reality** section: "If runtime context says Strategy: fresh, complete one phase and stop"
2. **Each phase ending** (4-6 times per prompt): "In fresh mode stop after this phase. In multiturn mode continue..."
3. **Rules section**: "Fresh mode = one phase. Multiturn mode = continuous phases."
4. **config.py Runtime Context**: Injects `Strategy: fresh`
5. **config.py Fresh Session Override**: "Complete exactly ONE phase, persist state to files, then stop"

In storyboard that's 6 identical "Persist state and continue according to strategy" sentences at the end of 6 phase protocols.

**Impact:** ~300-400 tokens wasted per prompt on restating the same constraint. The repetition doesn't reinforce — it's noise that dilutes the signal.

**Fix:** State the constraint ONCE prominently at the top. Remove per-phase repetition. Keep the config.py override as a safety net.

---

### PROMPT-9: Cross-prompt boilerplate duplication

**Severity:** LOW-MEDIUM — architectural debt
**Files:** All 4 `programs/*-session.md`

**Problem:** All 4 prompts repeat nearly identical sections with minor cosmetic variations:

| Section | Geo | Competitive | Monitoring | Storyboard | Content |
|---------|-----|-------------|------------|------------|---------|
| Operational Reality | 10 lines | 8 lines | 6 lines | 6 lines | ~identical: fresh/multiturn, CLI trust, evaluator note |
| Source-Quoting Req | 8 lines | 8 lines | 8 lines | 8 lines | Same structure, different source files |
| First Action | 4 lines | 4 lines | 4 lines | 4 lines | "Read session.md, read results.jsonl, decide" |
| Exit Checklist | 8 lines | 6 lines | 6 lines | 6 lines | findings.md + deliverables + results.jsonl |
| Rules section | 10 lines | 8 lines | 12 lines | 8 lines | Never ask, one-per-iteration, session.md 2K |
| API Failure Handling | 3 lines | 3 lines | 3 lines | 12 lines | "Log failure, don't retry same call" |

~50-60 lines of boilerplate per prompt, ~200+ lines total across 4 prompts.

**Impact:** Maintenance burden — fixing a cross-cutting issue (like the Source-Quoting Requirement) requires editing 4 files. No runtime token impact (each agent only sees one prompt).

**Fix:** Extract common sections into a shared preamble that `render_prompt()` prepends. Or address during Python rewrite when prompts become programmatic.

---

### PROMPT-10: GEO full-mode iteration types are dead weight during evolution

**Severity:** LOW-MEDIUM
**File:** `programs/geo-session.md` lines 55-90

**Problem:** The eval suite sets `max_iter: 6` for all GEO fixtures. The GEO prompt's EFFICIENCY MODE (lines 28-53) triggers when `MAX_ITER ≤ 6`. So EFFICIENCY MODE is **always** the active mode during evolution.

The full-mode "Iteration Types" section (lines 55-66), "Decision Flow" (lines 67-77), and the separate DISCOVER/COMPETITIVE/SEO_BASELINE/OPTIMIZE/REPORT descriptions describe a workflow that evolution never uses. That's ~35 lines (~400 tokens) of instructions for a mode that won't activate.

**Impact:** The agent reads EFFICIENCY MODE first (it comes before full mode in the prompt), so it likely follows the correct path. But the full-mode content still occupies context window and could confuse the agent about which mode it's in.

**Fix:** Either remove full-mode content when rendering for evolution (phase-stripping from PROMPT-3), or move full-mode to a separate file and only include it when MAX_ITER > 6.

---

### PROMPT-11: Stale tools in competitive prompt

**Severity:** MEDIUM — causes agent confusion and wasted turns
**File:** `programs/competitive-session.md` lines 318-321

**Problem:** Two tools listed in the competitive Tools section are irrelevant:

1. **`freddy query-monitor <monitor_id>`** (line 319): This is a monitoring command. The competitive agent has no `monitor_id` — it works with competitor domains. The agent might waste turns trying to use a monitoring tool that requires an ID it doesn't have.

2. **`freddy save <client> <key> <data>`** (line 321): Listed but never referenced in any competitive protocol. The GATHER protocol writes files directly to `competitors/{name}.json`. The ANALYZE protocol writes to `analyses/{name}.md`. No protocol says to use `freddy save`. Dead weight.

**Impact:** `freddy query-monitor` is the more dangerous one — an agent could try to call it without a valid monitor_id and waste a turn parsing the error. `freddy save` is harmless dead weight.

**Fix:** Remove both entries from the competitive Tools section.

---

### PROMPT-12: GEO Content Quality rules overlap

**Severity:** LOW
**File:** `programs/geo-session.md` lines 127-156 (CQ requirements) + lines 349-366 (Quality Rules)

**Problem:** The GEO prompt has two quality instruction sets that partially overlap:

**Content Quality Requirements (CQ-1→CQ-DATA, 30 lines):** Specific, numbered, with per-block enforcement.
**Quality Rules (AutoGEO, lines 349-366):** 15 generic "empirically validated rules."

Overlapping rules:
| CQ Rule | AutoGEO Rule | Content |
|---------|-------------|---------|
| CQ-1 (answer-first intro) | Rule #8 (answer-first introductions) | Same |
| CQ-2 (FAQ 5-7 self-contained) | Rule #6 (FAQ question-answer format) | Same |
| CQ-3 (HOWTO block) | Rule #10 (numbered/bulleted lists) | Subset |
| CQ-4 (comparison table) | Rule #9 (comparison tables) | Same |
| CQ-DATA (no simulated data) | Rule #2 (statistics and quantitative evidence) | Related |

The AutoGEO rules are generic content best practices (clear headings, statistics, expert quotes, schema markup). Several are already covered by CQ requirements or by the Block Formats section.

**Impact:** ~450 tokens of partially redundant instructions. The AutoGEO rules may dilute the specificity of the CQ requirements.

**Fix:** Merge AutoGEO rules that aren't covered by CQ into the CQ series. Remove duplicates.

---

### PROMPT-13: Competitive Constitution duplication

**Severity:** LOW
**File:** `programs/competitive-session.md` lines 7-51 (Constitution) + lines 354-363 (SYNTHESIZE CRITICAL REMINDERS)

**Problem:** The competitive prompt has a 45-line CONSTITUTION section AND a 10-line SYNTHESIZE CRITICAL REMINDERS section that repeats 5 Constitution points verbatim:

| CRITICAL REMINDER | Constitution source |
|-------------------|-------------------|
| "SOV = Share of Observed [Platform] Ad Volume" | Constitution rule #2 |
| "Every number needs a source" | Constitution rule #3 |
| "Confidence tags required" | Evidence Standards section |
| "Recommendations need 'could be wrong if...'" | Evidence Standards section |
| "Format vacuums need counterfactuals" | Not in Constitution — unique to SYNTHESIZE |

4 of 5 reminders are verbatim repeats. Only #5 (format vacuum counterfactuals) is new.

**Impact:** ~250 tokens of redundancy. The reminders say "Re-read before writing each section" — this is a workaround for the fact that the Constitution is 300+ lines earlier in the prompt.

**Fix:** Remove CRITICAL REMINDERS except #5. If Constitution proximity is the concern, move Constitution closer to SYNTHESIZE or add a one-line reference.

---

### PROMPT-14: Storyboard JSON example bloat

**Severity:** LOW
**File:** `programs/storyboard-session.md` lines 304-347

**Problem:** A 44-line example JSON story plan is embedded in the PLAN_STORY protocol to document the expected output schema. The example includes creative content (story about "Kael the Soul-debt Collector") that serves as both schema documentation and creative inspiration.

```json
{
  "index": 0,
  "title": "The Last Debt Collector of the Third Cycle",
  "logline": "A gaunt bureaucrat who collects soul-debts discovers his own name in the ledger",
  "protagonist": { "name": "Kael", "role": "Soul-debt collector", ... },
  "voice_script": [ ... 4 beats with delivery directions ... ],
  "audio_design": { "music_genre": "...", "music_timing": {...}, ... },
  ...
}
```

**Impact:** ~550 tokens. The schema has ~30 fields. A compact schema definition or table would convey the same structure in ~15 lines.

**Counterargument:** The example doubles as creative inspiration and tone-setting. Agents may produce better first-attempt plans when they have a concrete reference. The cost-benefit depends on how often agents need rework on schema compliance vs creative quality.

**Fix:** Replace with a compact schema definition + a brief note like "See v001 baseline stories for creative reference." Or keep the example but collapse the content (remove full voice_script, audio_design detail).

---

### PROMPT-15: Competitive Escape Hatch unreachable during evolution

**Severity:** LOW
**File:** `programs/competitive-session.md` line 366

**Problem:**
> "After 7 iterations total (any combination of GATHER/ANALYZE), if >= 2 analyzed competitors exist, you MUST proceed to SYNTHESIZE. This is a hard rule."

With `max_iter: 6` in the eval suite, the agent can have at most 6 iterations. The escape hatch at iteration 7 never triggers. Typical flow: 1 GATHER + 3 ANALYZE + 1 SYNTHESIZE + 1 VERIFY = 6 iterations.

**Impact:** 4 lines of dead code. Minimal token waste but could confuse the agent about its actual iteration budget ("I have 7 iterations before I MUST synthesize, but I only get 6 total").

**Fix:** Lower to 5 or remove. Or make it dynamic: "After using >80% of MAX_ITER on GATHER/ANALYZE..."

---

### PROMPT-16: Storyboard uses raw curl instead of freddy CLI

**Severity:** LOW — design gap, not a bug
**File:** `programs/storyboard-session.md` — throughout

**Problem:** The storyboard prompt uses raw `curl` to `${FREDDY_API_URL}/v1/...` endpoints while all other lanes use `freddy` CLI commands. This means:
- 10+ lines of API access boilerplate (env vars, auth headers, JSON parsing via `python3 -c`)
- Error handling is hand-rolled in bash (check HTTP status, parse error JSON, retry loops with backoff)
- No benefit from CLI-side validation, retry logic, rate limiting, or error messages

The other 3 lanes get freddy CLI error handling, argument validation, and output formatting for free.

**Impact:** The inline bash templates (PROMPT-4) are a direct consequence of this design choice. If storyboard used freddy CLI commands, the 126 lines of curl templates would shrink to ~20 lines of CLI calls.

**Fix:** Long-term: add `freddy storyboard analyze`, `freddy storyboard create`, `freddy storyboard verify` CLI commands. Short-term: this is low priority — the curl approach works, just verbose.

---

### PROMPT-17: Monitoring low-volume shortcut ordering complexity

**Severity:** LOW
**File:** `programs/monitoring-session.md` lines 68-83

**Problem:** The SELECT_MENTIONS protocol has a complex ordered sub-step sequence for the low-volume path (`< ~30 mentions`):

> Step 5: MANDATORY — append to results.jsonl BEFORE terminating (both normal and low-volume paths)
> Step 6 (if low-volume): follow these sub-steps IN ORDER (Step 5 MUST already have happened — do not re-order):
>   - a. Write brief status digest.md
>   - b. MANDATORY — Run freddy digest persist
>   - c. Set Status: COMPLETE only after steps a-b succeed

The prompt spends 16 lines emphasizing ordering constraints for an edge case. The bolded warnings ("MANDATORY", "do NOT re-order", "Calling freddy digest persist --help is NOT a substitute") suggest past failures where agents misordered steps.

**Impact:** ~200 tokens on an edge case. The verbose ordering instructions may be necessary given past agent behavior, but they could be simplified.

**Fix:** Simplify to a numbered list without bolded warnings. Or extract to a "Low-Volume Shortcut" subsection that's clearly separate from the main flow.

---

### PROMPT-18: Monitoring fresh_max_turns=15 is very tight

**Severity:** LOW-MEDIUM — contributes to phase detection deadlock (ISSUE-4)
**File:** `workflows/monitoring.py` line 101: `fresh_max_turns=15`

**Problem:** The monitoring workflow config sets `fresh_max_turns=15` while all other domains use the default `FRESH_MAX_TURNS=100`. This means the monitoring agent gets only 15 conversation turns per phase invocation.

For phases like SYNTHESIZE (read files, generate narrative, run evaluator, process feedback, rework, persist state), 15 turns is very tight:
- Read pattern files: 1-2 turns
- Generate synthesis: 1 turn
- Run evaluate_session.py: 1 turn (subprocess)
- Read evaluator output: 1 turn
- Rework if needed: 2-3 turns
- Write output files: 1-2 turns
- Update session.md + results.jsonl: 1-2 turns
Total: 8-12 turns for a clean run, 13-15 for rework

**Evidence:** v005 monitoring logs showed "Error: Reached max turns (15)" in iterations 2-4 — the agent hit its turn limit trying to complete CLUSTER_STORIES.

**Impact:** Phases that require rework almost certainly fail. Even phases without rework are tight. The 15-turn limit was likely set to keep monitoring fast (it has the simplest phases) but it doesn't account for evaluator integration.

**Fix:** Increase to 30-50. The default 100 is probably excessive for monitoring but 15 is insufficient for phases with evaluator integration.

---

## Triage — Pressure-Tested

Each issue re-evaluated for: (1) is it genuine, (2) concrete fix plan, (3) risk to quality.

### FIX NOW — High confidence, concrete plan, low risk

| ID | Issue | Fix plan | Risk assessment |
|----|-------|----------|----------------|
| **PROMPT-2** | Fresh override buried at end | Move `config.py:168-179` injection to BEFORE program text (3-line change) | None — strictly better ordering |
| **PROMPT-7** | Findings file unbounded growth | Add `text[:4000]` truncation after reading findings file in `config.py:147` | Negligible — files are currently 280 bytes; truncation only matters after 10+ generations |
| **PROMPT-11** | Stale tools in competitive | Delete `freddy query-monitor` and `freddy save` lines from competitive Tools section | None — these tools are irrelevant to competitive workflow |
| **PROMPT-15** | Escape Hatch unreachable | Change "7 iterations" to "5 iterations" on `competitive-session.md:366` | None — aligns with actual max_iter=6 budget |
| **PROMPT-18** | Monitoring fresh_max_turns=15 | Change `fresh_max_turns=15` to `fresh_max_turns=40` in `workflows/monitoring.py:101` | None — 15 caused documented failures; 40 gives room for evaluator integration without being wasteful |

### FIX NOW — Genuine but needs careful execution

| ID | Issue | Fix plan | Risk to watch for |
|----|-------|----------|-------------------|
| **PROMPT-1** | Source-Quoting references removed mechanism | Rewrite section in all 4 prompts: keep the principle ("ground claims in specific source data, cite file paths and concrete values") but remove the false mechanism ("verbatim grounding matcher", "fabricated entities = score 0"). Keep Good/Bad examples but reframe around quality, not mechanical scoring. | **Risk:** weakening too much → agents hallucinate numbers. Must preserve the data-grounding behavior while removing the fiction. |
| **PROMPT-5** | Prompt-evaluator criteria gaps | Add 1-2 lines per prompt for verified gaps only: competitive needs "organize brief around a single thesis" (CI-1 gap is real after re-checking — "open with most actionable finding" ≠ "thesis organizing entire document"), GEO needs "include where competitors genuinely win" (GEO-3), storyboard needs "the turn should recontextualize the beginning" (SB-4) and "plans must be genuinely different bets" (SB-8). **Drop CI-7, GEO-7, MON-3** — already covered on re-inspection. | **Risk:** "teaching to the test" → formulaic output. Mitigate by framing as quality principles, not checklist items. |
| **PROMPT-8** | Fresh/multiturn redundancy | Replace per-phase "In fresh mode stop after this phase. In multiturn mode continue..." with just "Persist state." (The fresh override at top handles mode branching.) Keep Operational Reality and Rules mentions as-is. | **Risk:** removing local reminders → agent starts next phase before harness kills it, wasting turns. Mitigated by PROMPT-2 (override moved to top). |
| **PROMPT-4** | Inline bash templates | Keep ONE example curl per endpoint pattern (showing URL, auth, body shape). Remove for-loop scaffolding, batch orchestration, retry loops. Agent constructs its own iteration logic. Saves ~800 tokens (conservative, not the full 1,500). | **Risk:** agent constructs slightly wrong curl commands → phase fails. Mitigate by keeping the critical details (endpoint paths, required headers, body field names) and only removing bash scaffolding. |
| **PROMPT-13** | Constitution duplication | Replace 10-line SYNTHESIZE CRITICAL REMINDERS with 2 lines: "Re-read the CONSTITUTION above before writing each section. Additionally: format vacuums need counterfactuals — explain why competitors might NOT use a format." Saves ~200 tokens, preserves reminder function. | **Risk:** Constitution is 300+ lines earlier — reminder removal means agent relies on memory. Mitigated by the 2-line reference that explicitly says "re-read." |
| **PROMPT-10** | GEO full-mode dead weight | Don't delete — add annotation: "**Note:** When MAX_ITER ≤ 6 (evaluation mode), EFFICIENCY MODE above applies. The following iteration types apply only to extended sessions with MAX_ITER > 6." (1 line added, nothing removed.) | **Risk:** None — preserves both modes, adds clarity. Saves 0 tokens but removes confusion. |

### WITHDRAWN — Not genuine or risk too high

| ID | Issue | Why withdrawn |
|----|-------|--------------|
| **PROMPT-6** | PLAN_STORY overload → reduce to 3 plans | **SB-8 evaluator criterion says "The five plans are genuinely different bets."** Reducing to 3 would conflict with the evaluator and lower scores. v004 Gossip.Goblin completed PLAN_STORY with 5 plans successfully — the overload concern was theoretical, not demonstrated. |
| **PROMPT-12** | GEO quality rules overlap → merge | The "15 empirically validated rules" framing may contribute to quality as an authority signal. Several unique rules (#3 authoritative citations, #12 E-E-A-T, #11 freshness signals) ARE useful and not in CQ. Merging saves ~100 tokens of true duplicates but risks losing the framing. **Not worth the risk for ~100 tokens.** |
| **PROMPT-14** | JSON example bloat → compact | The 44-line Kael story example sets creative quality bar and tone. v004 Gossip.Goblin's story plans were directly influenced by this reference. **550 tokens is cheap for creative calibration.** Compacting could produce blander first attempts → more rework → net negative. |
| **PROMPT-17** | Low-volume shortcut → simplify | The verbose ordering instructions (bold "MANDATORY", "do NOT re-order") exist because agents **repeatedly** misordered these steps in past runs. The complexity is earned through iterative debugging. **200 tokens is cheap insurance against ordering bugs.** |

### DEFERRED — Genuine but requires infrastructure changes

| ID | Issue | Why deferred | What it needs |
|----|-------|-------------|---------------|
| **PROMPT-3** | Phase bloat (50-70% irrelevant) | Requires changes to the `render_prompt()` pipeline: session.md phase detection, section boundary parsing, downstream-phase summary generation. Not a prompt-only fix. | Modify `config.py` to read session state, identify next phase, strip non-relevant phase sections. Medium effort. |
| **PROMPT-9** | Cross-prompt boilerplate | Only affects maintenance (editing 4 files vs 1). No runtime quality impact — each agent only sees one prompt. | Extract shared sections into a common file, prepend in render_prompt. |
| **PROMPT-16** | Storyboard no freddy CLI | Building `freddy storyboard analyze/create/verify` commands is backend CLI work, not a prompt fix. | New CLI command implementations. |

## Final Fix Plan

### Batch 1 — Zero-risk trivials (5 fixes)

```
PROMPT-2:  config.py — move fresh override injection before program text
PROMPT-7:  config.py — add findings file truncation
PROMPT-11: competitive-session.md — delete 2 stale tool lines
PROMPT-15: competitive-session.md — change escape hatch 7→5
PROMPT-18: workflows/monitoring.py — change fresh_max_turns 15→40
```

### Batch 2 — Careful rewrites (6 fixes)

```
PROMPT-1:  All 4 prompts — rewrite Source-Quoting (keep principle, remove false mechanism)
PROMPT-5:  3 prompts — add evaluator-aligned quality hints (CI-1, GEO-3, SB-4, SB-8)
PROMPT-8:  All 4 prompts — replace per-phase fresh/multiturn text with "Persist state."
PROMPT-4:  storyboard-session.md — trim bash loops to single-example-per-endpoint
PROMPT-13: competitive-session.md — replace CRITICAL REMINDERS with 2-line reference
PROMPT-10: geo-session.md — add 1-line annotation to full-mode section
```

### Withdrawn (4 issues) — risk outweighs benefit

```
PROMPT-6:  PLAN_STORY count — conflicts with SB-8 evaluator criterion
PROMPT-12: Quality rules overlap — "15 rules" framing may be load-bearing
PROMPT-14: JSON example — creative calibration worth the 550 tokens
PROMPT-17: Low-volume shortcut — verbose ordering is earned complexity
```

### Deferred (3 issues) — needs infrastructure changes

```
PROMPT-3:  Phase-stripping — needs render_prompt pipeline changes
PROMPT-9:  Shared preamble — maintenance-only, no runtime impact
PROMPT-16: Storyboard CLI — backend work
```
