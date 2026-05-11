# X_ENGINE lane

Ship-eligible X (Twitter) drafts in JR's voice against a single angle.
3-5 drafts per session across length brackets sharp / build / case_study.

## What's in the session_dir

- `drafts/<draft_id>.md` — deliverables. YAML frontmatter
  (`draft_id`, `angle_id`, `platform=x`, `length_bracket`, `char_count`,
  `voice_pillar`) + `[BODY]/[BODY]` + `[META]/[META]`.
  META keys: `hook`, `authority_anchor`, `specific_number`, `attribution`.
- `drafts/<draft_id>.eval.json` — per-draft eval (KEEP/REVISE/DROP +
  per-criterion scores X-1..X-6)
- `angles/<angle_id>.json` — the angle the agent worked from

## What's interesting

1. **Ship-eligible count + ratio** — "3 of 5 ship-eligible (KEEP)".
   `rprt-stat-grid` of (drafts written, ship-eligible, REVISE,
   voice_pillars covered).
2. **The strongest single draft** — highest-scoring KEEP draft. `[BODY]`
   in `rprt-pull-quote`, `[META].hook` above as a strong-element.
3. **Bracket distribution** — donut chart of brackets (sharp / build /
   case_study). If only one covered, flag it.
4. **X-1..X-6 per-criterion average** — bar chart when eval JSONs have
   per-criterion scores.

## Style

Punchy compressed black-and-amber (theme `x_engine`). Tight: short
paragraphs. Post text deserves Georgia-serif treatment to read like a
real post would.

## Exemplar

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ session at-a-glance</div>
  <div class="rprt-stat-grid">
    <div class="rprt-stat-tile"><div class="num">5</div><div class="label">drafts</div></div>
    <div class="rprt-stat-tile"><div class="num">3</div><div class="label">ship-eligible</div></div>
    <div class="rprt-stat-tile"><div class="num">8.4</div><div class="label">avg eval</div></div>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ strongest draft</div>
  <div class="rprt-spotlight">
    <strong>draft-001 · sharp · 268 chars · KEEP (8.4)</strong>
    <div class="rprt-pull-quote">
      <div class="qtext">Most pre-seed CTOs raise before the demo. The
      ones who ship first get the stronger term sheets…</div>
      <div class="qattr">— drafts/draft-001.md (angle: ship-before-fundraise)</div>
    </div>
  </div>
</div>
```

Don't render every draft's full body — pick ONE. The appendix renders all
drafts in a card layout below.
