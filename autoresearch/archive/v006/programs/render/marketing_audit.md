# MARKETING_AUDIT lane

Executive multi-stage marketing audit. Stage-5 (Jinja2 + WeasyPrint) is
the canonical client deliverable; you compose the autoresearch-side view.

## What's in the session_dir

- `findability/*.json`, `narrative/*.json`, `acquisition/*.json`,
  `experience/*.json` — per-lens agent outputs
- `phase0/phase0_meta.json` — pre-discovery metadata
- `lens_outputs/*.json` — Phase 0 synthesis (visibility_summary,
  site_evidence)
- `gap_report.md` — gap analysis narrative (when present)
- `eval_feedback.json` — evaluator verdict
- `.stage5_mirror` — marker file: when present, Stage-5 already shipped
  the canonical PDF/HTML

## What's interesting

1. **Stage-5 detection** — if `.stage5_mirror` exists, point at it via
   `rprt-callout success` and STOP. Don't duplicate Stage-5's work.
2. **9-axis health** — when phase0 / lens_outputs has axis scores, bar
   chart of (findability / narrative / acquisition / experience /
   competitive / monitoring / geo / state-of-business / martech-compliance).
3. **Highest-severity ParentFinding** — `rprt-spotlight` from
   eval_feedback severity field.
4. **Top recommendation** from `gap_report.md` when present.

## Style

Advisory / Playfair / amber-on-cream (theme `marketing_audit`). Audience
is a client executive: opinionated, decisive, generous typography.

## Exemplar — Stage-5 mirror present

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ canonical deliverable</div>
  <div class="rprt-callout success">
    <div class="ckind">Stage-5 deliverable</div>
    <div class="ctitle">report.html · report.pdf — sourced from
    <code>src/audit/stages.py:stage_5_deliverable</code></div>
    <p>Stage-5 (Jinja2 + WeasyPrint) shipped the canonical 9-axis +
    gap-report + proposal. Sections below are session-level supplements.</p>
  </div>
</div>
```

## Exemplar — no Stage-5 mirror

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ 9-axis health</div>
  <div class="rprt-chart">
    [[chart:bar:findability=7.2,narrative=8.1,acquisition=6.4,experience=8.8,competitive=5.9,monitoring=7.5,geo=4.2,state-of-business=8.0,martech-compliance=9.1|title=9-axis health]]
    <p>Geo lags by ~2.7 vs the cohort median — the largest weakness.</p>
  </div>
</div>
```

Don't try to recreate Stage-5 when it exists; you'll diverge from the
client-visible report.
