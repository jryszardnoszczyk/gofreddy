---
date: 2026-05-18
type: cross-check audit (v1 vs live code session_eval_*.py)
status: AUDIT COMPLETE
scope: 7 lanes (CI / GEO / MON / SB / MA / X / LI); SITE skipped (no live code)
baseline: fc99d64 for non-CI lanes; ce386b8 for CI
---

# Judge v1 vs Live Code Cross-Check Audit

## Method

For each of 7 lanes, inventoried (a) the live `CRITERIA: dict[str, str]` prose in `autoresearch/archive/v006/workflows/session_eval_*.py`, (b) the live structural-gate wrapper prose (banned phrases, doc facts, headers), and (c) the v1 spec's per-criterion score-1 / score-0 anchors. Mapped live IDs to v1 IDs (1:1 where preserved; merged or split where research-driven restructure occurred). Flagged load-bearing prose under four categories: PRESERVED (survived into v1), LOST (didn't appear in v1 at all), DRIFTED (same idea expressed differently — flag for JR to confirm), ADDED (new in v1, mostly expected per design guide §5 — flagged only when it feels like over-engineering relative to live code's tight phrasing).

Scope discipline: only prose JR iterated to land — concrete examples, behavioral imperatives, do-not-score nuance, banned-phrase lists, contract wrapper-text. Not flagged: increased criterion count (research-driven), per-vertical anchors (research-driven addition), longer word count (design-guide §5 amendment permits >150w when load-bearing).

SITE_ENGINE has no live code rubric (U15b unshipped, intentional). No cross-check possible. Section included for completeness.

---

## Per-lane findings

### CI (vs ce386b8) — `session_eval_competitive.py`

**Live code criteria inventory (8 criteria, 33–77w each):**
- **CI-1** "thesis, not just findings. A single strategic argument organizes the entire document. Every section serves that argument. The reader finishes knowing one thing clearly, not twelve things vaguely."
- **CI-2** "Every claim traces to something observed, and confidence is explicit. When data is incomplete or contradictory, the brief says so and adjusts its conclusions proportionally. No claim outruns its evidence."
- **CI-3** "Each competitor is understood by their trajectory — what they're building toward, not just where they are. The brief articulates apparent strategy, rate of change, and what each competitor is abandoning."
- **CI-4** "Recommendations are specific, time-bound, and sized to the client's actual capacity to act. \"Deploy llms.txt by Mar 26\" is good. \"Deploy llms.txt by Mar 26, your dev can do this in a half-day\" is better. Recommendations the client can't execute are decoration."
- **CI-5** "asymmetric opportunities — gaps in the landscape that match the client's strengths. Not just what no one is doing, but what no one is doing that this client is uniquely positioned to own."
- **CI-6** "Findings contradict each other or the client's assumptions, and the brief says so. Uncomfortable truths survive editing. The brief is not optimized to make the client feel good about their current approach."
- **CI-7** "hard calls about what matters most. Not everything is Priority 1. The reader knows which 2-3 actions drive disproportionate impact and which findings are interesting but not urgent."
- **CI-8** "When data sources failed, the brief recalibrates rather than speculates. It names what is missing, what analysis became impossible, and how the remaining data changes what can be concluded. It does not silently omit gap-affected sections or present inferred data with unearned confidence. The gap itself is treated as an intelligence finding."

**Live code wrapper / structural_gate carried prose:** `CI_BANNED_PHRASES` (12 phrases — "leverage social media," "stay ahead," "consider exploring," "it's clear that," "no doubt," "it goes without saying," "needless to say," "at the end of the day," "game-changer," "best-in-class," "synergy," "low-hanging fruit"); SOV-with-percentage-in-same-sentence check (negation-filtered, "Run #2 bug" reference); 2000-word ceiling; 3+ headings; 2+ citations.

**v1 spec criteria inventory (6 criteria):**
- **CI-1** Forces a concrete action commitment (posture/budget/roadmap/outreach/hiring/intel-ask + named target + decision-shape-appropriate gate)
- **CI-2** Trajectory over snapshot (2+ independent signals required)
- **CI-3** Structural mechanism of advantage ("can't or won't replicate" test)
- **CI-4** Uncomfortable truth surfaced (pushes against company's prior with evidence)
- **CI-5** Trade-off in the recommendation (CFO-recognizable cost named)
- **CI-6** Evidence chain survives tracing (top-3 claims + named signals + verifiable sources + alternative interpretations + AI-confabulation defense)

**Mapping table (live → v1):**

| Live | v1 | Notes |
|---|---|---|
| CI-1 (thesis) | absorbed across CI-1 + (implicit) | "One thing clearly, not twelve vaguely" survives as Reader spec discipline |
| CI-2 (evidence proportionality) | CI-6 | Generalized into evidence-chain survival |
| CI-3 (trajectory) | CI-2 | Tightened with 2+ independent signals + 6–18 month projection |
| CI-4 (specific time-bound recs) | CI-1 + CI-5 | Action commitment + trade-off |
| CI-5 (asymmetric opps) | LOST | No direct v1 equivalent |
| CI-6 (uncomfortable truth) | CI-4 | Sharpened to "push against company's prior" |
| CI-7 (hard prioritization) | absorbed in CI-1 ("single most consequential") |  |
| CI-8 (gap honesty) | CI-6 | Reframed into evidence chain / 0.5=unknown discipline |

**Findings:**

- **PRESERVED:** "Trajectory — what they're building toward, not just where they are" survives as CI-2 outcome question; "Uncomfortable truths survive editing" survives in CI-4 framing as "at least one person visibly uncomfortable"; "claim outruns its evidence" pattern survives in CI-6.

- **LOST (load-bearing — flag for JR):**
  1. **CI-4's concrete example pair** — `"Deploy llms.txt by Mar 26"` is good; `"... your dev can do this in a half-day"` is better. This is a JR-iterated capacity-to-act anchor (recommendation must be sized to *the client's actual* capacity, not abstract action). v1 CI-1's examples (Pinsent 1.4M / Anthropic MCP / DermaCenter $94K) are decision-class-shape examples — they don't carry the "capacity-to-act / sized for this client" nuance. Restore as 4th example or as a do-not-score line.
  2. **CI-5 ASYMMETRIC OPPORTUNITY criterion entirely.** "Not just what no one is doing, but what no one is doing that this client is uniquely positioned to own" is a JR-iterated framing — the gap × client-fit intersection, not just gap. v1 has no criterion for this. The CI-3 mechanism criterion catches "structural durability" but not "asymmetric opportunity sized for THIS client." Consider whether this absorbs into CI-1's target-naming, or whether it deserves restoration.
  3. **CI-7's "Not everything is Priority 1"** prioritization discipline — the "2–3 actions drive disproportionate impact" framing is gone. v1 CI-1 forces ONE single most-consequential call but doesn't require explicit prioritization across multiple findings. Live had two parallel concepts: "name the one thing" AND "everything is not Priority 1." v1 conflates.
  4. **CI-8 gap-honesty's "gap itself treated as an intelligence finding"** — this specific reframe is gone from v1. CI-6 score-0 names entity confabulation but doesn't carry the "gap → finding" inversion that JR iterated. Worth restoring in CI-6 score-1 or wrapper prose.
  5. **`CI_BANNED_PHRASES` list** — v1 §8 mentions extending the banned-phrase list with "AI-slop tells (em-dash density, 'let me explain why,' 'moreover,' 'furthermore')" but does NOT preserve the original 12-phrase list. JR's "leverage social media / stay ahead / consider exploring / it's clear that / synergy / low-hanging fruit / game-changer / best-in-class" is the consulting-slop blocklist iterated specifically for CI. The v1's "AI-slop" replacement is different. Both probably wanted.
  6. **SOV-percentage-in-same-sentence-negation-filtered check** — v1 doesn't reference this. The check fires on negation phrasing ("would be misleading"); JR's comment in code says "(Prevents passing on 'A 0% SOV label would be misleading' (run #2 bug))." This is empirical, iterated-from-a-real-failure code. v1 §8 enumerates new structural_gate checks (Klue 5-section / CB Insights triple / word-count band) but does NOT preserve the SOV check. Restore explicitly.

- **DRIFTED:**
  - CI-3 live ("apparent strategy, rate of change, and what each competitor is abandoning") → v1 CI-2 ("trajectory + 2+ signals"). v1 drops "what each competitor is abandoning" — that specific phrasing was a JR-iterated dimension. Confirm intentional.
  - Live CI-6 "not optimized to make the client feel good" → v1 CI-4 "at least one person visibly uncomfortable." Drift from internal posture (writer discipline) to external test (reader reaction). Different test surface; confirm intentional.

- **ADDED:** Decision-shape-aware routing (legal / AI-lab / healthcare); §1.5 LOCKED hybrid form factor; CI-6 evidence chain with confabulation defense; 3 vertical examples per criterion. All design-guide-driven. No over-engineering flags.

**Verdict: NEEDS-RESTORATION.** Specific items to address:
- Restore CI-4-equivalent capacity-to-act example pair (one llms.txt-style "good vs better" pair anywhere in v1 CI-1).
- Decide on CI-5 asymmetric-opportunity restoration (likely fits as a CI-1 extension or new sub-anchor).
- Restore CI-7's explicit "not everything is Priority 1" multi-finding prioritization discipline.
- Restore CI-8's "gap itself IS an intelligence finding" reframe in CI-6 score-1 prose.
- Preserve `CI_BANNED_PHRASES` list (12 phrases) explicitly in v1 §8 structural_gate list — not replace with "AI-slop tells."
- Restore SOV-negation-filter check explicitly in v1 §8.

---

### GEO (vs fc99d64) — `session_eval_geo.py`

**Live code criteria inventory (8 criteria):**
- **GEO-1** "self-contained, quotable answer ... AI retrieval system should be able to extract any single paragraph or FAQ answer and use it as a complete response — no meaning lost, no clicking through required."
- **GEO-2** "facts are specific, verifiable, and current. \"$249/month for 2,000 tracked keywords\" not \"affordable plans for every budget.\" Concrete numbers, named competitors, dated claims. Every data point traces to something the client can verify before publishing."
- **GEO-3** "honestly positions the client within the competitive landscape, including where they lose. First-party content has a natural credibility ceiling with AI engines. The only way through it is earned trust: acknowledge where competitors genuinely win."
- **GEO-4** "Every block fits the page's existing voice, structure, and scope — with placement instructions precise enough for a developer to ship without interpretation. Content reads like it was always there, not bolted on. Scoped to what this one page can realistically achieve."
- **GEO-5** "publishes knowledge only this company can credibly provide — the citability moat. Proprietary methodology, category-specific technical depth, unique feature explanations."
- **GEO-6** "Across all pages in a session, each one tells a different story. No two pages use the same primary differentiator, repeat the same competitive framing, or lean on the same statistics."
- **GEO-7** "directly and completely answers the target queries declared for the page... informational queries get explanations, commercial queries get comparisons, transactional queries get pricing and next steps. A page optimized for \"how much does Ahrefs cost\" that provides company history instead of pricing fails regardless of structural quality."
- **GEO-8** "Technical recommendations fix real problems found on the actual page, not boilerplate. \"21 of 22 images lack alt text\" is actionable. \"Consider adding alt text to images\" is not."

**Live code wrapper / structural_gate prose:** `[FAQ]` / `## FAQ` / `## Frequently Asked` marker required; `[INTRO]` bracket required (NOT `## Intro`); 300-word minimum; `gap_allocation.json` required at session root; `[INTRO]` FIX-prose mentions "40-60 word answer-first opening that names the product and a specific competitor differentiator in the first two sentences."

**v1 spec criteria inventory (6 criteria):**
- **GEO-1** Answer-first BLUF compliance (AND: extractable form AND substantive claim)
- **GEO-2** Evidence density (AND: extractable form AND off-domain verifiable substance)
- **GEO-3** Passage self-containment (AND: mechanical standalone AND substantive content)
- **GEO-4** Entity stability and third-party validation (AND: canonical retrieval form AND external substance)
- **GEO-5** Format-intent match and vertical-conditioned freshness
- **GEO-6** Evidence chain survives engine-side re-citation (NEW)

**Mapping table:**

| Live | v1 | Notes |
|---|---|---|
| GEO-1 (self-contained quotable) | GEO-3 | Reframed as passage self-containment |
| GEO-2 (specific verifiable current) | GEO-2 + GEO-4 | Evidence + entity |
| GEO-3 (honest positioning incl. losing) | LOST | No v1 equivalent for "acknowledge competitor wins" |
| GEO-4 (fits page voice + placement) | LOST | No v1 equivalent — v1 GEO-4 is entity stability, not "fit page voice" |
| GEO-5 (citability moat / unique knowledge) | LOST (mostly) | Proprietary-methodology / category-depth framing gone |
| GEO-6 (cross-page differentiation) | LOST | Per-page session diversity criterion gone |
| GEO-7 (intent match) | GEO-5 (partial) | v1 GEO-5 absorbs format-intent + freshness; loses the Ahrefs pricing example |
| GEO-8 (actionable technical recs) | LOST | "21 of 22 images lack alt text" specificity criterion gone |

**Findings:**

- **PRESERVED:** GEO-1 score-1 anchor "engine could emit those 75 words verbatim AND a sophisticated human reader would not classify as generic AI content" carries forward the "quotable answer ... no meaning lost" intent. Klinika Melitus / Dr. Maria Noszczyk anchor is preserved.

- **LOST (load-bearing — flag for JR):**
  1. **GEO-2's concrete example pair:** `"$249/month for 2,000 tracked keywords"` vs `"affordable plans for every budget."` This is a JR-iterated specific-vs-marketing-vague anchor that explicitly teaches the workflow what "specific" means. v1 GEO-2 examples are all vertical-anchored (Section 230 / AAD Botox guidelines / Linear G2 reviews) — they don't carry the "$249 vs affordable" tightness. Restore.
  2. **GEO-3 "acknowledge where competitors genuinely win" criterion entirely.** "First-party content has a natural credibility ceiling with AI engines. The only way through it is earned trust: acknowledge where competitors genuinely win." This is a JR-iterated insight about AI-engine trust mechanics — competitive humility as citability defense. v1 has no criterion for this. v1 GEO-3 is now passage self-containment. Restore as a 7th criterion or fold into GEO-2's evidence requirement.
  3. **GEO-4 "Every block fits the page's existing voice, structure, and scope — with placement instructions precise enough for a developer to ship without interpretation. Content reads like it was always there, not bolted on."** This is the page-fit / shippability criterion — about INTEGRATION with existing surface, not entity-stability. v1 GEO-4 is now entity stability (`sameAs` to Wikidata). The original GEO-4 is gone. "Reads like it was always there, not bolted on" is the JR-iterated test for surgical-content-injection. Restore.
  4. **GEO-5 "citability moat" / "publishes knowledge only this company can credibly provide" / "Proprietary methodology, category-specific technical depth, unique feature explanations."** This is the moat criterion — proprietary knowledge as durable AI-engine citation foundation. v1 has no equivalent. v1 GEO-5 is now format-intent + freshness. The moat framing is lost. Restore.
  5. **GEO-6 cross-page session diversity:** "Across all pages in a session, each one tells a different story. No two pages use the same primary differentiator, repeat the same competitive framing, or lean on the same statistics." This is JR-iterated against page-cohort cannibalization — the cross-item check is preserved at workflow level (`CrossItemCriterion(glob="optimized/*.md")`) but the criterion prose is gone from v1. v1 GEO-6 is now evidence-chain re-citation. Restore as a 7th criterion or fold into GEO-5.
  6. **GEO-7's "Ahrefs pricing not company history" example.** `'A page optimized for "how much does Ahrefs cost" that provides company history instead of pricing fails regardless of structural quality.'` This is the JR-iterated intent-mismatch anchor with a specific brand + query type pair. v1 GEO-5 talks about format-intent match in the abstract but does not carry this concrete query-vs-answer-mismatch example. Restore.
  7. **GEO-8's "21 of 22 images lack alt text" specificity** example. `'"21 of 22 images lack alt text" is actionable. "Consider adding alt text to images" is not.'` JR-iterated specificity-of-technical-recommendation anchor. v1 has no GEO-8 / no technical-recommendation criterion. The criterion is gone entirely. If GEO is producing technical-audit recommendations (per `audits/{slug}.full.json` in `load_source_data`), this is a real loss. Restore as a 7th criterion or as a sub-anchor in GEO-5.
  8. **`[INTRO]` bracket-marker prose** in structural_gate FIX-text: "40-60 word answer-first opening that names the product and a specific competitor differentiator in the first two sentences." JR-iterated — the "names the product AND a specific competitor differentiator" pairing is the BLUF discipline. v1 GEO-1 score-1 says "declarative entity definition + category placement + a differentiation claim" — close but not the same. The "names a specific competitor differentiator" is the load-bearing part (forces honest competitive positioning, links to lost GEO-3). Confirm preserved or restore.
  9. **Bracket-form discipline** (`[INTRO]`, `[FAQ]`, `[HOWTO]`, `[SCHEMA]`, `[TECHFIX]`, `[PRUNE]`, `[FILL]`): live code is explicit — `## Intro` / `## Introduction` will FAIL; brackets are required. v1 §1.5 specifies 10 form factors but does NOT enumerate the bracket markers. `scripts/build_geo_report.py` reads these — this is a real downstream contract. v1's structural_gate expansion (§8) replaces with schema.org validity / FAQPage JSON-LD checks. If the bracket-form readers are still consumed by downstream tooling, the bracket gate must persist. Check before shipping.

- **DRIFTED:**
  - Live GEO-2 "concrete numbers, named competitors, dated claims" → v1 GEO-2 "off-domain verifiable substance." Same intent, looser language. Confirm rewording intentional.
  - Live GEO-7's "informational queries get explanations, commercial queries get comparisons, transactional queries get pricing and next steps" specific query-class taxonomy → v1 GEO-5 talks about `geo_format` enum (10 types). Different taxonomy. The live taxonomy is informational/commercial/transactional (intent-class); v1 is form-factor (definition / how-to / comparison / listicle / faq / etc.). Confirm migration is intentional.

- **ADDED:** Per-fixture `geo_format` enum routing (10 form factors); AND-conjunction language at every criterion (dual-audience defense); 8 AI-failure structural_gate checks; 7 per-vertical Goodhart-collapse modes; KG-anchor tiering. Most design-guide and research-driven. No over-engineering flags.

**Verdict: NEEDS-RESTORATION (heavy).** This lane lost the most live-code prose of any. Specific items:
- Restore GEO-2's `"$249/month for 2,000 tracked keywords"` vs `"affordable plans for every budget"` example pair.
- Decide on GEO-3 "acknowledge where competitors win" — likely a missing 7th criterion or fold into GEO-2.
- Restore GEO-4's "fits page voice / reads like it was always there" — surgical-content-injection criterion.
- Restore GEO-5's "citability moat / proprietary methodology" — durable moat criterion.
- Decide on GEO-6 cross-page diversity — fold into v1 GEO-5 or restore as criterion.
- Restore GEO-7's Ahrefs pricing example into v1 GEO-5 score-1 prose.
- Restore GEO-8's technical-recommendation specificity ("21 of 22 images" example) — likely a 7th or 8th criterion.
- Confirm bracket-marker contract (`[INTRO]`, `[FAQ]`, etc.) survives in structural_gate before shipping.

JR has 8 live-code criteria distilled across multiple iterations; v1 reduced to 6 with substantial re-architecture (AND-conjunction, per-fixture form-factor routing, AI-failure surfaces). The 6 v1 criteria capture different things than the 8 live criteria; this is more re-architecture than restructure.

---

### MON (vs fc99d64) — `session_eval_monitoring.py`

**Live code criteria inventory (8 criteria):**
- **MON-1** "tells you what changed this period... backward-looking delta... \"Sentiment shifted from 41% to 62% positive\" not \"sentiment is 62% positive.\""
- **MON-2** severity classification + confidence + limitations + "Coverage gaps directly modify severity assessments: a crisis call on single-source data is flagged as provisional. When classification is a judgment call, the digest names the alternative reading."
- **MON-3** "names the one thing that matters most this week... If nothing extraordinary happened, it says that plainly."
- **MON-4** "Action items are specific, prioritized, and time-bound. Each one names who should act, by when, and what happens if they don't."
- **MON-5** "connects dots the reader wouldn't connect themselves — and projects where those connections lead. ... compound narratives (two signals together reveal something neither shows alone) AND names upcoming catalysts... \"this could escalate\""
- **MON-6** "Every number answers \"so what?\" and every absence is examined. Quantifies with interpretation, not decoration. Flags where expected signal is missing — the campaign that generated no coverage, the competitor that went quiet — because silence is often the most important data point."
- **MON-7** "connects to the arc of prior digests... last week's watchlist items escalated, stayed flat, or resolved. Follows up on previously recommended actions — was it taken, was it effective, or was it silently dropped?"
- **MON-8** "Word count is proportional to importance, not to data volume. ... Editorial restraint is visible — some available data was deliberately left out."

**Live code wrapper / structural_gate prose:** Per-story criteria `("MON-1", "MON-2", "MON-4", "MON-6")`; cross-item `MON-7` over `../*/digest.md` (prior digests); low-volume threshold mentions < 30 → bypass cluster/synthesize/recommend; "Session status is COMPLETE" required; "Only N synthesized vs M stories (<50%)" failure; ">3 rework attempts" failure; tier-distribution sanity (≥1 noise per 5).

**v1 spec criteria inventory (6 criteria):**
- **MON-1** Baseline-relative framing
- **MON-2** Severity classification with defensible reasoning (orthogonal axes)
- **MON-3** Highest-stakes lede in position one
- **MON-4** Action items with owner, deadline, consequence
- **MON-5** Absence-as-signal (NEW; split from live MON-6)
- **MON-6** Compound-claim evidence chain survives tracing (NEW; absorbs live MON-5 + adds AI-failure surface)

**Mapping table:**

| Live | v1 | Notes |
|---|---|---|
| MON-1 (delta from baseline) | MON-1 | Preserved with sharpening + research grounding |
| MON-2 (severity + confidence + alt reading) | MON-2 | Preserved with orthogonal-axis-pair addition |
| MON-3 (one thing that matters) | MON-3 | Preserved |
| MON-4 (specific, prioritized, time-bound) | MON-4 | Preserved with explicit owner/deadline/consequence |
| MON-5 (compound + projection) | MON-6 (compound) + MON-2 (catalyst projection absorbed) | Split; projection dropped per research |
| MON-6 (numbers + absence-as-signal) | MON-5 (absence) + (so-what loses standalone criterion) | Split |
| MON-7 (arc of prior digests / followup) | LOST as standalone criterion | Folded into MON-6 distinct-time-points requirement |
| MON-8 (editorial restraint / proportional length) | LOST | Routed to structural_gate word-count band |

**Findings:**

- **PRESERVED:** Live MON-1's `"Sentiment shifted from 41% to 62% positive" not "sentiment is 62% positive"` survives as v1 MON-1 score-1 (with research-anchored sharpening). Live MON-2's "Coverage gaps directly modify severity assessments: a crisis call on single-source data is flagged as provisional" survives in v1 MON-2 (with "Provisional pending Friday's confirmed-versus-rumored Above the Law count" example). Live MON-3's "If nothing extraordinary happened, it says that plainly" preserved as v1 MON-3 explicit low-volume branch.

- **LOST (load-bearing — flag for JR):**
  1. **MON-5's "this could escalate" example** as do-not-score anti-pattern. Live MON-5: `'Forward projections are conditional and falsifiable, not vague ("this could escalate")'`. This is JR-iterated do-not-score against vague forward-projection. v1 MON-6 absorbs compound-claim but does not explicitly preserve the "this could escalate" failure example. Forward-projection-aware structural_gate-or-judge check is named in §1 as "(see MON-5)" referring to absence rather than forward projection. The forward-projection axis is silently dropped per v1 revision history; the failure-shape anchor goes with it. Worth a do-not-score line in MON-2 ("decorative forward projections") or MON-6.
  2. **MON-6's "every absence is examined" + "the campaign that generated no coverage, the competitor that went quiet"** specific examples. v1 MON-5 score-1 has DermaCenter / competitor-CFO-absent examples (research-grounded) but loses the JR-iterated "campaign that generated no coverage" / "competitor that went quiet" specifically-shaped anchors. The "silence is often the most important data point" framing is preserved in §3a but not in score-1 example prose. Restore one of these to v1 MON-5.
  3. **MON-7 watchlist-arc criterion entirely.** "connects to the arc of prior digests... last week's watchlist items escalated, stayed flat, or resolved. Follows up on previously recommended actions — was it taken, was it effective, or was it silently dropped?" This is a JR-iterated continuity criterion that ALSO has a workflow infrastructure dependency (live code has `cross_item_criteria={"MON-7": CrossItemCriterion(glob="../*/digest.md", max_items=1, words_per_item=1000)}` — the prior digest is loaded). v1 absorbs into MON-6's "distinct time-points" requirement, but the specific watchlist-tracking framing ("escalated, stayed flat, or resolved" / "was it taken, was it effective, or was it silently dropped") is gone. v1 §8 open-q-1 acknowledges multi-week corpus context as urgent ops-integration — but the criterion-prose for watchlist tracking is not restored. Confirm whether MON-7 is intentionally absorbed or should be a 7th criterion.
  4. **MON-8 editorial restraint** entirely. "Word count is proportional to importance, not to data volume... Editorial restraint is visible — some available data was deliberately left out, making the remaining content sharper. The structure serves the content, not the reverse." v1 routes this to `structural_gate` word-count band (600–1,400) per §1.5 — but the test is different. The structural_gate tests presence of a word count; the live MON-8 tests editorial judgment (what was deliberately left out). These are not equivalent. The "editorial restraint is VISIBLE" outcome question is a real test that the v1 word-count gate doesn't cover. Worth restoring as a 7th criterion or wrapper-prose discipline.

- **DRIFTED:**
  - Live MON-2 "When classification is a judgment call, the digest names the alternative reading" → v1 MON-2 "orthogonal-axis-pair reasoning." Closely related; v1 names the mechanism (orthogonal axes); live names the surface behavior (alternative reading). Both wanted? v1 has lost the "names the alternative reading" surface phrasing.
  - Live MON-5 forward-projection criterion → v1 MON-2 partial absorption. Confirm projection is intentionally dropped per v1 revision history note.

- **ADDED:** Decision_shape routing (standard / event-driven / incident-driven); §1.5 LOCKED hybrid form (FullIntel / PDB / FAA-AD / Cision); MON-5 ABSENCE + MON-6 COMPOUND as TWO documented exceptions to ≤5 ceiling; structural_gate AI-failure plumbing; required-silence vs anomalous-silence distinction (load-bearing — FDA pre-approval / SEC quiet period / NRC classified). The required-silence-is-not-a-missed-signal addition is good research surface (load-bearing). 6 criteria with 2 documented exceptions is a substantial expansion.

**Verdict: MINOR-DRIFT.** Most live-code prose preserved or research-sharpened. Specific items:
- Restore live MON-5's `"this could escalate"` do-not-score anti-pattern somewhere (MON-2 or MON-6).
- Restore live MON-6's `"competitor that went quiet"` / `"campaign that generated no coverage"` specific absence anchors in v1 MON-5.
- Decide MON-7 watchlist-arc fate explicitly — likely should be 7th criterion OR explicit prose carry into MON-6.
- Restore MON-8 editorial-restraint test — judge-side or as v1 §8 structural_gate banned-phrase check on "should continue to monitor" (already noted) but not enough.
- Forward-projection criterion drop is documented; confirm intentional.

---

### SB (vs fc99d64) — `session_eval_storyboard.py`

**Live code criteria inventory (8 criteria):**
- **SB-1** "feels like the creator made it — not like someone studied the creator and generated a plausible imitation. Voice, obsessions, worldview, and the specific way they surprise an audience are all present."
- **SB-2** "hook is irreplaceable — a concrete, specific image or sentence that could not come from any other story. Something you would describe to a friend in one breath. The mechanism may be an impossible concept, raw emotional vulnerability, absurd juxtaposition, or visual impossibility — what matters is specificity and irreplaceability, not which mechanism achieves them."
- **SB-3** "Every emotional transition in the story is earned by a specific beat, not just declared in metadata. ... not asserted as \"the viewer now feels dread\" without a beat that produces dread."
- **SB-4** "turn recontextualizes the beginning. By the end, the opening scene means something different than it appeared to mean. The emotional arc is not just a progression but a reframing."
- **SB-5** "voice script is performable speech with designed silence. A voice actor could perform it cold, and the audio design — including what is deliberately absent, processed, or contrasted — carries as much story as the visuals."
- **SB-6** "Every scene describes something current AI video models can actually produce — not too vague (\"a person in a room\") and not too ambitious (subtle micro-expressions, specific text legibility). Consistency anchors are functional engineering decisions ... rather than decorative restatements of the character description."
- **SB-7** "pacing matches the platform and the creator's actual rhythm — scene count, cut frequency, and duration target are grounded in how the creator's real videos move, not in how a screenplay reads."
- **SB-8** "five plans are genuinely different bets — different premises, different emotional registers, different structural choices — while sharing a creative universe. They are not five variations on the plan the AI found easiest to generate."

**Live code wrapper / structural_gate prose:** "scenes" array length matches "scene_count"; voice_script + duration_target_seconds + scene_count required; cross-item SB-8 over `stories/*.json` max 4; JSON-object root.

**v1 spec criteria inventory (6 criteria):**
- **SB-1** Sounds like the creator made it (per cold-start regime)
- **SB-2** Irreplaceable hook (substitution test)
- **SB-3** Earned emotional arc with real stakes (sharpened; absorbs live SB-4 turn into hook-body alignment)
- **SB-4** Within rendering envelope (model + production-source)
- **SB-5** Creator pacing + portfolio diversity (cold-start reframed)
- **SB-6** Plan survives lived-experience and source-tracing (NEW — script confab defense)

**Mapping table:**

| Live | v1 | Notes |
|---|---|---|
| SB-1 (creator made it / obsessions) | SB-1 | Preserved + cold-start reframed |
| SB-2 (irreplaceable hook) | SB-2 | Preserved with substitution test verbatim |
| SB-3 (earned emotional transition) | SB-3 | Preserved + sharpened with stakes + hook-body alignment |
| SB-4 (turn recontextualizes) | SB-3 (partial) | "Opening means something different by the end" absorbed into SB-3 |
| SB-5 (voice script + designed silence) | LOST as standalone | "performable speech with designed silence" gone |
| SB-6 (within capability envelope) | SB-4 | Preserved with model-name routing to configs |
| SB-7 (pacing matches creator rhythm) | SB-5 (warm regime) | Preserved with cold-start fork |
| SB-8 (5 plans different bets) | SB-5 (warm regime) | Preserved with cold-start fork |

**Findings:**

- **PRESERVED:** Strong preservation overall. SB-2's "could not come from any other story" / substitution test survives intact in v1 SB-2 with "I Spent 50 Hours In Ketchup" example. SB-3's "the viewer now feels dread" as anti-pattern preserved in v1 SB-3 with a worked example. SB-6's "a person in a room" too-vague anchor preserved in v1 SB-4. SB-8's "5 variations on the plan the AI found easiest" preserved in v1 SB-5 warm regime score-0.

- **LOST (load-bearing — flag for JR):**
  1. **Live SB-5 entirely.** "voice script is performable speech with designed silence. A voice actor could perform it cold, and the audio design — including what is deliberately absent, processed, or contrasted — carries as much story as the visuals." This is the JR-iterated audio-design / voice-actor-cold-read criterion. v1 has no equivalent. v1's SB-1 / SB-3 touch voice-script but only as cadence / register / earned-arc tests — neither tests "performable cold" or "designed silence" / "deliberately absent, processed, contrasted" audio direction. This is real, specific JR criteria for the audio half of storyboard work. Restore.
  2. **Live SB-4 "turn recontextualizes"** as standalone test. "By the end, the opening scene means something different than it appeared to mean. The emotional arc is not just a progression but a reframing." v1 SB-3 absorbs hook-body alignment but the specific test is "hook promises X; body delivers X" — different from the live "turn / reframe / bookend" test. The bookend-reframe test is the recontextualization criterion. v1 SB-3 prose includes "opening means something different by the end (turn / reframe / bookend)" in score-1 — actually this is preserved. Confirm. (On re-read: PRESERVED, not LOST. Strike from LOST list, move to PRESERVED.)
  3. **Live SB-6's "subtle micro-expressions, specific text legibility"** as too-ambitious examples. v1 SB-4 score-1 has these (legible long text on signs, sustained multi-character lip-sync, etc.) — PRESERVED with research grounding. Strike.
  4. **Live SB-6's "Consistency anchors are functional engineering decisions ... rather than decorative restatements of the character description"** — PRESERVED in v1 SB-4 ("Consistency anchors are functional engineering decisions naming what must stay identical").

- **DRIFTED:**
  - Live SB-1 "Voice, obsessions, worldview, and the specific way they surprise an audience are all present." → v1 SB-1 cold-start vs warm fork with archetype examples (creator-led / founder-led / brand-author). The "specific way they surprise an audience" phrasing is gone in v1; replaced with "named details / sentence cadence / vocabulary register / opening shape." Different test surface; the JR phrase "surprise an audience" had affective load v1's mechanical voice-marker checklist doesn't. Confirm intentional.
  - Live SB-7 "how the creator's real videos move, not in how a screenplay reads" → v1 SB-5 warm regime "pacing matches creator's native cadence" + Rate-of-Revelation per unit. The "not how a screenplay reads" anti-pattern phrasing is gone. Worth restoring as do-not-score line.

- **ADDED:** Cold-start vs warm regime fork (per pattern-data-density flag); SB-6 source-tracing criterion (script confab defense); per-fixture model name routing to `configs/storyboard/supported_models.yaml`; 7 SB-1 structural_gate voice-fidelity checks; 4 SB-6 structural_gate source-tracing checks; 8 SB-4 structural_gate capability checks. All research-driven. The model-name routing to config is an explicit design-guide-respect choice (anchor stays out of judge prose). No over-engineering flags.

**Verdict: SAFE pending restoration of live SB-5.** Specific items:
- **Restore live SB-5 (audio design / performable cold / designed silence) as a 7th criterion or fold into v1 SB-1 prose.** This is the single biggest loss on SB lane — JR specifically iterated "audio design carries as much story as visuals" and "voice actor could perform it cold." The cold-perform test is testable.
- Restore SB-7's "not in how a screenplay reads" anti-pattern phrasing in v1 SB-5 do-not-score.
- Confirm SB-1 "specific way they surprise an audience" intentionally dropped or restore.

Otherwise the most-faithful v1 to live code; cold-start reframe is a real research-driven improvement not a drift.

---

### MA (vs fc99d64) — `session_eval_marketing_audit.py`

**Live code criteria inventory (8 criteria):**
- **MA-1** "Strategic Narrative Coherence — findings.md is organized around ONE strategic argument per section ... Every finding within a section serves the section's thesis ... Reader walks away with a strategic frame, not N disconnected problems."
- **MA-2** "Evidence Traceability — Every claim cites a lens_id AND ≥1 evidence_url. Numbers are source-attributed (no naked stats). Estimates carry 'estimated' or 'approx' with explicit confidence range. Generalizations from small N are flagged. ParentFinding addresses_rubrics arrays match the lens IDs cited in evidence."
- **MA-3** "Phase-0 Framing Applied — State-of-the-Business opener pulls measurements from phase0_meta.json (the 9 meta-frames). Per-section findings color by relevant Phase-0 frames... Phase-0 measurements that came back null are surfaced as findings (gap-honesty), NOT papered over."
- **MA-4** "Actionable + Capability-Mapped — Each ParentFinding's recommendation is STRATEGIC (≥50 words of substance, names what would solve this in terms the agency engagement delivers) AND maps cleanly to a capability_registry tier (fix_it / build_it / run_it). Recommendations are NOT DIY execution guides; they describe the work the agency would do."
- **MA-5** "Severity Calibration — Severity (0-3) on every SubSignal + ParentFinding is anchored to lens-specific severity_anchors from the rubric YAML. No severity inflation. ParentFinding severity = max of children (rollup rule). Severity distributions across the audit are credible — not a sea of '3's."
- **MA-6** "Polish + Voice Consistency — Prose has the voice quality of a customer-facing $1K-$15K agency artifact. No AI-tell vocabulary. Voice is consistent across sections (one author, not five). Em-dash density is restrained. Headings parallel; no section-level voice drift."
- **MA-7** "Gap Honesty — gap_flagged rubrics from per-agent rubric_coverage maps surface in gap_report.md. Missing-data findings are surfaced in findings.md, NOT papered over with speculation. Phase-0 nulls are findings. Provider-blocked lenses are honest gaps, not invented signals."
- **MA-8** "Engagement-Fit — Findings + proposal align with the capability_registry. Tier-mapping serves a pitch for a $15K+ engagement (not a $1K-only artifact). At audit-render time, the rubric judges whether the deliverable IS pitching a credible agency engagement vs. reading like a one-off audit report."

**Live code wrapper / structural_gate prose:** `MA_BANNED_PHRASES` (12 phrases — "in today's fast-paced world," "in the ever-evolving landscape," "leverage synergies," "drive impact," "unlock value," "best practices," "key takeaways," "deep dive," "moving forward," "going forward," "circle back," "low-hanging fruit"); 9 required sections (findability / narrative / acquisition / experience / competitive / monitoring / geo / state_of_business / martech_compliance); 5+ ParentFinding headers (`### `); 3+ source URLs; 800–8000 word band; 6+ subheadings; `proposal.md` 3 tier headers (`fix_it`, `build_it`, `run_it`).

**v1 spec criteria inventory (5 criteria):**
- **MA-1** Founder can name the binding constraint (with 2+ evidence sources)
- **MA-2** Reader commits to decision-shape-appropriate next action
- **MA-3** Every recommendation traces to a revenue mechanism
- **MA-4** Stage map + detail-vs-decision-class match + refuses wrong-stage best practices
- **MA-5** Surfaces upstream problem when that's the real constraint, sequenced not parallel-tracked

**Mapping table:**

| Live | v1 | Notes |
|---|---|---|
| MA-1 (strategic narrative coherence) | MA-1 (partial) | "Walks away with a strategic frame, not N disconnected problems" → "name binding constraint with 2 evidence sources" |
| MA-2 (lens_id + evidence_url traceability) | MA-1 (2 evidence sources sub-anchor) + MA-3 (revenue mechanism) | Split |
| MA-3 (Phase-0 framing / phase0_meta.json) | LOST | No v1 equivalent for Phase-0 9-meta-frame integration |
| MA-4 (capability_registry tier mapping) | LOST | No v1 fix_it / build_it / run_it mapping |
| MA-5 (severity calibration / rollup rule) | LOST | No v1 severity-anchor criterion |
| MA-6 (polish + voice consistency / agency artifact) | LOST | No v1 voice-quality criterion (only banned-phrase grep) |
| MA-7 (gap honesty) | LOST as standalone | Folded into MA-1 evidence + MA-5 upstream |
| MA-8 (engagement-fit / $15K+ pitching) | LOST | No v1 pitching-credibility criterion |

**Findings:**

- **PRESERVED:** "Reader walks away with a strategic frame, not N disconnected problems" (MA-1) survives as v1 MA-1 outcome question (in the form "name the binding constraint in one sentence"). Live MA-2's "Every claim cites a lens_id AND ≥1 evidence_url" / "Numbers are source-attributed (no naked stats)" survives as v1 §3d structural_gate metric-citation grep and v1 MA-1's 2-evidence-source CoT.

- **LOST (load-bearing — flag for JR):**
  1. **`MA_BANNED_PHRASES` list** (12 phrases) — JR's marketing-audit-specific AI-tell blocklist: "in today's fast-paced world / in the ever-evolving landscape / leverage synergies / drive impact / unlock value / best practices / key takeaways / deep dive / moving forward / going forward / circle back / low-hanging fruit." v1 §8 lists banned phrases ("industry-standard," "typical SaaS," "reportedly," "according to industry sources," em-dash density, "let me explain why," "moreover," "furthermore," "framework-name-without-supporting-analysis tells") — DIFFERENT list. JR's MA list targets "agency-artifact polish" (corporate-jargon-as-AI-tell); v1's list targets framework-citation slop. Both wanted? At minimum the original 12 should not be silently dropped.
  2. **MA-3 Phase-0 framing criterion entirely.** "State-of-the-Business opener pulls measurements from phase0_meta.json (the 9 meta-frames). Per-section findings color by relevant Phase-0 frames where applicable. Phase-0 measurements that came back null are surfaced as findings (gap-honesty), NOT papered over." This is a JR-iterated audit-architecture criterion that connects to a specific data substrate (`phase0_meta.json` is loaded in `load_source_data`). v1 has no equivalent. The Phase-0 / 9-meta-frame integration is workflow infrastructure that the criterion enforces. If the workflow still produces phase0_meta.json, the criterion is needed; if it doesn't (per v1's re-architecture), confirm. Restore or document drop.
  3. **MA-4 capability_registry tier-mapping criterion entirely.** "Each ParentFinding's recommendation ... maps cleanly to a capability_registry tier (fix_it / build_it / run_it). Recommendations are NOT DIY execution guides; they describe the work the agency would do." This is the JR-iterated agency-positioning criterion — the audit isn't a DIY playbook; it's a sales artifact. v1 has no equivalent. v1 MA-2 has Cluster-A/B/C decision-shape routing but does NOT carry the agency-vs-DIY framing or the fix_it/build_it/run_it tier mapping. The `proposal.md` 3-tier-header structural check is still there in live code; v1 doesn't reference it. Restore.
  4. **MA-5 severity-calibration criterion entirely.** "Severity (0-3) on every SubSignal + ParentFinding is anchored to lens-specific severity_anchors from the rubric YAML. No severity inflation. ParentFinding severity = max of children (rollup rule). Severity distributions across the audit are credible — not a sea of '3's." This is the JR-iterated anti-inflation criterion + the rollup-rule (severity = max of children). v1 has no equivalent. v1 MA-5 is upstream-vs-marketing, completely different. Restore — the "not a sea of 3's" anti-inflation test is empirical and load-bearing.
  5. **MA-6 polish-and-voice / "$1K-$15K agency artifact" criterion entirely.** "Prose has the voice quality of a customer-facing $1K-$15K agency artifact. ... Voice is consistent across sections (one author, not five). Em-dash density is restrained. Headings parallel; no section-level voice drift." v1 has no voice-quality criterion. v1 §3d names "polish" as a vague property; banned-phrase grep handles em-dash density via structural_gate. But "voice consistent across sections" / "one author not five" / "headings parallel" / "no section-level voice drift" are specific tests v1 has no criterion for. Restore.
  6. **MA-7 gap honesty as standalone criterion.** "gap_flagged rubrics from per-agent rubric_coverage maps surface in gap_report.md. Missing-data findings are surfaced in findings.md, NOT papered over with speculation. Phase-0 nulls are findings. Provider-blocked lenses are honest gaps, not invented signals." v1 absorbs into MA-1's 2-evidence-source CoT + MA-5's upstream-engaged-on-the-merits. But the specific "gap_flagged → gap_report.md" workflow contract is gone, AND the "provider-blocked lenses are honest gaps, not invented signals" framing (which catches the AI-fills-the-gap-with-fabrication failure) is gone. Restore at minimum the "invented signals" anti-pattern.
  7. **MA-8 engagement-fit / pitching-credibility criterion entirely.** "Tier-mapping serves a pitch for a $15K+ engagement (not a $1K-only artifact). At audit-render time, the rubric judges whether the deliverable IS pitching a credible agency engagement vs. reading like a one-off audit report." This is the JR-iterated audit-as-sales-artifact criterion. v1 has no equivalent. The 3-cluster routing (Personnel / Operational / Strategic) doesn't cover this — Cluster A/B/C is decision-class routing; MA-8 is about the audit's posture as agency-pitch. Different concern. Restore.
  8. **9-section structure requirement.** Live structural_gate enforces 9 deliverable sections (findability / narrative / acquisition / experience / competitive / monitoring / geo / state_of_business / martech_compliance). v1 §1.5 specifies 5 sections (verdict / stage-diagnostic / current-state / upstream-vs-marketing / 30-60-90) for Cluster B canonical. These are DIFFERENT structures. Either the v1 5-section is intentional re-architecture (then the 9-section live structural_gate must be retired) or v1 needs to acknowledge the gap. Confirm intentional.

