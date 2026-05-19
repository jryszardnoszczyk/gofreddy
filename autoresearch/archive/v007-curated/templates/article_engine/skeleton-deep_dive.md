---
draft_id: <draft-003>
topic: <article topic from $ARTICLE_ENGINE_TOPIC>
platform: blog
length_bracket: deep_dive          # 2,200-3,500 words; technical case study
voice_persona: <slug from $ARTICLE_ENGINE_VOICE_PERSONA_REF>
word_count: <count after writing>
meta_description: <140-160 chars; SEO snippet anchoring the case study>
---

# <H1: case-study headline; names the subject + the outcome>

<Opening paragraph: story-led; first 60 words deliver the falsifiable
claim that the case study substantiates. Anchor on a specific named
entity (project / company / system) from voice.md.>

## Context

<Why this case matters. What the reader is hoping to learn. Set the
problem with specific numbers + dated events. Two to three concrete
claims here alone.>

## The setup

<What the operator-reader needs to understand before the mechanism
matters. Architecture diagram brief, baseline metric, or "before"
state. Inline image brief here if a diagram clarifies.>

> **Inline image brief:** <describe; alt text + composition notes.>

## What we tried

<Mechanism section. Specific tools, prompts, configs. This is where
deep_dive earns its length — it's the section where the operator-
reader gets actionable detail they couldn't find in a standard blog
article. Three to five concrete claims here.>

```<language>
<code or config snippet showing the mechanism>
```

## What happened

<Evidence section. Numbers, dated events, before/after metrics. Cite
at least 3 sources via inline [N]. If you ran an experiment, describe
the sample size, control, and effect size.>

> **Hero image brief:** <describe; aspect ratio 16:9; alt text +
> composition notes for the image_engine handoff.>

## What we learned

<Implication section. Specific. Testable. What the operator-reader
should do differently. Avoid "schedule a demo" bait — describe a
pattern they can run themselves.>

## TL;DR

- <Bullet 1 — concrete; ideally a one-line summary of the mechanism>
- <Bullet 2 — concrete; the outcome metric>
- <Bullet 3 — concrete; the generalizable lesson>

## References

[1] <source name>, <URL>
[2] <source name>, <URL>
[3] <source name>, <URL>

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "<H1 verbatim>",
  "author": "<persona display name>",
  "datePublished": "<YYYY-MM-DD>",
  "image": "<hero image URL or placeholder>"
}
```
