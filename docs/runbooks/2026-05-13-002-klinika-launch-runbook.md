# Klinika Melitus launch runbook (instantiation of U18 template)

Concrete instantiation of
[the launch-runbook template](2026-05-13-002-launch-runbook-template.md)
for Klinika Melitus. Follow the template; the deltas below carry the
Klinika-specific facts the operator needs at execution time.

**Client slug:** `klinika-melitus`
**Display name:** Klinika Melitus
**Archetype:** `b2c_aesthetics` (first onboarded example, not design
center per §Generalization Justification)
**Created:** 2026-05-12

---

## Pre-flight facts

| Field | Value | Notes |
|---|---|---|
| Voice persona | `dr_maria` | Dr. Maria Noszczyk's published works as authority corpus |
| Reviewer-assist checklists | `[medical_pl]` | gdpr_eu defaults via archetype; medical_pl is the v1 authored checklist (U16) |
| Locale | `gl=pl, hl=pl, country=PL`, Warsaw | Requires Polish diacritic normalization |
| Brand strictness | `permissive` | Logo + photography library; no Figma design system yet |
| Enabled channels | storyboard, article_engine, image_engine, ad_engine, linkedin_engine, x_engine, site_engine | All 7 |
| Enabled ad platforms | meta only | LinkedIn ads premature for aesthetic vertical in PL |
| Content denylist | `[clinical_visuals, before_after_imagery]` | Per Art. 14 enforcement |
| Site engine target | https://klinikamelitus.pl | All 6 sections in scope |
| Site engine fallback | `codex_fallback: true` | Codex cyber filter trips on medical content; sonnet handles it |
| Primary reviewer | Dr. Maria Noszczyk (`dr.maria@klinikamelitus.pl`) | SLA `48h_business_pl` |
| Secondary reviewer | **TBD — nominate before launch** | TD-17 mandate for placeholder-regime medical_pl |
| Weekly publish target | 5 | Defines the 30-day launch-window success bar (≥5 publications) |
| Voice corpus consent | required (b2c_aesthetics default) | Parallel-track risk #1: Dr. Maria signoff pending |
| Article brief consumption | `primary_only` | b2c_aesthetics archetype default for compliance audit trail |
| **R22 gate-1 env** | **`EVOLUTION_RULE_SET=medical_pl`** | **MUST be set in every Klinika fixture's env block + every operator-launched evolution run. Without it, gate-1 SKIPS and Art. 14 violations slip through.** |

## Operational gates (parallel-track work, JR-owned)

These gates are real-world dependencies, NOT code blockers. The
substrate ships now; production launch waits on these:

1. **Voice corpus consent** (risk #1): Dr. Maria's
   written consent to ingest the medycyna-urody book chapters as
   authority corpus. Use
   [the voice consent template](2026-05-13-002-voice-consent-template.md).
   Without this, `voice_personas/corpora/dr_maria/` stays empty +
   the persona compiler emits a sparse-substrate warning.
2. **Engagement letter signed** (risk #12): the engagement letter
   must disclaim compliance opinion per §Compliance Posture (the
   reviewer-assist YAMLs are scaffolding, not legal-grade gates).
   Outside counsel draft is parallel-track.
3. **Secondary reviewer nominated** (TD-17 mandate): clinic admin or
   senior nurse with mandate to sign-off when Dr. Maria is
   unavailable. Update `pre_publish_reviewer_secondary` in
   `clients/klinika-melitus/client.yaml` once nomination lands.
4. **Outside-counsel review of medical_pl YAML** (risk #2): v1.5
   promotion gate. v1 ships authored from public regulatory text;
   counsel review converts the YAML from reviewer-assist to
   legal-grade and lifts the two-reviewer-signoff + 3/week cap.
5. **Brand assets delivery**: Klinika provides logo + palette +
   reference imagery via secure transfer (not git). Once on disk
   under `clients/klinika-melitus/brand/`, the brand_strictness
   preflight passes.

## Gate-1 verification (do this BEFORE first publish)

For Klinika every fixture must carry `EVOLUTION_RULE_SET=medical_pl`
in its env block. Run the regression check:

```bash
grep -l '"client": "klinika-melitus"' autoresearch/eval_suites/*.json | \
  xargs -I{} grep -L 'EVOLUTION_RULE_SET' {}
```

This lists Klinika fixtures missing the env. If non-empty, edit those
fixtures' env blocks to add `"EVOLUTION_RULE_SET": "medical_pl"`
before the first run. The runbook template's Step 0 has the full
fixture-env shape.

After the first dry-run, confirm each variant directory carries
`compliance-meta.json` proving the gate fired. Absence of the sidecar
== gate SKIPPED, which is a misconfiguration for Klinika (v1
production posture is two-reviewer-signoff + active gate-1 + ≤3/week
publish cap per TD-17 + §Compliance Posture).

## Site_engine onboarding sequence

Per the template's Step 5:

1. Snapshot `https://klinikamelitus.pl` at engagement start; store
   at `clients/klinika-melitus/site_engine/snapshots/<timestamp>/`.
2. First active scope: `sections_in_scope: [hero]`. After first
   Approve/Publish cycle, add `value_prop` + `social_proof`. After
   second cycle, add `faq`, `cta`, `pricing`.
3. Each section variant goes through reviewer with rendered preview
   inline (not raw HTML).
4. `weekly_section_target: 2` caps throughput.

## First dry-run picks

Per template Step 4:
- Lane: `linkedin_engine` (Dr. Maria byline format; lowest reviewer
  friction for first live demo).
- Brief: a single Klinika SEO topic from monitoring (post-onboarding
  monitoring run).
- Expected outcome: variant passes reviewer-assist gate with verdict
  `clean` or `soft_warn` (no `hard_block` — that would indicate a
  fixture or persona miscalibration).

## Artifact tracking

Each publication appends an entry to
[`klinika-artifacts.json`](2026-05-13-002-klinika-artifacts.json).

## Launch-window success criterion

≥5 approved-and-published artifacts within 30 calendar days of first
publication. Lane mix flexible; site_engine sections count
(one hero-section swap = one artifact). Below target → root-cause
review per template Step 7.
