# Brand-authority storyboard skeleton (U8)
#
# Cold-start template for `STORYBOARD_FORMAT_MODE=brand_authority` —
# voice-corpus-anchored thought-leadership shapes. SB-1 (creator
# authenticity) + SB-5 (performable voice script) UPWEIGHTED; SB-7
# (platform pacing) softened.
#
# REQUIRES `STORYBOARD_VOICE_PERSONA_REF` env var to be set; the lane
# fails-loud at start if it's missing — brand_authority anchors on
# the persona's voice_rules + style_anchors.
#
# Agents COPY this file as the first story plan, then iterate.

```json
{
  "story_id": "REPLACE-WITH-DESCRIPTIVE-SLUG",
  "format_mode": "brand_authority",
  "platform_target": "REPLACE-WITH-PLATFORM",
  "voice_persona_ref": "REPLACE-WITH-PERSONA-SLUG",
  "style_anchor": "REPLACE — pick one of the persona's style_anchors by name",
  "duration_seconds": 90,
  "scene_count": 4,
  "scenes": [
    {
      "scene_id": "s01",
      "camera_motion": "static",
      "prompt": "REPLACE — brand-anchored opening; image that signals the persona's POV",
      "voice_script": [
        {
          "line": "REPLACE — opener that quotes / paraphrases the voice_corpus",
          "delivery": "REPLACE — match persona's voice_rules tone",
          "silence_after_ms": 200
        }
      ]
    },
    {
      "scene_id": "s02",
      "camera_motion": "REPLACE",
      "prompt": "REPLACE — case-study / lived-example visual; brand imagery",
      "voice_script": [
        {
          "line": "REPLACE — first-person specific lived-work claim (must be in voice corpus)",
          "delivery": "REPLACE",
          "silence_after_ms": 150
        }
      ]
    },
    {
      "scene_id": "s03",
      "camera_motion": "REPLACE",
      "prompt": "REPLACE — synthesis visual referencing persona's anchor concept",
      "voice_script": [
        {
          "line": "REPLACE — frame the takeaway in persona's terms (use style_anchor)",
          "delivery": "REPLACE",
          "silence_after_ms": 250
        }
      ]
    },
    {
      "scene_id": "s04",
      "camera_motion": "REPLACE",
      "prompt": "REPLACE — closing brand visual; restate authority signal",
      "voice_script": [
        {
          "line": "REPLACE — one-line implication for the audience (≤12 words)",
          "delivery": "REPLACE",
          "silence_after_ms": 0
        }
      ]
    }
  ]
}
```

## Brand-authority requirements

- **SB-1 creator authenticity (HARD FLOOR)**: every first-person
  specific lived-work claim referencing a named entity (client,
  project, tool stack) MUST be in the loaded `voice_corpus`. Drift
  between the draft and the corpus = automatic factual penalty.
  Mirrors the x_engine / linkedin_engine voice substrate convention.
- **SB-5 performable voice script**: voice lines paraphrase or quote
  voice_corpus content. Use `delivery` to match persona's
  voice_rules (e.g. Dr. Maria's "lead with medical mechanism, then
  patient-experience benefit").
- **Style anchor**: pick ONE of the persona's `style_anchors` and
  declare it in the story_id metadata. The agent's pattern-codification
  pass references this anchor by name.

## Allowed content surfaces (brand_authority)

`voice_corpus_quotes`, `brand_imagery`, `case_study_visuals`. The lane
fails-loud at start (D17) if the client's `content_denylist` denies all
three. Klinika's `clinical_visuals + before_after_imagery` denylist
does NOT trigger D17 — voice_corpus_quotes + brand_imagery remain
available.
