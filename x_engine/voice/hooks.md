# Hooks — proven formats + no-go openers

Source-of-truth for the writer prompt's first-line strategy. Curated from §2 creators in research doc and from JR's pillars.

## Format A — Single observation

> "[surprising specific fact]. [implication or take]."

**Examples (study structure):**
- "I write 3 tweets a day across 4 accounts and I haven't actually typed a tweet myself in 5 months. claude writes them. I edit. I post. 12 minutes total."
- "raw scraping the web is not research. If the information is not structured, your other agents can't use it."

**When to use:** angle is one specific claim, JR has lived it, no thread needed.

---

## Format B — Numbered breakdown (5-7 items)

```
[topic statement]:

1. [specific point]
> [one-sentence elaboration]

2. [specific point]
> [one-sentence elaboration]

...
```

**When to use:** angle has 3-5 sub-points that compound. Cap at 7.

**Avoid the listicle anti-pattern:** "5 reasons why X is the future of Y" — generic and slop-coded. Use only when each item is concretely named (a tool, a step, a layer).

---

## Format C — Layer / stack exposition

```
[domain] in [year]:

1. [layer] (where [function] lives)
> [tool] [does specific thing]
> [tool] [does specific thing]

2. [next layer]
> ...
```

**Source pattern:** @MichLieben's GTM 4-layer stack thread.

**When to use:** the angle is genuinely a multi-layer architecture and JR can name specific tools per layer.

---

## Format D — Contradiction / pattern-break

> "[obvious assumption everyone holds]. but [specific evidence] says the opposite. [implication]."

**When to use:** JR has genuine contrary evidence. **Reject if it's just a hot take with no proof — that's slop.**

---

## Format E — Tool / file / repo announcement (JR's own work)

> "[just shipped/built/wired up] [specific thing]. [what it does in one line]. [link or repo]."

**When to use:** announcing JR's own work. Be specific about what it does; skip the marketing register.

---

## Format F — Quote-tweet take

The quoted post provides context. JR's text is purely his addition.

> "[take or extension that adds something the quoted post doesn't]"

**When to use:** the quoted post is genuinely worth amplifying AND JR has a non-trivial layer to add.

**Avoid:** quote-tweeting for "this 👆" / "exactly this" — empty engagement.

---

## NO-GO openers (writer must reject these — also enforced by slop_gate.py)

| Banned opener | Why |
|---|---|
| "Most people don't realize..." | Top-1 AI-slop tell |
| "Here's the thing..." | Top-2 AI-slop tell |
| "It turns out..." | Generic, no specificity |
| "Bookmark this" | Engagement bait |
| "Save this for later" | Engagement bait |
| "Not [X]. [Y]." | The em-dash reversal AI loves |
| "In a world where..." | Generic opener |
| "If you're not [X], you're already behind" | Hype register |
| "🚨 BREAKING:" | Crypto-Twitter register |
| "🧵👇" / "Save this thread 🔖" | Thread-promo bait |
| "Hot take:" | Telegraphing the take instead of stating it |
| "Unpopular opinion:" | Same |
| "PSA:" | Same |
| "Pro tip:" | Boomer-LinkedIn register |

## NO-GO mid-sentence patterns

- Em-dashes ( — ) — period or comma instead
- "X-coded" / "[noun]-pilled" — trend register
- "absolutely cooked" / "absolutely demolished" — hype register
- "this is the way" / "the future is here" — generic
- "It's not [X]. It's [Y]." — formulaic AI parallel structure
- "If you're [X], you'll love this" — copy register

## Length rules

- **Single tweet target:** 180-260 chars. Sub-180 is fine when the take is sharp; over 260 invites cut-offs and "...show more".
- **Thread:** 3-7 segments. Never longer than that for X content. If you have more, it's a blog post or a Substack.
- **First segment of a thread:** must work standalone if no one clicks "show this thread".