- **DRIFTED:**
  - MA-1 live "Strategic Narrative Coherence" → v1 MA-1 "Founder can name the binding constraint." Related but different: live tests organizational thesis-discipline (section-by-section narrative coherence); v1 tests reader-extraction of one constraint. Live MA-1 is structural; v1 MA-1 is behavioral. Confirm intentional.
  - MA-2 live "lens_id + evidence_url" mechanical traceability → v1 MA-1's "2+ independent named evidence sources" + v1 §8 metric-citation grep. The mechanical lens_id-to-rubric-mapping (`ParentFinding.addresses_rubrics matches lens IDs cited`) is gone from v1. If the rubric YAML / lens_id substrate persists in workflow, the gate must too.

- **ADDED:** 3-cluster decision-shape routing (Personnel A / Operational B / Strategic C); §1.5 LOCKED form factor for Cluster B with per-cluster routing for A/C; 5 AI-failure surfaces (financial-metric / channel-claim / competitor-data / marketing-misdiagnosis / recommendation hallucination); 7 structural_gate AI-failure checks; stage-applicability denylist; parallel-tracked-vs-sequenced as score-0 condition; upstream-evidence calibration weighting. All design-guide and research-driven. The Cluster A/B/C re-architecture is substantial — and may be the v1's intentional replacement for live MA-3 (Phase-0) + MA-4 (capability_registry) + MA-8 (engagement-fit), but if so, confirm and document.

