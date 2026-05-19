# medical_pl rule-set authoring notes

Companion document to `reviewer_assist/checklists/medical_pl.yaml` per
plan §U16. Captures the authoring trail: pattern provenance, regulatory
surfaces covered, false-positive / false-negative reasoning, and the
v1.5 promotion-gate handoff for outside-counsel review.

**Posture pin** (load-bearing for liability management): the YAML is
**reviewer-assist scaffolding, NOT a legal-grade compliance gate**. See
plan §Compliance Posture (§214-226). Counsel review of this catalog is
a v1.5 promotion gate, NOT a v1 ship blocker. The pre-publish human
reviewer (U7 service) carries the actual ship/no-ship decision; this
YAML accelerates their pattern-matching but does not replace their
judgment.

## Regulatory surfaces covered

| Surface | Reference | Rules touching it |
|---|---|---|
| Art. 14 Ustawa o działalności leczniczej (2011) — health-services advertising restraint | Public text via ISAP | `superlative_naj_quality`, `superlative_naj_novelty`, `superlative_naj_price`, `uniqueness_jedyn`, `market_leader_lider`, `cta_purchase_now`, `cta_book_visit`, `cta_urgency_limited`, `cta_subscribe_alert`, `price_explicit`, `discount_promotion`, `installments_financing`, `price_comparison_konkur`, `competitor_better_than`, `named_competitor`, `before_after_imagery_ref`, `celebrity_endorsement`, `referral_incentive`, `free_procedure`, `free_consult_with_purchase` |
| Kodeks Etyki Lekarskiej (KEL) Art. 65-68 — physician advertising dignity | Naczelna Izba Lekarska published text | `disease_fear_language`, `body_shame_defect`, `anti_aging_absolutism`, plus all judge-prose meta-flags that surface tone-pressure |
| Ustawa o wyrobach medycznych (2022) Art. 54-58 — medical device advertising | ISAP | `device_uncertified_claim`, `device_fda_only`, `outcome_guarantee`, `percent_efficacy`, `complete_cure`, `no_side_effects`, `minors_targeting` |
| Ustawa Prawo farmaceutyczne — prescription-medicine consumer-advertising restriction | ISAP | `rx_consumer_ad`, `off_label_drug_use`, `unapproved_treatment_claim`, `supplement_as_medicine` |
| Ustawa o zwalczaniu nieuczciwej konkurencji Art. 16 — false-advertising | ISAP | overlaps with most categories; primary callouts: `unsourced_clinical_proof`, `hospital_grade_equipment`, all comparative claims |
| Ustawa o ochronie konkurencji i konsumentów Art. 24 — unfair commercial practices | ISAP | `cta_urgency_limited`, `installments_financing`, `disease_fear_language`, `free_consult_with_purchase` |
| GDPR + Art. 9 special-category data | EU regulation 2016/679 | `testimonial_with_full_name`, `before_after_imagery_ref`, `celebrity_endorsement` |
| Krajowa Izba Lekarska published positions on advertising | NIL website | informs prose tone across the file |

## Authoring methodology

1. **Surface enumeration**: grouped categories by regulatory surface
   (superlatives / CTAs / prices / outcome guarantees / etc.), not by
   severity. Each category gets 1-6 rules.
2. **Polish inflection coverage**: most violations are stem-anchored
   regex with `\w*` suffix to capture case inflections (nom., gen.,
   dat., acc., instr., loc., voc., singular + plural). Critical fix
   during initial authoring:
   - `najlepsz\w*` MISSES `najlepsi` (masc.pers.pl.) — corrected to
     `najleps\w*`. Same correction for `najtań`, `najskutec`,
     `najnowo`, `najbezpiec`, `najpewn`, `najefekt`, `najkorzystn`.
   - `polec\w+` MISSES `poleć` (imperative ends in `ć` not `c`) —
     corrected to `pole[cć]\w*`.
3. **Severity selection**:
   - `hard_block` = unambiguous Art. 14 / KEL / device-act violation
     where the reviewer would always reject. 30 of 44 rules.
   - `soft_warn` = context-dependent surfaces requiring reviewer
     judgment. 14 of 44 rules.
   - 3 LLM-only rules (`pattern: null`) where surface markers don't
     adequately capture the violation: tone-pressure, vague-authority
     appeals, implied endorsement.
4. **Prose drafting**: every rule's prose carries reviewer-action
   guidance ("Reviewer: replace with…" / "Reviewer: verify…" /
   "Reviewer: remove the framing entirely"). Pinned by the dedicated
   test `test_flags_carry_prose_with_substitution_guidance` so the
   substrate enforces actionable prose.

## False-positive / false-negative reasoning

**Known false-positive surfaces** (operator should expect, plan around):

