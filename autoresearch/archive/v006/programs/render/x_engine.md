# X_ENGINE lane — renderer guidance

The X_ENGINE lane writes ship-eligible X (Twitter) drafts in JR's voice
against a single angle. 3-5 drafts per session across length brackets
sharp / build / case_study.

## What's in a session_dir

| Path | What it is |
|---|---|
| `drafts/<draft_id>.md` | The deliverable — YAML frontmatter + `[BODY]/[BODY]` + `[META]/[META]` |
| `drafts/<draft_id>.eval.json` | Per-draft eval (KEEP / REVISE / DROP + per-criterion scores) |
| `angles/<angle_id>.json` | The angle the agent worked from (cached at session start) |

Frontmatter fields: `draft_id`, `angle_id`, `platform=x`, `length_bracket`,
`char_count`, `voice_pillar`. META keys: `hook`, `authority_anchor`,
`specific_number`, `attribution`.

## What's interesting

1. **Ship-eligible count + ratio** — "3 of 5 ship-eligible (KEEP)" is
   the headline metric. A `rprt-stat-grid` of (drafts written,
   ship-eligible, REVISE, voice_pillars covered) is a strong opener.
2. **The strongest single draft** — pick the highest-scoring KEEP
   draft. Surface its [BODY] in a `rprt-pull-quote` (clearly attributed
   to the draft_id), with the [META].hook above it as a strong-element.
3. **Bracket distribution** — a donut chart of brackets shows
   coverage spread (sharp/build/case_study). If only one bracket is
   covered, that's a finding — flag it.
4. **X-1..X-6 per-criterion average** — when eval JSONs have scores
   per criterion (X-1 voice, X-2 specificity, X-3 hook, X-4
   slop-free, X-5 structural richness, X-6 cross-cohort), a small
   bar chart of average per criterion shows where the cohort is
   strong/weak.

## Style note

X-engine theming is punchy compressed black-and-amber
(`.rprt-page.rprt-theme-x_engine`). Lean tight: short paragraphs,
the post text deserves Georgia-serif treatment to read like a real
post would, not a dashboard widget.

## Exemplar

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ session at-a-glance</div>
  <div class="rprt-stat-grid">
    <div class="rprt-stat-tile">
      <div class="num">5</div><div class="label">drafts</div>
    </div>
    <div class="rprt-stat-tile">
      <div class="num">3</div><div class="label">ship-eligible</div>
    </div>
    <div class="rprt-stat-tile">
      <div class="num">2</div><div class="label">brackets covered</div>
    </div>
    <div class="rprt-stat-tile">
      <div class="num">8.4</div><div class="label">avg eval</div>
    </div>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ strongest draft</div>
  <div class="rprt-spotlight">
    <strong>draft-001 · sharp · 268 chars · KEEP (8.4)</strong>
    <div class="rprt-pull-quote">
      <div class="qtext">Most pre-seed CTOs raise before the demo. The
      ones who ship first get the stronger term sheets. I watched a
      friend close $2M in 6 days after he tweeted the live product.
      The deck killed nothing. The demo killed everyone else.</div>
      <div class="qattr">— drafts/draft-001.md (angle: ship-before-fundraise)</div>
    </div>
    <p>Hook lands in 7 words. Authority anchor is first-person
    lived-work ("watched a friend") — passes X-2's hard floor for
    specific lived-work claims that trace to voice.md.</p>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ per-criterion average</div>
  <div class="rprt-chart">
    [[chart:bar:X-1_voice=8.6,X-2_specificity=8.0,X-3_hook=8.8,X-4_slop_free=8.4,X-5_structural=7.9,X-6_cross_cohort=7.2|title=Cohort criterion averages]]
    <p>X-6 (cross-cohort variety) is the cohort's weakest dimension —
    two of the five drafts share the "founder-watching-friend-ship"
    pattern. Either the angle is repetitive or the next session needs
    voice-pillar diversity guidance.</p>
  </div>
</div>
```

## Anti-pattern

Don't render every draft's full body. Pick ONE representative. The
deterministic appendix renders all drafts in a card layout below.
Your job is curation, not enumeration.