**Verdict: NEEDS-RESTORATION (heavy).** Per-criterion this is the most-rewritten lane — only 1 of 8 live criteria has a direct v1 mapping. The 5 v1 criteria capture a different concern (decision-class action + revenue mechanism + stage map + upstream surface) than the 8 live criteria (strategic narrative + evidence traceability + Phase-0 framing + capability mapping + severity calibration + voice quality + gap honesty + engagement fit). Specific items:
- Restore `MA_BANNED_PHRASES` 12-phrase list explicitly (or document deliberate replacement).
- Decide on Phase-0 framing criterion (MA-3 live) — is `phase0_meta.json` still being produced? If yes, criterion needed; if no, document drop.
- Decide on capability_registry / fix_it / build_it / run_it tier mapping (MA-4 live) — agency-vs-DIY framing is load-bearing.
- Restore severity-calibration criterion (MA-5 live) — "not a sea of 3's" anti-inflation test.
- Restore voice-quality / agency-artifact criterion (MA-6 live) — voice consistency across sections + restrained em-dash density.
- Restore gap-honesty's "invented signals" anti-pattern (MA-7 live).
- Restore engagement-fit / $15K+ pitching criterion (MA-8 live) — the audit-as-sales-artifact framing.
- Confirm 5-section v1 structure vs 9-section live — and update structural_gate accordingly.

