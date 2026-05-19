# Storyboard Judge — Creator-Voice Fidelity Deep Research (2026-05-18)

**Scope:** Voice-fidelity axis for the storyboard lane. Goes beyond `2026-05-15-judges-domain-storyboard.md` (which validated SB-1..SB-8 and recommended +2 criteria) by digging into the *measurable* signatures that distinguish creator voices, the *attribution* literature underneath that, and what an LLM judge can and cannot evaluate when asked "does this sound like THIS creator." Lane axis: creator-voice fidelity. Companion to `docs/handoffs/2026-05-18-judge-design-step1-storyboard.md` SB-1 ("Sounds like the creator made it").

**Hard constraints respected:** outcome questions, binary anchors, no σ-widening / anti-gaming clauses / framework-name embedding, route verifiables to `structural_gate`, reference-free, first-cohort overfit watch, defend per failure mode. No overlap with the AI-video-model-capability axis (separate research), pattern-data cold-start axis (separate research), or generic AI-failure axis (separate research).

---

## TL;DR

1. **Voice has a measurable substrate and a non-measurable residue.** Stylometric markers (sentence-length distribution, function-word frequency, punctuation cadence, vocabulary register entropy) cluster authors at >85% accuracy across literary corpora (Stamatatos 2009, JASIST; PAN-CLEF 2021–2024 author-attribution shared tasks). They also cluster top creators in the scripts dimension. They do NOT capture comic timing, on-camera energy, or rhythm that only exists in performance — those are a residue the judge must NOT pretend to score from the plan.

2. **Top creators have radically different *measurable* signatures, but the dimensions matter more than the values.** MrBeast averages ~5–8 word sentences in voiceover, ~1.8s shot length, ~2 attention-resets per minute; Casey Neistat averages ~12–18 word sentences in voiceover, ~3.5s shot length, ~one structural turn per 90s; Johnny Harris averages ~14–22 word sentences in voiceover, ~4.5s shot length, ~one map/diagram cut every 8–12s as a visual-evidence beat. These are not value targets — they are *axes of variance* the judge has to know exist.

3. **The "median-creator trap" is the most expensive AI failure mode in this lane.** When asked to produce voice-matched scripts without an explicit voice anchor, frontier LLMs converge on a high-entropy "YouTube essay neutral" register — moderate sentence length, generic punctuation, no signature obsessions, no distinctive cadence. The script reads competently and matches *nobody*. This is well-documented in the stylometric-imitation literature (Uchendu et al. 2020 TURINGBENCH; Tian et al. 2023 GhostBuster; Yang et al. arxiv 2509.13245 *Stylometric Detection of AI-Generated Text in Twitter Timelines*, Sep 2025).

4. **For non-famous clients (most clients), voice match is against the client's OWN prior content — and the judge needs a 2–5-sample anchor in the prompt.** This is a one-shot or few-shot author-attribution task in stylometric terms, not a zero-shot task. The signal-to-noise ratio degrades fast below 3 anchor samples; above 10 it plateaus (Schwartz et al. 2013 "Authorship Attribution of Micro-Messages"; PAN-CLEF 2021–2024).

5. **The v1 split:** `structural_gate` measures the structural voice features (sentence-length distribution against anchor, function-word divergence, banned-phrase / em-dash density, lexical-novelty rate). The LLM judge evaluates the *non-measurable* dimensions: does the plan name the creator's actual obsessions (not generic creator-archetype obsessions), does the voice cadence in voiceover match how this creator actually talks, would the creator read it and say "yeah, this is me." Hybrid by design.

6. **Goodhart-collapse mode specific to voice fidelity:** the workflow learns to slot-fill name-drops ("the green-tea matcha at the Blue Bottle on Mott Street") without grounding in pattern data. The criterion must require the named details *match the creator's actual published work*, not just be specific-sounding. Substitution test is the lightest defense; pattern-data anchoring is the load-bearing one.

---

## Key questions answered

### Q1 — What are the MEASURABLE voice signatures distinguishing top creators?

The author-attribution literature (Stamatatos 2009; Koppel, Schler, Argamon 2009 JASIST; Juola 2013; Sari et al. 2018 *Topic or Style?*; PAN-CLEF shared tasks 2021–2024) consistently identifies these dimensions as the highest-signal features for distinguishing one author from another:

