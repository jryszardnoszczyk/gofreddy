# Phase D rubric spec — `marketing_audit` lane

**North Star (Phase A):** First-runnable pipeline producing a marketing audit deliverable JR would proudly send to a paying client at $1–3K, generated end-to-end automatically — no manual prose-writing.

**Optimization target (Phase A):** Decision-changing insight density + engagement-pull (sev-3 findings map to build_it/run_it; capability_id ∈ registry; shape-fit to prospect) PLUS gap-honesty pitfall (hiding measurement gaps = capped score).

**Phase C status:** Could not validate empirically — `archive/v189` for marketing_audit contained templates only, no real session fixtures. Spec proceeds on Phase B research strength (5,230 lines of prior planning + 2026-05 emerging signals).

**Architectural note:** This lane uses a different judge architecture from `geo`/`competitive`/`monitoring`. Each MA-N judge returns a **JSON envelope** on stdout with deterministic counts (severity rollup, capability_id ∈ registry, banned-vocab counts, gap_flagged delta, NER thread counts). No gradient prose. Hard-rule caps fire on catastrophic boundary violations. Deliberate: the lane scores a structured 9-section deliverable, not free-form prose, and mechanical verifiability prevents judge drift across the evolve loop.

---

## Section 1: Summary table

| ID    | Tier      | Quality                                                                | Disposition  |
|-------|-----------|------------------------------------------------------------------------|--------------|
| MA-1  | essential | One strategic argument per section + audit-level; contradictions named. | STRENGTHEN   |
| MA-2  | essential | Every claim sourced; ≥2 numeric tokens median per evidence_summary.    | STRENGTHEN   |
| MA-3  | important | Phase-0 nine frames anchor SoB + per-section.                          | KEEP         |
| MA-4  | essential | Recommendations strategic, numeric-anchored, mapped to specific `capability_id`. | STRENGTHEN |
| MA-5  | important | Severity 0-3 anchored; rollup correct; distribution credible.           | KEEP         |
| MA-6  | important | Zero banned vocab + zero synonym-cluster floods; em-dash restrained.    | STRENGTHEN + promote optional → important |
| MA-7  | pitfall   | Gaps surfaced honestly; Phase-0 nulls named; hard-cap if gap_flagged missing. | KEEP         |
| MA-8  | essential | Sev-3 → build_it/run_it; `capability_id` ∈ registry; shape-fit.         | KEEP         |
| MA-9  | essential | Decision-changing density: ≥18/25 findings move the proposal.           | NEW          |
| MA-10 | important | Brand-replace test: ≤2/25 findings survive find-replace.                | NEW          |
| MA-11 | important | Cross-section threading: ≥3 non-prospect NER entities in ≥3 of 9 sections. | NEW          |

**Architecture preserved:** All 11 judges return a JSON envelope on stdout (not gradient prose). Deterministic counts where mechanically computable. Hard-rule caps where boundary violations are catastrophic. Aggregated by geometric mean across 11 — a single rubric floor demotes the variant, which is the load-bearing property keeping MA-10 (brand-specificity) from being optional credit.

**Final count:** 11 criteria — 5 essential (MA-1, MA-2, MA-4, MA-8, MA-9), 5 important (MA-3, MA-5, MA-6, MA-10, MA-11), 1 pitfall (MA-7), 0 optional.

---

## Section 2: Final criterion prose

### MA-1 — Strategic narrative coherence (STRENGTHEN, essential)

**Inputs**
- `findings.md` (primary deliverable, 9 sections)
- `report.md` (narrative summary; cross-reference for audit-level argument)
- `phase0_meta.json` (for cross-checking the central-argument anchor)

**What to check**

1. **Section thesis** — Each of the 9 sections opens with a 1-2 sentence thesis naming the section's strategic argument.
2. **Within-section coherence** — Findings build/support the section thesis, not disconnected tactical observations.
3. **Audit-level argument** — State-of-the-Business names one central strategic argument; the other 8 sections advance it.
4. **Named contradictions with resolution** — When sections imply disagreement (Findability says organic up 22% YoY; Brand says branded-search declining), the audit names the contradiction in a labeled callout, cites both sides, proposes resolution or names the tension. Silent averaging into "mixed signals" is a 1-tier failure.
5. **Walkthrough-priority ordering** — Findings ordered by impact + most-arguable first, not by lens_id ascending.

**JSON envelope**

