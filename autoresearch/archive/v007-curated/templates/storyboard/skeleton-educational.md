# Educational storyboard skeleton (U8)
#
# Cold-start template for `STORYBOARD_FORMAT_MODE=educational` — explainer
# / how-to / informational shapes. Compared to narrative mode, SB-3
# (earned transitions) + SB-4 (recontextualizing turn) are RELAXED;
# SB-6 (AI-producibility of info-density visuals) is UPWEIGHTED.
#
# Agents COPY this file as the first story plan, then iterate.

```json
{
  "story_id": "REPLACE-WITH-DESCRIPTIVE-SLUG",
  "format_mode": "educational",
  "platform_target": "REPLACE-WITH-PLATFORM",
  "hook_taxonomy": "REPLACE-WITH-ONE-OF: curiosity | value | contrarian",
  "duration_seconds": 60,
  "scene_count": 5,
  "scenes": [
    {
      "scene_id": "s01",
      "camera_motion": "static",
      "prompt": "REPLACE — concrete problem-statement visual; informational not narrative",
      "voice_script": [
        {
          "line": "REPLACE — one-sentence problem framing (≤15 words)",
          "delivery": "REPLACE — direct, declarative tone",
          "silence_after_ms": 0
        }
      ]
    },
    {
      "scene_id": "s02",
      "camera_motion": "REPLACE",
      "prompt": "REPLACE — first info-payload; diagram or screen-capture preferred",
      "voice_script": [
        {
          "line": "REPLACE — concrete data point or named mechanism",
          "delivery": "REPLACE",
          "silence_after_ms": 100
        }
      ]
    },
    {
      "scene_id": "s03",
      "camera_motion": "REPLACE",
      "prompt": "REPLACE — second info-payload; build on s02",
      "voice_script": [
        {
          "line": "REPLACE — second concrete claim with attribution",
          "delivery": "REPLACE",
          "silence_after_ms": 100
        }
      ]
    },
    {
      "scene_id": "s04",
      "camera_motion": "REPLACE",
      "prompt": "REPLACE — synthesis visual; data viz or comparison frame",
      "voice_script": [
        {
          "line": "REPLACE — synthesis sentence tying s02+s03 to the problem",
          "delivery": "REPLACE",
          "silence_after_ms": 200
        }
      ]
    },
    {
      "scene_id": "s05",
      "camera_motion": "REPLACE",
      "prompt": "REPLACE — takeaway / next-action visual",
      "voice_script": [
        {
          "line": "REPLACE — actionable closer (≤10 words)",
          "delivery": "REPLACE",
          "silence_after_ms": 0
        }
      ]
    }
  ]
}
```

## Educational-mode requirements

- **SB-6 AI-producibility**: every scene's `prompt` describes content
  that current AI video models can render — info-density visuals
  (diagrams, screen-captures, animated data visualization, simple
  product shots). NO complex multi-character scenes.
- **Info density**: each non-opening scene carries ≥1 concrete data
  point, named mechanism, or attributed claim. "Studies show" without
  inline source is a SB-2 Score-3.
- **SB-3 / SB-4 relaxation**: educational shapes don't need an
  emotional arc; recontextualizing turn is optional. The reweighting
  in workflows/storyboard.py applies this automatically.

## Allowed content surfaces (educational)

`informational_visuals`, `diagrams`, `screen_captures`, `data_visualization`.
The lane fails-loud at start (D17) if the client's `content_denylist`
denies all four. Klinika's denylist (`clinical_visuals`,
`before_after_imagery`) does NOT trigger D17 here — informational
visuals are still available.
