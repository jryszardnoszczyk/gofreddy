# LINKEDIN_ENGINE lane — renderer guidance

The LINKEDIN_ENGINE lane writes ship-eligible LinkedIn drafts in JR's
voice against a single angle. Sibling to X_ENGINE; same shape but
different length brackets + a `hashtags` META key.

## What's in a session_dir

| Path | What it is |
|---|---|
| `drafts/<draft_id>.md` | The deliverable — YAML frontmatter + `[BODY]/[BODY]` + `[META]/[META]` |
| `drafts/<draft_id>.eval.json` | Per-draft eval (KEEP / REVISE / DROP + per-criterion scores) |
| `angles/<angle_id>.json` | The angle the agent worked from |

Frontmatter: `draft_id`, `angle_id`, `platform=linkedin`, `length_bracket`,
`char_count`, `voice_pillar`, `hashtags` (count). META keys: `hook`,
`authority_anchor`, `specific_number`, `attribution`, `hashtags`
(formatted string).

Length brackets: `short_take` (500-900), `thought_leader` (1500-2500),
`case_study` (2500-3000).

## What's interesting

Mostly the same as X_ENGINE — refer to that file's "What's interesting"
list and substitute LinkedIn brackets + criteria.

LinkedIn-specific signals:

1. **Hashtag adherence** — the LI-6 ideal is 3-5 hashtags. A small
   list / pill row showing each draft's hashtag count vs the band
   surfaces compliance fast. Drafts with 0-2 or 6+ hashtags are
   suboptimal.
2. **Thought-leader length distribution** — when drafts span all
   three brackets, surface the spread; when only short_take is
   covered, flag it as missing depth.

## Style note

LinkedIn-engine theming is professional blue + Source Serif 4
(`.rprt-page.rprt-theme-linkedin_engine`). The body of any quoted
post deserves the serif treatment so it reads like a real post.

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
      and the agency lost on speed. The pattern was identical: the
      agency was billing for "strategy + execution" but the in-house
      team only paid for execution.</div>
      <div class="qattr">— drafts/draft-101.md (angle: agency AI pricing)</div>
    </div>
    <p>4 hashtags lands in the LI-6 ideal band (3-5). Authority anchor
    is direct-conversation ("agency owners I work with") — passes
    LI-2's first-person specific lived-work floor.</p>
  </div>
</div>

<div class="rprt-meta-pattern">
  <div class="label">↳ hashtag adherence</div>
  <table class="rprt-key-table">
    <thead><tr><th>Draft</th><th>Hashtags</th><th>Band</th><th>Verdict</th></tr></thead>
    <tbody>
      <tr><td><code>draft-101.md</code></td><td>4</td>
          <td>3-5 ideal</td>
          <td><span class="rprt-metric">in-band</span></td></tr>
      <tr><td><code>draft-102.md</code></td><td>2</td>
          <td>1-2 suboptimal</td><td>below ideal — REVISE</td></tr>
    </tbody>
  </table>
</div>
```

## Anti-pattern

Same as X_ENGINE — don't enumerate every draft. Pick a representative
and a curation angle (bracket coverage, hashtag adherence, voice
pillar spread). Let the appendix dump all drafts.
