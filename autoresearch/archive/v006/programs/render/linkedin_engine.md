# LINKEDIN_ENGINE lane

Sibling to X_ENGINE — same shape, different length brackets +
`hashtags` META key.

## What's in the session_dir

- `drafts/<draft_id>.md` — YAML frontmatter (incl. `hashtags` count) +
  `[BODY]` + `[META]` (META adds `hashtags` formatted string).
  Length brackets: `short_take` (500-900), `thought_leader` (1500-2500),
  `case_study` (2500-3000).
- `drafts/<draft_id>.eval.json` — LI-1..LI-6 per-criterion scores
- `angles/<angle_id>.json` — angle the agent worked from

## What's interesting

Mostly same as X_ENGINE. LinkedIn-specific signals:

1. **Hashtag adherence** — LI-6 ideal is 3-5 hashtags. Small table
   showing per-draft hashtag count vs band; 0-2 or 6+ are suboptimal.
2. **Bracket distribution** — when drafts span all 3 brackets, surface
   the spread; when only short_take, flag it.

## Style

Professional blue + Source Serif 4 (theme `linkedin_engine`). Quoted
post bodies deserve serif so they read like a real post.

## Exemplar

```html
<div class="rprt-meta-pattern">
  <div class="label">↳ strongest draft</div>
  <div class="rprt-spotlight">
    <strong>draft-101 · short_take · 745 chars · KEEP (8.0)</strong>
    <div class="rprt-pull-quote">
      <div class="qtext">Three agency owners I work with all dropped
      four-figure retainers in March. Same story across all three: the
      client built an internal AI team, ran a head-to-head bake-off,
      and the agency lost on speed.</div>
      <div class="qattr">— drafts/draft-101.md (angle: agency AI pricing)</div>
    </div>
    <p>4 hashtags lands in the LI-6 ideal band (3-5).</p>
  </div>
</div>
```

Same as X_ENGINE: pick a representative + a curation angle. Let the
appendix dump all drafts.
