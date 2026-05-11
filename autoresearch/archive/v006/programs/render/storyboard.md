# STORYBOARD lane

Video-content production. Agent watches top-performing creator videos,
extracts patterns, generates ship-eligible storyboards (5-10 scenes each).

## What's in the session_dir

- `storyboards/*.json` — generated storyboard deliverables
  (title, scenes[], beats, emotion_arc, protagonist_description, anchor_preview_image_url)
- `stories/*.json` — intermediate story-cluster artefacts (5 per session)
- `patterns/*.json` — per-source-video pattern + creator_synthesis.json
- `evals/story-*.json` — eval feedback per story

## What's interesting

1. **The strongest single storyboard** — pick highest-scoring or most-cohesive.
   `rprt-spotlight` with `target_emotion_arc` + `protagonist_description`.
2. **Scene-by-scene table** for the strongest one ONLY (#, title/shot/camera,
   beat, duration). Don't do this for every storyboard.
3. **Pattern signal** — quote one distinctive pattern from
   `creator_synthesis.json` (e.g. "all 5 videos open with a 3s visual gag").
4. **Storyboards-vs-source ratio** — "5 source videos → 3 storyboards"
   when the ratio is interesting.

## Style

Cinematic dark mode + amber accent (theme `storyboard`). Visual, less
data-tabley, poetic prose tolerated more than other lanes.

## Exemplar

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ most-likely-to-watch</div>
  <div class="rprt-spotlight">
    <strong>Storyboard "Subway Surfers Goes Home" — strongest of 5</strong>
    <div class="rprt-pull-quote">
      <div class="qtext">A grandfather plays in the window seat. The
      camera holds on his hands; we never see the phone. Win-screen
      audio plays under a slow-motion shot of a child laughing in the
      next car.</div>
      <div class="qattr">— scenes 4-6 of storyboards/sb-002.json</div>
    </div>
    <p>Emotion arc: <code>warmth → recognition → uplift</code>.</p>
  </div>
</div>
```

Don't render every storyboard's full scenes — pick one or two, do them well.
