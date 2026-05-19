# Content Engine Lanes v1 — 4 new lanes + R22 gate-1 + Path-A closure

Implements `docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md`.
37 commits, ~205 files, +26k/-2k LOC. Single PR because the scope is one
cohesive feature; commit-level navigation below.

## Summary

- **4 new lanes**: `article_engine`, `image_engine` (Gemini 3 Flash Preview),
  `ad_engine` (5-DI-provider signal aggregator), `site_engine` (nh3
  sanitizer + brand-tokens Pydantic schema).
- **Storyboard extension**: 5 platform_targets × 3 format_modes + voice-
  corpus input + custom_score format-mode reweighter.
- **Voice migrations**: `linkedin_engine` + `x_engine` cut over to
  the U3 voice-persona framework via `compile_substrate` (shared
  helper).
- **Brief emission**: `geo` + `monitoring` + `marketing_audit` emit
  findings-briefs at promote-time per D8 (U9/U10/U10b).
- **3 reviewer-assist YAMLs**: `medical_pl` (44 rules, Art. 14 +
  KEL + Medical Devices Act), `legal_pl` (33 rules, KERP + Zbiór +
  bar codes), `gdpr_eu` (load-bearing for Klinika+DWF EU clients).
  Posture per §Compliance Posture: reviewer-assist scaffolding,
  NOT legal-grade compliance gates — counsel review is a v1.5
  promotion gate.
- **R22 gate-1 wired** into `autoresearch/evolve.py` (the architectural
  fix surfaced by CE-review adversarial ADV-001 — previously the
  compliance check was a library with no production callers).
  Opt-in via `EVOLUTION_RULE_SET` env.
- **Foundation primitives**: per-client config (U2), voice persona
  framework (U3), findings-brief contract (U4), reviewer-assist
  framework (U5), image composer (U6), portal moments event-schema
  extension (U6b), pre-publish review service (U7), Playwright site
  render (U7b).
- **Operational substrate**: launch-runbook template + voice-consent
  template + Klinika + DWF instantiations + per-client artifact
  manifests (U18 substrate-side; operator-side gates remain
  parallel-track).
- **Architectural CI**: D11 archetype-coverage assertion (U19) +
  cross-lane voice consistency test (SC4) + brand_tokens.json
  Pydantic threat-model schema.

## Commit navigation (chronological → architectural)

### Foundation primitives (U0–U7b)
- `fbb5cc2` U0 remove AXIS_COLLAPSE escape hatch
- `6d707a6` U0a graduate HOLDOUT + FRAGILE_FIXTURES
- `dc650b9` U1 derived RUBRICS count invariant
- `eb74271` chore(tests) clean up pre-existing test rot before U2
- `5e3ad39` U2 per-client config object
- `c224f39` U3 voice persona framework
- `27016a6` U4 findings-brief contract
- `e43e69c` U6b canonical event-schema extension for portal moments
- `4c9ecdd` U5 reviewer-assist framework primitive
- `443b075` U6 static-image composition module (Pillow)
- `f0e659b` U7 pre-publish human review service
- `4f4d6e0` U7b Playwright site render utility
- `0f20520` hardening(foundation) — 4-agent review security + correctness fixes
- `d3c955d` hardening(foundation) — contract additions + field renames + cleanup

