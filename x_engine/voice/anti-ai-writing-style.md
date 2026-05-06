# Anti-AI Writing Style — v1 starter

> **Status: STARTER v1.** Replace with @rubenhassid's full version (~1,168 lines) once JR downloads from how-to-ai.guide. This file is the LAST READ before generation. The writer + critic both check against it.

## Goal

Filter AI-generated patterns out of JR's posts. Default rule: **if removing the phrase doesn't lose meaning, the phrase was filler.**

## Rule priority (when rules collide)

1. Be accurate
2. Be clear
3. Be specific
4. Sound human
5. Use style only when it improves the sentence

## §1 — Banned opening phrases

These are tier-1 AI tells. Reject any draft that starts with one.

- "Most people don't realize..."
- "Here's the thing..."
- "Here's what I learned..."
- "Here's why..."
- "It turns out..."
- "Imagine this:"
- "Picture this:"
- "Did you know..."
- "Have you ever wondered..."
- "Let me tell you about..."
- "I want to talk about..."
- "Today I want to discuss..."
- "In a world where..."
- "If you're not [X], you're already behind"
- "If you're a [role], you know..."
- "Hot take:"
- "Unpopular opinion:"
- "PSA:"
- "Pro tip:"
- "🚨 BREAKING:"
- "ICYMI:"

## §2 — Banned mid-sentence phrases

- "dives into" / "delves into"
- "navigates the landscape of"
- "the realm of"
- "in the realm of"
- "at the intersection of"
- "in today's fast-paced world"
- "ever-evolving landscape"
- "rapidly changing"
- "cutting-edge"
- "game-changer" / "game-changing"
- "revolutionary"
- "groundbreaking"
- "tapestry"
- "embark on a journey"
- "unleash" / "unlock" / "unleashing"
- "harness the power of"
- "leverage" (verb form, when "use" works)
- "supercharge"
- "needle-mover"
- "10x" / "100x" (when not literal)
- "low-key" / "no-cap" (Gen-Z register, wrong for JR)
- "actually" used as filler

## §3 — Banned closing patterns

- "It's not [X]. It's [Y]." parallel structure
- "Not [X]. [Y]."
- "What do you think?" generic prompt
- "Drop your thoughts below"
- "Like + RT if you agree"
- "Follow for more"
- "Save this thread 🔖"
- "Bookmark this"
- "Tag a friend who needs this"

## §4 — Banned punctuation

- **Em-dashes (—).** Use commas, periods, or new sentences. Em-dashes are the single most reliable AI tell in 2026.
- **En-dashes (–) used as em-dashes.** Same rule.
- **Excessive ellipses...** End sentences with periods.
- **Smart quotes ("…")** when the rest of the document uses straight quotes.

## §5 — Banned structural patterns

- **Numbered lists with the same opener for every item** ("1. First, [verb]. 2. Second, [verb]. 3. Third, [verb].")
- **Tricolon for everything** ("X, Y, and Z" repeating in every sentence)
- **"It's [adjective]. It's [adjective]. It's [adjective]." anaphora**
- **Generic 5/7/10 listicles** without each item being concretely named

## §6 — Banned hedge patterns

These are AI-overcautious filler. Replace with direct statements.

- "It's important to note that..."
- "It's worth noting that..."
- "While it's true that [X], it's also..."
- "However, that's not to say..."
- "It's worth mentioning that..."
- "It should be noted that..."

(These are different from honest hedging — "I think", "my read is", "probably" — which are FINE.)

## §7 — Banned verbs

- "elevate" (when "improve" works)
- "transform" (when "change" works)
- "empower" (when "help" works)
- "facilitate" (when "let" works)
- "utilize" (use "use")
- "leverage" (use "use")
- "ideate" (use "think")
- "operationalize"
- "orchestrate" (when "run" works — exception: when literally about agent orchestration)

## §8 — Banned framings

- **"In conclusion"** / "To wrap up" / "To summarize"
- **"At the end of the day"**
- **"When all is said and done"**
- **"The bottom line is"** (use "bottom line:" only when actually summarizing data)

## §9 — JR-specific

(JR — add patterns that specifically annoy you here)

- TODO

## §10 — When the rule conflicts with the message

If the most accurate phrasing happens to use a banned word in a context where it's the precise word, allow it. **Spirit over letter.** Example: "the agent leverages the observation" might be fine if "leverages" is technically what's happening. Example: "the harness orchestrates 4 lanes" is fine — orchestration is literally what it does.

The deterministic regex in `pipeline/slop_gate.py` will flag, but the ambiguous cases get an LLM judgment via `prompts/slop_check.md`.
