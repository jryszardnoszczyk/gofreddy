# MONITORING lane

Weekly brand-mention digest. Agent ingests mentions, clusters into
stories, detects anomalies, recommends actions. Action-before-Monday view.

## What's in the session_dir

- `digest.md` — the weekly summary (deliverable)
- `mentions/*.json` — per-mention records (sentiment, baselines)
- `stories/*.json` — clustered story bundles
- `anomalies/*.json` — detected anomalies (type, score, summary)
- `synthesized/*.md` — per-story synthesis writeups
- `recommendations/*.md` — `action_items.md`, `cross_story_patterns.md`,
  `executive_summary.md`
- `eval_feedback.json` / `digest_eval.json` — judge feedback

## What's interesting

1. **The loudest anomaly** — `rprt-spotlight` with the score as a
   `rprt-metric` chip + the anomaly summary.
2. **Sentiment / volume trend** — sparkline of week-over-week mention
   counts when `mentions/baseline.json` + week summaries exist.
3. **Top recommendation** — `recommendations/action_items.md` first
   action surfaced as priority-1 row.
4. **Cross-story pattern** — single sharpest pattern from
   `cross_story_patterns.md`.

## Style

Dashboard / dense / green accent (theme `monitoring`). Operations-focused:
verdict first, evidence second, action third.

## Exemplar

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ loudest anomaly</div>
  <div class="rprt-spotlight">
    <strong>Measurement-silence anomaly on engineering blog
    <span class="rprt-metric">score 0.84</span></strong>
    <p>Weekly mention count dropped 27 → 4 between Apr 20 and Apr 27.
    Likely editorial pause, not sentiment shift (sentiment baseline
    unchanged).</p>
  </div>
</div>
```

Don't summarise every mention. The appendix dumps them all — your job is
"the one thing the team should react to before Monday."
