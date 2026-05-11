# COMPETITIVE lane

A strategic-positioning brief mapping the client against named competitors.

## What's in the session_dir

- `brief.md` — the deliverable (markdown brief)
- `competitors/*.json` — per-competitor records (domain, score, summary)
- `competitors/_client_baseline.json` — client's own positioning bundle
- `analyses/*.md` — per-competitor narrative writeups
- `eval_feedback.json` — evaluator verdict on the brief

## What's interesting

1. **The single asymmetric move** — surface the brief's central thesis
   in `rprt-pull-quote` with the iteration where it stabilised.
2. **Competitor-vs-client comparison** — small table of 2-3 axes (price
   band / feature depth / market position).
3. **Top tactic per competitor** — one row per competitor with the
   sharpest single move; cite `analyses/<name>.md`.
4. **Composite score chart** when competitors have a `score` field.

## Style

Editorial / serif / pull-quote-heavy (theme `competitive`). Magazine-feature
energy: prominent quote, narrative flow. Less data-dashboard.

## Exemplar

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ asymmetric move</div>
  <div class="rprt-spotlight">
    <strong>The play: ship a per-creator template gallery before Canva.</strong>
    <div class="rprt-pull-quote">
      <div class="qtext">Canva's strength is the long tail of templates;
      their weakness is per-vertical curation. A first-mover would forfeit
      Canva's defensibility before they realise the market exists.</div>
      <div class="qattr">— brief.md, iteration 4 stabilised</div>
    </div>
  </div>
</div>
```

Don't write "the competitive landscape is…" — open on the move.
