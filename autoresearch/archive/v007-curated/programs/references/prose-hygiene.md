# Prose Hygiene — AI-Writing Tells, Filler, and Transition Discipline

Sources (Corey Haines marketingskills repo):
- `seo-audit/references/ai-writing-detection.md`
- `copywriting/references/natural-transitions.md`
- `copy-editing` SKILL.md

Shared reference used by GEO (authoritative-tone Princeton lever), Monitoring (MON-8 concision + high insight-to-word ratio), and Storyboard (SB-5 voice-script line drafting). Applies to any prose GoFreddy produces: optimized page content, digest narratives, voice scripts, brief executive summaries.

AI-tell words and filler erode the exact signal GEO's authoritative-tone lever (+25%) and MON-8's insight-to-word ratio are supposed to carry. This reference is the blocklist + the substitutions.

---

## Plain-English alternatives (voice-script and body-copy lint)

Replace the word on the left with the word on the right. No exceptions unless the original is a genuine technical term.

| Replace | With |
|---------|------|
| utilize | use |
| leverage | use |
| implement | set up, build |
| facilitate | help |
| foster | grow, build |
| bolster | strengthen |
| underscore | show |
| streamline | simplify |
| enhance | improve |
| empower | help, let |
| orchestrate | arrange, run |
| delve into | look at |
| deep dive | walk through |
| unleash | release, free |
| harness | use |
| in order to | to |
| due to the fact that | because |
| at this point in time | now |
| in the event that | if |
| with respect to | about |

---

## AI-tell vocabulary blocklist

These are dead giveaways of LLM-generated prose. Strip them from every artifact.

**Adjectives to avoid:**
robust, comprehensive, pivotal, crucial, vital, transformative, cutting-edge, groundbreaking, seamless, holistic, synergistic, best-in-class, state-of-the-art, world-class, game-changing, next-generation, mission-critical.

**Nouns/verb phrases to avoid (without hard evidence):**
paradigm shift, ecosystem, journey, solution (as a generic noun), offering, deliverable, stakeholder (without context), thought leadership, value proposition (in prose — fine as a strategy term).

**Filler and intensifiers to cut:**
absolutely, actually, basically, certainly, clearly, definitely, essentially, extremely, fundamentally, incredibly, really, simply, truly, ultimately, very, just (as intensifier).

**Openers that signal "this was written by an LLM":**
- "In today's fast-paced / digital / evolving landscape…"
- "In an era where…"
- "In the ever-changing world of…"
- "It's important to note that…"
- "Let's delve into…"
- "When it comes to the realm of…"

---

## Transition-phrase blocklist vs. approved

**Avoid (overused AI transitions):**
- "That being said,"
- "It's worth noting that,"
- "At its core,"
- "To put it simply,"
- "This begs the question,"
- "Furthermore,"
- "Moreover,"
- "In conclusion," (as a paragraph opener)
- "As we all know,"
- "Without further ado,"

**Approved (carry argument without burning words):**
- "As a result,"
- "This leads to,"
- "The bottom line:"
- "Here's the key takeaway:"
- "What matters most:"
- "The difference:"
- "Because of this,"
- "In practice,"

---

## Em-dash discipline

Heuristic: **more than one em dash per page is a revise threshold**. LLMs over-use em dashes as all-purpose connectors; human writers use commas, colons, parentheses, or two sentences.

- One em dash: fine, usually for parenthetical emphasis.
- Two or more per ~400 words: rewrite. Replace with commas for parentheticals, colons for "here's what I mean" setups, parens for asides, or break into two sentences.

---

## Hedging vocabulary (for MON-2 severity calibration)

Monitoring confidence language. Use deliberately; don't hedge with generic softeners.

**Use when confidence is qualified:**
- "may," "might," "tends to," "generally," "in most cases," "evidence suggests," "the data indicates," "at least N of M sources."

**Avoid (these hedge too hard or not at all):**
- "could possibly," "might perhaps," "it seems like maybe" (over-hedge — reads uncertain without being informative)
- "clearly," "obviously," "definitely" (false certainty — violates MON-2 severity calibration)

---

## Seven-sweep edit pass order (applies to any artifact before commit)

From Corey's `copy-editing` skill. Run in order, not parallel:

1. **Clarity** — can a reader understand each sentence on first read? If not, rewrite.
2. **Voice** — does it sound like the author / brand / creator? Strip tone drift.
3. **So what** — for each paragraph, the "so what" test. If you can't answer, cut it.
4. **Prove it** — every claim has an anchor (number, source, quote, observed behavior). Unanchored claims are zeros.
5. **Specificity** — replace vague with specific. "Save time" → "Save 4 hours/week." "Many customers" → "2,847 teams."
6. **Emotion** — does the reader feel something specific? Boring passes clarity but fails outcome.
7. **Zero Risk** — [reserved — conversion-CTA-specific; **skip for GoFreddy narrative artifacts**. Retained here only for completeness of reference.]

For GoFreddy, sweeps 1-6 apply. Sweep 7 is a CRO-only rule and is intentionally excluded — it would dilute CQ-3 (honest positioning) and SB-4 (earned emotional transitions).

---

## Specificity examples (operationalizes CQ-1 / SB-2)

| Vague | Specific |
|-------|----------|
| "Save time" | "Save 4 hours/week" |
| "Many customers" | "2,847 teams" |
| "A long time ago" | "47 days ago" |
| "We processed a lot of revenue" | "We processed $47,329 in revenue" |
| "Big impact" | "$1.2M ARR in 90 days" |
| "Plenty of room to grow" | "22 of 50 seats filled" |
| "A while" | "11 minutes" |
| "Impressive growth" | "+34% WoW for 6 consecutive weeks" |

Rule: if the number is knowable and not a confidentiality violation, include the number.

---

## Rhythm: "Short. Breathe. Land." (for voice scripts and any narrated prose)

From Corey's `social-content/reverse-engineering.md`. A structural pattern for spoken or near-spoken lines:

- **Short.** One-beat line — punch, fact, or setup.
- **Breathe.** Slightly longer — carries the listener forward, gives room to absorb.
- **Land.** Short again — the payoff, rhythm closes, silence works.

Example:
> She opened the ledger.
>
> On page forty-seven, written in her own handwriting, was her name.
>
> She'd never seen this book before.

Use for storyboard `voice_script[n].line` beats. Also works for monitoring digest lead paragraphs.

---

## Application by domain

**GEO** — run sweeps 1-6 on every optimized page before `results.jsonl` `optimize` entry. The Princeton authoritative-tone lever (+25%) is cancelled by any AI-tell word; strip them.

**Monitoring** — run blocklist on digest prose. MON-8 concision and insight-to-word ratio are directly improved by cutting filler/intensifiers. Hedging vocabulary calibrates MON-2 severity.

**Storyboard** — run on every `voice_script[n].line`. Pair with existing SB-5 heuristics (strip adverbs that duplicate delivery). "Short. Breathe. Land." maps rhythm for narrated beats.

**Competitive** — apply to brief prose, especially executive summary (CI-1 single thesis survives hygiene pass).
