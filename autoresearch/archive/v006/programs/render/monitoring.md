# MONITORING lane — renderer guidance

MONITORING is the weekly ops-digest lane. The agent ingests brand
mentions, clusters them into stories, detects anomalies, synthesises
recommendations, and writes a `digest.md` for the team to action
before next Monday.

## What's in a session_dir

| Path | What it is |
|---|---|
| `digest.md` | The deliverable — weekly summary |
| `mentions/*.json` | Per-mention records (week summaries, baselines, sentiment) |
| `stories/*.json` | Clustered story bundles |
| `anomalies/*.json` | Detected anomalies (anomaly_type, score, summary) |
| `synthesized/*.md` | Per-story synthesis writeups |
| `recommendations/*.md` | Action items + cross-story patterns + executive_summary |
| `eval_feedback.json` + `digest_eval.json` | Judge feedback |

## What's interesting

1. **The loudest anomaly** — open on it. Pull the anomaly's `summary`
   into a `rprt-spotlight` with the score as a `rprt-metric` chip.
2. **Sentiment / volume trend** — if `mentions/baseline.json` +
   `mentions/week-*-summary.json` exist, a sparkline of week-over-week
   mention counts is a strong second component.
3. **Top recommendation** — `recommendations/action_items.md` is the
   "what to do this week" file. Surface the top action with a
   priority-1 row.
4. **Cross-story patterns** — `recommendations/cross_story_patterns.md`
   is the "what's connected across stories" synthesis. Pull the
   single sharpest pattern.

## Style note

Monitoring theming is dashboard / dense / green accent
(`.rprt-page.rprt-theme-monitoring`). Reviewer is operations-
focused; deliver the verdict first, evidence second, action third.

## Exemplar

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ loudest anomaly</div>
  <div class="rprt-spotlight">
    <strong>Measurement-silence anomaly on engineering blog
    <span class="rprt-metric">score 0.84</span></strong>
    <p>Weekly mention count dropped from 27 → 4 between Apr 20 and
    Apr 27. The cluster previously dominated by "performance" +
    "scaling" terms went dark. Likely: an editorial pause, not a
    sentiment shift (sentiment baseline unchanged).</p>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ mention volume trend</div>
  <div class="rprt-chart">
    [[chart:sparkline:w1=18,w2=22,w3=27,w4=4,w5=6|title=Weekly mentions]]
    <p>The Apr-27 dip is the anomaly above. The recovery in week 5
    is the engineering team's first content drop of May.</p>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ top action this week</div>
  <div class="rprt-action-list">
    <div class="rprt-action-row">
      <div class="priority">1</div>
      <div><strong>Confirm with eng-blog editorial</strong> — was the
      Apr-20→27 silence intentional? If yes, log expected resume date;
      if no, route to content-ops as a missed-publish.</div>
    </div>
  </div>
</div>
```

## Anti-pattern

Don't summarise every mention/story/anomaly. There are too many. The
deterministic appendix below dumps them all. Your job is to surface
the *one* thing the team should react to before Monday.
