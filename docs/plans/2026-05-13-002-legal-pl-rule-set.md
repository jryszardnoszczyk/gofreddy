# legal_pl rule-set authoring notes

Companion to `reviewer_assist/checklists/legal_pl.yaml` per plan §U17
(mirror of U16). Captures pattern provenance, regulatory surfaces,
false-positive / false-negative reasoning, and the v1.5 promotion-gate
handoff for outside-counsel review.

**Posture pin** (same as U16): reviewer-assist scaffolding, NOT legal-
grade compliance gate. Counsel review is v1.5 promotion gate, NOT v1
ship blocker. U7 pre-publish reviewer is the safety mechanism.

## Regulatory surfaces covered

| Surface | Reference | Rules touching it |
|---|---|---|
| Kodeks Etyki Radcy Prawnego (KERP) Art. 31-33 — practice information + advertising restraint | Krajowa Izba Radców Prawnych published text | `solicitation_hire_us`, `solicitation_aggressive_choice`, `solicitation_call_now`, `competitor_better_than`, `market_leader`, `unique_specialization`, `expert_self_proclaimed`, `comparative_fee`, `clickbait_legal_news`, `quasi_clinical_legal` |
| Zbiór Zasad Etyki Adwokackiej §23 — information sharing about practice (advocates) | Naczelna Rada Adwokacka published text | mirror surfaces to KERP Art. 32 — covered by same rules above; treated jointly per typical Polish-firm membership of both KIRP + NRA |
| KERP Art. 36 + Zbiór §50 — contingency-fee restrictions | KIRP / NRA | `no_win_no_fee` |
| KERP Art. 27 — judicial respect + collegiality between lawyers | KIRP | `named_judge_influence`, `court_connections`, `solicitation_aggressive_choice` (collegiality clause) |
| KERP Art. 25-26 + Zbiór §51 — fee-splitting with non-lawyers | KIRP / NRA | `referral_incentive` |
| KERP Art. 21 — conflict-management obligation | KIRP | `judge_engagement_letter_omission` (LLM-only) |
| KERP Art. 27 + Zbiór §10 — bar-secrecy obligation | KIRP / NRA | `testimonial_with_name`, `case_outcome_naming`, `celebrity_client_claim`, `judge_secrecy_friction` (LLM-only) |
| KERP Art. 33 — advertising dignity | KIRP | `fee_explicit_amount`, `discount_promotion`, `clickbait_legal_news`, `quasi_clinical_legal` |
| Ustawa o radcach prawnych Art. 22-23 — practice advocacy + secrecy | ISAP | overlaps with KERP coverage above |
| Ustawa Prawo o adwokaturze Art. 6-7 — advocate independence + dignity | ISAP | overlaps with Zbiór coverage |
| Ustawa o zwalczaniu nieuczciwej konkurencji Art. 16 — false-advertising | ISAP | `competitor_better_than`, `market_leader`, `comparative_fee`, `win_rate_puffery`, `global_presence_overclaim` |
| Ustawa o ochronie konkurencji i konsumentów Art. 24 — unfair commercial practices | ISAP | `solicitation_call_now`, `fear_loss`, `victim_targeting`, `panic_urgency` |
| GDPR Art. 6 + Art. 9 — special-category data overlap | EU 2016/679 | `testimonial_with_name`, `case_outcome_naming`, `celebrity_client_claim` |

## Authoring methodology

Mirrors U16 (`docs/plans/2026-05-13-002-medical-pl-rule-set.md`):
surface enumeration first, Polish inflection coverage with stem-
anchored `\w*`, severity selection per category. 33 rules: 18
hard_block + 15 soft_warn + 4 LLM-only meta-flags.

**Distinguishing characteristic vs medical_pl**: Polish bar codes are
TONE-restraint codes. Most violations are framing/tone, not specific
words. LLM-only meta-flags carry more weight here (4 vs 3 in
medical_pl):

- `legal_pl_judge_solicitation_tone` — surfaces solicitation framing
  even when individual phrases pass.
- `legal_pl_judge_engagement_letter_omission` — surfaces conflict-
  management obligation gaps (KERP Art. 21).
- `legal_pl_judge_secrecy_friction` — surfaces matter-detail
  stacking that would let a reader triangulate to a specific client
  (KERP Art. 27 / Zbiór §10) even when no name is given.
- `legal_pl_judge_implied_endorsement` — surfaces unattributed
  authority appeals (regulatory bodies, court endorsements).