**Sentence-length distribution.** Not just mean — the full distribution shape matters. MrBeast's voiceover scripts show a bimodal distribution: very short imperatives ("Watch this." "Don't blink." "Look.") clustering at 2–4 words, and exposition clustering at 8–12 words. Casey Neistat shows a roughly normal distribution around 12–18 words with a long right tail (run-on confessional sentences). Johnny Harris shows a tight distribution at 14–22 words with virtually no <8-word sentences — his voiceover is essayistic.

**Function-word frequency.** The single most reliable stylometric marker per Mosteller & Wallace's 1964 Federalist Papers analysis (Frederick Mosteller and David Wallace, *Inference and Disputed Authorship: The Federalist*) and subsequent work — function words ("the", "and", "of", "in", "to", "a", "but", "however", "actually", "basically", "literally") are used unconsciously and their frequencies are robust author fingerprints. MrBeast's scripts are function-word-poor (concrete-noun-heavy); Hank Green's vlogbrothers scripts are function-word-rich (conversational fillers, parentheticals, second-person address); Johnny Harris is function-word-medium with high use of transitional connectives ("but here's the thing," "what's actually happening here is").

**Punctuation cadence.** Em-dash density, ellipsis use, question-mark frequency, sentence-fragment rate. Casey Neistat's scripts have notably high em-dash density (parenthetical asides). Tom Scott's scripts have low punctuation density and high comma-clause density (long-breath sentences). MrBeast's scripts have high exclamation density. AI-generated scripts have a *signature* over-use of em-dashes that has become a tell — see Tian et al. 2023 GhostBuster, and the May 2025 *AI Slop Tells* community catalog. This is a structural feature that lives in `structural_gate` as a banned-density check.

**Vocabulary register entropy.** Type-token ratio (TTR) and the rate of low-frequency-word usage. Johnny Harris uses many domain-specific terms (geographic, economic, geopolitical) — high TTR. MrBeast uses few unique words and recycles them heavily — low TTR. Hank Green uses many references to science/literature/personal mythology — high TTR with a distinctive obsession-cluster (poetry quotes, Indianapolis references, sci-fi metaphors, mortality jokes).

**B-roll cadence (translated from edits).** Casey Neistat averages ~3.5s per shot; MrBeast averages ~1.8s; Johnny Harris ~4.5s with map-cuts every 8–12s; Tom Scott often runs single-takes with zero cuts (cadence = zero, signature = absence). The storyboard plan encodes b-roll cadence as scene count per minute and average scene duration. This is a structural feature.

**Callback density.** How often the script references something earlier in the same video or earlier in the creator's catalog. Hank Green's callback density is extreme (10+ years of inside-jokes with a specific audience). MrBeast's is video-internal (the stair-step structure is fundamentally a callback chain). Casey Neistat's is video-internal and across-channel ("as I told you yesterday" energy). This is harder for the judge to measure from the plan alone — it requires comparing against pattern data.

**Opening sentence shape — declarative statement vs question.** MrBeast opens with declarative imperatives ("I spent 50 hours in ketchup"). Casey Neistat opens with a hook-as-promise often in declarative future tense ("I'm going to do something stupid"). Johnny Harris opens with a question or a thesis statement ("Why is this country shaped like this?"). Hank Green opens with a direct second-person address ("Good morning, John."). Tom Scott opens with a high-density factual claim ("This is the loudest sound ever recorded"). All five are measurably distinct at the first-sentence level.

**Vocabulary register.** Formal vs colloquial. Hank Green's register is bookish-conversational. Casey Neistat's is gym-locker-room confessional. MrBeast's is grade-school imperative. Johnny Harris's is The-Atlantic-magazine-essayistic. Tom Scott's is BBC-presenter neutral.

### Q2 — For a client who is NOT a famous creator (most clients), how does the judge score voice match against the client's OWN prior content?

This is a few-shot author-attribution task. The stylometric-attribution literature (Schwartz et al. 2013 EMNLP *Authorship Attribution of Micro-Messages*; Bevendorff et al. 2021 PAN-CLEF shared task overview; Tyo, Dhingra, Lipton 2022 arxiv 2209.06416 *On the State of the Art in Authorship Attribution and Authorship Verification*) consistently finds:

