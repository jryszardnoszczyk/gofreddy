# GEO lane — renderer guidance

GEO is the AI-citation visibility lane. The agent fetches a brand's pages,
benchmarks against competitors, optimises copy, then measures whether the
optimised pages actually surface in answer-engine citations (ChatGPT,
Perplexity, Gemini).

## What's in a session_dir

| Path | What it is |
|---|---|
| `pages/*.json` | Cached scrape of brand + competitor pages (title, URL, word_count, schema_types, H1, meta) |
| `optimized/*.md` | Agent-authored re-write of the page (the deliverable) |
| `evals/optimized-*.json` | Per-page judge feedback (KEEP / REVISE / DROP + critique) |
| `competitors/visibility.json` | Cloro citation measurement: per-engine citation count, brand-citation share |
| `gap_allocation.json` | Strategic gap → assigned page slug + the gap narrative |
| `report.json` | Pre-aggregated structured output: `recommended_blocks`, `top_questions`, `top_heading_targets`, `offsite_domains` |
| `verification-schedule.json` | Phase verification plan |

## What's interesting

In order of likely-signal-strength:

1. **Citation deltas** — visibility.json has per-engine counts. A
   chart of brand vs competitor citations across the 3 engines is
   almost always the lead.
2. **Block-mix recommendations** — `report.json.recommended_blocks` is
   a dict of `block_type → count`. A bar chart of the top 6 is the
   second-most-common chart.
3. **Page-by-page optimisation status** — which pages got KEEP, which
   needed REVISE. A small table or inline list with per-page judge
   verdicts.
4. **Strategic gap** — `gap_allocation.json` typically has 1-2
   allocations. Quote the `assigned_gap` text in a `rprt-pull-quote`.
5. **Top questions to answer** — `report.json.top_questions` is a
   list of LLM-extracted questions the brand could rank for. List
   the top 5-8.

## Style note

GEO theming is clinical-blue serif (see `.rprt-page.rprt-theme-geo` in
the report base CSS). Lean structured: tables, key-value lists,
explicit per-page status. Less hero-card-and-pull-quote energy than
competitive; more "data dashboard."

## Exemplar — a strong GEO highlights block

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ citation evidence</div>
  <div class="rprt-chart">
    [[chart:bar:chatgpt=12,perplexity=4,gemini=8|title=Brand citations by engine]]
    <p>ChatGPT leads at 12 brand citations, Perplexity is the laggard at 4.
    The Cloro run sampled 18 prompts per engine, so 4/18 ≈ 22% capture rate
    on Perplexity vs 67% on ChatGPT — a fixable gap.</p>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ block-mix recommendation</div>
  <h3>Recommended block additions for the next iteration</h3>
  <div class="rprt-chart">
    [[chart:bar:howto=8,faq=6,comparison=4,table=3,definition=2|title=Block types to add (top 5)]]
    <p>The synthesis pass identified 8 missing how-to blocks across the
    7 cached pages. Add those first — every missing how-to block on
    enterprise/ + pricing/ matches a top-question the brand isn't
    ranking for.</p>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ per-page status</div>
  <table class="rprt-key-table">
    <thead><tr><th>Slug</th><th>Eval</th><th>Reason</th></tr></thead>
    <tbody>
      <tr><td><code>brand-radar.md</code></td><td><strong>KEEP</strong></td>
          <td>9-axis schema + answer-block format pass; Cloro picks up
          first 2 paragraphs.</td></tr>
      <tr><td><code>pricing.md</code></td><td>REVISE</td>
          <td>No comparison block; competitors all have one.</td></tr>
      <tr><td><code>site-explorer.md</code></td><td>KEEP</td>
          <td>FAQ schema valid; <span class="rprt-metric">+34%</span>
          word-count vs prior iteration.</td></tr>
    </tbody>
  </table>
</div>
```

## Anti-pattern

Don't write a generic "GEO is about citation visibility" intro
paragraph. The reviewer knows what GEO is. Open on the *delta* this
session produced.
