# GEO lane

GEO measures whether the agent's optimised pages surface in answer-engine
citations (ChatGPT / Perplexity / Gemini) vs competitors.

## What's in the session_dir

- `pages/*.json` — cached scrapes (title, URL, schema_types, H1, meta)
- `optimized/*.md` — agent-rewritten pages (the deliverables)
- `evals/optimized-*.json` — judge feedback per page
- `competitors/visibility.json` — Cloro citation counts per engine
- `gap_allocation.json` — strategic gap → assigned page slug
- `report.json` — pre-aggregated `recommended_blocks`, `top_questions`,
  `top_heading_targets`, `offsite_domains`

## What's interesting

1. **Citation deltas** — `visibility.json` per-engine counts. Bar chart of
   brand vs competitor citations across 3 engines is almost always the lead.
2. **Block-mix recommendations** — `report.json.recommended_blocks` as a
   bar chart of the top 6.
3. **Page-by-page optimisation status** — KEEP/REVISE/DROP per page.
4. **Strategic gap** — quote `gap_allocation.json:assigned_gap` in a
   `rprt-pull-quote`.

## Style

Clinical-blue serif (theme `geo`). Lean structured: tables, key-value lists,
explicit per-page status. Less hero-card, more dashboard.

## Exemplar

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ citation evidence</div>
  <div class="rprt-chart">
    [[chart:bar:chatgpt=12,perplexity=4,gemini=8|title=Brand citations by engine]]
    <p>ChatGPT leads 12, Perplexity laggard at 4 (22% capture vs ChatGPT's 67%).</p>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ per-page status</div>
  <table class="rprt-key-table">
    <thead><tr><th>Slug</th><th>Eval</th><th>Reason</th></tr></thead>
    <tbody>
      <tr><td><code>brand-radar.md</code></td><td><strong>KEEP</strong></td>
          <td>9-axis schema + answer-block format pass.</td></tr>
      <tr><td><code>pricing.md</code></td><td>REVISE</td>
          <td>No comparison block; competitors all have one.</td></tr>
    </tbody>
  </table>
</div>
```

Don't open with "GEO is about citation visibility" — anchor on the delta.