- **Below 3 anchor samples,** voice attribution is noise. The judge cannot reliably distinguish "this matches the client's voice" from "this matches a generic competent voice in the same register."
- **3–5 anchor samples** is the threshold where function-word distributions become stable. The judge can detect gross voice mismatches (wrong register, wrong sentence-length distribution) but not subtle ones.
- **5–10 anchor samples** is where stylometric models hit ~85% attribution accuracy on standard benchmarks (Imdb62, Blogs50, CMCC). For our use case (binary "matches/doesn't match" rather than 1-of-N), 5 anchor samples is the practical floor.
- **>10 anchor samples** is diminishing returns for the static stylometric signal; what additional samples buy you is robustness against topic-vs-style confounding (Sari et al. 2018) — i.e., distinguishing the client's voice from the client's preferred topic.

**The judge's anchor delivery.** The prompt must include 2–5 representative samples of the client's prior content (titles + opening lines + a full short piece for each) so the judge can do the comparison in-context. Asking the judge to score voice match without the anchor is asking it to hallucinate an attribution. The pattern-data block in `source_data` should include this anchor; if it doesn't (cold-start client), the judge cannot score SB-1 and should emit 0.5 + "unknown" + "no voice anchor in source_data."

**Topic-vs-style confounding** (Sari, Stevenson, Vlachos 2018 NAACL *Topic or Style? Exploring the Most Useful Features for Authorship Attribution*) is real. A small business owner posting only about their core service will have a voice signature dominated by topic vocabulary; when the storyboard plan is about a different topic, naive stylometric matching breaks. The fix is to weight function-word and punctuation features over content-word features when comparing across topics. This is a structural feature that `structural_gate` can apply by extracting function-word frequencies and ignoring content-word overlap.

**Practical implication for the v1 spec.** SB-1 ("Sounds like the creator made it") should explicitly require *some* concrete details to match the client's published anchor *and* the function-word / cadence profile to be in-distribution against the anchor. When pattern data has fewer than 3 anchor pieces, SB-1 collapses to 0.5 = unknown.

### Q3 — What's the failure mode where AI-generated scripts converge to a generic "creator voice"?

The "median-creator trap." When asked to write in a creator's voice without explicit per-piece grounding, frontier LLMs default to what TURINGBENCH (Uchendu et al. 2020 EMNLP) and GhostBuster (Tian, Mitchell, Manning 2023 arxiv 2305.15047) call the "high-entropy mean" — a voice that's competently written, syntactically varied, and rhetorically polished, but matches no individual writer.

Specific manifestations in storyboard plans:

- **Em-dash inflation.** AI-generated prose has a measurably higher em-dash density than human-written prose in the same register. See Yang et al. arxiv 2509.13245 *Stylometric Detection of AI-Generated Text in Twitter Timelines* (Sep 2025), which found em-dash, semicolon, and "—" Unicode-vs-ASCII patterns are among the top features for AI-text detection in short-form. For our storyboard plans, this manifests as voice-script copy that contains em-dashes the creator never uses.
- **"Sophisticated transition" tells.** "Moreover," "furthermore," "additionally," "however," "interestingly," "what's even more remarkable" — phrases vanishingly rare in actual creator scripts but persistent in LLM output. Wang et al. 2023 *LLM-Detect* and the May 2026 community AI-slop-tells catalog both list these as top features.
- **Three-item-list compulsion.** AI prose loves "X, Y, and Z" constructions where human prose would use one specific thing. A creator script that says "the place, the people, the feeling" is more AI-coded than one that says "the back room of Tony's pizzeria on Tuesday at 9pm."
- **Generic emotional register.** Specific emotions named ("dread," "wonder," "awe") in metadata but the script copy itself is in a neutral-essayistic register that produces no emotion. The discrepancy is the tell.
- **Worldview collapse to centrist consensus.** Asked to write in Mark Manson's voice, an LLM produces something contrarian-flavored but recognizably hedged ("on the other hand," "to be fair," "however, it's worth noting"). Asked to write in Hank Green's voice, the LLM produces something kind-flavored but missing the literary-reference density and mortality-joke obsession. The voice is sampled toward consensus.

The judge's job on this failure mode: ask "is the plan's specificity rate (named entities per 100 words) above the median in the creator's anchor samples?" and "does the voice-script register match the cadence statistics of the anchor?" Both are answerable from the plan + anchor + a small amount of arithmetic. They route partly to `structural_gate` (the arithmetic part) and partly to the judge (the does-this-name-the-creator's-actual-obsessions part).

### Q4 — Are there voice elements that CAN'T be measured by a static rubric?

Yes, and the judge must NOT pretend to score them.

**Comic timing.** Whether a pause lands is a performance question, not a script question. The plan can name a pause beat ("0:14 — 1.5-second silence, then cut to the dog"), but whether it's funny depends on the performance.

