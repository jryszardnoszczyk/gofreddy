# Edit-Pass Order + Specificity Rules for Storyboard

Sources (Corey Haines marketingskills repo):
- `copy-editing` SKILL.md
- `social-content/references/reverse-engineering.md`

Use when drafting `voice_script[n].line` and scene prompts. Gives storyboard's SB-2 (hook specificity), SB-3 (earned transitions), and SB-5 (performable voice) a concrete edit order and a specificity taxonomy, complementing `hook-patterns.md` (taxonomies) and `prose-hygiene.md` (AI-tell blocklist).

---

## The seven-sweep edit order (run 1-6; skip 7)

**Run in order, not parallel.** Each sweep assumes the prior passed.

1. **Clarity.** Can a first-time listener understand the line without rewinding? If not, rewrite.
2. **Voice.** Does the line sound like {client}? Strip tone drift from neighboring lines.
3. **So what.** For each line, answer "so what?" If you can't, cut the line.
4. **Prove it.** Every claim anchored in observed behavior, a number, a named thing. Unanchored = zero.
5. **Specificity.** Replace vague with specific (see taxonomy below).
6. **Emotion.** Does the listener feel a specific thing at this beat? If not, the line is neutral — either intentional or a problem.
7. ~~Zero Risk (conversion-CTA framing).~~ **Skip for storyboard.** Zero-risk language (guarantees, risk-reversal, "try it free") contradicts SB-3 (earned emotional transitions) and SB-4 (recontextualizing turn). Explicitly excluded.

---

## Specificity taxonomy (SB-2 made operational)

The difference between a hook that gets cited and a hook that doesn't is specificity. These are the exact transformations:

| Vague | Specific |
|-------|----------|
| "Save time" | "Save 4 hours/week" |
| "Many customers" | "2,847 teams" |
| "A long time ago" | "47 days ago" |
| "Big revenue" | "$47,329 in revenue" |
| "A while" | "11 minutes" |
| "A lot of people" | "Lived with it for 6 years" |
| "Growing fast" | "+34% week-over-week for six weeks" |
| "Popular / trusted" | "Picked by 3 of 5 Fortune 100 biotech R&D teams" |
| "Strange / weird / unusual" | "A ledger dated before he was born, in his own handwriting" |
| "Struggled" | "Missed payroll three months running" |

**Rule:** if the number is knowable and not a confidentiality violation, include the number. If the object is describable, describe it. If the moment is reconstructable, name one concrete detail from it.

---

## "Short. Breathe. Land." rhythm (SB-5 structural discipline)

A three-beat rhythm for narrated lines. Map to `voice_script[n]` beats:

- **Short.** One-beat line — punch, fact, or setup. ≤7 words.
- **Breathe.** A slightly longer line — carries listener forward, gives room to absorb. 15-25 words.
- **Land.** Short again — the payoff; silence works after.

Example (storyboard voice script):

> *Short.* She opened the ledger.
>
> *Breathe.* On page forty-seven, written in her own handwriting, she found her name and a date she'd never lived.
>
> *Land.* She'd never seen this book before.

This rhythm is the structural pattern behind most successful creator narration — even when not strictly enforced, deviation from it should be deliberate.

---

## Plain-English substitutions for voice scripts

From `prose-hygiene.md`, but especially load-bearing for spoken lines (voice actors can't perform a buzzword):

| Replace | With |
|---------|------|
| utilize | use |
| leverage | use |
| implement | set up, build |
| facilitate | help |
| foster | grow |
| streamline | simplify |
| enhance | improve |
| in order to | to |
| due to the fact that | because |
| at this point in time | now |

Apply in Sweep 2 (Voice).

---

## Pattern-codification schema (for `analyze_patterns` phase)

When recording creative patterns in `patterns/*.json`, Corey's reverse-engineering framework suggests a Pattern / Example / Why-it-works triple for each identified element. Can be adopted as a light schema extension:

```json
{
  "video_id": "...",
  "patterns": {
    "hook_pattern": {
      "type": "curiosity | story | value | contrarian",
      "example": "exact first-line quote from video",
      "why_it_works": "specific mechanism — opens loop, drops mid-incident, promises outcome, contradicts belief"
    },
    "format_pattern": {
      "type": "narrative | demo | list | rant | essay",
      "example": "what structure the video follows",
      "why_it_works": "..."
    },
    "voice_pattern": {
      "type": "specific-over-vague | short-breathe-land | emotion-first | understatement",
      "example": "representative line from the video",
      "why_it_works": "..."
    }
  }
}
```

Feeds SB-1 (creator authenticity) by anchoring the storyboard's voice choices in named patterns from the source.

---

## Reverse-engineering workflow (maps to `analyze_patterns`)

Corey's 6-step framework, translated to the storyboard `analyze_patterns` phase:

1. **Identify top N videos** (by view-count velocity, not absolute views — normalize for channel size and age).
2. **Collect the set** — already what pattern-analysis does via `/v1/analyze/videos`.
3. **Rank by engagement rate** (views × engagement_rate vs. views alone).
4. **Codify hook / format / voice patterns** using the schema above.
5. **Layer voice rules** — specific-over-vague, short-breathe-land, emotion-first.
6. **Convert pattern knowledge into story plans.**

Step 3 (ranking by engagement rate, not raw view count) is the step most storyboard sessions skip — and it's the one that separates "what {client} makes" from "what {client} makes that lands."

---

## Application by storyboard phase

**`analyze_patterns`** — codify patterns using the triple schema (Pattern / Example / Why-it-works). Rank by engagement rate.

**`plan_story`** — tag each hook against `hook-patterns.md` taxonomy. Run the specificity taxonomy on the logline; iterate until the sentence points at exactly one story.

**`voice_script` drafting** — run sweeps 1-6 on each line. Apply Short/Breathe/Land rhythm. Strip adverbs that duplicate `delivery` field. Substitute plain English per this reference.

**`ideate` (generate storyboard)** — before calling `/v1/video-projects/storyboard`, verify all `voice_script[n].line` entries pass Sweeps 3 (So-what) and 5 (Specificity).

**`report`** — run `prose-hygiene.md` blocklist on narrative prose in `report.md`.