This is the lane where "v1 didn't read live code" shows most starkly: the v1 spec captures research-driven Cluster A/B/C decision-shape routing but loses 7 of 8 JR-iterated criteria. Either substantial restoration or explicit consent to architectural rewrite.

---

### X (vs fc99d64) — `session_eval_x_engine.py`

**Live code criteria inventory (6 criteria):**
- **X-1** "Voice — JR's first-person, opinionated, plain-language register, accessible to a non-engineer founder/marketer. Jargon without inline plain-English context caps this dimension."
- **X-2** "Factual specificity — SOURCE claims trace to source_text; INTERPRETIVE claims framed as JR's view. HARD FLOOR: any first-person specific lived-work claim REQUIRES the named entity to appear in programs/references/voice.md."
- **X-3** "Hook strength — bracket-aware. SHARP earns 5 with one sharp claim+support pair in the first 12 words. BUILD/CASE-STUDY: the first 1-2 sentences must beat the show-more cutoff."
- **X-4** "Slop-freeness — zero AI-tells. Banned phrases per slop_gate.py regex are a deterministic floor; this dimension judges what slips through (parallel structures, formulaic transitions, cadence)."
- **X-5** "Structural richness — bracket-aware. SHARP earns 10 with one sharp claim+support pair; BUILD with prose intro + structural pivot + 3-5 bullets + authority anchor + outcome metric; CASE-STUDY with multi-paragraph narrative + sensory detail + numbers timeline + implication close. Pad-to-length = ≤4."
- **X-6** "Cross-cohort — across all drafts in this session's drafts/, no two use the same primary differentiator, source, or hook archetype. Spread across voice_pillars listed in angle metadata."