### Lane work (U8–U15b)
- `6f931d4` U8 storyboard extension (5 platforms × 3 modes + voice + denylist + custom_score)
- `1b22277` U9 + U10 + U10b promote-time brief emission for geo / monitoring / marketing_audit
- `c1dc44e` U11 linkedin_engine voice persona migration
- `04b1a16` U12 x_engine voice persona migration + factor compile_substrate
- `581b07c` U13 article_engine lane
- `cd57f6e` U14 image_engine lane (Gemini 3 Flash Preview — supersedes D24's 2.5)
- `ff2d447` U15 ad_engine lane (5-provider signal aggregator, claude/sonnet inner-pin)
- `cad75bc` U15b site_engine lane (nh3 sanitizer + brand_tokens schema)

### Reviewer-assist authoring (U16/U17/U18)
- `5a586f5` U19 architectural CI diff assertion for config-only onboarding
- `b9f3fa7` U16 medical_pl reviewer-assist checklist authoring (44 rules)
- `07037ad` U17 legal_pl reviewer-assist checklist authoring (33 rules)
- `00db1f9` U18 launch-runbook substrate + voice-consent template
- `b29cd38` close audit gaps — brand_tokens schema + U16/U17 authoring-notes
- `e252dd7` close Success-Criteria substrate gaps (SC1 D11 programmatic + SC4 cross-lane voice)

### CE-review architectural closure (Path A)
- `4692d67` Unicode normalization in compliance judge — defeats
  ZWSP/fullwidth/Cyrillic-homoglyph bypasses (CE-review ADV-003)
- `cfe13ac` Polish regex bug class — close 10+ false-negative +
  false-positive gaps (CE-review C-1..C-10 + ADV-003 + ADV-009)
- `e1d847a` Compliance rubrics use prose_ref=None — was minting
  unresolvable anchors (CE-review C-11)
- `a166298` Delete TD-43 reviewer_diff_capture scaffolding — YAGNI
  per CE-review MAINT-1
- `df86a18` Fix mislabeled test regressions + 2 substrate bugs
  surfaced (CE-review testing test-1..test-4)
- `b1220d0` R22 gate-1 wired into evolve.py — `src/compliance/lane_gate.py`
  bridges evaluate_compliance to per-lane variant lifecycle
  (CE-review adversarial ADV-001)

### Final prep
- `468604f` Merge origin/main (portal-moments PR #61) — resolves
  3-file conflict in events.py / test_events.py / plan-002.md;
  adds `sla_escalation` to KNOWN_KINDS
- `b54b539` Runbook docs for EVOLUTION_RULE_SET — template Step 0 +
  Klinika + DWF per-client deltas

## Architectural call-outs

### R22 gate-1 is wired but OPT-IN

The plan's §R22 "two-gate compliance" architecture lands in this PR
with one half active and one deferred:

- **Gate-1 (in-loop fitness check)**: wired in
  `autoresearch/evolve.py` via `src/compliance/lane_gate.py`.
  Opt-in via `EVOLUTION_RULE_SET` env. When set, fires before
  scoring; on hard_block, variant is discarded; on soft_warn,
  variant passes through scoring with a sidecar persisted for the
  pre-publish reviewer.

- **Gate-2 (pre-publish human review)**: library wired (`src/review/service.py`
  + `src/api/review_webhook.py`); operator-invocation surface (publish
  CLI / lane post-publish hook) lands at U18 because lanes don't
  publish automatically in v1 — operator picks winners from
  evolution + manually submits.

### EVOLUTION_RULE_SET — operator opt-in for gate-1

Without this env set, gate-1 returns SKIPPED. The runbook updates
in `b54b539` document the contract:
- Klinika fixtures → `EVOLUTION_RULE_SET=medical_pl`
- DWF fixtures → `EVOLUTION_RULE_SET=legal_pl`
- SaaS / b2b_tech → unset OR `gdpr_eu` for EU-targeting

Verification: post-run, `<variant_dir>/compliance-meta.json` exists
== gate fired. Absence == gate SKIPPED (misconfiguration for
regulated clients).

### Operator-side parallel-track gates (NOT this PR)

These are plan §Parallel-Track Risks; they gate first PUBLICATION,
NOT this PR's merge:

1. Klinika voice corpus consent (risk #1) — gates voice ingestion
   for Dr. Maria's medycyna-urody corpus
2. DWF engagement letter signed (risk #12) — gates DWF onboarding
3. Outside-counsel review of medical_pl + legal_pl YAML (risk #2) —
   v1.5 PROMOTION gate; lifts two-reviewer-signoff + ≤3/week cap
4. Secondary reviewer nominations (TD-17 mandate)
5. Brand assets delivery (operator-side)
6. Production API keys (Anthropic, Gemini 3 Flash Preview, 5 ad
   signal-aggregator providers) — DI callable pattern means
   production wiring is a per-lane env swap

### Posture pin

The `medical_pl` + `legal_pl` reviewer-assist YAMLs are operator-
authored from public regulatory text. Plan §Compliance Posture
(§214-226) explicitly classifies them as REVIEWER-ASSIST scaffolding,
NOT legal-grade compliance gates. Operator-facing surfaces (review
emails, audit logs, error messages) carry the same framing.
Engagement-letter language disclaims compliance opinion (parallel-
track risk #12).

## Test plan

Substrate test state (across all v1 trees, post-merge):

- [x] tests/clients/ (30) — ClientConfig schema + loader
- [x] tests/voice/ (22 + 12 cross-lane consistency) — persona
      compilation + corpus loading
- [x] tests/briefs/ (multiple) — findings-brief contract
- [x] tests/compliance/ (88 + 11 lane_gate + 7 bypass) —
      reviewer-assist checklists + judge + gate-1
- [x] tests/review/ — HMAC review service
- [x] tests/onboarding/ (12) — D11 archetype coverage + U19 stub
- [x] tests/ads/ — 5-provider signal aggregator
- [x] tests/site_engine/ (32 brand_tokens + sanitizer) — nh3 +
      Pydantic schema
- [x] tests/evaluation/ (18) — rubrics invariant + resolve_prose
- [x] tests/source_material/ — md/PDF/HTML loader
- [x] tests/verification/ — DI citation verifier
- [x] tests/autoresearch/ (768 / 1 env-only fail) — full lane
      substrate, storyboard extension fixed to import from
      v007-curated (not gitignored current_runtime), linkedin/
      x_engine fixtures fixed for U11/U12 voice-persona-ref
      requirement
- [x] tests/portal/ + tests/audit/ + tests/test_api/ (664) —
      main's incoming portal-moments tests pass

**Total: ~1,825 substrate tests pass, 2 known failures**:
- `test_opencode_smoke` — opencode binary not installed locally
  (genuinely env-only; pre-existing on main)
- `test_marketing_audit_lanespec_callables_wired` — marketing_audit
  custom_score is None per L3-deferred substrate decision; the
  test from PR #45 still expects it set (verified failing on
  `origin/main` HEAD, NOT introduced by this branch)

Plus 1 skipped (intentional, env-gated).

### Pre-merge smoke (operator-do)

Before merge, run a 1-iter smoke against a Klinika fixture to
verify gate-1 fires end-to-end in the actual evolution loop:

```bash
EVOLUTION_RULE_SET=medical_pl \
  AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES=1 \
  freddy autoresearch run \
    --lane article_engine \
    --iterations 1 --candidates 1 \
    --fixture article_engine-klinika-procedure-botox
```

Then inspect `<variant_dir>/compliance-meta.json`:
- File exists + `verdict == "clean" | "soft_warn"` → gate works
- File exists + `verdict == "hard_block"` → gate works; the
  variant prompt needs adjustment (still demonstrates gate fires)
- File missing → gate SKIPPED; env not propagating correctly

Cost: ~$30-50 / ~30-45 min.

## CE-review history

This PR went through a 5-agent CE-review pass that surfaced 4 P0s
+ multiple P1/P2 findings. Path A (chosen by the reviewer) closed
the architectural gaps:

- **ADV-001 (P0)**: gate-1 orphaned — wired in `b1220d0`
- **ADV-002 (P0)**: gate-2 orphaned — deferred to U18 per
  publish-time-not-evolution-time correct design
- **ADV-003 (P0)**: Unicode bypasses — closed in `4692d67`
- **ADV-004 (P0)**: sanitizer byte-equality false-rejects — deferred
  to U18 dry-run (site_engine doesn't run in production yet)
- **C-1..C-10 (P1)**: Polish regex bugs — closed in `cfe13ac`
- **C-11 (P1)**: prose_ref anchor mismatch — closed in `e1d847a`
- **test-1..test-4 (P1)**: mislabeled test regressions — closed in
  `df86a18` (+ surfaced 2 substrate bugs: missing
  evaluate_artifact_glob in v007-curated eval_cache.py + storyboard
  custom_score wire pointing at gitignored current_runtime)
- **MAINT-1 (P1)**: TD-43 scaffolding YAGNI — deleted in `a166298`

Deferred to v1.5 / U18 (per Path A scope):
- ADV-005 YAML hot-read drift mid-evolution
- ADV-006 reviewer-assist disclaimer in operator surfaces
- ADV-007 brand_tokens layout-collapse validators
- sec-1 voice consent runtime enforcement
- sec-2 citation_verifier SSRF guard (production fetcher lands at U18)

## DO NOT (carryover from session memory)

- Don't run automated fal.ai I2V (operator runs manually per TD-45)
- Don't write to remote channels until U18 ships + operator gates lift
- Don't ship U16/U17 as "legal-grade compliance gates" without
  outside-counsel review — §Compliance Posture is load-bearing
- HMAC secret `REVIEW_HMAC_SECRET` — never commit; quarterly rotation

## Test plan checklist

- [ ] Operator: run 1-iter smoke per "Pre-merge smoke" section above
- [ ] Operator: confirm `<variant_dir>/compliance-meta.json` exists +
      verdict is sane
- [ ] CI: full test suite green (sub bullets above documented as
      pre-existing/env-only)
- [ ] Reviewer: skim commit-by-commit per the navigation above
- [ ] Reviewer: confirm §Compliance Posture framing matches plan
- [ ] Reviewer: confirm gate-2 deferral is acceptable

🤖 Generated with [Claude Code](https://claude.com/claude-code)
