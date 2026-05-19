# DWF Poland launch runbook (instantiation of U18 template)

Concrete instantiation of
[the launch-runbook template](2026-05-13-002-launch-runbook-template.md)
for DWF Poland. Follow the template; the deltas below carry DWF-
specific facts the operator needs at execution time.

**Client slug:** `dwf-poland`
**Display name:** DWF Poland
**Archetype:** `b2b_regulated` (first onboarded example, not design
center per §Generalization Justification)
**Created:** 2026-05-12

---

## Pre-flight facts

| Field | Value | Notes |
|---|---|---|
| Voice persona | `partner_jamka` | Maciej Jamka's published articles as authority corpus |
| Reviewer-assist checklists | `[legal_pl]` | gdpr_eu defaults via archetype; legal_pl is the v1 authored checklist (U17) |
| Locale | `gl=pl, hl=pl, country=PL`, Warsaw | Polish diacritic normalization |
| Brand strictness | `strict` | International firm with established brand book |
| Enabled channels | article_engine, linkedin_engine, x_engine, site_engine | No storyboard / no Meta ads / no image-heavy lanes (legal-firm tone) |
| Enabled ad platforms | none | Legal-firm advertising restraint per KERP Art. 32 |
| Content denylist | empty | Bar-codes restrict tone not content categories |
| Site engine target | https://dwf.law/en/poland | All 6 sections in scope |
| Site engine fallback | `codex_fallback: true` | Codex cyber filter trips on legal content (litigation vocabulary); sonnet handles it |
| Primary reviewer | Maciej Jamka (`maciej.jamka@dwf.law`) | SLA `72h_business_pl` (partner review + RES practice clearance buffer) |
| Secondary reviewer | **TBD — nominate before launch** | TD-17 mandate for placeholder-regime legal_pl |
| Weekly publish target | 3 | Lower throughput than aesthetic clinic; defines launch window success bar |
| Voice corpus consent | required (b2b_regulated default) | Maciej's clearance gates corpus ingest |
| Article brief consumption | `primary_only` | b2b_regulated archetype default for compliance audit trail |

## Operational gates (parallel-track work, JR-owned)

Same five-gate structure as Klinika; the parallel-track risks for
DWF specifically:

1. **Voice corpus consent** (risk #1): Maciej Jamka's written
   consent to ingest his prior partner articles as authority corpus.
   Specifically — the bar-secrecy clause in the
   [consent template](2026-05-13-002-voice-consent-template.md) is
   load-bearing for DWF: the corpus must consist of public
   case-commentary + expert opinions, NOT internal matters.
2. **Engagement letter signed** (risk #12): outside counsel drafts
   per §Compliance Posture.
3. **Secondary reviewer nominated** (TD-17 mandate): second partner
   (e.g. RES practice deputy) or senior associate with sign-off
   mandate when Maciej is unavailable. Update
   `pre_publish_reviewer_secondary` in
   `clients/dwf-poland/client.yaml` once nomination lands.
4. **Outside-counsel review of legal_pl YAML** (risk #2): v1.5
   promotion gate.
5. **DWF brand assets**: DWF provides international firm style
   guide + Polish-specific palette + logo via secure transfer.
   Strict brand_strictness means SVG logo + WOFF2 fonts required
   (no PNG/system-font fallback).

## Site_engine onboarding sequence

Per the template's Step 5, with DWF-specific cadence:

1. Snapshot `https://dwf.law/en/poland` at engagement start.
2. First active scope: `sections_in_scope: [value_prop]`. The hero
   section for a legal firm is operationally sensitive (partner
   bylines, firm positioning) — start with value_prop section which
   is content-heavier but lower partner-review friction.
3. `weekly_section_target: 1` caps throughput at one section per
   week. Partner review + RES clearance buffer (72h) means rapid
   iteration isn't realistic.

## First dry-run picks

Per template Step 4:
- Lane: `article_engine` (Maciej byline format; bar-restraint-tone
  exercises the legal_pl checklist on its primary surface).
- Brief: a single DWF KSeF-implementation topic from monitoring
  (Polish regulatory commentary is partner_jamka's strong domain).
- Expected outcome: variant passes reviewer-assist gate with
  verdict `clean` or `soft_warn`. A `hard_block` on a KSeF article
  is almost always a persona-calibration miss (corpus didn't
  capture the bar-restraint tone).

## Artifact tracking

Each publication appends an entry to
[`dwf-artifacts.json`](2026-05-13-002-dwf-artifacts.json).

## Launch-window success criterion

≥5 approved-and-published artifacts within 30 calendar days of first
publication. Lane mix flexible; site_engine sections count. At lower
weekly throughput (3) the window is tighter — partner availability
is the rate-limiting factor.