**Live code wrapper / structural_gate prose:** Frontmatter required (`draft_id`, `angle_id`, `platform`, `length_bracket`, `char_count`, `voice_pillar`); `[BODY]` / `[META]` blocks required; META keys (`hook`, `authority_anchor`, `specific_number`, `attribution`); length brackets sharp 250–300 / build 500–900 / case_study 1000–1500; `xeng slop-check` runs deterministic; voice substrate at `programs/references/voice.md` loaded as `parents[2]`.

**v1 spec criteria inventory (5 criteria):**
- **X-1** Earns the next tap (hook discipline, 3-axis CoT)
- **X-2** Carries specific knowledge only this author could write
- **X-3** Asserts something falsifiable
- **X-4** Form matches function (single post or 3–12-unit thread)
- **X-5** Survives the screenshot test in the account's voice (gestalt, regime-aware)

**Mapping table:**

| Live | v1 | Notes |
|---|---|---|
| X-1 (voice / JR first-person register) | X-5 | Reframed to "screenshot test" |
| X-2 (factual specificity / voice.md HARD FLOOR) | X-2 (partial) | Lived-work-claim test; the voice.md hard floor is implicit |
| X-3 (hook strength / bracket-aware / 12 words) | X-1 | Reframed to forward-vector + first-fixation + hook-body |
| X-4 (slop-freeness / parallel structures) | X-5 (partial) | Folded into gestalt-stack test |
| X-5 (structural richness / bracket-aware) | X-4 | Form-matches-function; pad-to-length test |
| X-6 (cross-cohort differentiator) | LOST | No cross-cohort criterion in v1 |