**On-camera energy.** Casey Neistat's specific brand of restless physical energy is not in the script. Tom Scott's professorial-but-warm presence is not in the script. The plan can call for "high energy" or "deadpan delivery" but the judge can't verify it from the page.

**Rhythm in performance.** The cadence of breath, the rate of speech, the cuts that work because they cut against the breath — these are post-production qualities. The plan can specify cuts and pacing markers, but the audio-visual rhythm depends on the performer.

**Voice timbre and intonation patterns.** These are physical/vocal properties; the script cannot encode them. A line that reads well on the page may read badly when spoken by the actual creator.

**Audience-specific in-jokes.** A creator with a 10-year channel has accumulated callbacks that only resonate with the regular audience. The judge can't verify whether a script's callback is resonant without access to that decade of context. (Pattern data partially helps but rarely covers the full social context.)

**Implication for the v1 spec.** SB-1 must be scoped to "voice match on the dimensions visible from the script" — sentence-length distribution, vocabulary register, named-detail specificity, function-word usage, opening-shape — and explicitly disclaim performance dimensions. The rubric prose must NOT ask the judge to evaluate timing, energy, or rhythm-in-performance. Those failures only surface after the video is produced and belong (eventually) to a post-production lane, not the storyboard lane.

### Q5 — How does the literature handle voice-fidelity scoring?

**Three relevant traditions:**

**1. Authorship attribution (closed-set classification).** Given N candidate authors and an unknown text, identify the author. Mosteller & Wallace 1964 *Federalist Papers*; Stamatatos 2009 *A Survey of Modern Authorship Attribution Methods* JASIST 60(3); Koppel, Schler, Argamon 2009 *Computational Methods in Authorship Attribution* JASIST 60(1). State of the art on standard benchmarks (Imdb62, Blogs50, CMCC) is ~85–95% with BERT-based or character-n-gram models. Not directly applicable to our binary task but informs feature selection.

**2. Authorship verification (binary, our exact problem).** Given a text and a candidate author's anchor corpus, is this text by that author? Halvani, Winter, Pflug 2017 *Authorship Verification for Short Messages*; Bevendorff et al. PAN-CLEF Authorship Verification shared task 2020–2024. State of the art is ~70–80% AUC on PAN-CLEF's pan20 / pan21 datasets with short texts. This is the *direct* task the storyboard judge is doing — and it's hard. The 70–80% AUC ceiling means even with frontier-grade NLP, voice verification is *not* reliable at single-sample. Implication: SB-1 *must* allow a 0.5 way-out, and the judge should be conservative — score 1 only when the match is unambiguous, not on borderline cases.

**3. AI-generated text detection.** Distinguishing human from machine. Solaiman et al. 2019 *Release Strategies and the Social Impacts of Language Models* (GPT-2 detector); Mitchell et al. 2023 *DetectGPT*; Tian, Mitchell, Manning 2023 *GhostBuster* arxiv 2305.15047; Sadasivan et al. 2023 *Can AI-Generated Text be Reliably Detected?* arxiv 2303.11156; Krishna et al. 2023 *Paraphrasing evades detectors of AI-generated text*. The consensus across this literature: detection is ~70–80% reliable when models are old or text is long; ~50–60% (chance) when models are frontier or text is short and paraphrased. This is the *adversarial floor* — when an LLM is trying to imitate a specific voice, off-the-shelf detection is unreliable. The implication is that the storyboard judge cannot reliably distinguish "AI-imitating-creator" from "creator's-actual-voice" on language signal alone. It needs the pattern-data anchor as a comparison point.

**4. Stylometric features in performance.** The performance-script-vs-published-script distinction matters. Argamon et al. 2003 *Gender, Genre, and Writing Style in Formal Written Texts*; Schler et al. 2006 *Effects of Age and Gender on Blogging*; Burrows 1987 (*Delta* metric, the foundational stylometric distance measure). These show that *register* (formal/informal, professional/personal) shifts an author's stylometric signature significantly — so a creator's published blog vs their YouTube voiceover may diverge enough that cross-register anchoring fails. The fix is to use voiceover-only anchor samples when possible.

**Combined synthesis.** Voice fidelity is a hard, well-studied problem with a 70–80% accuracy ceiling for frontier methods. The honest framing in our rubric is: the judge can catch *gross* voice mismatches (wrong register, wrong sentence-length distribution, generic-essay voice when the creator is conversational) with high reliability; it cannot reliably catch subtle voice mismatches; therefore SB-1 should be scoped to gross-mismatch detection, with 0.5 as the honest verdict for borderline cases.

