# Hook Patterns — Openings That Earn the Next Scene

Source: adapted from Corey Haines's `copywriting` and `social-content` skills.
URL: https://github.com/coreyhaines31/marketingskills/tree/main/skills/copywriting
URL: https://github.com/coreyhaines31/marketingskills/tree/main/skills/social-content

Use this when drafting the `voice_script[0]` (the hook beat) and scene 0 visual prompt. The first two seconds of a storyboard are load-bearing. These patterns are not templates to lift — they're taxonomies to check against ("what kind of hook is this actually, and is there a sharper version of it?").

---

## Four hook taxonomies

### Curiosity hooks
Open a cognitive loop the viewer feels pulled to close.
- "I was wrong about {common belief}."
- "The real reason {outcome} happens isn't what you think."
- "{Impressive result} — and it only took {surprisingly short time}."

**Storyboard use:** the opening scene frames something that doesn't yet make sense. The protagonist sees something the viewer can't interpret. By the end (SB-4 recontextualizing turn), the meaning locks in.

### Story hooks
Drop the viewer mid-incident, not pre-incident.
- "Last week, {unexpected thing} happened."
- "I almost {big failure}."
- "Three years ago I {past state}. Today, {current state}."

**Storyboard use:** the hook scene is *inside* the action, not before it. Not "a person walks toward a door" — "a hand hovering over a doorknob that shouldn't be warm."

### Value hooks
Promise a specific outcome the viewer wants, and be specific about the path.
- "How to {desirable outcome} without {common pain}."
- "{Number} {things} that {outcome}."
- "Stop {common mistake}. Do this instead."

**Storyboard use:** rare as a pure opener for narrative pieces, but strong for creators who explain/teach. Pair with a concrete demonstration in the first beat.

### Contrarian hooks
Contradict a belief the audience holds and then earn the contradiction.
- "Unpopular opinion: {bold statement}."
- "{Common advice} is wrong. Here's why."
- "I stopped {common practice} and {positive result}."

**Storyboard use:** works when the creator's brand is opinion-forward. The opening asserts something the audience disagrees with, and the rest of the story earns it.

---

## Specificity over vagueness (the SB-2 bar)

From the copywriting skill's core principles, but especially load-bearing for SB-2:

| Vague hook | Specific hook |
|------------|---------------|
| "A man finds something strange" | "A man finds his own name in a ledger dated before he was born" |
| "Save time on reporting" | "Cut your weekly reporting from 4 hours to 15 minutes" |
| "An unexpected discovery" | "The photograph was there on Tuesday. On Wednesday it wasn't" |

Rule: if the hook can describe a dozen different stories, it's not a hook — it's a category. Keep iterating until one sentence points at exactly one story.

---

## Writing-style rules that survive translation to dialogue (SB-5)

Corey's core copywriting principles. Apply these to `voice_script[n].line` before committing:

1. **Simple over complex.** "Use" not "utilize." "Help" not "facilitate."
2. **Specific over vague.** Cut "streamline," "optimize," "innovative." A voice actor can't perform a buzzword.
3. **Active over passive.** "She opened the ledger" not "The ledger was opened."
4. **Confident over qualified.** Remove "almost," "very," "really," "just."
5. **Show over tell.** Describe the moment, don't adverb it. "She whispered" > "she said quietly."
6. **Honest over sensational.** Fabricated stakes erode trust. Earn them.

Red flags that a voice-script line needs a rewrite:
- Jargon that would confuse a first-time viewer.
- A sentence doing more than one job.
- An exclamation point. (Delete it. Let delivery carry the emphasis — that's what SB-5's `delivery` field is for.)
- Adverbs substituting for direction ("angrily" instead of "clipped, through teeth").

---

## Content atom mindset (for SB-7 pacing)

A scene in a 55-second storyboard is equivalent to a "content atom" in Corey's repurposing framework — self-contained, interpretable without the surrounding structure. If a scene depends on the previous scene to make sense, it's not yet an atom. Good atom types, remapped for storyboard scenes:

| Atom type | What it looks like in a scene |
|-----------|-------------------------------|
| Quotable moment | One spoken line that would survive as a 15-second clip |
| Story arc | A self-contained beat (setup / turn / payoff) in a single scene |
| Tactical demonstration | An action that shows, not tells, a method |
| Contrarian take | A visible violation of the expected next move |
| Data/stat callout | A concrete number or artifact the camera lingers on |
| Behind-the-scenes texture | Unpolished, authentic detail that signals real |

Scenes that aren't one of these are usually transitions — and transitions rarely survive the eval's "AI-producible" (SB-6) and "earned transitions" (SB-3) checks.

---

## How to apply in a storyboard session

1. **During `plan_story`:** tag the logline's implicit hook type. Try rewriting the hook scene with two other taxonomies before locking one in — SB-8 (diversity of plans) rewards plans that don't all default to the same hook family.
2. **During `voice_script` drafting:** run each line through the six style rules. Strip any adverb that duplicates the `delivery` field.
3. **During scene prompting:** check each scene against the atom types. If it's a pure transition, either fold it into the next scene or give it content-atom work to do.
4. **Cross-check with SB-2:** if you can't rewrite your opening sentence to name exactly one story, the hook isn't specific enough yet.
