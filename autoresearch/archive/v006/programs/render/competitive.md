# COMPETITIVE lane — renderer guidance

The COMPETITIVE lane produces a strategic-positioning brief. The agent
maps the client against named competitors, identifies asymmetric moves,
and writes a deliverable `brief.md`.

## What's in a session_dir

| Path | What it is |
|---|---|
| `brief.md` | The deliverable — markdown strategic brief |
| `competitors/*.json` | Per-competitor records: domain, score/composite, summary, raw scrape fields |
| `competitors/_client_baseline.json` | The client's own positioning bundle |
| `analyses/*.md` | Per-competitor narrative writeup (1-5 KB each) |
| `eval_feedback.json` | Evaluator verdict on the brief |

## What's interesting

1. **The single asymmetric move** — surface the brief's central thesis
   in one quote. Use `rprt-pull-quote` with the brief.md sentence and
   the iteration where it stabilised.
2. **Competitor-vs-client comparison** — a small table of 2-3 axes
   (price band / feature depth / market position) with the client
   row highlighted via `rprt-metric` chips.
3. **Top tactic per competitor** — one row per competitor with the
   single sharpest move they made; cite analyses/<name>.md.
4. **Score / composite chart** — when competitors have a `score` or
   `composite` field, a horizontal bar chart of (client + top 5
   competitors) can be a strong opener.

## Style note

Competitive theming is editorial / serif / pull-quote-heavy
(`.rprt-page.rprt-theme-competitive`). Lean magazine-feature: a
prominent quote, narrative flow, less data-dashboard energy.

## Exemplar

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ asymmetric move</div>
  <div class="rprt-spotlight">
    <strong>The play: ship a per-creator template gallery before Canva.</strong>
    <div class="rprt-pull-quote">
      <div class="qtext">Canva's strength is the long tail of templates;
      their weakness is per-vertical curation. A first-mover on a
      creator-template marketplace would forfeit Canva's defensibility
      before they realise the market exists.</div>
      <div class="qattr">— brief.md, iteration 4 stabilised</div>
    </div>
    <p>The earlier iterations chased a "build a better generic editor"
    framing. Iteration 3's pivot to "creator-template marketplace"
    survived two rework loops and is the brief's anchor.</p>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ competitive landscape</div>
  <div class="rprt-chart">
    [[chart:bar:figma=8.4,canva=7.9,framer=7.1,miro=6.2,client=5.8|title=Composite score]]
    <p>Client's composite trails Figma by 2.6 points; the gap is
    concentrated in template breadth (1.8 pts) and per-vertical
    onboarding (0.8 pts). The brief targets the second.</p>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ top tactic per competitor</div>
  <table class="rprt-key-table">
    <thead><tr><th>Competitor</th><th>Sharpest move</th><th>Source</th></tr></thead>
    <tbody>
      <tr><td>Figma</td>
          <td>Plugin marketplace as a moat — third-party devs locked
              into the Figma ecosystem.</td>
          <td><code>analyses/figma.md</code></td></tr>
      <tr><td>Canva</td>
          <td>Free-tier loss-leader on social templates; converts
              4.2% to paid (their metric).</td>
          <td><code>analyses/canva.md</code></td></tr>
    </tbody>
  </table>
</div>
```

## Anti-pattern

Don't write "the competitive landscape is..." — that's filler.
Open on the asymmetric move and back into the landscape.
