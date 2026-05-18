# Narrative storyboard skeleton (U8)
#
# Cold-start template for `STORYBOARD_FORMAT_MODE=narrative` — the pre-U8
# default shape. Mirrors linkedin_engine v040's cold-start fix:
# prescriptive skeleton lets the agent produce structurally-valid drafts
# on first iteration instead of inventing the shape from scratch.
#
# Agents COPY this file as the first story plan, then iterate. The
# structural gate validates against this shape; rubrics SB-1..SB-8
# score the prose quality.

```json
{
  "story_id": "REPLACE-WITH-DESCRIPTIVE-SLUG",
  "format_mode": "narrative",
  "platform_target": "REPLACE-WITH-PLATFORM",
  "hook_taxonomy": "REPLACE-WITH-ONE-OF: curiosity | story | value | contrarian",
  "duration_seconds": 60,
  "scene_count": 4,
  "scenes": [
    {
      "scene_id": "s01",
      "camera_motion": "static",
      "prompt": "REPLACE — concrete visual; an irreplaceable opening image",
      "voice_script": [
        {
          "line": "REPLACE — speakable speech, ≤7 words, hook the audience",
          "delivery": "REPLACE — direction the voice actor reads",
          "silence_after_ms": 0
        }
      ]
    },
    {
      "scene_id": "s02",
      "camera_motion": "REPLACE — static | pan | dolly | tracking | handheld | zoom",
      "prompt": "REPLACE — raise stakes; visual + audio cue",
      "voice_script": [
        {
          "line": "REPLACE — 15-25 word development of the hook",
          "delivery": "REPLACE",
          "silence_after_ms": 200
        }
      ]
    },
    {
      "scene_id": "s03",
      "camera_motion": "REPLACE",
      "prompt": "REPLACE — the recontextualizing turn (SB-4); ending changes meaning of opening",
      "voice_script": [
        {
          "line": "REPLACE — payoff line",
          "delivery": "REPLACE",
          "silence_after_ms": 0
        }
      ]
    },
    {
      "scene_id": "s04",
      "camera_motion": "REPLACE",
      "prompt": "REPLACE — final visual; recontextualizing image",
      "voice_script": [
        {
          "line": "REPLACE — one-beat closer ≤7 words",
          "delivery": "REPLACE",
          "silence_after_ms": 0
        }
      ]
    }
  ]
}
```

## Narrative-mode requirements

- **SB-2 hook specificity**: scene `s01.prompt` must describe an
  irreplaceable image. Generic ("a hand reaches for a phone") is a
  Score-3. Specific ("a hand reaches for a phone glowing with the
  caller's name dated before they were born") scores higher.
- **SB-4 recontextualizing turn**: `s03` and `s04` must change the
  meaning of `s01`. Not just resolution — re-interpretation.
- **SB-5 performable voice script**: lines are speakable, not prose.
  Use `delivery` for tone; use `silence_after_ms` for designed pauses.
- **SB-3 earned emotional transitions**: every emotional shift PRODUCED
  by a beat (revelation, action, juxtaposition), never declared in
  metadata. "Viewer feels dread" is a zero.

## Allowed content surfaces (narrative)

`depicted_scenes`, `voiceover_with_b_roll`, `animated_visualizations`.
The lane fails-loud at start (D17) if the client's `content_denylist`
denies all three.