```json
{
  "rubric": "MA-1",
  "score": 7,
  "reason": "9 explicit theses; State-of-the-Business names central argument and 6 of 9 sections advance it. 1 contradiction named and resolved. Walkthrough-priority ordering in 6 of 9.",
  "section_thesis_count": 9,
  "section_with_strong_through_line_count": 6,
  "audit_level_argument_named": true,
  "named_contradictions_count": 1,
  "named_contradictions_resolved_count": 1,
  "contradictions_unresolved": [],
  "walkthrough_ordered_sections": 6,
  "sections_total": 9
}
```

**Score scale**

- **0-2** Sections are bullet-list of findings; no thesis structure; contradictions in evidence but unsurfaced.
- **3-4** Some sections have implicit thesis; most read as findings-list; contradictions averaged into "mixed signals."
- **5-6** Most sections have explicit thesis; through-line is weak across sections; 0 contradictions named.
- **7-8** Every section has explicit thesis; through-line is present and supported; ≥1 contradiction named (may or may not be resolved); walkthrough-priority ordering present in majority.
- **9-10** Audit-level central argument is named in State-of-the-Business; every section advances it; ≥1 contradiction named AND resolved; all sections walkthrough-ordered. **Anchor:** the kind of audit a CMO emails to their team Friday saying "everyone read this."

**Hard rule**

If `audit_level_argument_named = false` AND `section_with_strong_through_line_count < 5`: cap score at 4. A findings-list without a central argument is not a $1-3K deliverable.

Return ONLY the JSON envelope on stdout.

---

### MA-2 — Evidence traceability + numeric specificity (STRENGTHEN, essential)

**Inputs**
- `findings.md`
- `report.json` (machine-readable; cross-check `sources` array against narrative claims)

**What to check**

1. Every ParentFinding has a `Sources:` line OR inline source URLs.
2. Quantitative claims cite a source ("Foreplay shows N ads", "DataForSEO indexed M keywords").
3. Estimates carry "estimated" / "approx" with a confidence range.
4. Small-N patterns (N=2-3) carry "(N=2)" or "(small sample)" caveats.
5. `addresses_rubrics` IDs match the lens IDs cited in evidence.
6. **Numeric specificity floor** — count numeric tokens (integers, decimals, percentages, dollar amounts, dates, counts like "3 of 5 surfaces") per ParentFinding `evidence_summary`. Median across all ParentFindings must be ≥2 for score 9. Qualitative-only audits ("trust signals weak") demote.

**JSON envelope**

```json
{
  "rubric": "MA-2",
  "score": 8,
  "reason": "All 23 ParentFindings sourced. 4 quantitative claims unattributed; 1 small-N uncaveated. Numeric tokens per evidence_summary: median 3, p10=1, p90=6. 2 findings qualitative-only.",
  "findings_with_sources_count": 23,
  "findings_total": 23,
  "quantitative_claims_unsourced_count": 4,
  "estimates_presented_as_facts_count": 0,
  "small_n_uncaveat_count": 1,
  "numeric_tokens_median": 3,
  "numeric_tokens_p10": 1,
  "numeric_tokens_p90": 6,
  "findings_with_zero_numeric_tokens": 2
}
```

**Score scale**

- **0-2** Most findings have no source attribution; <30% of findings carry any numeric token.
- **3-4** Some sourced; numbers float without attribution; median 0-1 numeric tokens per evidence_summary.
- **5-6** Most sourced; estimates not labeled; median 1-2 numeric tokens.
- **7-8** Every finding sourced; estimates labeled; small-N caveats present; median ≥2 numeric tokens.
- **9-10** Above + cross-section evidence-graph internally consistent + ≤1 finding with 0 numeric tokens.

**Hard rule**

If `numeric_tokens_median < 1` (the audit is adjectival, not measured): cap score at 4. A marketing audit without numbers does not survive client cross-examination.

Return ONLY the JSON envelope on stdout.

---

### MA-3 — Phase-0 framing applied (KEEP, important)

Kept as drafted in `programs/marketing_audit/prompts/judges/MA-3-judge.md`. No rubric redesign. Phase B confirmed the 9 Phase-0 frames are the right architectural innovation; the existing scale (0-2 / 3-4 / 5-6 / 7-8 / 9-10) and JSON envelope shape stand. Implementation note: judge cross-checks `phase0_meta.json` for null/degraded frames and verifies they appear as `state_of_business` findings — already covered by MA-7 hard rule.

---

### MA-4 — Actionable + capability-mapped + numeric-anchored (STRENGTHEN, essential)