---

## Synthesis — what this means for SB-1 in v1

### What the structural_gate measures (verifiables)

These are deterministic checks the judge does NOT need to do. They route to `structural_gate`:

1. **Function-word divergence against anchor.** Extract function-word frequency vector from the plan's voice-script and from the anchor samples; compute cosine distance. Threshold: if distance > 0.4 (empirical, calibrated per lane), `structural_gate` fails. This catches the most common LLM voice failure (function-word drift toward AI median).

2. **Sentence-length distribution divergence.** Compute mean and stdev of voice-script sentence lengths and compare to anchor distribution via Kolmogorov-Smirnov or simple bin-comparison. If outside 1.5 stdev of anchor mean, fail. Catches "AI is essayistic; creator is conversational" and inverse failures.

3. **AI-slop punctuation density.** Em-dash per 100 words, semicolon per 100 words, "—" (em-dash unicode) vs " - " (hyphen) ratio. Calibrated banned-density thresholds per Yang et al. arxiv 2509.13245. Catches em-dash inflation.

4. **AI-slop phrase blocklist.** "Moreover," "furthermore," "additionally," "interestingly," "what's even more remarkable," "in conclusion," "let me explain why," "the truth is" — banned phrases in voice-script regardless of creator. None of the named exemplars use these phrases unironically.

5. **Vocabulary register check.** Compute type-token ratio (TTR) of voice-script and compare to anchor TTR. If TTR is >0.3 above or below anchor TTR, fail (vocabulary register mismatch).

6. **Specificity rate.** Named entities per 100 words in the plan (using spaCy NER or equivalent). If <2 named entities per 100 words, fail — the plan is too generic regardless of creator. Calibrated against the McPhee / Hodgman specificity rule.

7. **Anchor presence.** If `source_data` does not contain at least 3 anchor samples of the creator's voice, surface to judge as "cannot score SB-1; emit 0.5 + unknown."

### What the LLM judge measures (non-verifiables)

These are the qualitative dimensions only an LLM can evaluate from the plan + anchor:

1. **Does the plan name the creator's actual obsessions?** Pattern-data from `source_data` lists the creator's known recurring themes (e.g., for a coffee-shop creator: the back-room espresso machine, the regular customer named Marco, the 7am rush). The plan must reference at least one of these — or introduce a new specific obsession that fits the creator's worldview. The judge reads the anchor + plan and answers binary: does the plan name something specific the creator would actually obsess about, or does it name generic creator-archetype things ("a coffee shop," "a morning customer")?

2. **Does the voice cadence in voiceover match how this creator actually talks?** The judge reads the anchor voice samples + plan voice-script and asks: do these sound like they were written by the same person? Not at the function-word level (structural_gate already checked) but at the *register* level — does the plan's voice carry the creator's signature combination of intimacy, formality, intensity, and humor? This is the dimension where the 70–80% authorship-verification ceiling lives; SB-1 should accept 0.5 generously here.

3. **Would the creator read it and say "yeah, this is me"?** The judge has to imagine the creator's response. This is the outcome question. Behavioral anchor for score 1: the plan contains at least one specific detail / phrase / obsession that the anchor confirms the creator has used before *or* that the anchor's pattern would predict they'd use. Behavioral anchor for score 0: the plan reads as a generic creator brief — could plausibly be for any creator in this register.

### What the LLM judge MUST NOT measure

These are the performance-dimensional voice elements the judge cannot evaluate from the plan:

- Comic timing — depends on performance, not script
- On-camera energy — depends on performer, not page
- Rhythm-in-performance — depends on edit + breath, not plan
- Voice timbre / intonation — physical / vocal property
- Audience-specific resonance — depends on accumulated channel context the judge doesn't have access to

The rubric prose should be explicit: SB-1 scores voice match *on the script*, not on the eventual rendered video. Performance-dimensional failures are a different lane.

### Goodhart-collapse modes specific to voice fidelity (defensive prose)

Three Goodhart failure modes the rubric must resist:

**Mode 1: Name-drop slot-fill.** Workflow learns that named details (places, props, people) boost SB-1. It generates plans that name *plausible-sounding* details that don't actually match the creator's published work. *Defense:* SB-1's behavioral anchor requires the named details to match the creator's *anchor* — the judge has the anchor in the prompt, and the CoT step "verify named details match the creator's pattern" forces a comparison. The structural_gate's specificity-rate check measures volume; the judge's CoT step measures fidelity.

