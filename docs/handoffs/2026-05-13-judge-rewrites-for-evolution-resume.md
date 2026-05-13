---
date: 2026-05-13
type: handoff (judge-design → evolution-runner)
status: ready-to-execute
prerequisites: read this doc + audit-findings-2026-05-13.md
estimated-work: ~1-2 hours to patch all 14 changes across resume-target variants
---

# Judge Rewrites for Evolution Resume — Handoff

## What this handoff is

A specification of 14 changes (13 anchor rewrites + 1 new criterion) to make to specific variant `workflows/session_eval_<lane>.py` files in the autoresearch archive **before resuming the next evolution generation**.

The rewrites raise Score-5 bars from "has X" to "X with sustained, falsifiable specificity" — addressing 13 ceiling-bound criteria (post-fix data: mean > 0.90, σ < 0.15) and adding X-9 to catch a known x_engine algorithm-penalty failure mode.

## Why these specific changes

Empirical discrimination analysis on post-2026-05-11 archived caches (after the axis-collapse fix shipped in PR #60) showed:

| Lane | Ceiling-bound criteria | Sample N |
|---|---|---|
| monitoring | MON-1, MON-3, MON-4, MON-5, MON-6 (5/8 criteria) | 5 |
| competitive | CI-1, CI-5, CI-6, CI-7 (4/8 criteria) | 3 |
| storyboard | SB-1, SB-2, SB-3, SB-5 (4/8 criteria) | 5 |
| geo | none — rubric is healthy (σ 0.21-0.36) | 32 |
| x_engine | none — but X-9 added for documented URL-penalty failure | 18 |

Source: `docs/brainstorms/2026-05-12-judge-design-deep-research/audit-findings-2026-05-13.md` + `/tmp/discrimination_analysis.py` output.

The 13 criteria are decorative as currently written — competent-baseline artifacts satisfy Score 5 uniformly, so the rubric doesn't separate "good" from "great" and evolution selects on noise.

## What's NOT changing (don't re-debate)

These were considered and rejected:

- **MON-2, MON-7, MON-8** — keep current; not ceiling-bound (σ > 0.20)
- **CI-2, CI-3, CI-4, CI-8** — keep current; not ceiling-bound or insufficient data
- **SB-4, SB-6, SB-7, SB-8** — keep current
- **All GEO criteria** — rubric is healthy (σ 0.21-0.36 across 32 samples)
- **All LinkedIn criteria** — no discrimination data; not changing
- **All MA criteria** — no post-fix data; not changing
- **All x_engine criteria except X-9 added** — rubric is healthy (σ 0.19-0.42)

Also rejected from earlier kernel proposals: MON-9 fabrication AUTO-CAP, MA-9 decision-density, GEO-9 named-expert, CI-9 triangulation — these are now superseded by the anchor rewrites covering the same failure modes more cheaply, OR judged empirically unwarranted on post-fix data.

## Where to apply

For each lane, the changes go to:

```
autoresearch/archive/<resume-target-version>/workflows/session_eval_<lane>.py
```

The `<resume-target-version>` is whichever variant the lane's `current.json` head points at as the parent for the next evolution generation. To find it:

```bash
cat autoresearch/archive/v<N>/programs/<lane>/current.json
# follow the "head" or equivalent pointer to the parent variant
```

When new generations clone from the patched parent, children inherit the new prose.

**Affected lanes:** monitoring, competitive, storyboard, x_engine. (geo + linkedin_engine + marketing_audit not affected.)

## The 14 changes

For each: criterion ID, why this criterion, what to replace, what to replace it with.

---

### MON-1 (monitoring)

**Why:** Current "quantify at least one metric" passes any digest with one number. Empirical: mean 1.000, σ 0.000 across 5 post-fix samples.

**Replace current prose:**
> "It tells you what changed this period. Surfaces the backward-looking delta — what is different compared to prior weeks or baseline expectations — with direction and magnitude, not just current state. \"Sentiment shifted from 41% to 62% positive\" not \"sentiment is 62% positive.\" For first-week digests, it identifies what in the current data deviates from what a naive observer would expect."

**With:**
> "Every material claim quantifies direction, magnitude, AND a named baseline (specific prior period with a calendar date, rolling-average with stated window, or named industry benchmark). Movements within historical variance (smaller than 2× recent week-to-week variation) are explicitly flagged as noise, not silently treated as signal. Trajectory classifications include a falsifiable next-period prediction with a stated fallback condition (\"if metric stays under X by date Y, the prediction was wrong\"). Surprises name the contradicted prior expectation — what did we expect, why, what does this challenge. Anti-gaming: cosmetic baselines (\"vs all-time average\" attached reflexively to every number), retroactive expectations invented to make data look surprising, and predictions without fallbacks all fail this."

---

### MON-3 (monitoring)

**Why:** Current "reader knows the highest-stakes development in first sentences" passes any digest with a lede. Empirical: mean 1.000, σ 0.000 across 5 samples.

**Replace:**
> "It names the one thing that matters most this week. Before the detail, the reader knows the single highest-stakes development and why it outranks everything else. If nothing extraordinary happened, it says that plainly."

**With:**
> "Within the first few sentences, the digest names the highest-stakes development AND explicitly compares it against the runner-up — naming what could have been the lede and explaining why it isn't. The priority call is falsifiable: a reader who disagreed could point at specific evidence the digest weighs incorrectly. Score 3: ranking is structural (it's first) without an argued case — a reader could rearrange sections and the digest still scans. Score 5: the priority argument exposes itself to challenge with named runners-up. If nothing extraordinary happened, the digest says so AND names what it tracked and ruled out."

---

### MON-4 (monitoring)

**Why:** Current "action items have who/when/consequence" passes any well-formatted digest. Empirical: mean 1.000, σ 0.000.

**Replace:**
> "Action items are specific, prioritized, and time-bound. Each one names who should act, by when, and what happens if they don't. Items that can't wait until next week are flagged as such."

**With:**
> "Each action item names a specific individual or role with single decision-making authority (not \"Brand team\" / \"Marketing\" — those name groups, not deciders). Each includes a bounded timeframe with an explicit terminating condition (\"by Friday 17:00 OR escalate to comms director\"), not just a deadline. Each states a consequence the responsible party would specifically want to avoid (\"continued silence leads Reuters to publish without our quote\"), not generic \"negative impact.\" Items are organized into explicit decision rules (\"if signal X appears by date Y, do Z\") rather than a flat urgency ranking. Anti-gaming: the same generic role applied to every item, or open-ended timeframes (\"next week,\" \"soon\"), fail."

---

### MON-5 (monitoring)

**Why:** Current "compound narratives where two signals reveal a risk" passes any digest with one cross-story sentence. Empirical: mean 1.000, σ 0.000.

**Replace:**
> "It connects dots the reader wouldn't connect themselves — and projects where those connections lead. Cross-story pattern recognition that surfaces compound narratives (two signals together reveal something neither shows alone) AND names upcoming catalysts, developing threats, or competitor moves that will shape next week. Forward projections are conditional and falsifiable, not vague (\"this could escalate\")."

**With:**
> "The digest surfaces at least one compound narrative where the joint signal across stories carries an implication neither story carries alone — a causal chain, trend amplification, or structural risk visible only at the cross-story level. Each compound narrative includes a forward projection with a specific next-period condition that would confirm or refute it. Score 3: noting co-occurring events (\"these happened in the same period\") without analytical synthesis — pattern is a label, not new information. Anti-gaming: unfalsifiable projections (\"we expect this to continue\") and patterns produced by re-categorizing existing stories under a shared label both fail."

---

### MON-6 (monitoring)

**Why:** Current "every number has interpretation + absent signals flagged" passes any well-written digest. Empirical: mean 1.000, σ 0.000.

**Replace:**
> "Every number answers \"so what?\" and every absence is examined. Quantifies with interpretation, not decoration. Flags where expected signal is missing — the campaign that generated no coverage, the competitor that went quiet — because silence is often the most important data point."

**With:**
> "Every statistic is paired with interpretation that names a specific client decision it would change — not restated description (\"32% increase represents significant growth\" fails). At least one statistic pre-empts a reader's likely alternative interpretation, naming what someone might wrongly conclude and why that reading fails (\"up 32% — but watch out, this is from a near-zero baseline, so absolute volume is still small\"). Absent expected signals are flagged AND interpreted (\"Competitor X went quiet, which is consistent with either Y or Z, and we'll know which by next period\"). Action implications include falsifiable next-period conditions for being wrong. Anti-gaming: bare comparison frames, advice without falsification conditions (\"monitor closely\"), and uninterpreted absence flags all fail."

---

### CI-1 (competitive)

**Why:** Current "brief has a thesis, sections serve the argument" passes any well-organized brief. Empirical: mean 1.000, σ 0.000.

**Replace:**
> "The brief has a thesis, not just findings. A single strategic argument organizes the entire document. Every section serves that argument. The reader finishes knowing one thing clearly, not twelve things vaguely."

**With:**
> "The brief states a single, client-specific, contestable thesis containing a strategic recommendation the client could accept or reject. The thesis passes the client-substitution test: replacing the client's name with a generic peer breaks the recommendation's specificity (recommendation only makes sense for THIS client given its specific capabilities). The brief presents at least one substantive piece of evidence-against, paired with an explicit reason the recommendation survives despite the counter — not a single dismissive sentence (\"while X, the client's broader platform compensates\"). Score 3: thesis is generic enough that any peer could fit it, or counter-evidence is defused immediately. Anti-gaming: \"challenges\" sections containing weak counter-arguments that don't actually complicate the recommendation fail."

---

### CI-5 (competitive)

**Why:** Current "client capability for each gap" passes any brief that names a client product. Empirical: mean 1.000, σ 0.000.

**Replace:**
> "It identifies asymmetric opportunities — gaps in the landscape that match the client's strengths. Not just what no one is doing, but what no one is doing that this client is uniquely positioned to own."

**With:**
> "For each named gap, the brief cites a client capability that passes the competitor-substitution test: replacing the client with its closest peer would break the strategic logic. The capability rests on something the client uniquely has (a specific data asset, a specific integration partner, a specific team composition, a specific market position) — not a generic label (\"our AI platform,\" \"our enterprise sales motion\"). Score 3: pairing is generic enough that a competitor with similar capabilities could pursue the same gap with the same logic. Anti-gaming: capability names without a single concrete asset behind them (a named product feature, a named partnership, a named customer base) fail."

---

### CI-6 (competitive)

**Why:** Current "uncomfortable truths survive editing" passes any brief with hedged challenges. Empirical: mean 1.000, σ 0.000.

**Replace:**
> "Findings contradict each other or the client's assumptions, and the brief says so. Uncomfortable truths survive editing. The brief is not optimized to make the client feel good about their current approach."

**With:**
> "The brief includes at least one finding that would prompt a real strategic decision if the client accepted it — naming a capability the client cannot quickly close, a market position eroding faster than the client's plans assume, or a structural shift that invalidates a piece of the client's stated strategy. The uncomfortable truth is specific enough that a stakeholder could plausibly veto its inclusion (\"we shouldn't say this\") rather than waving it through as standard caution. Score 3: uncomfortable findings narrowly scoped to not threaten the position (e.g., a competitor wins in a market the client doesn't compete in), or immediately neutralized within the same paragraph. Anti-gaming: hedge-defused counters (\"while X is concerning, broader strengths compensate\") in the same sentence fail."

---

### CI-7 (competitive)

**Why:** Current "top 2-3 actions clearly separated" passes any brief with a priority ranking. Empirical: mean 1.000, σ 0.000.

**Replace:**
> "The brief makes hard calls about what matters most. Not everything is Priority 1. The reader knows which 2-3 actions drive disproportionate impact and which findings are interesting but not urgent."

**With:**
> "The top 2-3 actions are ranked AND the brief makes an explicit case for the sequencing — naming what's lost by doing lower-ranked actions first, what's gained by doing the top action despite its costs. The case is specific enough that a stakeholder could rebut it by challenging the brief's tradeoff weighting. Score 3: ranking rests on labels (\"Priority 1\" / \"Priority 2\") without explaining why doing 1 first beats doing 2 first. Anti-gaming: applying multiple priority axes (\"Priority 1, Quick Win, Strategic\") without forcing a single sequence, or labeling everything \"high impact,\" both fail. The ranking must be a commitment, not a categorization."

---

### SB-1 (storyboard)

**Why:** Current "story feels like the creator made it" passes any plan that references pattern data. Empirical: mean 1.000, σ 0.000.

**Replace:**
> "The story feels like the creator made it — not like someone studied the creator and generated a plausible imitation. Voice, obsessions, worldview, and the specific way they surprise an audience are all present."

**With:**
> "The plan cites at least 3 distinct creator-specific pattern details, each meeting all three tests: source-cited (names which prior creator output the reference draws from — episode, video title, or pattern_id), passes the creator-substitution test (replacing the pattern data with a different creator's would break the reference), AND plan-shaping (drives a concrete storytelling choice — scene order, surprise mechanism, character reaction — not just a name-drop in setup paragraph). Score 3: references abstract enough that a different creator's pattern data could plausibly fit. Anti-gaming: 3 creator-specific name-drops concentrated in the first paragraph followed by a generic plan body fails — references must distribute across the plan's actual structural choices."

---

### SB-2 (storyboard)

**Why:** Current "hook is irreplaceable" is subjective; passes any specific hook. Empirical: mean 1.000, σ 0.000.

**Replace:**
> "The hook is irreplaceable — a concrete, specific image or sentence that could not come from any other story. Something you would describe to a friend in one breath. The mechanism may be an impossible concept, raw emotional vulnerability, absurd juxtaposition, or visual impossibility — what matters is specificity and irreplaceability, not which mechanism achieves them."

**With:**
> "The hook is immediately arresting AND passes the substitution test: removing or changing the specific creator, setting, or stakes would break the hook's appeal. The hook depends on this story's specific context for its impact — at least one element a competing creator could not replicate without copying this story's specific premise. Score 3: hook has a specific element but could exist in a different story unchanged — identifiable, not irreplaceable. Anti-gaming: generic high-stakes phrasing (\"a man with everything to lose,\" \"the impossible choice\") that could attach to any story fails."

---

### SB-3 (storyboard)

**Why:** Current "emotional transitions earned by beats" passes any plan with structured emotional_map. Empirical: mean 1.000, σ 0.000.

**Replace:**
> "Every emotional transition in the story is earned by a specific beat, not just declared in metadata. The emotional arc described in the plan is actually produced by the story structure — through concrete revelations, actions, or juxtapositions — not asserted as \"the viewer now feels dread\" without a beat that produces dread."

**With:**
> "Each emotion in emotional_map maps to a specific beat containing a diegetic cause — a revelation, action, or juxtaposition that would produce that emotion in a viewer who didn't yet know what to feel (cause must be on-screen content, not narration about feelings). Transitions are justified by content the viewer just received, with the transition's logic visible in the preceding beat — not by the emotional_map asserting them. The climactic emotional moment rests on context unique to THIS story, not on a generic dramatic structure (sacrifice, recognition, reversal) any story in the genre could use. A viewer reading beats in order with the emotional_map hidden would experience the predicted emotions inevitably. Anti-gaming: beats that say \"the viewer feels X\" without a cause the viewer would experience fail."

---

### SB-5 (storyboard)

**Why:** Current "voice script + audio design specificity" passes any plan with delivery directions. Empirical: mean 1.000, σ 0.000.

**Replace:**
> "The voice script is performable speech with designed silence. A voice actor could perform it cold, and the audio design — including what is deliberately absent, processed, or contrasted — carries as much story as the visuals."

**With:**
> "Voice script delivery directions vary line-to-line to track each line's rhetorical purpose — not the same instruction (\"intense,\" \"slow and measured\") attached to every dramatic line. Silence/absence is specified as a timed beat with a stated narrative function (\"0:42-0:45 three seconds silence, marking the moment the character realizes\") — not just \"dramatic pause.\" Vocal-quality shifts map to specific story turns with explicit story-event tie. At least one audio element (music cue, SFX, silence) carries story information the visuals and voice do NOT — a sound revealing what the camera doesn't show, a music shift contradicting dialogue's surface meaning. Anti-gaming: music labeled \"tension\" or \"release\" that just underscores what visuals already show fails."

---

### X-9 (x_engine) — NEW CRITERION

**Why:** Empirical: Phase C of judge audit found 3/3 archived 2026-05-12 x_engine drafts violate by including external URLs in [BODY] or [REPLY]. Buffer 2026 18.8M-post analysis: median engagement ~0% for non-Premium link posts since March 2025. X's open-source `TweetUrlMultiplier` confirms 30-50% algorithm penalty. None of existing X-1..X-6 catch this.

**Add as new CRITERIA entry:**
> "X-9": (
>     "The [BODY] block and any [REPLY] blocks contain no external URLs (http://, https://, "
>     "bare domains like 'example.com/path', or markdown link syntax). URLs to x.com / "
>     "twitter.com are exempt. Citations name sources inline (\"per the 2024 Buffer analysis\") "
>     "rather than embedding links. Drafts with disguised redirects (URL shorteners, \"link "
>     "in bio,\" \"DM for the PDF,\" QR codes, pasted reference codes) fail — the substrate "
>     "must not route the user off-platform indirectly. Rationale: Buffer 2026 18.8M-post "
>     "analysis shows ~0% median engagement for non-Premium link posts since March 2025; X's "
>     "open-source TweetUrlMultiplier confirms 30-50% algorithm penalty. Any [BODY]/[REPLY] "
>     "URL is a structural reach-failure regardless of body-text quality."
> ),

**Also add to PER_STORY_CRITERIA / lane structure as appropriate** — match the existing X-1..X-6 wiring.

**Also update `autoresearch/archive/<resume-target-version>/workflows/session_eval_x_engine.py`** to add X-9 to whatever lane-spec includes it (mirror the existing X-1..X-6 inclusion pattern in that file).

---

## Verification after patching

1. **File-level check:** run `python -c "from workflows.session_eval_<lane> import CRITERIA; print(len(CRITERIA))"` from inside the patched variant directory. Counts should be unchanged for monitoring/competitive/storyboard; x_engine count should increase by 1.

2. **Per-fixture eval check:** run one fixture per affected lane through the patched variant's `evaluate_session.py`. The resulting `.last_eval_cache.json` per-criterion `feedback` strings should reference the new prose elements ("named baseline" / "substitution test" / "falsifiable" / "anti-gaming"). Direct evidence the new prose reaches the judge.

3. **Post-generation discrimination check:** after the next 1-2 evolution generations complete, re-run `/tmp/discrimination_analysis.py` (or equivalent) against the new cache files. Expected: σ widens on rewritten criteria (MON-1/3/4/5/6, CI-1/5/6/7, SB-1/2/3/5). If σ stays flat, the rewrite calibration needs tuning — surface back to judge-design for retune (don't tune unilaterally).

## Rollback path

If any rewrite produces unexpectedly harsh scoring (everything collapses to Score 1):

1. The original CRITERIA prose is preserved in this handoff doc — paste it back into the affected variant's `workflows/session_eval_<lane>.py`.
2. RUBRIC_VERSION will regenerate to the old hash; cached scores under the new prose's bucket stay in their bucket.
3. Surface the regression back to judge-design with the specific criterion + observed score distribution.

## Out of scope for this handoff

- Substrate-level AUTO-CAP wiring (X-9 enforces algorithm penalty via judge prompt only; not at composite-cap level)
- The HTTP API rubrics in `src/evaluation/rubrics.py` — already committed at `896f366`, serves a different code path
- Cross-lane behavior changes
- New criteria beyond X-9
- Score-grain changes (stays 3-level: 0 / 0.5 / 1.0)
- LinkedIn / MA / GEO rubrics (not affected — no rewrites)

## Related artifacts

- Long-form v2 prose (committed): `src/evaluation/rubrics.py` at commit `896f366`
- Audit findings: `docs/brainstorms/2026-05-12-judge-design-deep-research/audit-findings-2026-05-13.md`
- Earlier kernel proposals (now rejected): `docs/brainstorms/2026-05-12-judge-design-deep-research/phase-d-master-spec-v2.md` (Phase D v3 in place)
- Discrimination analysis script: `/tmp/discrimination_analysis.py`
- Validation script (for post-generation σ check): `scripts/validate_rubric_rewrites.py` (not yet committed; use as reference)