**Inputs**
- `findings.md` (recommendation lines per finding)
- `proposal.md`
- `proposal.json` + `report.json`
- `data/capability_registry.yaml` (capability tiers + specific items)

**What to check**

1. Every ParentFinding `recommendation` is ≥50 words.
2. Recommendations name engagement scope (NOT DIY execution steps).
3. Recommendations map to a specific `capability_registry` item by `capability_id` (not just a tier name like "build_it") — required for score 5 and above.
4. **Numeric anchor in recommendation** — every recommendation contains ≥1 numeric anchor (capacity, timeframe, expected delta). Examples: "rebuild positioning in 60 days," "stand up CRO program at 2 experiments/wk," "expected lift of 8-15% on /pricing CR." Adjectival-only recommendations ("strengthen positioning," "improve CRO") demote.
5. Cost-of-delay framing on high-severity (sev-3) findings.
6. Proposal tier entries reference finding IDs.

**JSON envelope**

```json
{
  "rubric": "MA-4",
  "score": 7,
  "reason": "21/23 recommendations ≥50 words. 19/23 strategic; 4 DIY-flavored. 18/23 map to specific capability_id (not just tier). Numeric anchors on 16/23. All proposal entries reference finding IDs. Cost-of-delay on 4/6 sev-3.",
  "recommendations_50_word_count": 21,
  "recommendations_total": 23,
  "diy_flavored_count": 4,
  "capability_id_specific_count": 18,
  "capability_id_tier_only_count": 5,
  "numeric_anchored_recommendation_count": 16,
  "proposal_entries_with_finding_refs": 12,
  "proposal_entries_total": 12,
  "sev3_with_cost_of_delay_count": 4,
  "sev3_total": 6
}
```

**Score scale**

- **0-2** Tactical bullet lists; no capability mapping; no numeric anchors.
- **3-4** Some strategic; many DIY; sparse capability mapping (tier-only); <30% numeric-anchored.
- **5-6** Most strategic ≥50 words; partial specific capability_id mapping; 30-60% numeric-anchored.
- **7-8** All strategic + specific capability_id mapped; proposal references findings; ≥70% numeric-anchored.
- **9-10** Above + cost-of-delay on every sev-3 finding; numeric anchors on every recommendation; mapping internally consistent.

**Hard rule**

If `capability_id_specific_count / recommendations_total < 0.5` (more than half map only to tier, not to a specific registry item): cap score at 5. Tier-only mapping ("build_it") doesn't generate a buyer's mental model of what they'd actually buy.

Return ONLY the JSON envelope on stdout.

---

### MA-5 — Severity calibration (KEEP, important)

Kept as drafted in `programs/marketing_audit/prompts/judges/MA-5-judge.md`. Deterministic ParentFinding severity = max(children.severity) rollup check, lens-anchor verification of SubSignal severities, distribution check (30-50% sev 1, 30-40% sev 2, 10-20% sev 3, ~10% sev 0), inflation flag at >60% sev 3. JSON envelope shape stands. No rubric redesign required.

---

### MA-6 — Polish + voice + lexical-inflation cluster (STRENGTHEN, important — promoted from optional)

**Inputs**
- `findings.md`
- `report.md`
- `surprises.md`
- `proposal.md`

**What to check**

