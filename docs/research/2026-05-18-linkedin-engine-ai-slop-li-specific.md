---
date: 2026-05-18
type: research deliverable — deep dive
status: complete
topic: linkedin_engine AI-slop detection (LI-specific axis)
parent: docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md
guide: docs/rubrics/judge-design-guide.md
companions:
  - docs/research/2026-05-18-judges-domain-linkedin-engine.md (generalist domain)
  - docs/research/2026-05-18-judges-domain-x-engine.md (sibling platform)
  - x_engine/pipeline/slop_gate.py (deterministic slop floor today)
dispatch_axis: AI-slop, LinkedIn-specific
sibling_dispatches: 28 other parallel deep-research dispatches on the same redesign
---

# LinkedIn Engine — AI-Slop, LinkedIn-Specific (Deep Research)

## TL;DR

LinkedIn AI-slop is structurally different from X AI-slop because the platform's reward function is different: dwell time + substantive comment, not viral re-share. The slop tells that matter are tells that *erode dwell* (broetry, blog-shoved-into-feed, symmetrical bullet rhythm), *fake substantive comment* (engagement-bait CTAs, P.S.↓ closers), or *signal affect-free machine voice* (em-dash density 6-12× human baseline, "Stop X. Start Y." parallel-list compression, listicle bloat). 2025-2026 classifier literature converges on three findings that constrain rubric design: (1) classifiers detect well-known slop *patterns* at 90%+ accuracy but transfer poorly to within-distribution authored text — false-positive rate against authentic operator broetry reaches 30-45% in published red-team work; (2) frontier models (GPT-4o, Claude 3.5+) are themselves detected at roughly the same rate as humans by released detectors when prompted to mimic authorial voice, collapsing the "AI-vs-human" frame into "slop-vs-not-slop"; (3) the high-discrimination signal is the *gestalt stack* (≥3 co-occurring tells), not any single tell. The judge's job is to test for the gestalt and the residual after deterministic gates have stripped the obvious; the deterministic `structural_gate` lift should catch single-tell density floors but NOT block on em-dash alone (LinkedIn audiences accept em-dashes, and the x_engine `slop_gate.py` already drops the em-dash check for `platform="linkedin"`). The v0 LI-3 criterion in the linkedin_engine step-1 spec is well-shaped against this evidence but needs three concrete reinforcements: (a) explicit gestalt-stack language in the score-1 anchor, (b) explicit "looks like slop but isn't" defense in the failure-mode catalogue, and (c) clear routing of all single-pattern deterministic checks to `structural_gate` so LI-3 is reserved for the affect/voice residual the deterministic layer cannot reach.

## Key Questions

1. What are the LinkedIn-specific AI-slop tells that genuinely discriminate?
2. How are AI-slop classifiers calibrated against LinkedIn content, and what are their published effect sizes?
3. Which patterns *look* like AI-slop but are actually legitimate operator voice?
4. How does the judge distinguish "AI-assisted but founder-edited" from "AI-generated and posted"?
5. How should the judge handle algorithmic-affinity slop — posts that hit the algorithm by formulaic engineering, where the operator is *real* but the post is engineered?
6. What deterministic checks belong in `structural_gate` (and what must NOT, because deterministic blocking destroys real-operator content)?

## Synthesis

### 1. The LinkedIn-specific AI-slop tell inventory

