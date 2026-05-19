---
draft_id: <draft-001>
topic: <article topic from $ARTICLE_ENGINE_TOPIC>
platform: blog
length_bracket: standard           # standard | deep_dive
voice_persona: <slug from $ARTICLE_ENGINE_VOICE_PERSONA_REF>
word_count: <count after writing>
meta_description: <140-160 chars; SEO snippet>
---

# <H1 headline matching the article topic + falsifiable angle>

<Opening paragraph (first 60 words deliver a falsifiable claim, named
subject, or concrete result — testable against the body's main
thesis). Story-led; first-person; lived-work specific. Anchor on
something from the voice persona's corpus or the source material.>

## <First subhead; introduces the problem>

<Body paragraphs 2-4 sentences each. Three to four concrete claims
per 1,000 words — numbers, named entities, dated events. Every
attributive claim carries an inline [N] reference.>

## <Second subhead; mechanism>

<Continue the problem → mechanism → evidence → implication arc.
Hero image brief embedded below; inline image briefs sprinkled where
the prose needs a visual anchor.>

> **Hero image brief:** <describe the visual; aspect ratio 16:9;
> alt text + composition notes for the image_engine handoff.>

## <Third subhead; evidence>

<Cite at least 2-3 sources via inline `[N]`. Each [N] resolves to a
named source in the reference list at the end. Verifier-checkable
URLs preferred; voice.md entity references are also valid.>

> **Inline image brief:** <describe; alt text + composition notes.>

## <Fourth subhead; implication>

<Close with what the reader should do differently. Specific +
testable. Not "schedule a demo" — pattern they can run themselves.>

## TL;DR

- <Bullet 1 — concrete>
- <Bullet 2 — concrete>
- <Bullet 3 — concrete>

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
