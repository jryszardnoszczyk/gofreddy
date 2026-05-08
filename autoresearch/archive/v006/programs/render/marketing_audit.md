# MARKETING_AUDIT lane — renderer guidance

The MARKETING_AUDIT lane produces an executive multi-stage marketing
audit. Stage-5 of the canonical pipeline (`src/audit/stages.py:stage_5_deliverable`)
already generates a Jinja2+WeasyPrint report. When that's present
(`.stage5_mirror` marker file exists), defer to it — your job is then
just to point at it cleanly.

When Stage-5 is NOT present (autoresearch-only run), you compose from
the per-agent JSON outputs.

## What's in a session_dir

| Path | What it is |
|---|---|
| `findability/*.json` | Findability lens agent output |
| `narrative/*.json` | Narrative framing |
| `acquisition/*.json` | Acquisition path analysis |
| `experience/*.json` | UX / experience lens |
| `phase0/phase0_meta.json` | Pre-discovery metadata |
| `lens_outputs/*.json` | Phase 0 synthesis (visibility_summary, site_evidence) |
| `gap_report.md` | Gap analysis narrative (when present) |
| `eval_feedback.json` | Evaluator verdict |
| `.stage5_mirror` | Marker — Stage-5 canonical PDF/HTML mirror present |

## What's interesting

1. **Stage-5 detection** — if `.stage5_mirror` exists and `report.html`
   pre-dates this render, point at it via a `rprt-callout success`
   and stop. Don't duplicate Stage-5's work.
2. **9-axis health** — when phase0 / lens_outputs has axis scores,
   a horizontal bar chart of (findability / narrative / acquisition
   / experience / competitive / monitoring / geo / state-of-business
   / martech-compliance) is the canonical opener. Title it
   `9-axis health` — readers know what that means.
3. **Highest-severity ParentFinding** — the eval_feedback or
   per-agent JSON usually has finding objects with severity. Pull
   the top one as a spotlight.
4. **Gap-report top recommendation** — when `gap_report.md` exists,
   surface its highest-priority recommendation as an action row.

## Style note

Marketing-audit theming is advisory / Playfair / amber-on-cream
(`.rprt-page.rprt-theme-marketing_audit`). The audience is a
client's executive — opinionated, decisive, generous typography.

## Exemplar — Stage-5 mirror present

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ canonical deliverable</div>
  <div class="rprt-callout success">
    <div class="ckind">Stage-5 deliverable</div>
    <div class="ctitle">report.html · report.pdf — sourced from
    <code>src/audit/stages.py:stage_5_deliverable</code></div>
    <p>The audit's canonical view (9-axis health + gap report +
    proposal + sources) was already rendered by Stage-5 (Jinja2 +
    WeasyPrint). The sections below are session-level supplements —
    reasoning trail, evaluator outputs, and the agents' raw
    per-lens JSON.</p>
  </div>
</div>
```

## Exemplar — no Stage-5 mirror, dynamic compose from agent outputs

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ 9-axis health</div>
  <div class="rprt-chart">
    [[chart:bar:findability=7.2,narrative=8.1,acquisition=6.4,experience=8.8,competitive=5.9,monitoring=7.5,geo=4.2,state-of-business=8.0,martech-compliance=9.1|title=9-axis health]]
    <p>Geo lags by ~2.7 vs the cohort median — the largest weakness.
    Martech-compliance is the strength — every key tag intact.</p>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ highest-severity finding</div>
  <div class="rprt-spotlight">
    <strong>Geo-2 · Local landing pages missing for 4 of 6 priority
    metros</strong>
    <div class="rprt-pull-quote">
      <div class="qtext">Of the 6 metros the brand explicitly targets
      in its martech plan (NYC, SF, Chicago, Boston, Austin, Seattle),
      only NYC + SF have dedicated landing pages with city-specific
      schema. The 4 missing ones forfeit ~38% of geo-targeted query
      volume.</div>
      <div class="qattr">— eval_feedback.json, severity=critical</div>
    </div>
  </div>
</div>
```

## Anti-pattern

Don't try to recreate the Stage-5 canonical deliverable when it
exists — you don't have the same data + you'll diverge from the
client-visible report.