1. **Banned vocabulary** across all 4 files. Banned: `utilize, leverage, facilitate, robust, comprehensive, pivotal, delve, seamless, landscape, tapestry, realm, embark, harness (v), unlock (v), supercharge, empower, paradigm, holistic, synergize, transformative, absolutely, actually, clearly, very, just, simply, basically, essentially, fundamentally, ultimately`.
2. **Banned transitions**: `that being said, it's worth noting, at its core, in today's landscape, in the realm of, when it comes to`.
3. **Em-dash density** per paragraph (>1 = polish failure).
4. **Lexical-inflation synonym cluster** — adjacent fillers in the same semantic slot as banned vocab. Four clusters, total count:
   - **Strength:** `strong, comprehensive, industry-leading, best-in-class, world-class, top-tier, premier, cutting-edge, next-gen, state-of-the-art`
   - **Motion:** `drive, accelerate, propel, fuel, supercharge, elevate, amplify`
   - **Improvement:** `improve, enhance, optimize, streamline, refine, polish, sharpen` (adjectival only — verbs paired with numeric deltas don't count)
   - **Strategic-platitude:** `strategic alignment, holistic approach, end-to-end, full-stack (non-technical), turnkey, white-glove, future-proof`
5. **Voice consistency** — single author or agent-voice leak (Findability section tonally distinct from Narrative).
6. **Templated-sentence detection** — sentence-start patterns ("It's important to note that," "The key thing to remember is").

**JSON envelope**

```json
{
  "rubric": "MA-6",
  "score": 6,
  "reason": "Banned vocab 8 hits; transitions 4; em-dash overuse in 3 paragraphs. Lexical-inflation cluster 14 hits (strength=5, motion=4, improvement=3, platitude=2). Voice mostly consistent; Acquisition section tonally distinct.",
  "banned_vocab_hits": [{"word": "leverage", "count": 3}, {"word": "robust", "count": 2}, {"word": "utilize", "count": 1}, {"word": "seamless", "count": 1}, {"word": "landscape", "count": 1}],
  "banned_transitions_hits": [{"phrase": "it's worth noting", "count": 2}, {"phrase": "at its core", "count": 2}],
  "em_dash_overuse_paragraphs": 3,
  "lexical_inflation_cluster_hits": {"strength": 5, "motion": 4, "improvement": 3, "strategic_platitude": 2},
  "lexical_inflation_total": 14,
  "voice_consistency_verdict": "mostly-consistent-with-section-drift",
  "templated_sentence_count": 2
}
```

**Score scale**

- **0-2** Multiple banned-vocab hits per page; sounds like raw LLM output; lexical-inflation cluster ≥30 hits.
- **3-4** Some sections clean; others have AI tells; voice inconsistent; cluster 15-30 hits.
- **5-6** Most clean; 2-5 banned-vocab hits; cluster 8-15 hits.
- **7-8** Zero banned-vocab; em-dash restrained; voice consistent; cluster ≤7 hits.
- **9-10** Above + recognizable editorial fingerprint (specific, blunt, evidence-anchored); cluster ≤3 hits.

**Hard rule**

If `banned_vocab_hits ≥ 10` OR `em_dash_overuse_paragraphs ≥ 5` OR `lexical_inflation_total ≥ 25`: cap score at 3 regardless of other dimensions. The polish floor is non-negotiable; banned-vocab and synonym-substitution are equivalent failure modes.

Return ONLY the JSON envelope on stdout.

---

### MA-7 — Gap honesty (KEEP, pitfall)

Kept as drafted in `programs/marketing_audit/prompts/judges/MA-7-judge.md`. The hard rule (cap at 4 if ≥3 gap_flagged lenses missing from `gap_report.md`, OR phase0 frame null/degraded without `state_of_business` finding naming it) is the strongest mechanical defense against the false-completeness slop pattern. No rubric redesign. Implementation note: judge counts `gap_flagged` rows across the 4 agent `rubric_coverage` maps and joins against `gap_report.md` rows — deterministic.

---

### MA-8 — Engagement-fit (KEEP, essential)

Kept as drafted in `programs/marketing_audit/prompts/judges/MA-8-judge.md`. Two hard rules stand: (a) any `capability_id` ∉ `data/capability_registry.yaml` caps at 3 (off-registry pitching is commercial-integrity failure); (b) <50% of sev-3 findings mapping to `build_it`/`run_it` caps at 5 (without engagement-pull the audit is just a $1K artifact). See Section 5 for discussion of how MA-8's hard-rule philosophy informed the MA-6 promotion.

---

### MA-9 — Decision-changing insight density (NEW, essential)

**Inputs**
- `findings.md` (ParentFindings with recommendation lines)
- `proposal.md` + `proposal.json` (recommendation hashes)
- `report.json` (machine-readable finding-to-proposal map)

**What to check**

1. **Deletion test per ParentFinding** — for each of the 25-32 ParentFindings, hash the proposal recommendations, mentally null the finding, re-derive the proposal from the remaining 24-31 findings. If the proposal still produces the same tier+capability_id+scope recommendation, the finding is decorative.
2. **Count decision-moving findings** — N findings whose deletion moves the proposal (any of: tier change, capability_id change, severity-3-to-2 demotion of a proposal entry, scope change in the narrative anchor).
3. **High-leverage marker** — at least 3 findings should be load-bearing for a `build_it` or `run_it` tier proposal entry. Their deletion should reframe (not just remove) that entry.
4. **Observation-only fail check** — flag findings whose recommendation matches stock-vapid phrases ("monitor closely," "consider evaluating options," "conduct further research"). These count as decorative regardless of the deletion test.

**JSON envelope**

```json
{
  "rubric": "MA-9",
  "score": 7,
  "reason": "23 total. Deletion test: 19/23 move proposal (tier/capability_id/scope change). 4 decorative (3 observation-only, 1 duplicating sibling SubSignal). 3 reframe build_it entries; 1 reframes run_it. No stock-vapid recommendations.",
  "findings_total": 23,
  "findings_move_proposal_count": 19,
  "findings_decorative_count": 4,
  "findings_reframe_build_or_run_count": 4,
  "observation_only_recommendation_count": 3,
  "stock_vapid_recommendation_count": 0
}
```

**Score scale**

- **0-2** <8/25 findings move proposal. Audit is observation theatre.
- **3-4** 8-12/25 move proposal. Half decorative.
- **5-6** 13-17/25 move proposal. Acceptable density; not impressive.
- **7-8** 18-22/25 move proposal. Each finding earns its slot.
- **9-10** ≥23/25 move proposal AND ≥3 findings would reframe a `build_it`/`run_it` tier item. Every finding is load-bearing. **Anchor:** every finding visible in the proposal's narrative anchor or in a specific tier entry.

**Hard rule**

If `observation_only_recommendation_count ≥ 5` OR `stock_vapid_recommendation_count ≥ 2`: cap score at 4. Stock-vapid recommendations are a 1-tier slop pattern and override the deletion-test math.

Return ONLY the JSON envelope on stdout.

---

### MA-10 — Brand-specificity floor (brand-replace test) (NEW, important)

**Inputs**
- `findings.md`
- `report.json` (for prospect-domain, competitor-names, vertical, segment from `state_of_business`)
- `phase0_meta.json` (for prospect identity)

**What to check**

1. **Identify prospect** — from `phase0_meta.json` or `state_of_business`, extract brand name, domain, named competitors.
2. **Sample 5 ParentFindings** — deterministic seed `hash(run_id) mod findings_total`.
3. **Per-finding brand-specific anchor count.** Five anchor types:
   - **a.** Prospect-domain URL paths quoted (`/pricing`, `/security`, `/blog/...`)
   - **b.** Prospect-page copy quoted verbatim (≥6 consecutive words)
   - **c.** Named competitors with own-domain evidence URLs (`competitor.com/pricing`, not "competitors in general")
   - **d.** Prospect-specific badge/asset presence/absence (SOC 2 on /security; G2 on /pricing; schema markup detected)
   - **e.** Prospect-vertical-specific phrasing ("for legal-tech buyers") with evidence backing the vertical claim
4. **Brand-replace mental check** — find-replace prospect brand with `<COMPETITOR>` per finding; if still reads true and actionable → boilerplate.

**JSON envelope**

```json
{
  "rubric": "MA-10",
  "score": 7,
  "reason": "5 sampled. Mean anchors 2.6. Types: 8 URL paths, 4 page-copy quotes, 6 named-competitor evidence URLs, 3 badge/asset checks, 1 vertical phrasing. 1/5 survives brand-replace (the Phase-0 trajectory finding generalizes appropriately).",
  "findings_sampled": 5,
  "brand_specific_anchors_per_finding": [4, 3, 2, 3, 1],
  "brand_specific_anchors_mean": 2.6,
  "anchor_type_counts": {"url_path": 8, "page_copy_quote": 4, "competitor_evidence_url": 6, "badge_asset": 3, "vertical_phrasing": 1},
  "findings_surviving_brand_replace": 1,
  "estimated_findings_surviving_brand_replace_full_audit": 5
}
```

**Score scale**

- **1** Find-replace brand; ≥18/25 findings still read true. Generic-B2B-SaaS audit.
- **3** 13-17/25 still read true. Mostly generic.
- **5** 8-12/25 still read true. Mixed.
- **7** 3-7/25 still read true. Mostly brand-specific; sampled findings carry ≥2 anchors on average.
- **9-10** ≤2/25 still read true; every sampled finding has ≥2 brand-specific anchors AND ≥1 anchor of types (b)/(c)/(d) (the structural defenses against ChatGPT-90-second baseline). **Anchor:** findings are deeply anchored to THIS prospect's URLs, copy, competitors, pricing.

**Hard rule**

If `brand_specific_anchors_mean < 1.0` across the sampled findings: cap score at 3. Sub-1.0 means even sampling charity, the audit is boilerplate.

Return ONLY the JSON envelope on stdout.

---

### MA-11 — Cross-section thread continuity (NEW, important)

**Inputs**
- `findings.md`
- `report.md`
- `report.json` (for section labels + ParentFinding list keyed by section)

**What to check**

1. **Extract named entities** from the deliverable using the NER taxonomy below (Section 3 of this spec).
2. **Top-5 entities by mention count** across the audit.
3. **Per-entity section spread** — count distinct sections (of the 9) each top-5 entity appears in.
4. **State-of-the-Business cross-reference** — verify that the top-3 threaded entities are named explicitly in the State-of-the-Business opener (not just in their owning section).
5. **Threading evidence diversity** — for each threaded entity, the evidence cited in each of the ≥3 sections it appears in should be distinct (different URL/lens_id/page). Same-evidence repetition across sections is restatement, not threading.

**JSON envelope**

```json
{
  "rubric": "MA-11",
  "score": 7,
  "reason": "Top-5: Acme (prospect, 47, 9/9), Stripe Atlas (competitor, 18, 4/9), '/pricing' (asset, 15, 3/9), 'EU mid-market' (segment, 12, 3/9), Klaviyo (competitor, 9, 2/9). 3 non-prospect entities thread ≥3 sections; evidence diversity passes; SoB names Stripe Atlas and '/pricing'.",
  "top_5_entities": [{"entity": "Acme", "type": "prospect", "mentions": 47}, {"entity": "Stripe Atlas", "type": "competitor", "mentions": 18}, {"entity": "/pricing", "type": "asset", "mentions": 15}, {"entity": "EU mid-market", "type": "segment", "mentions": 12}, {"entity": "Klaviyo", "type": "competitor", "mentions": 9}],
  "section_spread": {"Acme": 9, "Stripe Atlas": 4, "/pricing": 3, "EU mid-market": 3, "Klaviyo": 2},
  "entities_threaded_3plus_sections_excluding_prospect": 3,
  "state_of_business_references_top_3": 2,
  "evidence_diversity_passed": true
}
```

**Score scale**

- **1** No non-prospect named entity appears in >1 section. Four parallel mini-audits.
- **3** Top non-prospect entity appears in 2 sections; no other entity threads.
- **5** 1-2 non-prospect entities thread across ≥3 sections.
- **7** 3 non-prospect entities thread across ≥3 sections.
- **9-10** ≥3 non-prospect entities thread across ≥3 sections AND State-of-the-Business explicitly references the threaded entities by name AND evidence diversity passes (no same-URL repetition across threading sections).

**Hard rule**

If the prospect's own brand is the only entity threading across ≥3 sections (everything else stays parochial): cap score at 4. Audits about the prospect can't help mentioning the prospect; threading is about what *else* shows up.

Return ONLY the JSON envelope on stdout.

---

## Section 3: 9-section threading mechanic for MA-11

The threading check needs a stable NER definition. The judge runs NER over the full `findings.md` + `report.md` deliverable; cheap LLM-NER (the judge's own pass) is acceptable because the bar is recurrence-counting, not extraction quality. Provide the taxonomy in the judge prompt; let it apply.

### NER taxonomy for marketing_audit

Six entity types. The judge tags each mention as one type, lower-cases for matching, and counts distinct mentions across sections.

1. **prospect** — the audited company's brand name and known aliases. Read from `phase0_meta.json.prospect_brand` and any `state_of_business` aliases. The prospect itself is excluded from the "≥3 entities thread" bar because it trivially appears everywhere; track separately to verify it does appear in all 9 sections (a sanity check on coverage).
2. **competitor** — named competitor companies (proper nouns) with evidence URLs on their own domain OR named in the prospect's positioning copy. Excludes generic "competitors" / "incumbents" / "the market." Examples: Stripe Atlas, Klaviyo, Brex, Mercury.
3. **asset** — specific prospect-owned surfaces or pages, identified by URL path or canonical phrase. Examples: `/pricing`, `/security`, `/blog/series-name`, "the homepage hero," "the demo CTA modal." Asset mentions tie findings to specific tactical evidence.
4. **segment** — prospect's named customer segments or ICP descriptors. Read from Phase-0 `customer_segment` frame and audit prose. Examples: "EU mid-market," "legal-tech procurement gatekeepers," "Series B founders," "SMB ecom merchants."
5. **capability** — specific `capability_registry` items mentioned in proposal entries or recommendations. Read from `proposal.json.entries[*].capability_id`. Examples: `positioning_rebuild`, `cro_program_b2b`, `geo_content_engine`.
6. **person** — named individuals at the prospect or in competitor evidence (founder names, CMOs, prominent customer testimonials). Lowest-frequency type; usually 0-2 per audit. Examples: "Patrick Collison" (if quoted in a Stripe Atlas evidence URL); the prospect's CEO if quoted from a podcast.

### Computation

1. Run NER pass over `findings.md` + `report.md` with this taxonomy as the prompt's instructions.
2. Normalize entity strings (case, articles, plural forms); judge canonicalizes via judgment ("Stripe Atlas" ≡ "Atlas (Stripe's incorporation product)") — no synonym database.
3. Count mentions per entity per section, section = one of the 9 in `report.json.sections`. Section assignment follows that mapping, not prose drift.
4. Top-5 by total mention count; for each, count distinct sections.
5. **Threading bar:** ≥3 of top 5, *excluding the prospect (trivially threads)*, appear in ≥3 of 9 sections.

**Why NER + recurrence works.** Phase B's observation: 4-agent parallel synthesis produces 4 disjoint mini-audits unless Stage-3 cross-cutting actually crosses. Threading is the observable artifact of cross-cutting. Recurrence catches it whether intentional (Stage-3 wove "Stripe Atlas" through Brand + Competitive + Proposal) or accidental (load-bearing entity surfaced independently by multiple agents — still a positive signal). Judge counts; doesn't reason about why.

**Edge cases.** Asset paths `/pricing` and `/pricing/enterprise` are distinct unless audit groups them. If judge tags "growth" or "marketing" as entities, downgrade — those are nouns; the prompt enumerates the six types and refuses common-noun captures.

---

## Section 4: Implementation notes

**Deterministic checks preserved.** MA's defining property is count-checks in the JSON envelope. Existing: MA-5 severity rollup + distribution; MA-6 banned-vocab + em-dash counts; MA-7 `gap_flagged` join against `gap_report.md` rows + Phase-0 null detection; MA-8 `capability_id` ∈ registry + sev-3-to-build/run ratio.

**New deterministic checks (this spec).** MA-2: numeric token count per `evidence_summary` (regex over integers, decimals, percentages, dollar amounts, dates, "N of M" patterns) → median/p10/p90. MA-4: `capability_id` specific-vs-tier-only count; numeric anchor presence per recommendation. MA-6: 4-cluster lexical-inflation count (keyword lists embedded). MA-9: stock-vapid regex + observation-only detection (recommendation <50 words AND zero numeric anchors AND no `capability_id`). MA-10: reproducible sample seed `hash(run_id) mod findings_total`; anchor-type regex counts. MA-11: NER pass is LLM, but section-spread + top-5 + threading-bar post-processing is mechanical.

**Cross-reference paths.** `data/capability_registry.yaml` (MA-4, MA-8); `phase0_meta.json` (MA-3, MA-7, MA-10, MA-11); per-agent `rubric_coverage` in `agents/<a>/agent_output.json` (MA-7); `findings.md`, `report.md`, `report.json`, `proposal.md`, `proposal.json`, `surprises.md`, `gap_report.md` (varies). Lane runtime ensures presence pre-judge (existing behavior, unchanged).

**RUBRIC_VERSION hash.** Each judge prompt file in `programs/marketing_audit/prompts/judges/MA-N-judge.md` hashes into `RUBRIC_VERSION`. Strengthening MA-1/MA-2/MA-4/MA-6 changes content → hash → version. New MA-9/MA-10/MA-11 add entries. Cache invalidates on next variant; expected cost = 11 × N variants × judge-call. Geomean aggregates across 11.

**Geomean aggregation.** Lane aggregator stays geometric mean (updated from 8 to 11 rubrics). Geomean's single-low-rubric-demotes-overall property is the load-bearing protection against MA-10 (brand-specificity) being weight-diluted credit. A variant scoring 9 on MA-1..8 + 9 on MA-9/MA-11 + 2 on MA-10 lands at geomean ≈ 6.4, correctly demoting "competent but boilerplate." No min-of-rubrics fallback — geomean is the right shape.

---

## Section 5: Engagement-fit threshold + MA-6 promotion

**MA-8's hard rules are the model.** MA-8 caps at 3 if any `capability_id` ∉ registry, and at 5 if <50% of sev-3 findings map to `build_it`/`run_it`. The failure modes — pitching off-registry capabilities, top findings not generating engagement — are commercial-integrity catastrophes no other rubric catches. Geomean alone wouldn't: a variant scoring 8 across MA-1..7 and 6 on MA-8 lands at ≈7.7, too high for a deliverable pitching work the agency can't deliver. The hard caps invert that to 3, killing the variant. This hard-cap-for-catastrophic-boundary pattern propagates across six of 11 rubrics in this spec (MA-2, MA-6, MA-7, MA-8, MA-9, MA-10) — intentional, because the lane is high-stakes commercially and the evolve loop needs structural protection against optimization-for-prose-only.

**Why MA-6 promotes optional → important.** Optional in the existing stack means MA-6's polish weight is diluted in geomean — a variant could score 4 on MA-6 and still aggregate ~7.0 if MA-1..5 hit 8s. In May 2026 the ChatGPT-amateur baseline (Phase B §5.2) raises the polish floor: clients have seen 90-second AI audits; if our audit *reads* like one, no strategic substance recovers it. Promoting MA-6 pulls its geomean weight up and triggers variant pressure on the lexical-inflation cluster fix (synonym substitution past the banned-vocab list). The MA-6 hard rule (banned ≥10 OR em-dash overuse ≥5 OR cluster ≥25) caps at 3 (not 1) — distinguishing "bad" from "catastrophic" within the capped range so geomean math propagates appropriately.

**Tier composition net:** 5 essential / 5 important / 1 pitfall / 0 optional. The lane has no optional rubrics. Phase B's MA-6 promotion + the introduction of MA-9/MA-10/MA-11 collapses optional entirely. A $1-3K deliverable has no room for "credit but optional" dimensions — every rubric earns weight or gets cut.

---

## Section 6: Validation plan

Phase C couldn't validate (`archive/v189` was templates-only). Validation defers to the first 5 real paid client audits. Three judge-targeting tests + two diagnostic guardrails.

### Test 1 — Brand-replace test (MA-10 ground truth, primary)

For each of the first 5 paid audits: take `findings.md`, find-replace prospect brand with `<COMPETITOR>` (preserve URLs, page-copy quotes; only swap the brand string), manually rate each ParentFinding for "still reads true and actionable for a generic B2B SaaS competitor in the same vertical/segment," compare manual count vs. MA-10 predicted count. **Pass criteria:** within ±20%, score-vs-manual correlation r > 0.7 by audit #5. If MA-10 over-counts brand-specific anchors, tighten page-copy quote length floor and named-competitor evidence requirement; if it under-counts, loosen anchor type (e) (vertical-specific phrasing — softest type).

### Test 2 — Deletion test (MA-9 ground truth)

For each of the 5 audits: manually null each ParentFinding in a copy, re-derive the proposal, count decorative findings (proposal unchanged). Compare to MA-9 predicted. **Pass criteria:** within ±15%; for audits scoring MA-9 ≥7, manual decorative count should be ≤5/25. If MA-9 ≥7 but manual says >7 decorative, judge is inflating — tighten the stock-vapid regex and observation-only detection.

### Test 3 — Threading test (MA-11 ground truth)

For each audit, manually identify top-5 non-prospect entities and section-spread; compare to MA-11 computed list. **Pass criteria:** top-3 entities match; section-spread within ±1 per entity. If NER mis-tags common nouns (e.g., "growth" surfaces as top-5), enumerate the six entity types more strictly in the prompt and explicitly refuse common-noun captures.

### Test 4 — Boilerplate baseline regression (sanity check)

Generate a deliberately-boilerplate audit using ChatGPT ("write me a marketing audit for example.com," no Phase-0, no lens catalog). Run the 11-judge stack. **Pass criteria:** MA-10 ≤3, MA-9 ≤4, MA-2 ≤4, MA-6 ≤4, geomean ≤4.0. If the boilerplate scores >5.0 geomean, one or more rubrics is failing to discriminate against the ChatGPT-amateur baseline — tighten anchors, re-run.

### Test 5 — Commercial ground truth + inter-rubric independence (lagging)

Track walkthrough conversion (target >40%) and $15K+ engagement close rate (target >25%) on audits scoring geomean ≥7. If geomean-7 audits convert at the same rate as geomean-5 audits, the judge isn't capturing decision-changing quality. Concurrently, across the first 20 variants in the evolve loop, compute pairwise rubric correlations: any pair with r > 0.85 is collapsible. MA-9/MA-10 high correlation = one absorbs the other. MA-1/MA-11 high correlation = move threading from MA-1's sub-check to MA-11 only.

---

**End of spec.**