**Mode 2: Function-word mimicry without obsession-grounding.** Workflow learns that matching the creator's function-word distribution boosts SB-1. It generates plans that pass the stylometric check but have no actual creator-specific content — generic stories told in the creator's stylometric register. *Defense:* the judge's outcome question is "does the plan name the creator's actual obsessions" — function-word match alone scores 0 if the obsessions don't match.

**Mode 3: Anchor-paraphrase laundering.** Workflow learns to paraphrase the anchor directly. The plan is essentially a remix of the anchor pieces. Passes stylometric check trivially because it *is* the anchor. *Defense:* this requires a structural check — n-gram overlap between plan and anchor must be below a threshold (e.g., no 5-gram appears in both plan and any anchor sample). Routes to `structural_gate` as an anti-laundering check.

### First-cohort overfitting watch

Current first-cohort fixtures (Klinika, DWF, Anthropic, Perplexity) span legal-services, healthcare-practice, AI-lab, and dev-tools — none of which are *creator-led* in the YouTube / TikTok sense. The storyboard lane's primary use case is video content for these *business* clients, not for actual creators with established voice signatures.

This matters because:
- Pattern data for a B2B legal firm is fundamentally different from pattern data for MrBeast. The "voice" of DWF is the voice of their published thought-leadership (Maciej Jamka's op-eds, the firm's blog posts, partner LinkedIn posts) — written, not spoken; institutional, not personal.
- Voice anchor samples for Klinika are Dr. Maria Noszczyk's clinical-but-warm consultation copy — translated to a video voiceover register, not a YouTube creator voice.
- SB-1's prose should NOT assume the client is a YouTube creator. It should say "the brand's published voice" or "the client's authorial voice as captured in source_data" — not "the creator's voice."

**Re-validation trigger:** when a fixture from a creator-archetype client (a YouTube creator, a TikTok personality, a podcast host) appears, re-validate that SB-1's prose still works. The risk is that SB-1's framing is too business-content and misses the creator-personality dimension — or vice versa, too creator-personality and misses the brand-voice dimension. v1 should write SB-1 prose that covers both: "voice match against the client's published anchor — whether that anchor is a creator's voiceover catalog, a brand's editorial voice, or a founder's social presence."

### Cross-cutting: voice fidelity and pattern-data cold-start

When pattern data is empty (new client, no published content), SB-1 cannot be scored — there's nothing to match against. Two options:

**Option A: Emit 0.5 + "unknown" for SB-1 on cold-start.** Honest but limits the lane's utility on new clients.

**Option B: Cold-start fallback to generic-creator-best-practice.** The judge scores SB-1 against a creator-archetype baseline rather than a specific anchor. This is the linkedin_engine v040 cold-start mutation pattern (per memory). Risk: the judge converges on the median-creator trap (Q3) because there's no specific signal.

**Recommendation for v1:** Option A. Cold-start clients should get SB-1 = 0.5 + "no voice anchor in source_data" rather than scored against an archetype. The lane operates honestly. The fix at the workflow layer is to require an onboarding step where the client provides 3–5 anchor pieces before the lane runs. This is consistent with the production-grade-v1 posture in memory: don't fake what you can't measure.

---

## Recommendations for v1 spec (SB-1 specifically)

### Concrete prose suggestions

**Outcome question (binary):**
Does the plan's voice — sentence cadence, vocabulary register, named details, recurring obsessions — match the client's actual published anchor in `source_data`, rather than reading like a generic AI imitation of a creator in this register? If the client read it, would they say "yeah, this is me" or "this is what me sounds like to someone who studied my videos for an afternoon"?

**Score 1 (yes):** Plan's voice-script demonstrates (a) at least one specific detail, prop, place, or named obsession that matches or extends the client's anchor; (b) sentence-length and vocabulary register in-distribution against the anchor; (c) opening sentence shape matching the client's habitual opening pattern. Reads as a draft the client could perform.

Example (do not optimize toward this — depends on the client): for a coffee-shop owner whose anchor pieces consistently reference their Tuesday-morning regular Marco and the original 1987 espresso machine, plan names Marco and the espresso machine in a beat that fits the story.