**Inflection-coverage fixes during initial authoring** (same shape as
medical_pl): `gwarantujemy\s+(wygran|...)` failed on `wygraną` —
corrected to `gwarantujemy\s+(wygran\w*|...)`. Trailing `\b` after
`%` doesn't fire (both `%` and space are non-word) — dropped trailing
`\b` for `%`-ending patterns.

## False-positive / false-negative reasoning

**Known false-positive surfaces**:

- `legal_pl_expert_self_proclaimed` fires on any "jesteśmy
  ekspertami od" / "specjalizujemy się w". Real firm marketing
  references "experience in" practice areas constantly. Soft_warn
  so reviewer can clear when the framing references actual
  bar-recognized specialisation or factual experience years.
- `legal_pl_global_presence_overclaim` may fire on firms with
  genuine multi-jurisdiction offices when the prose reads as
  marketing-puffery. Soft_warn — reviewer verifies the claim
  matches firm structure.
- `legal_pl_european_court_authority` is narrow: must combine
  ECHR/CJEU mention + success-implication. Real factual references
  to ECHR practice pass.

**Known false-negative surfaces**:

- Solicitation tone in fully-grammatical informational prose (the
  LLM-only `judge_solicitation_tone` is the primary catch — but
  inherently imperfect).
- Cross-cycle matter-detail revealing (one article anonymises;
  three articles together let triangulation). `judge_secrecy_friction`
  scopes to single-artifact analysis.
- Implicit fee-splitting via revenue-share arrangements with
  business-development partners (vs explicit referral incentives) —
  not catchable by surface markers; engagement-letter review
  catches this.

## Test coverage map

`tests/compliance/test_legal_pl_rule_set.py` — 21 dedicated tests +
1 fixture test in `test_compliance_judge.py`. Mirrors U16's coverage
matrix:

| Category | Test |
|---|---|
| Solicitation | `test_hire_us_solicitation_fires_hard_block`, `test_call_now_urgency_fires_hard_block`, `test_takeover_case_fires_hard_block` |
| Fee references | `test_explicit_fee_fires_hard_block`, `test_no_win_no_fee_fires_hard_block`, `test_comparative_fee_fires_hard_block` |
| Outcome guarantees | `test_outcome_guarantee_fires_hard_block`, `test_win_rate_puffery_fires_hard_block` |
| Competitor comparison | `test_competitor_comparison_fires_hard_block`, `test_market_leader_fires_hard_block` |
| Judicial influence | `test_court_connections_fires_hard_block` |
| Fear / pressure | `test_fear_loss_fires_hard_block` |
| Celebrity client / referral | `test_celebrity_client_fires_hard_block`, `test_referral_incentive_fires_hard_block` |
| Clean artifact baseline | `test_clean_informational_artifact_returns_clean` |
| Reviewer-guidance prose | `test_flags_carry_prose_with_substitution_guidance` |
| Integrity (count / severity / prefix / posture) | `test_legal_pl_loads_with_reviewer_assist_posture`, `test_legal_pl_rule_count_within_plan_envelope`, `test_legal_pl_severity_distribution_has_both_classes`, `test_legal_pl_has_llm_only_judge_surfaces`, `test_legal_pl_rule_ids_use_consistent_prefix` |

## v1.5 promotion-gate handoff (outside-counsel review)

Mirror of U16's handoff brief. Focus areas specific to legal_pl:

1. **Posture confirmation** as in U16.
2. **Per-rule legal accuracy**:
   - Contingency-fee surfaces (`no_win_no_fee`) — counsel verifies
     current KIRP/NRA position on partial-contingency vs pure-
     contingency (positions have evolved since KERP last updated).
   - Bar-secrecy surfaces (`testimonial_with_name`, `case_outcome_naming`,
     `judge_secrecy_friction`) — counsel verifies the
     triangulation-prevention threshold matches current enforcement.
   - Judicial-influence surfaces (`named_judge_influence`,
     `court_connections`) — counsel verifies the criminal-law
     overlap (corruption-influence offenses) is correctly described.
3. **False-negative gap analysis** as in U16.
4. **Promotion decision** (same metadata-update pattern as U16).
5. **Coordination with bar association**: per KIRP guidance
   (counsel-to-confirm), high-volume marketing programs may
   benefit from informal KIRP consultation before launch. Operator
   may engage KIRP communications office during v1.5 promotion as
   an extra signal.

## Updates ledger

| Date | Change | Rationale |
|---|---|---|
| 2026-05-19 | Initial authoring | 33 rules from public regulatory text |
| TBD | Counsel review (v1.5) | parallel-track risk #2 |
| TBD | Operator false-positive calibration (post first 50 artifacts reviewed) | reviewer feedback loop per TD-43 |
