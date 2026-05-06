# Hooks — long-form-first format library

Source-of-truth for the writer prompt. **Default bracket is BUILD-IN-PUBLIC (500-900 chars).** SHARP (250-300) and CASE-STUDY (1000-1500) are the special cases.

Curated 2026-05-06 from analysis of >1000-like AI/agent/marketing posts on X (see `docs/research/2026-05-06-x-content-engine.md` §2 + the in-line research call that produced this update).

---

## BUILD-IN-PUBLIC (500-900) — the workhorse

This is what every shipped-an-AI-agent post in our niche looks like in 2026. Use as the default unless the angle is genuinely a one-line take or a long case study.

```
[Hook line — concrete result, sensory image, or industry signal]
[2-3 sentences: why now / market context / who it's for]

Here's how the system works:
→ [step 1 + named tool]
→ [step 2 + named tool]
→ [step 3 + named tool]
→ [step 4 + named tool]
→ [optional step 5]

[Authority anchor — JR's actual work from voice/about-me.md]
[Outcome metric — % / $ / count / duration]
[Soft CTA — "DM if you want the skill" / "repo in reply" / nothing]
```

**Variations on the structural pivot line** (line that introduces the bullets):
- "Here's how the system works:"
- "Here's what's actually inside:"
- "The setup is small:"
- "The breakdown:"
- "What I keep coming back to:"
- "Here's the loop:"
- "Layers I run on top:" (gofreddy-flavor)

**Substantive bullets discipline:**
- 3-5 bullets, never more than 7
- Each bullet = `[verb or named component] + [what it does in one short clause]`
- Each bullet ≤ 120 chars
- Use `→` not `-` (the right-arrow signals "and then" — `-` is more LinkedIn-coded)
- Bullets named tools/repos/components inline, no @-mention required

**Authority anchor library** (lived-work positions JR can deploy honestly):
- "I run this same loop in gofreddy's autoresearch."
- "In our marketing audit lens catalog…"
- "In my harness work, [pattern]."
- "I keep hitting the same wall in [agency / harness / Claude Code] setups…"
- "After running [autoresearch / Hermes / multi-provider] in production…"

**Outcome metrics he can claim** (from voice/about-me.md):
- 149-lens marketing audit catalog
- 413 tests on the autoresearch loop
- 30+ commits since cbf01f5 on origin/main
- 1,534-line audit pipeline plan
- ~$0/run inference cost (codex/ChatGPT subscription)

---

## SHARP (250-300)

For genuine one-line takes. No bullets. No padding.

```
[Concrete claim or counter-future, one sentence]
[One sentence of supporting reasoning OR implication. Name a tool/number.]
```

**Examples to model on (from real high-engagement posts in our niche):**

> Eric Schmidt said the agent era rewards builders. The credential is whatever you shipped this week, not the brand on your resume.

> $0/run is the inference cost JR's tweet pipeline reports today. When the LLM is your ChatGPT subscription, the per-token economics flip.

**Use SHARP when:**
- The take is genuinely sharp and one-line
- There's no walkthrough to expose
- You want the post to be a quote-tweet seed for replies

**Don't use SHARP when:**
- The angle has a system, a fix, or a walkthrough — that's BUILD-IN-PUBLIC
- You're tempted to pad (every "but you could explain more" → BUILD-IN-PUBLIC)

---

## CASE-STUDY (1000-1500)

Long-form narrative. Use sparingly — only when the angle has substance for a long read.

```
[Hook line]
[2-3 paragraphs: what we did, what happened, sensory/quoted detail]

[Mechanism: 3-5 sentences OR small bullet block]

[Numbers paragraph: timeline beats with $/%/count anchors]

[Implication / close — one paragraph, no question mark]
```

**Earn the length with:**
- A literal walkthrough (not a generalization)
- Quoted material (an LLM's own words, a user reaction, a vendor pricing line)
- Sensory or unexpected detail ("the room jumped from 35 dB to 93 dB")
- Numbers across a timeline (not one stat)

**Reject CASE-STUDY when:**
- You don't have walk-through substance — it'll read padded → BUILD-IN-PUBLIC
- The post is mostly opinion → SHARP

---

## NO-GO openers (writer must reject — also enforced by `slop_gate.py`)

| Banned opener | Why |
|---|---|
| "Most people don't realize..." | Top-1 AI-slop tell |
| "Here's the thing..." | Top-2 AI-slop tell |
| "It turns out..." | Generic, no specificity |
| "Bookmark this" / "Save this" | Engagement bait |
| "Not [X]. [Y]." | The em-dash reversal AI loves |
| "In a world where..." | Generic opener |
| "If you're not [X], you're already behind" | Hype register |
| "🚨 BREAKING:" | Crypto-Twitter register |
| "🧵👇" / "Save this thread 🔖" | Thread-promo bait |
| "Hot take:" / "Unpopular opinion:" / "PSA:" / "Pro tip:" | Telegraphing instead of stating |
| "Comment 'X' to get the [skill/repo/template]" | Engagement bait CTA |
| "Tag a friend who needs this" | Engagement bait |

---

## NO-GO mid-sentence patterns

- Em-dashes (—) — period or comma instead
- "X-coded" / "[noun]-pilled" — trend register
- "absolutely cooked" / "absolutely demolished" — hype register
- "this is the way" / "the future is here" — generic
- "It's not [X]. It's [Y]." parallel structure — formulaic
- "If you're [X], you'll love this" — copy register
- "supercharge", "game-changer", "leverage", "elevate", "transform"
- "delve into", "dive into"

---

## Length rules

- **SHARP target:** 220-300 chars
- **BUILD-IN-PUBLIC target:** 600-900 chars (sweet spot for AI-agent posts)
- **CASE-STUDY target:** 1100-1500 chars
- **Never pad to hit a length.** Bracket should match content density.

## Bullet rules

- **3-5 bullets max** (7 is the upper bound — anything more reads listicle)
- `→` not `-` for action-step bullets
- `-` only for feature/capability lists (rare)
- Numbered (1. 2. 3.) only when the order matters and there are exactly N steps
- Each bullet ≤ 120 chars

## URL placement

External URLs go in `first_reply_text` (a separate companion post JR posts as the first reply), NOT in the main post body. X penalizes external links in the main post by 30-50% reach.

Exception: in-line @-mention of a tweet author is fine.