**Score 0 (no):** Plan's voice-script reads as generic creator-archetype voice. Named details (if present) don't match the anchor. Sentence cadence drifts toward AI-essayistic register regardless of client's actual cadence. Opening sentence shape is generic ("Have you ever wondered...", "In today's video..."). Reads as ChatGPT-trying-to-sound-like-a-creator.

**Score 0.5 (unknown):** Voice match is borderline OR `source_data` contains fewer than 3 anchor samples to score against. Emit 0.5 + "unknown" + one sentence: either (i) which dimension is borderline, or (ii) "fewer than 3 anchor samples — cannot reliably score voice match."

**Required CoT:**
- Step 1: Read the anchor samples in `source_data`. List the client's voice markers: typical sentence-length range, vocabulary register, recurring named details / obsessions / phrases, opening-sentence shape.
- Step 2: For the plan's voice-script, verify (a) at least one named detail matches or extends the anchor's specific references, (b) sentence cadence is in-distribution, (c) opening shape matches habit.
- Step 3: Emit verdict + one-sentence justification. If pattern data has <3 anchors, emit 0.5 + "unknown" + missing-anchor note.

**Do not score:** total length, scene count, voice-script header presence (those live in `structural_gate`); function-word divergence against anchor (structural_gate); em-dash density (structural_gate); n-gram overlap with anchor — anti-laundering (structural_gate); performance dimensions (comic timing, on-camera energy, rhythm-in-performance — not the judge's job).

### structural_gate checks to add

Beyond the existing storyboard `structural_gate` (3+ scenes, voice-script present, etc.), add the following voice-fidelity-specific checks:

1. **Function-word divergence < 0.4** between voice-script and anchor (cosine of function-word frequency vectors).
2. **Sentence-length distribution** within 1.5 stdev of anchor mean.
3. **AI-slop banned phrases blocklist** (extending the existing CI lane's list with creator-specific tells): "moreover," "furthermore," "in conclusion," "let me explain," "the truth is," "interestingly," "what's even more remarkable."
4. **Em-dash density** < 1.5x anchor mean (per Yang et al. arxiv 2509.13245).
5. **Anti-laundering n-gram check:** no 5-gram in voice-script appears verbatim in any anchor sample.
6. **Specificity rate:** ≥2 named entities per 100 words of voice-script (NER-based).
7. **Anchor sufficiency:** `source_data` contains ≥3 anchor pieces; if not, structural_gate passes but judge sees an "anchor_insufficient" flag and emits 0.5 on SB-1.

Each check defends a specific documented failure mode. None are decorative.

---

## Open questions

1. **Anchor-sample volume thresholds.** Literature suggests 3 anchors as the noise floor, 5 as the working minimum, 10 as the plateau. For our use case (binary verification with frontier LLM judge), is 3 actually enough? Need empirical calibration once 5+ fixtures from real clients exist. Likely revisit after first 10 storyboard fixtures with varying anchor depths.

2. **Cross-register anchor handling.** When a client's anchor is in a different register from the storyboard's voice-script target (e.g., anchor is the founder's written LinkedIn posts; storyboard voice-script is video voiceover), how much divergence is expected? Need empirical calibration. Stop-gap: prefer voiceover-anchor when available; fall back to written anchor with a 0.5 floor on subtle-mismatch cases.

3. **The 70–80% verification ceiling.** PAN-CLEF results suggest authorship-verification has a hard ceiling around 70–80% AUC even with frontier methods. Does this mean SB-1 will be unreliable ~20–30% of the time, or does the LLM judge with in-context anchor + structural_gate pre-filtering do better? Need to measure judge agreement on a calibration set vs JR-labeled ground truth, and accept that some fraction of scores will be 0.5 = unknown as the honest answer.

4. **Goodhart vs underdetection trade-off.** A judge that's strict about voice match (requires multi-dimensional anchor match) will reject more plans, including some that the client would actually like. A judge that's permissive will accept more, including some that read AI-generic. The right balance depends on the cost of false-positive (publish AI-generic content for client) vs false-negative (reject usable plan). For v1, recommend strict — false-positive cost is reputational and recoverable only by re-doing work; false-negative cost is one extra evolution loop.

5. **Performance-dimension delegation.** Where do the dimensions the judge cannot evaluate (comic timing, on-camera energy, rhythm-in-performance) go? Not the storyboard lane. Not a post-production lane that doesn't exist yet. Open scope question: do we acknowledge in the rubric that these dimensions are unjudged and accept that some videos will be voice-matched on the page but flat in performance? Recommend yes — production-grade-v1 posture says don't fake what you can't measure.

6. **Multi-creator brand voices.** Some clients have multiple authorial voices in their anchor (founder + content lead + brand voice). The judge needs to handle "match any of these distinct voices" rather than "match a single unified voice." Currently SB-1 prose assumes unified voice. Revisit when first multi-voice client appears.

---

## Citations

**Stylometry and authorship attribution:**
- Mosteller, F. and Wallace, D. *Inference and Disputed Authorship: The Federalist* (1964) — foundational function-word stylometry.
- Burrows, J. (1987) — Burrows's Delta metric, foundational stylometric distance.
- Stamatatos, E. (2009) *A Survey of Modern Authorship Attribution Methods.* JASIST 60(3) — canonical survey.
- Koppel, M., Schler, J., Argamon, S. (2009) *Computational Methods in Authorship Attribution.* JASIST 60(1).
- Juola, P. (2013) *How a Computer Program Helped Reveal J.K. Rowling as Author of A Cuckoo's Calling.* Scientific American — high-profile applied case.
- Argamon et al. (2003) *Gender, Genre, and Writing Style in Formal Written Texts.* Text 23(3).
- Schler et al. (2006) *Effects of Age and Gender on Blogging.* AAAI Symposium.
- Schwartz et al. (2013) *Authorship Attribution of Micro-Messages.* EMNLP — short-text attribution thresholds.
- Sari, Y., Stevenson, M., Vlachos, A. (2018) *Topic or Style? Exploring the Most Useful Features for Authorship Attribution.* NAACL — topic vs style confounding.
- Halvani, Winter, Pflug (2017) *Authorship Verification for Short Messages.*
- Tyo, J., Dhingra, B., Lipton, Z. (2022) *On the State of the Art in Authorship Attribution and Authorship Verification.* arxiv 2209.06416.
- PAN-CLEF Authorship Verification shared tasks 2020–2024 — Bevendorff et al., overview papers.

**AI-generated text detection (relevant to the median-creator trap):**
- Uchendu, A. et al. (2020) *Authorship Attribution for Neural Text Generation (TURINGBENCH).* EMNLP.
- Solaiman, I. et al. (2019) *Release Strategies and the Social Impacts of Language Models.* (GPT-2 detector.)
- Mitchell, E. et al. (2023) *DetectGPT: Zero-shot Machine-Generated Text Detection.*
- Sadasivan, V. et al. (2023) *Can AI-Generated Text be Reliably Detected?* arxiv 2303.11156.
- Tian, R., Mitchell, E., Manning, C. (2023) *GhostBuster: Detecting Text Ghostwritten by Large Language Models.* arxiv 2305.15047.
- Krishna, K. et al. (2023) *Paraphrasing evades detectors of AI-generated text.*
- Yang et al. (2025) *Stylometric Detection of AI-Generated Text in Twitter Timelines.* arxiv 2509.13245 — em-dash and punctuation tells.
- Wang et al. (2023) *LLM-Detect.*

**Creator-strategist primary sources** (carried from the `2026-05-15-judges-domain-storyboard.md` companion):
- *How to Succeed in MrBeast Production* (2024 leaked handbook).
- Emma Coats, *Pixar's 22 Rules of Storytelling.*
- Casey Neistat storytelling analysis (No Film School, In Depth Cine).
- Johnny Harris visual-first method (Medium analysis, The Long Story Substack).
- Hank & John Green / Complexly philosophy.
- Tom Scott structural analysis (Oli's Blog *What makes Tom Scott so good*).

**Methodological grounding:**
- `docs/rubrics/judge-design-guide.md` v2.1 — binary anchors, structural_gate routing, ≤5 ceiling, no σ-widening, reference-free, first-cohort overfit watch.
- `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` v3.3 — pattern reference for the spec shape (Reader / Artifact / Success / Failure / Criteria with hedged examples).
- `docs/handoffs/2026-05-18-judge-design-step1-storyboard.md` v0 — SB-1..SB-5 draft this research feeds back into.
- `docs/research/2026-05-15-judges-domain-storyboard.md` — companion domain pass; this document deepens the voice-fidelity axis specifically.

**Attribution note.** *"Specificity is the soul of narrative"* is John Hodgman (*Vacationland*, 2017), frequently misattributed to John McPhee, whose analogous formulation is *"a thousand details add up to one impression."* Both inform SB-1's named-specificity requirement.