- `medical_pl_named_competitor` is conservative — it requires the
  word "klinika" + a clearly negative comparative adverb within 80
  chars. Real benign mentions ("doktor X pracowała wcześniej w
  klinice Y, gdzie zajmowała się…") may fire when "gorsza" appears
  later. Soft_warn severity so reviewer can resolve.
- `medical_pl_unsourced_clinical_proof` fires on any "badania
  potwierdzają" / "naukowo udowodnione" / "klinicznie sprawdzone".
  Real articles cite specific studies, so the reviewer's task is
  to verify the citation accompanies the claim. False-positive
  rate expected: 20-40% in well-cited articles. Soft_warn.

**Known false-negative surfaces** (gaps the YAML doesn't catch;
reviewer must catch via U7 judgment):

- Image-only violations (e.g. promotional graphics with prices
  rendered as raster). Reviewer-assist YAML is text-only; image
  vision goes through vision_judge (`src/evaluation/vision_judge.py`).
- Tone-pressure surfaces in fully-grammatical prose without
  trigger phrases (e.g. an article that builds aspirational
  pressure without using "boisz się" / "wstydzisz się"). Captured
  partially by `medical_pl_judge_emotional_pressure` LLM rule.
- Multi-rule emergence: an artifact with 5 soft_warn rules each
  individually defensible may be cumulatively predatory. Reviewer
  must judge the aggregate, not just per-rule.

## Test coverage map

Each marquee category has a dedicated sample-artifact test in
`tests/compliance/test_medical_pl_rule_set.py` that pins the
regulatory surface by name (Rule 9 — tests verify intent). Total:
22 dedicated tests + 2 fixture tests in `test_compliance_judge.py`.

| Category | Test |
|---|---|
| Art. 14 superlatives | `test_superlative_najlepszy_inflected_fires_hard_block`, `test_superlative_najnowoczesniejszy_fires_hard_block`, `test_market_leader_fires_hard_block` |
| Art. 14 CTAs | `test_book_visit_cta_fires_hard_block`, `test_urgency_today_fires_hard_block` |
| Art. 14 prices | `test_explicit_price_fires_hard_block`, `test_discount_promotion_fires_hard_block`, `test_financing_for_procedure_fires_hard_block` |
| Outcome guarantees | `test_outcome_guarantee_fires_hard_block`, `test_complete_cure_fires_hard_block`, `test_no_side_effects_fires_hard_block` |
| Off-label / unapproved | `test_unapproved_disease_cure_fires_hard_block` |
| Celebrity / referral | `test_celebrity_endorsement_fires_hard_block`, `test_referral_incentive_fires_hard_block` |
| Clean artifact baseline | `test_clean_informational_artifact_returns_clean` |
| Case-insensitivity | `test_patterns_default_case_insensitive` |
| Reviewer-guidance prose | `test_flags_carry_prose_with_substitution_guidance` |
| Integrity (count / severity / prefix / posture) | `test_medical_pl_loads_with_reviewer_assist_posture`, `test_medical_pl_rule_count_within_plan_envelope`, `test_medical_pl_severity_distribution_has_both_classes`, `test_medical_pl_has_llm_only_judge_surfaces`, `test_medical_pl_rule_ids_use_consistent_prefix` |

## v1.5 promotion-gate handoff (outside-counsel review)

When outside counsel is engaged (parallel-track risk #2 lift), the
review brief is:

1. **Posture confirmation**: counsel reads §Compliance Posture in the
   plan + the YAML's `metadata` block. Counsel confirms the
   reviewer-assist-NOT-legal-grade framing is sustainable post-review.
2. **Per-rule legal accuracy**: counsel reviews each `prose` block
   against the cited Art./KEL/Zbiór section + current case law.
   Particular focus areas:
   - Off-label drug claims (`medical_pl_off_label_drug_use`,
     `unapproved_treatment_claim`) — current text restricts to
     specific examples (Botox migraine, hyaluronic depression). Add
     procedure-specific carve-outs counsel identifies.
   - Patient testimonials (`testimonial_with_full_name`,
     `celebrity_endorsement`) — counsel verifies GDPR Art. 9
     consent specifics for medical context.
   - Outcome guarantees (`outcome_guarantee`, `complete_cure`,
     `no_side_effects`) — counsel confirms the substitution prose
     (probabilistic + duration-bounded language) is legally safe.
3. **False-negative gap analysis**: counsel reviews the known
   false-negative section above + adds any surfaces missing from
   v1 authoring.
4. **Promotion decision**: counsel signs off via metadata change
   (`legal_review_status: "counsel-reviewed YYYY-MM-DD; <firm name>"`).
   Operationally this lifts the two-reviewer-signoff + 3/week
   publish cap noted in `metadata.two_reviewer_signoff_required` +
   `weekly_publish_rate_cap`.
5. **Quarterly review cadence**: counsel re-reviews on regulatory
   changes or new case law. Track in
   `docs/runbooks/medical_pl-quarterly-review-log.md` (to be
   created on first quarterly).

## Updates ledger

| Date | Change | Rationale |
|---|---|---|
| 2026-05-19 | Initial authoring | 44 rules from public regulatory text |
| TBD | Counsel review (v1.5) | parallel-track risk #2 |
| TBD | Operator false-positive calibration (post first 50 artifacts reviewed) | reviewer feedback loop per TD-43 |
