# STORYBOARD lane — renderer guidance

STORYBOARD is the video-content production lane. The agent watches
top-performing creator videos, extracts patterns, and generates
ship-eligible storyboards (5-10 scenes each: title, shot, camera,
beat, duration).

## What's in a session_dir

| Path | What it is |
|---|---|
| `storyboards/*.json` | Generated storyboard deliverables (full structure: title, scenes[], beats, emotion_arc, protagonist_description, anchor_preview_image_url) |
| `stories/*.json` | Intermediate story-cluster artefacts (5 per session) |
| `patterns/*.json` | Per-source-video pattern analysis + creator_synthesis.json |
| `evals/story-*.json` | Eval feedback per story |
| `clips/`, `frames/` | (typically empty — reserved for downstream production) |

## What's interesting

1. **The strongest single storyboard** — pick the highest-scoring or
   most-cohesive one. Surface its title in a spotlight, its
   `target_emotion_arc` + `protagonist_description` as supporting
   prose.
2. **Scene-by-scene table** — for the strongest storyboard ONLY,
   render scenes as a table (#, title/shot/camera, beat, duration).
   Don't do this for every storyboard — it'd be visually heavy.
3. **Pattern signal** — `patterns/creator_synthesis.json` is the
   summary of what made the source videos work. Quote one
   distinctive pattern (e.g. "all 5 videos open with a 3-second
   visual gag before the verbal hook").
4. **Emotion-arc comparison** — if multiple storyboards have
   different `target_emotion_arc` values, a small list comparing
   them helps the reviewer pick.
5. **Storyboard count vs source count** — "5 source videos →
   3 storyboards" is a crisp data point if it's an interesting ratio.

## Style note

Storyboard theming is cinematic dark mode + amber accent
(`.rprt-page.rprt-theme-storyboard`). Lean visual, less data-tabley,
poetic prose tolerated more than other lanes.

## Exemplar

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ most-likely-to-watch</div>
  <div class="rprt-spotlight">
    <strong>Storyboard "Subway Surfers Goes Home" — strongest of 5</strong>
    <div class="rprt-pull-quote">
      <div class="qtext">A grandfather plays Subway Surfers in the
      window seat. The camera holds on his hands; we never see the
      phone. The win screen's audio plays under a slow-motion shot
      of a child laughing in the next car.</div>
      <div class="qattr">— scenes 4-6 of storyboards/sb-002.json</div>
    </div>
    <p>Emotion arc: <code>warmth → recognition → uplift</code> —
    matches the highest-engagement creator pattern (Khaby.Lame
    pattern: "let the action carry, not the dialogue").</p>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ scene breakdown</div>
  <table class="rprt-key-table">
    <thead><tr>
      <th>#</th><th>Title / shot</th><th>Beat</th><th>Dur</th>
    </tr></thead>
    <tbody>
      <tr><td>1</td><td>Open · wide est. shot · static</td>
          <td>train interior; grandfather visible left of frame</td>
          <td>3s</td></tr>
      <tr><td>2</td><td>Cut to close · push-in</td>
          <td>hands on phone; thumbs moving fast</td>
          <td>4s</td></tr>
      <tr><td>3</td><td>Reverse · hold on grandfather's face</td>
          <td>brief smirk at a near-miss; we still don't see the phone</td>
          <td>3s</td></tr>
    </tbody>
  </table>
</div>
```

## Anti-pattern

Don't render every storyboard's full scene list — that's the
deterministic composer's old behaviour and it produced 100KB of
report HTML for borderline-watchable storyboards. Pick one or two,
do them well.