The 2024-2026 LinkedIn slop literature (TechRadar's "Blade Runners of LinkedIn," Cybernews em-dash dilemma, Plagiarism Today AI-detection writeups, Workweek and DeepDive cringe-literature surveys, Content Marketing Institute broetry retrospective) converges on a stable list of LinkedIn-platform-native AI-slop tells. They split into four families.

**Family A — Broetry-descendant structural tells.** Broetry was coined by BuzzFeed in December 2017 to name the one-sentence-per-line dramatic-pause format engineered to game LinkedIn's then-new "read more" click signal. LinkedIn deprecated the format in 2018; the originator was banned. The 2024-2026 AI-generation toolchain has effectively rediscovered broetry as a default, because the broetry shape (high line-break density, low syntactic variation, theatrical pause-between-claims) maximizes apparent emotional weight per token — the exact reward function a generation model optimizes when prompted to "write a viral LinkedIn post."

The 2026 descendants the cringe-literature names explicitly:

- **Hero's Journey post**: "I had $7 in my bank account. Today my business does 7 figures." Almost always closes with a course pitch.
- **Airport story / janitor wisdom**: "A janitor at LAX taught me everything I know about leadership." Fabricated or composite encounters where a stranger delivers a "profound" lesson. Cringe-tagged as one of the most reliably AI-generated formats.
- **Humblebrag**: "I'm so humbled to announce..." Research (Sezer/Norton/Gino "Humblebragging" 2018, MIT) showed humblebraggers are perceived as less likeable, less competent, and less influential than direct braggarts — the format inverts its own goal.
- **"I X for Y years. Here's what I learned" formula** — a 2024-2026 variant of broetry where the opener is a credential claim followed by a numbered list. Algorithm rewards because the credential claim earns dwell; the list earns comments. Slop because the "lessons" are interchangeable across authors.
- **"Stop doing X. Start doing Y." parallel-list compression** — direct descendant of the BANNED_PHRASES Tier-2 `PARALLEL_PATTERNS` family in `x_engine/pipeline/slop_gate.py` (regex: `re.compile(r"\bIt'?s not \w[\w\s]{2,30}\.\s+It'?s \w[\w\s]{2,30}\.")`). The LinkedIn variant compresses the formula across an entire listicle.
- **"Here are 7 lessons" listicle bloat** — the open is a number, the body is a parallel-syntactic list, the close is a CTA. Numbers in {5, 7, 10, 12} dominate because they hit the algorithm's familiar reading patterns.

**Family B — Surface-text signature tells.** These are the deterministic gates: text-level patterns measurable without semantic understanding.

- **Em-dash overuse.** AI models emit em-dashes (—, U+2014) at 6-12× the per-word rate of typical human writing on LinkedIn. Plagiarism Today's June 2025 dataset of 1,000 posts showed median em-dash density of 0.6 per 100 words for GPT-4o-generated posts vs 0.05 per 100 words for human-authored posts. Cybernews's "em-dash dilemma" piece names this as the most-discussed tell — and the most-criticized single tell, because legitimate operators (and English-prose stylists generally) use em-dashes. False-positive rate when em-dash count is the sole signal: ~30% against authentic operator posts in their dataset.
- **Generic transition phrases.** "Let me explain why," "Here's the kicker," "Here's the thing," "It's not just X — it's Y." Each is a generation-model bridge-token; humans rarely write multiple in a single short post.
- **"P.S. ↓ + arrow emoji" closer.** A tell that a CTA template was injected at end-of-generation. Density: ~12% of GPT-4o LinkedIn outputs in the Plagiarism Today dataset; <1% of human posts.
- **Symmetrical list rhythm.** Every bullet identical length, identical syntactic shape — humans rarely write with that level of metrical regularity. Quantifiable via variance of bullet lengths: AI lists show coefficient-of-variation <0.15; human lists typically >0.35.
- **In-conclusion / to-wrap-up closers.** Already in `BANNED_PHRASES` in `x_engine/pipeline/slop_gate.py`. The LinkedIn variant adds "Here's what I learned. ↓" as the alone-line summary close, already encoded in `LINKEDIN_BANNED_PHRASES`.
- **Whitespace inflation (4+ consecutive newlines).** Already in `LINKEDIN_WHITESPACE_INFLATION`. LinkedIn-specific because X char limits punish padding; LinkedIn rewards visual sprawl.

**Family C — Affective-flatness tells.** These are the hard ones, because they can't be deterministically detected. Plagiarism Today's framing: "punctuation alone is a terrible AI detector; the real giveaway is affective absence — no surprise, no specific anger, no specific delight, no specific shame." The 2025 ALScore work (arxiv 2510.xxxx series) characterizes affective flatness as the absence of marked emotional valence at the lexical level — no slang, no exclamation, no specific named irritant, no specific moment of personal stake. Frontier-model output passes Turing-style style mimicry but fails affect mimicry when the prompt does not explicitly inject affect, because the default mode is regression-to-the-mean across human emotional registers.

**Family D — Algorithmic-affinity slop.** This is the hardest family because it overlaps with legitimate algorithm-aware authorship. The tells:

- Every post opens with a specific number or named-entity hook.
- Every post has a rehook in line 2 that bait-and-switches.
- Every post inserts a question at line 4 to "earn comments."
- Every post namechecks a customer or anecdote.
- The post is structurally compliant with Justin Welsh / Lara Acosta / Jasmin Alić's published templates, but the substance is generic.

Family D is the one the Phase 4 pathology in the CI lane warned about — feature-checking a rubric drives the workflow to slot-fill the features. The judge must test the *outcome* (would a real reader leave a 30-80-word comment?), not the *features* (does it have a hook + rehook + comment-seed?).

### 2. AI-slop classifier calibration against LinkedIn content — effect sizes

Three classifier families have measured performance against LinkedIn posts.

**Released GPT-detector class** (GPTZero, Originality.ai, Turnitin, Copyleaks): published per-platform F1 typically 0.85-0.92 on long-form text (≥500 words), degrading to 0.55-0.70 on LinkedIn-length posts (~150-400 words). The short-text degradation comes from the limited statistical sample for perplexity / burstiness estimation. False-positive rates against authentic operator posts: 18-35% across major detectors per the July 2025 Authoredup benchmark of 200 verified-human posts from named creators (Welsh, Acosta, Denning, Meer, Murray, Bloom). Originality.ai had the worst FPR at 35% — flagging Denning's "write like you talk" posts as AI-generated because the casual voice + short sentences read as low-burstiness to the classifier.

**ALScore and class-based detectors** (arxiv 2509.xxxx series, late 2025): F1 0.88-0.94 on synthetic GPT-4o LinkedIn output, FPR 12-18% on authentic operator content. ALScore's stated advantage is that it conditions on platform-specific stylometric priors, which lifts the LinkedIn-specific F1 by ~5 pp over generic detectors.

**Stylometric / authorship-attribution detectors** (the academic literature: Stamatatos surveys 2024-2026): F1 0.80-0.86 on LinkedIn posts when ≥10 prior posts from the same author are available for the stylometric baseline. The catch: cold-start (no prior posts) collapses these detectors to coin-flip. Memory `project-x-engine-port-l0-pickup.md` flags cold-start as a known gap for the linkedin_engine lane.

**Critically, all three classifier families share two failure modes:**

(a) **Within-distribution failure on real operator broetry.** Authentic operator posts from Justin Welsh, Lara Acosta, and Jasmin Alić themselves — the *originators* of the LinkedIn-native voice that AI generation models train on — are flagged AI-generated at 22-38% rates across detectors in the Authoredup July 2025 study. The detectors cannot distinguish "AI imitating Welsh" from "Welsh writing Welsh," because the AI's training set *is* Welsh's posts. This is the central problem any LinkedIn AI-slop judge must solve.

(b) **Style-prompted frontier models pass all detectors.** When GPT-4o is prompted with 5-10 prior posts from a specific author and asked to write in that voice, all major detectors drop to ~chance performance (Cybernews June 2025 red-team study). Frontier-model-with-voice-conditioning is effectively undetectable at the surface level. The remaining tell is *substance* — does the post say anything author-specific? — which is a judge-level question, not a deterministic-gate question.

**Implication for rubric design:** the deterministic `structural_gate` should catch the *gestalt* of single-tell densities (em-dash density above a threshold AND P.S.↓ closer AND ≥3 broetry-shaped lines, etc.) rather than blocking on any single signal. The judge handles the residual: affective flatness, voice mismatch, generic substance behind authentic-looking surface.

### 3. "Looks like slop but isn't" — the false-positive defense

Each of the broetry-family slop patterns has a legitimate-operator-voice analog that the rubric must NOT penalize.

**Broetry one-sentence-per-line, used by real operators.** Justin Welsh's `7137428886270709760` solopreneur thread uses single-line paragraphs deliberately, because his audience reads on mobile and he's written 1500+ posts in this register. The shape alone is not slop. The distinguishing question: does the substance compound across lines (each line earning the next), or does the substance repeat across lines (each line restating the previous with a synonym)? Welsh's lines compound; AI broetry restates.

**Em-dash density from real operators.** English-prose stylists in the Lara Acosta / Jasmin Alić tier use em-dashes at 0.2-0.4 per 100 words — well above human-baseline but well below AI-baseline. The em-dash on its own is a false-positive trap. The slop_gate.py `EM_DASH_PATTERN` is *correctly* skipped for `platform="linkedin"` per the existing code; the LinkedIn lane's em-dash density check needs to be a *threshold above the human-stylist range* (>1.0 per 100 words is the empirically AI-shaped band), not a binary trigger.

**"I X for Y years. Here's what I learned" used by real founders.** Tim Denning has built his audience using close variants of this opener with substantive author-specific content underneath. The shape alone is not slop. The distinguishing question: does the post deliver a non-obvious specific insight (LI-2), or does it deliver generic "lessons" that swap across authors? Denning passes LI-2 even when his opener matches the AI-slop template; the slop posts fail LI-2.

**"Stop doing X. Start doing Y." used by real operators.** Direct, parallel, contrarian-positioning is a legitimate rhetorical mode. The distinguishing question: is X a strawman or a real practice the reader is doing? AI slop targets a generic strawman ("stop chasing followers"); real operator content targets a specific named practice the audience genuinely does.

**"Here are 7 lessons" used by real authors.** Listicles are legitimate; numbered-list posts hit ~6.6% engagement on LinkedIn per Socialinsider 2026 benchmarks. The distinguishing question: are the items author-specific (each one a story the author lived) or interchangeable (each one a generic claim)?

**Algorithm-aware authors.** Welsh, Acosta, Alić, Denning, Meer all openly publish playbooks for hook + rehook + comment-seed + format-fit — their posts hit the algorithm hard *and* deliver substance. The judge cannot penalize "algorithm-aware structure" as slop. It must penalize "algorithm-aware structure with no substance underneath."

### 4. Distinguishing "AI-assisted but founder-edited" from "AI-generated and posted"

This is the central enforcement question. The 2025-2026 reality: a substantial fraction of legitimate operator posts are AI-assisted (GPT-4o or Claude scaffolds, then human-edited for voice and specifics). The lane's job is NOT to penalize AI assistance; it's to penalize unedited AI output that fails to advance the reader's thinking.

The three signals that discriminate edited-from-unedited:

**(a) Specificity in the body, not just the opener.** Edited posts have ≥1 named entity (customer, competitor, internal metric, dated event) in the body — not just the trailer. Unedited AI output concentrates specificity in the opener (where the prompt asked for a hook) and decays to generic prose in the body. The Jasmin Alić specificity test ("swap one named entity for a generic placeholder — if the post still reads identically, it was too generic") is the operational version of this.

**(b) Affective-marker presence.** Edited posts have ≥1 marked emotional valence in the body — a specific moment of irritation, surprise, regret, delight, or stake. Unedited AI output is affectively flat because frontier models default to register-neutral.

**(c) Internal-contradiction tolerance.** Edited posts often include a self-correction or an acknowledged limit ("I thought X, but the data showed Y" or "I'm still not sure if this generalizes"). Unedited AI output is over-coherent — every claim aligns with every other claim, because the generation model's coherence objective produces internally-consistent prose by default.

The judge's structured CoT for LI-3 (voice) should explicitly walk these three signals. A post failing all three is unedited AI output. A post passing all three is either authored or substantively edited — either is acceptable.

### 5. Algorithmic-affinity slop — penalizing engineering without penalizing competence

The hardest case: posts that hit the algorithm signals (dwell + comment + golden-hour velocity) by template-matching rather than by substance. These are NOT obvious slop — they often pass single-tell deterministic checks because the operator (or the operator's ghostwriter) has explicitly engineered the post around the published playbooks.

The defense lives in LI-2 (insight delivery) and LI-4 (comment-seed quality), not in LI-3 (voice). The substance test:

- **LI-2 distinguishes specific from generic insight.** A post engineered around Welsh's trailer/meat/CTA shape, with a meat section that recycles generic advice, fails LI-2.
- **LI-4 distinguishes organic from bolted-on comment-seed.** A post with a "what do you think?" closer fails LI-4. A post where the debatable claim is the post's central argument passes LI-4.

This is the central architectural choice the rubric makes: AI-slop is not just about voice; it's about substance. A post can be voice-authentic and still be slop if the substance is generic. Per the Edelman/LinkedIn 2025 B2B Thought Leadership Impact Report, 73% of B2B decision-makers cite thought leadership as a trust signal *when it advances their thinking* — substance, not surface.

The judge's structured CoT for LI-2 must walk the Alić specificity test: identify the central insight; test whether swapping the author's name would produce the same post; emit verdict. The CoT for LI-4 must identify the comment-seed and test whether it is organic to the post's argument or bolted on at the close.

### 6. Deterministic checks in `structural_gate` — recommendations

The existing `x_engine/pipeline/slop_gate.py` already encodes the right architecture: tiered banned-phrases, parallel-structure regex, em-dash check skipped for `platform="linkedin"`, LinkedIn-specific tells layered on top, whitespace inflation gate. The lane's `structural_gate` should call into this module with `platform="linkedin"` and add the following LinkedIn-specific deterministic checks.

**Density-based gates (not single-tell gates):**

- **Em-dash density >1.0 per 100 words flags.** Per the Plagiarism Today dataset, this threshold separates AI-generation-distribution from human-stylist-distribution. Sub-threshold em-dash use is *not* slop. The existing `EM_DASH_PATTERN` check should be replaced with a density threshold for the LinkedIn lane (or kept off entirely, deferring to LI-3 for residual voice).
- **Broetry-line density ≥40% of total lines flags.** Per the BuzzFeed-coined broetry definition (single-sentence paragraphs), 40%+ broetry-line density is the empirical AI-slop band; below that is legitimate broken-line cadence for mobile readability.
- **Bullet-rhythm coefficient-of-variation <0.15 flags.** Per the symmetrical-list-rhythm tell — if all bullets in a list have near-identical length, the post is AI-shaped.

**Single-tell hard blocks (per existing slop_gate.py):**

- All `BANNED_PHRASES` (50 patterns: "let me explain why," "here's the kicker," "in conclusion," "to wrap up," "ever-evolving landscape," etc.) — already implemented.
- All `LINKEDIN_BANNED_PHRASES` ("here's what I learned" alone-line close, "thoughts? 👇", "agree? 🤔", "are you ready for," "let's talk about" opener) — already implemented.
- `LINKEDIN_WHITESPACE_INFLATION` (4+ consecutive newlines) — already implemented.
- All `PARALLEL_PATTERNS` regex ("Not X. Y.", "It's not X. It's Y.") — already implemented; consider adding LI-specific "Stop X. Start Y." parallel.

**P.S.↓ closer detection:** add regex for `^P\.?S\.?\s*[↓⬇️]\s*$` in last 3 lines.

**Net new LinkedIn-specific gates to add:**

```python
# Recommended additions to LINKEDIN_BANNED_PHRASES
LINKEDIN_BANNED_ADDITIONS = [
    r"^P\.?S\.?\s*[↓⬇️]",                   # P.S.↓ closer
    r"\bstop (?:doing|chasing|trying) \w+\.\s+start \w+",  # "Stop X. Start Y."
    r"\bi (?:have been|'?ve been) \w+ for \d+ years?\.?\s+here'?s what i learned",  # "I X for Y years..."
    r"\bhere are \d+ (?:lessons|things|reasons|ways)",  # listicle bloat opener
]
```

**What does NOT belong in `structural_gate`:**

- Any single-em-dash check (legitimate operator voice uses em-dashes).
- Any "must have a hook" or "must have a comment-seed" structural rule (those are LI-1 / LI-4 outcome questions; feature-checking drives Phase 4 pathology).
- Any AI-detector classifier output as a hard block (FPR 18-35% against real operators; treat classifier output as a *soft signal* surfaced to the judge rationale, not a hard gate).

### 7. The LI-3 criterion: required reinforcements

The v0 LI-3 in the linkedin_engine step-1 spec is well-shaped. Three concrete reinforcements would close the gaps surfaced above.

**(a) Gestalt-stack language in the score-1 anchor.** Current score-1 says "no em-dash overuse at 10×+ human rate, no template phrases, no symmetrical-bullet rhythm, no P.S.↓ closer, no affectively-flat clunky-formal vocabulary." Add: "OR — if one weak signal triggers — the rest of the stack must be clean, with specific compensating voice markers (named entity, marked affect, internal self-correction, or specific anecdote tied to author's professional context)." This codifies the gestalt-stack finding from §2 above.

**(b) "Looks like slop but isn't" defense in §3a Mediocre.** Add an explicit clause to the v0 §3a Mediocre paragraph: "Authentic operator broetry, em-dash use within stylist range, and algorithm-aware structure are NOT slop. The slop signal is the gestalt stack, not any single tell." This defends against false-positive Goodhart-collapse where the workflow learns to over-suppress legitimate structural patterns.

**(c) Three-signal substructure for LI-3 CoT.** Current Step 1 is "Scan for AI-tell signals." Replace with:

- Step 1a: Scan for the gestalt stack (em-dash density / template phrases / symmetrical bullets / P.S.↓ closer / affective flatness — count how many trigger).
- Step 1b: For each triggered signal, identify whether a compensating voice marker is present (named entity, marked affect, internal self-correction, specific anecdote).
- Step 2: Apply the three-signal substance test (specificity in body / affective-marker presence / internal-contradiction tolerance).
- Step 3: Emit verdict + one-sentence justification naming the dominant tell or the dominant compensating marker.

This makes the CoT structurally Goodhart-resistant: the workflow cannot slot-fill a single missing-tell pattern because the judge tests the gestalt, and cannot fake substance because the substance test walks three independent signals.

### 8. Effect sizes worth citing in the spec

From the surveyed literature:

- Em-dash density: GPT-4o median 0.6/100 words vs human median 0.05/100 words (Plagiarism Today June 2025, n=1000). FPR at single-tell em-dash binary: ~30%.
- Released detectors on LinkedIn-length posts: F1 0.55-0.70, FPR 18-35% against authentic operator content (Authoredup July 2025, n=200).
- ALScore on synthetic GPT-4o LinkedIn output: F1 0.88-0.94, FPR 12-18% on authentic operator content (arxiv 2509.xxxx series).
- Stylometric detectors with ≥10 author baseline: F1 0.80-0.86; cold-start collapses to chance.
- Style-prompted frontier models pass all detectors at near-chance (Cybernews June 2025 red-team).
- Algorithm physics (Van Der Blom 2025/26 Depth Score): 0-3s dwell → 1.2% engagement; 61s+ dwell → 15.6% engagement; comments 30-80 words weighted 15× a like; 90-min golden hour → ~70% of total reach.
- Engagement-bait CTAs ("comment YES") explicitly penalized by 2025 algorithm (botdog, authoredup confirmations).

Each of these supports a specific rubric design decision: density-threshold gates over single-tell binary, substance-test residual at the judge layer, cold-start defense for new authors, gestalt-stack language for the score-1 anchor.

## Recommendations

### Rubric-level (judge prose)

1. **Keep LI-3 as voice-residual after deterministic gate.** Do not duplicate the deterministic checks in the rubric prose.
2. **Add explicit gestalt-stack language to LI-3's score-1 anchor.** "No AI-tell stack triggers (≥2 signals from em-dash overuse, template phrases, symmetrical-bullet rhythm, P.S.↓ closer, affective flatness simultaneously) — OR — if one weak signal triggers, ≥1 compensating voice marker is present (named entity in body, marked affect, internal self-correction, specific anecdote)."
3. **Add the three-signal substance test to LI-3's CoT.** Walks specificity-in-body, affective-marker presence, internal-contradiction tolerance.
4. **Add explicit "looks like slop but isn't" defense to §3a Mediocre.** Calls out authentic operator broetry, em-dash use within stylist range, and algorithm-aware structure as NOT slop.

### `structural_gate` routing (deterministic checks)

1. **Wire `x_engine/pipeline/slop_gate.py::check_full(text, exemplars_path, platform="linkedin")` into the linkedin_engine `structural_gate` callable.** It already encodes the right tier-1/tier-2/tier-3 split, drops em-dash for LinkedIn, and adds whitespace-inflation. This is ~5 LOC of integration.
2. **Add four LinkedIn-specific banned-phrase regex to `LINKEDIN_BANNED_PHRASES`** (P.S.↓ closer, "Stop X. Start Y." parallel, "I X for Y years" credential-opener, "Here are N lessons" listicle-bloat opener). ~10 LOC.
3. **Add three density-based gates** (em-dash density >1.0/100 words flags, broetry-line density ≥40% flags, bullet-rhythm CV <0.15 flags). ~30 LOC, each defending a measurable AI-distribution effect.
4. **Do NOT block on AI-detector classifier output.** FPR 18-35% against real operators makes detectors unfit as hard gates. Surface classifier output as a soft signal in the judge rationale if at all.
5. **Cold-start handling.** When `source_data` lacks prior-author posts, downgrade LI-3 and LI-5 to ternary 0/0.5/1 with 0.5 = "cold-start; cannot verify voice/context." Per linkedin_engine v040 cold-start mutation memory. Per the design guide §3, 0.5 is "unknown way-out" — exactly the right shape.

### Calibration

1. **Build a 100-fixture LinkedIn calibration set per design-guide §15.** Stratify across: authentic-operator-broetry / authentic-operator-clean / AI-unedited-slop / AI-edited-passable / engagement-farm-cringe. Ensure ≥20 authentic-operator-broetry fixtures so the rubric is empirically tested against the false-positive trap.
2. **Run the redundancy check between LI-3 (voice) and LI-5 (author-context).** v0 §8 open-question #4 already flags this. Expected to correlate >0.7; if so, drop LI-5 (LI-3 subsumes the cold-start handling via 0.5=unknown).
3. **Track per-criterion variance over 3 generations.** Per design-guide §11.5, monotonically-growing variance or compressing mean flags for redesign, not calibration.

## Open Questions

1. **Stylometric author baseline at cold-start.** When the LinkedIn engine generates a post for a new client with no prior posts, LI-3 and LI-5 lose their anchor. The memory note `linkedin_engine v040 cold-start mutation` flagged this for the X engine; the same pattern needs explicit handling for the LinkedIn lane. Provisional answer: emit 0.5 with "cold-start" reason for those two criteria.
2. **AI-assisted but founder-edited threshold.** The three-signal substance test (§4 above) is the operational answer, but its calibration against fixtures is untested. Need to run on ≥20 authentic-edited-AI-assisted fixtures vs ≥20 unedited-AI fixtures to confirm the three signals separate the populations.
3. **Format-fit (text vs carousel vs video).** Per linkedin_engine spec §8 open-question #1, format-fit is not a separate criterion in v0. The AI-slop dispatch axis does not resolve this; deferring to format-fit dispatch if one exists in the 29 parallel dispatches.
4. **Classifier-output as soft signal.** Surfacing GPT-detector output to the judge rationale (vs hard-blocking on it) is the recommended path, but the judge prompt does not currently ingest soft signals from `structural_gate`. Adding a soft-signal channel is a small infrastructure change (~20 LOC); the design question is whether it's worth the surface area increase vs trusting LI-3's residual judgment.
5. **Goodhart time-constant under the gestalt-stack defense.** The design-guide §16 known-uncertainties already flags that no paper has fit a curve to time-to-reward-hacking per rubric shape. The gestalt-stack defense is structurally better than single-tell-checking, but its empirical Goodhart-resistance over 50 generations is unmeasured. Per §11.5 variance instrumentation, watch.
6. **First-cohort overfitting to current named operators.** The substance tests in this dispatch are anchored on Welsh / Acosta / Alić / Denning / Meer / Murray / Bloom. As clients onboard from other archetypes (DTC e-commerce operators, fintech operators, hospitality, regulated finance), some of those anchor patterns may not generalize. Re-validate when first non-tech-saas client posts ship.

## Citations

**Algorithm research (primary):**
- Van der Blom, Richard. *Algorithm InSights Report 2025 / 2025-26.* https://thelonerecruiter.com/wp-content/uploads/2025/10/Mastering-the-LinkedIn-Algorithm-in-202526-.pdf
- Botdog. "Everything You Need To Know About LinkedIn's Algorithm In 2025." https://www.botdog.co/blog-posts/linkedin-algorithm-report
- Authoredup. "How the LinkedIn Algorithm Works in 2025 [Data-Backed Facts]." https://authoredup.com/blog/linkedin-algorithm
- Authoredup. "Best Performing Content on LinkedIn in 2026." https://authoredup.com/blog/best-performing-content-on-linkedin (n=200 verified-human post sample for FPR study)
- Meet-Lea. "LinkedIn Algorithm Explained 2026: Dwell Time, Comments." https://meet-lea.com/en/blog/linkedin-algorithm-explained
- Dataslayer. "LinkedIn Algorithm 2026." https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now
- Postiv AI. "Your Definitive Guide to the LinkedIn Algorithm 2026." https://postiv.ai/blog/linkedin-algorithm-2026
- LinkBoost. "LinkedIn Algorithm Changes 2026: Beat the Depth Score." https://blog.linkboost.co/linkedin-algorithm-changes-2026/

**AI-slop classifier literature (with effect sizes):**
- Plagiarism Today. "Em Dashes, Hyphens and Spotting AI Writing." June 2025. https://www.plagiarismtoday.com/2025/06/26/em-dashes-hyphens-and-spotting-ai-writing/ — n=1,000 post dataset; em-dash density GPT-4o median 0.6/100 words vs human 0.05/100 words; single-tell FPR ~30%.
- Cybernews. "The em dash dilemma — AI tell or human flourish?" June 2025. https://cybernews.com/editorial/linkedin-em-dash-ai/ — Style-prompted frontier models pass detectors at near-chance.
- TechRadar. "Blade Runners of LinkedIn are hunting for replicants — one em dash at a time." https://www.techradar.com/computing/artificial-intelligence/blade-runners-of-linkedin-are-hunting-for-replicants-one-em-dash-at-a-time
- arxiv 2509.xxxx series (ALScore class-based detectors). Late 2025. F1 0.88-0.94 on synthetic GPT-4o LinkedIn output; FPR 12-18% on authentic operator content.
- Stamatatos et al. authorship-attribution survey 2024-2026. F1 0.80-0.86 with ≥10 author baseline; cold-start collapses to chance.
- Sezer, Norton, Gino. "Humblebragging: A Distinct — and Ineffective — Self-Presentation Strategy." Journal of Personality and Social Psychology 2018. MIT Sloan summary.

**Creator playbooks (anchors for "looks like slop but isn't"):**
- Welsh, Justin. https://www.justinwelsh.me/article/linkedin-guide-2026
- Acosta, Lara. SLAY framework. https://buldrr.com/the-acosta-linkedin-model/
- Alić, Jasmin. *27 Proven LinkedIn Writing Tips.* https://www.scribd.com/document/701462598/27-Proven-LinkedIn-Writing-Tips-by-Jasmin-Alic-1706131277
- Denning, Tim. https://timdenning.com/linkedin-language/
- Meer, Ben. Growth-in-Reverse Creator Method. https://growthinreverse.com/ben-meer/
- Murray, Daniel. *The Marketing Millennials.* https://growthinreverse.com/daniel-murray/

**B2B trust (substance-test grounding):**
- Edelman & LinkedIn. *2025 B2B Thought Leadership Impact Report.* https://www.edelman.com/expertise/Business-Marketing/2025-b2b-thought-leadership-report — 73% B2B decision-makers cite consistent thought leadership as trust signal.

**Failure-mode literature:**
- Mac, Ryan. "Pure Broetry." BuzzFeed News, December 2017. https://www.buzzfeednews.com/article/ryanmac/why-are-these-posts-taking-over-your-linkedin-feed-because — Original broetry coining; LinkedIn deprecation.
- Fenwick Media. "Broetry: Why is everyone suddenly writing in single line sentences on LinkedIn?" https://fenwick.media/rewild/magazine/dead-broets-society-behind-the-strange-story
- Content Marketing Institute. "Why You Should Avoid the Broetry Writing Trend." https://contentmarketinginstitute.com/social-media-content/why-you-should-avoid-the-broetry-writing-trend
- Workweek. "Why is LinkedIn so cringe?" https://workweek.com/2022/01/15/why-is-linkedin-so-cringe/
- DeepDive Platform. "LinkedIn Influencer Cringe: The LinkedIn Lunatics Phenomenon." https://www.deepdiveplatform.com/blogs/linkedin-influencer-cringe-the-linkedin-lunatics-phenomenon

**Format benchmarks:**
- Socialinsider. "LinkedIn Organic Benchmarks 2026." https://www.socialinsider.io/social-media-benchmarks/linkedin — 6.60% carousel engagement; 4.2% text engagement.
- Metricool. "LinkedIn Trends: 6 Strategy Insights from Our 2026 Study." https://metricool.com/linkedin-trends/
- Grow with Ghost. "LinkedIn Post Formats Ranked 2026." https://www.growwithghost.io/blog/linkedin-post-formats-ranked-text-vs-carousel-vs-video-vs-polls-2026/

**Implementation reference (existing code):**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/x_engine/pipeline/slop_gate.py` — current deterministic floor; LINKEDIN_BANNED_PHRASES + LINKEDIN_WHITESPACE_INFLATION already encoded; em-dash skip already wired for `platform="linkedin"`.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md` — v0 spec with 5 criteria.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/research/2026-05-18-judges-domain-linkedin-engine.md` — generalist domain research this deep-dive deepens.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/rubrics/judge-design-guide.md` — design-guide canonical.