**Findings:**

- **PRESERVED:** X-2's "first-person specific lived-work claim" test survives in v1 X-2 (with Cody Schneider / SOC2 examples). Live X-3's "beat the show-more cutoff" survives in v1 X-1 (as "first-fixation 400–700ms" + "Pinsent / Naval examples"). Live X-4's "what slips through (parallel structures, formulaic transitions, cadence)" survives as v1 X-5's gestalt-stack test with "looks like slop but isn't" defense.

- **LOST (load-bearing — flag for JR):**
  1. **X-1 live: "JR's first-person, opinionated, plain-language register, accessible to a non-engineer founder/marketer."** This is JR's explicit voice anchor — first-person, opinionated, plain-language, accessible to non-engineers. v1 X-5 generalizes to "the account's voice" (any account) and adds cold-start regime forking. The JR-specific first-person voice anchor is gone. If x_engine is multi-author (lane serves multiple clients), the generalization is correct; if x_engine is JR's account specifically (live code is in `programs/references/voice.md` which loads JR's first-cohort voice), the specific anchor is load-bearing. Confirm intentional.
  2. **X-1 live "Jargon without inline plain-English context caps this dimension."** The jargon-must-be-glossed-inline rule is gone from v1. This is JR-iterated for accessibility-to-non-engineer-founder/marketer. v1 X-5's "X-vs-LinkedIn discriminator" handles register-mismatch but not jargon-without-gloss. Restore as do-not-score line.
  3. **X-2 live "HARD FLOOR: any first-person specific lived-work claim REQUIRES the named entity to appear in `programs/references/voice.md`."** This is a JR-iterated provenance-gate: lived-work claims must trace to the voice.md substrate. v1 X-2 score-0 flags "specific-looking details that are confabulated" but does NOT require the named entity to appear in voice.md. The HARD FLOOR is structural (in live code's `load_source_data` voice.md is loaded explicitly) but the score-cap is judge-side. Restore as explicit hard-floor in X-2 score-0.
  4. **X-3 live bracket-aware scoring** (`SHARP earns 5 with one sharp claim+support pair in the first 12 words`). v1 X-1's CoT mentions "first ~7 words ±2 for single post" but does NOT use the bracket-aware scoring (SHARP / BUILD / CASE-STUDY tiers from frontmatter `length_bracket` field). v1's artifact-shape (§1.5) is single-post or thread-of-3-12; doesn't reference the bracket taxonomy. Live code has three brackets enforced at structural_gate (sharp 250–300 / build 500–900 / case_study 1000–1500). v1's artifact-shape and live's bracket-shapes don't match. Confirm.
  5. **X-5 live structural richness with PER-BRACKET anchors:** "SHARP earns 10 with one sharp claim+support pair; BUILD with prose intro + structural pivot + 3-5 bullets + authority anchor + outcome metric; CASE-STUDY with multi-paragraph narrative + sensory detail + numbers timeline + implication close. Pad-to-length = ≤4." This is JR-iterated structure-per-bracket prescription. v1 X-4 generalizes to "single post" / "thread of 3-12" with "Rate of Revelation per unit" — but loses the BUILD-shape and CASE-STUDY-shape prescriptions (prose intro + structural pivot + 3-5 bullets + authority anchor + outcome metric; multi-para narrative + sensory + numbers timeline + implication close). If the lane still produces BUILD and CASE-STUDY artifacts, the per-shape prescription matters. Confirm dropped or restore.
  6. **X-6 cross-cohort criterion entirely.** "Across all drafts in this session's drafts/, no two use the same primary differentiator, source, or hook archetype. Spread across voice_pillars listed in angle metadata." This is the cross-draft diversity test (parallel to live storyboard SB-8, live GEO-6). v1 has no cross-cohort criterion. v1 §1.5 acknowledges artifact-shape (single-post or thread) but not multi-draft session diversity. The `cross_item_criteria={"X-6": CrossItemCriterion(glob="drafts/*.md", max_items=10, words_per_item=400)}` is the workflow contract. If the lane still produces multi-draft sessions, criterion needed. Confirm intentional.

- **DRIFTED:**
  - X-4 live "Banned phrases per slop_gate.py regex are a deterministic floor; this dimension judges what slips through" → v1 X-5 + structural_gate routing. Mechanism preserved but renamed; v1 is more explicit about the deterministic-floor vs gestalt-residual split. Probably intentional improvement.

- **ADDED:** Forward-vector + first-fixation + hook-body alignment 3-axis CoT on X-1; X-5 cold-start sub-anchor (data-rich ≥30 prior posts vs cold-start <30); "looks like slop but isn't" defense; 6 structural_gate checks (em-dash density / signature-phrase blocklist / tricolon density / "Stop X. Start Y." regex / listicle-uniformity / external-link-suppression); 3 sample-and-flag telemetry signals; numerical-weight strip from wrapper (operator-community reconstructions = soft Goodhart vector). All research-driven. The X-5 cold-start regime fork is good. No over-engineering flags.

**Verdict: NEEDS-RESTORATION.** Specific items:
- Restore X-2's voice.md HARD FLOOR ("lived-work claim REQUIRES named entity in voice.md") as explicit score-cap in X-2.
- Restore X-1 live's jargon-without-inline-gloss anti-pattern.
- Decide on bracket-aware scoring (SHARP / BUILD / CASE-STUDY) — if the artifact-shape with brackets persists in workflow, criteria need bracket awareness; if v1's two-shape (single + thread) replaces the three-bracket taxonomy, document and update structural_gate.
- Decide on X-6 cross-cohort criterion — likely restore as 6th criterion or as a cross-item check in v1 §8.
- Confirm voice anchor generalization (JR's first-person → "the account's voice") is intentional.

---

### LI (vs fc99d64) — `session_eval_linkedin_engine.py`

**Live code criteria inventory (6 criteria):**
- **LI-1** "Voice — JR's LinkedIn first-person, story-led, professional register, accessible to B2B buyers + agency operators + C-suite. The lever is thoughtful authority, not contrarian punch. AUTOMATIC ≤4 if the draft reads as bait-y or Twitter-translated."
- **LI-2** "Factual specificity — same SOURCE/INTERPRETIVE split as X-2. HARD FLOOR: lived-work claims REQUIRE the named entity in voice.md. Score capped at 7 for any first-person specific claim that doesn't name the entity (LinkedIn audience punishes vague specificity harder)."
- **LI-3** "Hook strength — story-led + concrete-result openings. PUNISHES contrarian hot-takes that work on X (≤3 even when the same hook would score 5 on X). First 1-2 sentences must beat the show-more cutoff at ~210 chars."
- **LI-4** "Slop-freeness — zero AI-tells AND zero LinkedIn-AI-tells. Banned phrases per slop_gate.py --platform linkedin regex are a deterministic floor; this dimension judges what slips through (`Thoughts? 👇`, `Agree? 🤔`, `Here's what I learned.` close, etc.)."
- **LI-5** "Structural richness + hashtag-count quality. Bracket-aware: SHORT_TAKE/THOUGHT_LEADER/CASE_STUDY each have distinct structural bars. 3-5 targeted hashtags = ideal; 1-2 = suboptimal (cap at 7); 0 = ≤4. Spam (>5) is hard-failed by structural_gate."
- **LI-6** "Cross-cohort — narrative archetype variance (story-led vs lesson-led vs comparison vs case-study) AND voice_pillar spread. Punishes same-tone-same-format streaks. Hashtag-set diversity is NOT scored here (per-pillar drafts may legitimately share signature combos)."

**Live code wrapper / structural_gate prose:** Length brackets short_take 500–900 / thought_leader 1500–2500 / case_study 2500–3000; META requires `hashtags` field (LinkedIn-only on top of X's 4 required); hashtag count `[1, 5]` enforced (0 blocked; >5 spam guardrail); `xeng slop-check --platform linkedin`; voice substrate at `programs/references/voice.md` loaded same as X-engine.

**v1 spec criteria inventory (5 criteria):**
- **LI-1** Trailer earns the "...more" click
- **LI-2** Delivers one non-obvious insight (Alić specificity test)
- **LI-3** Voice is recognizably the author's, not the AI's (gestalt-stack)
- **LI-4** Gives a real reader something substantive to comment on (4 mechanism families)
- **LI-5** Author-context coherence (credible thought leadership / register match)

**Mapping table:**

| Live | v1 | Notes |
|---|---|---|
| LI-1 (JR LinkedIn voice / thoughtful authority not contrarian / bait-y or Twitter-translated cap) | LI-3 (partial) + LI-5 (partial) | Voice + register-coherence split |
| LI-2 (factual specificity / voice.md HARD FLOOR / score capped at 7) | LI-2 (partial) | Alić specificity test; HARD FLOOR implicit |
| LI-3 (hook / story-led / concrete-result / contrarian-hot-takes ≤3) | LI-1 | Reframed to trailer earns the cut |
| LI-4 (slop-freeness / `Thoughts? 👇`, `Agree? 🤔`, `Here's what I learned.`) | LI-3 (gestalt) + structural_gate | Folded |
| LI-5 (structural richness + hashtag-count quality + 3-5 ideal) | LOST as judge criterion | Routed to structural_gate (hashtags `[1,5]` already enforced) |
| LI-6 (cross-cohort narrative archetype variance) | LOST | No cross-cohort criterion in v1 |

**Findings:**

- **PRESERVED:** LI-2 specificity test "swap one named entity, number, or moment ... and the post reads differently" preserved as Alić specificity test in v1 LI-2. LI-3's "story-led + concrete-result" survives in v1 LI-1 (trailer earns the cut). LI-4's specific bait-string examples (`Thoughts? 👇`, `Agree? 🤔`) survive in v1 §3c LinkedIn engagement-bait classifier-suppression routing.

- **LOST (load-bearing — flag for JR):**
  1. **LI-1 "JR's LinkedIn first-person, story-led, professional register, accessible to B2B buyers + agency operators + C-suite."** Specific JR voice anchor with named target audiences (B2B buyers + agency operators + C-suite). v1 LI-3 generalizes to "the author's voice" / "compensating voice markers." Similar to X-1, this is voice-anchor generalization that may or may not be intentional. Confirm.
  2. **LI-1's "AUTOMATIC ≤4 if the draft reads as bait-y or Twitter-translated."** Score-cap rule for two named anti-patterns. v1 LI-3 mentions "looks like slop but isn't" but does NOT carry the explicit "bait-y or Twitter-translated → cap at 4" cap. The bait-y / Twitter-translated cap is JR-iterated empirical. Restore as explicit score-cap or do-not-score line.
  3. **LI-1's "lever is thoughtful authority, not contrarian punch"** — JR's positioning that distinguishes LinkedIn from X. v1 LI-3 + LI-5 cover voice + register-coherence but lose this "thoughtful authority vs contrarian punch" lever specifically. Worth restoring.
  4. **LI-2's HARD FLOOR: "lived-work claims REQUIRE the named entity in voice.md. Score capped at 7."** Same as X-2 hard floor but with LinkedIn-specific cap (7, not just generic "score 0"). The "LinkedIn audience punishes vague specificity harder" JR comment is iterated empirical. v1 LI-2 score-0 names generic-specificity ("customer name dropped but underlying claim is a truism") but does NOT carry the voice.md substrate requirement or the score-7 cap. Restore.
  5. **LI-3's "PUNISHES contrarian hot-takes that work on X (≤3 even when the same hook would score 5 on X)."** This is JR-iterated cross-platform calibration — same content type scores differently on LI vs X. v1 LI-4 (comment-seed) discusses Graham DH4–DH5 vs DH0–DH2 framing but does NOT carry the explicit "hook that scores 5 on X scores ≤3 on LI" cap. Restore.
  6. **LI-4's specific bait-string examples** (`Thoughts? 👇`, `Agree? 🤔`, `Here's what I learned.` close) — survive as engagement-bait classifier-suppression in §3c but are NOT in v1 LI-3 / LI-4 score-0 prose. Worth re-quoting in LI-4 score-0 for vividness.
  7. **LI-5 hashtag-count quality criterion entirely** as judge criterion. v1 routes to structural_gate (which already enforces `[1, 5]`). But the live criterion is more nuanced: "3-5 targeted hashtags = ideal; 1-2 = suboptimal (cap at 7); 0 = ≤4. Spam (>5) is hard-failed by structural_gate." The 3-5-ideal / 1-2-suboptimal-cap-at-7 / 0-cap-at-4 graduated scoring is judge-side, not gate-side. v1 absorbs to structural_gate which only enforces hard fail. Restore the graduated quality scoring OR document drop.
  8. **LI-5 bracket-aware structural richness** (SHORT_TAKE / THOUGHT_LEADER / CASE_STUDY each have distinct structural bars). Same as X-5 — JR-iterated per-bracket structural prescription. v1 has no bracket-aware structure criterion. v1 §1.5 specifies 600–2,000 char text post — DIFFERENT length than the live brackets (500–900 / 1500–2500 / 2500–3000). Confirm intentional re-architecture.
  9. **LI-6 cross-cohort criterion entirely.** "narrative archetype variance (story-led vs lesson-led vs comparison vs case-study) AND voice_pillar spread. Punishes same-tone-same-format streaks." Parallel to X-6, SB-8, GEO-6. v1 has no cross-cohort criterion. The "Hashtag-set diversity is NOT scored here (per-pillar drafts may legitimately share signature combos)" do-not-score nuance is JR-iterated. Restore as 6th criterion.

- **DRIFTED:**
  - LI-3 live "story-led + concrete-result" → v1 LI-1 "specific entity, number, claim, or counterintuitive framing tied to the post's professional context." Same intent; v1's language is more abstract. Confirm intentional.
  - LI-4 live `Thoughts? 👇` / `Agree? 🤔` / `Here's what I learned.` → v1 §3c bait-string list. Same content; gated separately.

- **ADDED:** Trailer-vs-body coherence (LI-1); Welsh / Acosta / Alić / Denning / Meer creator-archetype reference set; Graham DH4–DH5 vs DH0–DH2 reply-ladder; "looks like slop but isn't" defense; Topic Authority awareness in wrapper; engagement-bait classifier (~60% distribution suppression); 4 mechanism families for LI-4; per-criterion Goodhart-collapse defense. Research-driven. No over-engineering flags.

**Verdict: NEEDS-RESTORATION.** Specific items:
- Restore LI-1's "thoughtful authority, not contrarian punch" lever distinguishing LI from X.
- Restore LI-1's "AUTOMATIC ≤4 if draft reads as bait-y or Twitter-translated" score cap.
- Restore LI-2's voice.md HARD FLOOR + "score capped at 7" rule.
- Restore LI-3's "contrarian hot-takes that work on X (≤3 even when same hook scores 5 on X)" cross-platform cap.
- Restore LI-5's graduated hashtag-count scoring (3-5 ideal / 1-2 cap-at-7 / 0 cap-at-4) — or document drop.
- Restore LI-6 cross-cohort criterion (narrative archetype variance + voice_pillar spread).
- Decide bracket-aware structure (SHORT_TAKE / THOUGHT_LEADER / CASE_STUDY) vs v1's unified 600–2000 char text post.

---

### SITE (no live code)

NOTE: SITE has no live code rubric (U15b unshipped, intentional per project memory). No cross-check possible.

The v1 spec at `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` was drafted from `docs/rubrics/site-quality.md` (SE-1..SE-8, 346 lines) as calibration substrate — but no `session_eval_site_engine.py` exists. This is the design-intent direction: when the lane wires into the substrate, the v1 spec becomes the live rubric.

---

## Summary table

| Lane | Verdict | # Lost (load-bearing) | # Drifted | # Added (flagged) | Recommendation |
|---|---|---|---|---|---|
| **CI** | NEEDS-RESTORATION | 6 | 2 | 0 | Restore CI-4 capacity-example, CI-5 asymmetric-opp, CI-7 prioritization, CI-8 gap-as-finding, BANNED_PHRASES list, SOV check |
| **GEO** | NEEDS-RESTORATION (heavy) | 8 | 2 | 0 | Restore 5 of 8 live criteria (GEO-3 honest positioning, GEO-4 page-fit, GEO-5 moat, GEO-6 cross-page, GEO-8 actionable tech); $249 example; Ahrefs example; bracket-marker contract |
| **MON** | MINOR-DRIFT | 4 | 2 | 0 | Restore MON-5 "this could escalate" anti-pattern, MON-6 "competitor went quiet" example, MON-7 watchlist-arc, MON-8 editorial restraint |
| **SB** | SAFE (with one restoration) | 1 | 2 | 0 | Restore live SB-5 (audio design / performable cold / designed silence) |
| **MA** | NEEDS-RESTORATION (heavy) | 8 | 2 | 0 | Most rewritten lane: restore MA_BANNED_PHRASES list + decide on MA-3 Phase-0, MA-4 capability_registry, MA-5 severity-calibration, MA-6 voice quality, MA-7 invented-signals, MA-8 engagement-fit; reconcile 5-section vs 9-section |
| **X** | NEEDS-RESTORATION | 6 | 1 | 0 | Restore X-2 voice.md HARD FLOOR, X-1 jargon anti-pattern, bracket-aware scoring, X-6 cross-cohort criterion; confirm voice generalization intent |
| **LI** | NEEDS-RESTORATION | 9 | 2 | 0 | Restore LI-1 levers + automatic-≤4 cap, LI-2 HARD FLOOR + score-7 cap, LI-3 cross-platform-cap, LI-5 graduated hashtag scoring, LI-6 cross-cohort; reconcile bracket vs unified length |
| **SITE** | N/A | — | — | — | No live code; v1 IS the spec |

## Aggregate findings

**Common patterns of loss across lanes:**

1. **Cross-cohort / cross-item criteria dropped consistently.** GEO-6 (cross-page), SB-8 (5-plan portfolio — partially preserved in v1 SB-5), X-6 (cross-draft session), LI-6 (cross-cohort narrative archetype). The workflow contract (`cross_item_criteria={...CrossItemCriterion(glob=...)}`) is alive in live code but the v1 specs (except SB) drop the criterion-prose. JR iterated this category — workflow produces multi-item sessions, judge tests cross-item diversity. v1 needs to either restore as 6th-criterion documented exceptions OR explicitly retire the cross-item contract.

2. **Concrete JR-iterated examples consistently lost.** "Deploy llms.txt by Mar 26" (CI-4), "$249/month for 2,000 tracked keywords" vs "affordable plans" (GEO-2), "21 of 22 images lack alt text" (GEO-8), "competitor that went quiet" (MON-6), "Thoughts? 👇" (LI-4 — partially preserved in §3c). These are JR's specific-vs-vague teaching anchors. v1 replaces with research-anchored vertical-spanning examples (Pinsent / Linear / Klinika / DermaCenter). Both are useful; only one survives. Per design-guide §7 reference-free principle: research examples are hedged with "do not optimize toward this" — same hedge could carry JR's specific anchors. Restore as additional examples, not replacements.

3. **Voice substrate / HARD FLOOR rules lost in X-2, LI-2.** "any first-person specific lived-work claim REQUIRES the named entity to appear in `programs/references/voice.md`" is the substrate-anchored provenance rule. v1 specs flag confabulation but don't preserve the explicit substrate-lookup hard floor. This is the load-bearing JR rule that says: lived-work claims are NOT free; they must be in voice.md or explicitly flagged scripted-fiction.

4. **Bracket-aware scoring lost in X / LI.** Live X-3, X-5, LI-5 are explicitly bracket-aware (SHARP/BUILD/CASE-STUDY for X; SHORT_TAKE/THOUGHT_LEADER/CASE_STUDY for LI). v1 absorbs to single-post/thread (X) or 600–2000 char text post (LI). If the workflow's frontmatter `length_bracket` field persists, the criteria need to respect it; if v1's reduced bracket set is intentional re-architecture, structural_gate needs updating.

5. **Banned-phrase lists silently replaced, not augmented.** CI's 12-phrase consulting-slop list, MA's 12-phrase corporate-jargon list — both are JR-iterated against specific failure modes in those lanes. v1 specs (when they discuss banned phrases at all, in §8) name a different list ("moreover," "furthermore," "let me explain," em-dash density). The two lists target different failure surfaces (consulting-slop vs AI-slop). Both wanted.

**Which v1 specs are SAFE to ship after JR review:**

- **SB** — single restoration needed (audio design / performable cold). Otherwise the most-faithful v1 to live code.

**Which need restoration before shipping:**

- **MON** — minor restoration (4 items).
- **CI** — moderate restoration (6 items including criterion-level CI-5 asymmetric opp).
- **X / LI** — moderate-to-heavy restoration (voice.md HARD FLOOR, bracket-aware scoring, cross-cohort, score-cap rules).
- **GEO** — heavy restoration (5 of 8 live criteria substantively lost).
- **MA** — heavy restoration (7 of 8 live criteria lost; may be intentional re-architecture but needs explicit JR consent).

**SITE has no live code — v1 stands alone.**

**Meta-observation.** The v1 specs broadly succeed at the design-guide §5 amendment (outcome-question framing, AND-conjunction discipline, AI-failure surface routing, decision-shape routing, ≤5-ceiling with documented exceptions). What they consistently miss is the JR-iterated empirical specificity in the live code: the specific examples that teach what "specific" means, the score-cap rules that bound common-failure-mode scores, the cross-cohort criteria that defend portfolio shape, the substrate-anchored hard floors. These are the things JR iterated over multiple phases to land; they're not in the research deliverables, so they didn't make it into v1.

Recommendation: a Path-A pass on each lane where JR reads v1 score-1 / score-0 anchors alongside live code prose, then surgically restores the JR-iterated load-bearing items as additions (not replacements) to the v1 architecture. This preserves the research-driven re-architecture AND the empirical specificity that made the live rubrics work in production.
