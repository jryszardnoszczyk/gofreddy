---
date: 2026-05-18
type: research deliverable (1 of 29 parallel deep-research dispatches)
status: complete
lane: storyboard
axis: LLM-specific failure modes in short-form video story planning
parent: docs/handoffs/2026-05-18-judge-design-step1-storyboard.md
guide: docs/rubrics/judge-design-guide.md
siblings:
  - docs/research/2026-05-15-judges-domain-storyboard.md (creator-strategist domain — what excellent looks like)
  - docs/research/2026-05-18-ci-ai-failure-modes.md (CI sibling — methodological template)
  - docs/handoffs/2026-05-17-judge-design-step1-competitive.md (CI-6 pattern — documented ≤5-ceiling exception this lane may replicate)
---

# LLM-Specific Failure Modes in Storyboard (Short-Form Video Story Plan) Generation

Companion to `docs/research/2026-05-15-judges-domain-storyboard.md` (creator-strategist quality ceiling — what excellent looks like when an *author* writes it) and v0 spec at `docs/handoffs/2026-05-18-judge-design-step1-storyboard.md`. Creator-strategist literature assumes a human author. It does not catch the failure modes when an LLM writes the plan instead. This deliverable catalogues those LLM-specific failures, walks SB-1..SB-5 against them, and recommends where AI-failure detection should live.

The doc stays strictly on the AI-failure axis. Voice fidelity, AI-video-model capability, pattern-data sufficiency, pacing match, portfolio diversity — owned by other criteria and other dispatches. Scope here is the failure surface introduced by the LLM author itself.

---

## TL;DR

SB v0 (SB-1 voice / SB-2 hook / SB-3 emotional-arc-with-stakes / SB-4 model-capability / SB-5 pacing-and-portfolio) is sharp on creator-strategist quality but has limited coverage of five LLM-specific failure modes documented at measurable rates in adjacent domains (open-ended generation 40–80% hallucination per 2026 compilations; citation 19.9% per Chelli et al. 2025; legal-case fabrication 75% per Stanford 2024 RegLab).

The five failure modes:

1. **Script confabulation — fake stats, studies, quotes.** Invented numerics, fabricated study citations, plausible-attribution quotes. Catastrophic specifically for storyboards because the resulting video *broadcasts* the falsehood.
2. **False personal experience — first-person "I" for events that didn't happen.** Only the creator can detect, only after committing to shoot. Unverifiable from outside.
3. **Narrative-arc gaming — structurally compliant, semantically empty.** Plan hits hook → tension → payoff → CTA as labels; tension isn't tensed, payoff doesn't pay off, hook promises X and body delivers Y. The Phase 4 rollback pathology in storyboard form.
4. **Hook-formula slot-fill / cliché openers.** Tested patterns work (measured retention lift), but slot-filling them across all 5 plans produces 5 plans that read as one.
5. **Video-specific confabulation — shots, b-roll, stats that can't be sourced.** Travel/rights/prop/guest confab; chart-of-fake-stat where underlying number is mode-1 confab.

**Recommendation: structural_gate owns Mode 1 (stat-grep, quote-grep, "as of" date) and part of Mode 5 (rights-flag grep); judge owns Mode 2, Mode 3, semantic parts of Mode 4 and Mode 5.** Add one new judge criterion **SB-6 "Plan survives lived-experience and source-tracing,"** mirroring the CI-6 ≤5-ceiling exception per `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` §7. Sharpen SB-3, SB-4, SB-5 prose. Extend structural_gate with 4 deterministic anti-confabulation checks.

---

## Key questions

1. **Confabulation rates?** §1 — open-ended 40–80%; citation 19.9–75%; StoryScope per-model fingerprints compound narrative-content failure shape.
2. **Arc gaming without penalizing tight structure?** §3 — outcome questions test what beat *does to reader*, not whether beat-header exists.
3. **Hook-formula scoring without penalizing tested patterns?** §4 — test is *across-5-plans diversity*, not within-plan formula bans.
4. **False personal experience?** §2 — judge criterion only (deterministic verification impossible at plan stage).
5. **Video-specific confab?** §5 — splits across structural_gate (rights, stat consistency) + judge (production-feasibility).
6. **Deterministic structural_gate checks?** §7 — 4 anti-confabulation checks (stat-grep, quote-grep, "as of" date, rights-flag).
7. **Dedicated AI-failure criterion warranted?** §7 — yes, CI-6 justified-breach pattern.

---

## 1. Script confabulation — fake stats, studies, quotes

Short-form plans frequently hook or payoff on a factual claim. The LLM, with no episodic anchor and no source corpus the workflow currently checks against, generates plausible-sounding numerics, study citations, and attributed quotes — none verifiable.

**Sub-shapes:** fabricated stat ("73% of creators…" / "$47K average revenue" with no cited source); fabricated study citation ("A Harvard study showed…" / "the Pew 2024 report" — plausible authority, paper doesn't exist); fabricated attributed quote ("As [famous person] once said…" — amplifies human-side misattributed-quote problem of Einstein/Twain/Jobs); fabricated personal-anecdote stat ("Last week I got 2.3M views" — first-person manufactures authority without pattern-data confirmation).

**Effect sizes.** Open-ended 40–80% (sqmagazine 2026 compilation of TruthfulQA / HaluEval / domain evals); citation 19.9% (Chelli et al. 2025, GPT-4o literature reviews); legal QA 75% case fabrication (Stanford 2024 RegLab; Charlotin database 2026 logs 1,227 court submissions); NeurIPS 2025 100-fabricated-citation incident (arxiv 2602.05930): Total Fabrication 66%, Partial Attribute Corruption 27%, Identifier Hijacking 4%; GhostCite (arxiv 2602.06718) 14–95% across 13 LLMs × 40 domains.

**Asymmetric risk vs CI.** Storyboard outputs *broadcast* the confabulation to thousands or millions of viewers; reputational cost dominates production cost. Unlike CI briefs (one decision-maker who verifies before acting), storyboard fabrication goes public.

**Detection — deterministic:** stat-grep against citation list; quote-grep against citation list; "as of" date on time-sensitive claims; named-entity verification via Wikidata for famous-person attributions. Routes to structural_gate. Human-creator literature (MrBeast / Pixar / Neistat) all assume the author *wrote* the script — failure mode is endogenous to LLM-as-author.

---

## 2. False personal experience — first-person "I" for events that didn't happen

**The failure.** Plan generates first-person voice-script describing events the creator didn't experience. "I tried X for 30 days" when they didn't. "When I was in Tokyo last summer" when they weren't. "My mom always told me" — fabricated relational anecdote plausibly matching the voice extracted from pattern data, but never happened.

**Distinct from Mode 1.** A fabricated stat is deterministically verifiable (Pew 2024 either exists or doesn't). A fabricated personal anecdote is *not* externally verifiable — only the creator knows. Structural_gate cannot catch this; the judge must.

**Why dangerous.** Personal anecdotes are the highest-trust signal in short-form (the entire vlog / personal-essay genre rests on this). A fabricated "I did X" produces one of three outcomes: (a) creator rejects mid-shoot when they can't fake the experience, killing production; (b) ships despite being a lie, eroding audience trust if discovered; (c) gets reshaped into "imagine if I tried" framing — at which point the hook collapses because it was built on first-person authority.

**Effect-size basis.** ArXiv 2505.01800 (Distinguishing AI-Generated and Human-Written Text via Psycholinguistic Analysis, May 2025) maps 31 stylometric features to cognitive processes: "Human-authored writing reflects deliberate discourse planning, often integrating references to real events, individuals, or timelines that emerge from episodic memory… AI models, while capable of mimicking named entities, lack experiential grounding and may introduce irrelevant or inaccurate references… AI-generated sentiment is based on statistical patterns rather than experiential grounding, and as a result, emotional expressions in AI texts often appear flat, stereotyped, or overly uniform." StoryScope (arxiv 2604.03136) confirms across 10,272 prompts × 5 LLMs: AI fiction over-explains themes, favors tidy single-track plots, shows reduced moral ambiguity — signatures consistent with no-episodic-anchor.

**Sub-shapes:** pure fictional anecdote; mis-scaled anecdote (creator did 3-day, plan says 30); relational fabrication ("my mom" / "my sister" with biographical detail LLM invented).

**Detection — judge only.** Workflow-side pattern-data lookup is fragile (free-form schema); only reliable verifier is "would the creator recognize this?" Routes to new SB-6.

---

## 3. Narrative-arc gaming — structurally compliant, semantically empty

**The failure.** Plan hits all the formal beats — hook, tension, payoff, CTA — but each beat is generic filler that doesn't earn its position. Tension isn't tensed (nothing at risk). Payoff doesn't pay off (no question answered, no expectation reversed). Hook promises X, body delivers Y. Structure compliant, substance empty. Storyboard analogue of CI-lane "plausible strategy memo with no actionable specifics" (CI v3 §3a) and MrBeast handbook's named "well-shot, well-paced, pointless."

**Why dangerous for an evolution-loop judge.** A feature-checking judge rewarding "has hook beat / has tension beat / has payoff / has CTA" is exactly the Phase 4 pathology rolled back at `c76f051`. Under 50-generation selection pressure, the workflow slot-fills the beat headers regardless of whether each earns its position. Second-most-likely Goodhart collapse path (after hook-formula slot-fill — §4).

**Sub-shapes:** hook-promise / body-payoff mismatch; tension-without-stakes; payoff-without-question; CTA orphaning ("subscribe for more" with no thematic tie); single-signal multi-beat extension (one underlying idea expanded into 4 beats — CI-lane Phase-4 "trajectory by single-signal restated three ways" in storyboard form).

**Effect-size basis.** ArXiv 2509.04239: AI stories lack narrative arc; "unconvincing, repetitive, or misaligned with desired tone or character development." StoryScope (arxiv 2604.03136): AI fiction clusters in shared narrative space; human fiction shows greater diversity, more morally ambiguous protagonists, increased temporal complexity. The cluster-center *is* the gaming pathology — workflow learns cluster-center is high-scoring, converges there.

**Detection — sharpen SB-3, no new criterion.** SB-3 already owns earned-emotional-arc-with-stakes. Extend to include hook-promise / body-payoff coherence test + single-signal-extension penalty. Penalty without penalizing tight structure: test is outcome, not structure. Plan with no labeled beats but hook promising X and body delivering X scores 1. Plan with perfectly-labeled hook/tension/payoff/CTA where hook promises X and body delivers Y scores 0.

---

## 4. Hook-formula slot-fill / cliché openers

**The failure.** AI plans default to a small set of high-retention tested patterns: "what if I told you…", "the [X] you didn't know existed", "I tried [X] for 30 days", "stop doing [Y]", "this changed everything." Patterns *work* — OpusClip / Subscribr / TikTok publish measured 3-second-hold rates showing these openers materially lift completion vs flat intros. The pattern itself isn't the failure. **The failure is templated reuse across the portfolio**: all 5 plans use the same opener, producing 5 plans that read as one.

**Effect-size basis.**
- TikTok 2026 (Socialync May 2026; Napolify July 2025 duplicate-content penalty): duplicate-content includes "identical trend templates without adding substantial originality, even if footage is technically new." Quality/tone/originality scan downranks templated content.
- YouTube 2026 (Mohan January letter; eweek): 1 in 5 recommended Shorts is AI-slop. Kapwing: 278 AI-slop channels at 63B views, $117M ad revenue — bottom-tier. ~33% of feed AI-generated.
- OpusClip Shorts: 80–90% completion for top performers; below 50% triggers suppression. Silent bold-caption +40% completion; early-CTA +58% conversion.

**Why hard.** Banning tested patterns is wrong (they work). Within-plan originality is SB-2's substitution test. Correct frame: tested patterns fine; *templated reuse* across the portfolio is the failure.

**Detection — extend SB-5, no new criterion.** Current SB-5 tests 3+ genuinely different bets across 5 plans. Sharpen to include hook-formula fingerprinting: opener patterns must vary (e.g., "what if I told you" + "specific sensory scene" + "stat-led" + "tension-first" + "question-first" = 5 different formulas; 5 "what if I told you" openers = one).

**No structural_gate check.** Deterministic formula detection is fragile — patterns mutate faster than a regex list; banned-phrase list produces false positives on creators whose voice uses these patterns. Judge is the right home.

**Goodhart-resistance.** Workflow learning to insert one each of five different formulas without any being irreplaceable still fails SB-2. SB-5 portfolio-diversity + SB-2 irreplaceability together close the gaming surface — 5 different formulas necessary, irreplaceability necessary, neither alone sufficient.

---

## 5. Video-specific confabulation — shots, b-roll, stats that can't be sourced

**The failure.** Plan calls for shots, b-roll, or visual evidence that cannot be sourced or produced within the creator's actual production constraints. Distinct from SB-4 (AI-video-model capability), this is *production-source* capability — what the creator can shoot or acquire.

**Sub-shapes:** travel / location confab ("Tokyo skyline drone" when creator shoots Brooklyn kitchen); rights-violating b-roll ("2007 iPhone reveal" / "that scene from Inception"); unavailable guest ("interview with [named expert]" never contacted); impossible-prop b-roll ("working 1985 Macintosh"); stat-as-visual confab (chart of mode-1 fabricated number).

**Effect-size basis.** Artlist 2026 (Hallucinations in AI for Video Creators): "vague prompts, missing references, or conflicting requests often lead to confident fabrication." Moonlight 2026 (Survey on Hallucination in Video LLMs): two categories — dynamic distortion and content fabrication driven by statistical priors when no clear visual evidence is present.

**Detection split:**
- **Structural_gate (deterministic):** rights-flag grep on copyrighted references (commercial film titles, named musical tracks, identifiable commercial logos in scene-description) — fails if present without `rights_status: licensed`. Stat-grep consistency: numerics in voice-script AND scene-description must match a citation.
- **Judge (semantic):** "Does every scene describe something the creator can plausibly source within stated production constraints (location, budget, guest access)?" Routes to SB-4 prose extension — SB-4 owns "can it be rendered/produced" and generalizes naturally from AI-model capability to production-source capability.

**Why the judge owns the semantic part.** Production-feasibility is creator-specific. "Aerial drone of Brooklyn Bridge sunset" is feasible for an FAA-122-cert Brooklyn creator, infeasible for a kitchen-counter cook. Pattern data + judge reasoning is the only way to draw the line.

---

## 6. Cross-cutting — what SB v0 catches vs misses

| Criterion | 1 Script confab | 2 False personal exp | 3 Arc gaming | 4 Hook formula | 5 Video confab |
|---|---|---|---|---|---|
| SB-1 voice | NO | partial | NO | NO | NO |
| SB-2 hook | NO | NO | partial | partial | NO |
| SB-3 emotional arc | NO | NO | partial | NO | NO |
| SB-4 model capability | NO | NO | NO | NO | partial |
| SB-5 pacing + portfolio | NO | NO | NO | partial | NO |

**Partial catches:** Mode 3 (SB-3 catches no-stakes, not hook-promise mismatch); Mode 4 (SB-2 catches per-plan formulas, SB-5 catches across-5 templating); Mode 5 (SB-4 catches AI-model capability, not production-source/rights); Mode 2 (SB-1 catches voice-mismatched anecdotes; voice-matched fabrication invisible).

**Zero catches:** Mode 1 — no stat-grep, no quote-grep, no citation existence check. Most of Mode 2. Most of Mode 5.

**Asymmetric risk.** A plan fabricating "Harvard 2024 study" hook + "last month I tried" anecdote + templated "what if I told you" + Tokyo-drone b-roll the creator can't shoot can score 5/5 under v0. Perfect score; strategically empty AND structurally unproduceable AND publicly-broadcast confabulation. The architectural gap.

---

## 7. Recommendations

**Three-layer split (deterministic / judge / workflow), mirroring CI-6 at `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` §7:**

| Failure mode | Home | Why |
|---|---|---|
| 1 Script stat / study / quote confab | structural_gate | Deterministic regex + citation match. Cheap, binary. |
| 2 False personal experience | judge (new SB-6) + workflow pattern-data anchor | Only reliably verified by "would creator recognize this?" Semantic. |
| 3 Arc gaming | judge (sharpen SB-3) | Already SB-3 territory. |
| 4 Hook-formula slot-fill | judge (sharpen SB-5 + SB-2) | Covered when SB-5 = formula-fingerprint variety AND SB-2 = substitution per-plan. |
| 5 Video / production confab | structural_gate (rights + stat consistency) + judge (sharpen SB-4) | Rights-flag deterministic; production-source feasibility semantic. |

**Concrete edits:**

**Edit 1 — Add SB-6 (judge criterion):**

```
### SB-6 — Plan survives lived-experience and source-tracing

Outcome question (binary):
For each factual claim and each first-person experiential claim
in the voice-script, can the reader trace the claim — to a cited
source for factual claims, OR to a pattern-data anchor (or
explicit scripted-fiction flag) for first-person claims? Or does
the plan include claims the creator would have to fabricate on
camera or quietly drop before production?

Score 1 (yes) — Every factual claim (stat, study, named-source
quote) has a citation in the plan's source list AND every
first-person experiential claim either (a) matches a pattern-data
anchor, (b) is flagged scripted-fiction, or (c) is generically
lived-in.

Score 0 (no) — At least one stat / study / quote asserted with
no citation; OR a specific first-person claim cannot be matched
to pattern-data and is not flagged scripted.

Score 0.5 (unknown) — Citations or anchors partially present;
at least one major claim is borderline. Emit 0.5 + "unknown" +
one sentence on which claim is unanchored.

Required CoT:
- Step 1: List every factual claim in the voice-script.
- Step 2: List every first-person experiential claim.
- Step 3: For factual claims, verify citation; for experiential
  claims, verify pattern-data anchor or scripted-fiction flag.
- Step 4: Emit verdict + one-sentence justification.

Do not score: citation count, source quality, completeness of
pattern-data.
```

**Edit 2 — ≤5-ceiling exception.** Per design guide §5 amended clause, SB-6 is justified breach: literature documents an LLM-specific failure surface (open-ended 40–80%, citation 19.9%, episodic-memory absence) SB-1..SB-5 cannot catch. Redundancy check applies — if SB-6 correlates >0.7 with SB-1 (voice anchor) or SB-3 (earned arc) across re-runs, redundant criterion gets dropped to restore 5. Most-likely-to-merge: SB-1 ↔ SB-6 (both test grounded-vs-ungrounded at different layers).

**Edit 3 — Sharpen SB-3:** add hook-promise / body-payoff coherence test + single-signal-extension penalty.

**Edit 4 — Sharpen SB-4:** extend from "AI-model can render" to "AI-model can render AND creator can plausibly source" (location, rights, guest access).

**Edit 5 — Sharpen SB-5:** explicitly require hook-formula fingerprint variety across the 5 plans.

**Edit 6 — Structural_gate additions:**
- **Stat-grep** — every numeric in voice-script (`\d+%`, `\$\d+`, `\d+x`, ranked-list patterns) must appear in `citations` with source URL.
- **Quote-grep** — every direct quote (string in `""` + attribution verb) must match a verified citation.
- **"As of" date** required on time-sensitive factual claims.
- **Rights-flag grep** — commercial film titles, copyrighted footage, named commercial music in scene-description must be paired with `rights_status: licensed`.

Banned-phrase list extended with AI-slop tells from X / LinkedIn lanes (em-dash density, "let me explain why," "moreover," "furthermore" — StoryScope arxiv 2604.03136 named over-explanation pathology).

---

## 8. First-cohort overfit watch

Following CI v3.3 pattern: failure modes are research-grounded against creator-strategist + general LLM-hallucination literature. They generalize to short-form video creators broadly. **No first-cohort overfit risk specific to this axis.** Only vertical-sensitive sub-shape is Mode 1 *fabricated study citation* — legal/medical/scientific-explainer creators carry higher reputational stakes than lifestyle creators, but the failure mode itself is uniform.

Re-validation trigger: fixtures from new content verticals (children's content, longer-form documentary, music-video) — check whether SB-6 prose generalizes or vertical-specific anchors are needed (e.g., music-video may need a different rights-flag taxonomy).

---

## 9. Open questions

1. **Redundancy check for SB-6.** Most-likely-to-merge pair SB-1 ↔ SB-6. Run pairwise correlation across 5 fixtures × 6 criteria × 3-model panel before propagating.
2. **Pattern-data anchor format.** SB-6 score-1 requires "match against pattern_data anchor" for first-person claims. Current `pattern_data` is free-form blob; SB-6 needs `recurring_anecdotes` or `personal_history` field at minimum. Operator-side schema cleanup required.
3. **Cold-start (no pattern data).** SB-1 already faces this. SB-6 inherits — when `pattern_data == {}`, every first-person claim auto-fails. Recommendation: when empty, SB-6 collapses to "are all first-person claims explicitly flagged scripted-fiction OR generically lived-in?"
4. **Stat-grep regex robustness.** False-positive risk on time-codes ("at 0:35"), scene-numbers ("scene 3"), shot-lengths ("3-second hold"). Calibrate against real-fixture voice-scripts.
5. **Rights-flag list maintenance.** Most operationally expensive structural_gate addition. Can defer to v2 if SB-6 judge-side coverage suffices at launch.
6. **Sample-consistency check.** Generate same plan 3× with different seeds; flag claims that don't appear in all 3 as "low-confidence." Workflow side, not judge. Defer to v2.
7. **Propagation to other lanes.** Modes 1–3 generalize across content lanes (X, LinkedIn, marketing_audit). Cross-lane convergence on stat-grep / quote-grep / "as of" date is likely.

---

## 10. Citations with effect sizes

**Open-ended hallucination rates:**
- sqmagazine 2026 ("LLM Hallucination Statistics 2026"): open-ended 40–80%; summarization-grounded <2%; legal QA 75%.
- Suprmind 2026: legal 18.7%; medical 15.6%; best-model floor 0.7% on summarization.

**Citation hallucination:**
- Chelli et al. 2025 (EurekAlert): 19.9% GPT-4o citations in lit reviews fabricated.
- GhostCite (arxiv 2602.06718): 14–95% across 13 LLMs × 40 domains.
- Compound Deception (arxiv 2602.05930): NeurIPS 2025, 100 hallucinated citations in 53 accepted papers (1%); Total Fabrication 66%, Partial Attribute Corruption 27%, Identifier Hijacking 4%.
- GPTZero ICLR 2026: 50 of 300 submissions with obvious hallucination despite 3–5 expert reviewers.
- arxiv 2604.03173: web-search-grounded models still 3–13% URL hallucination.

**Legal-case fabrication (transfers to "Harvard study" patterns):**
- Stanford 2024 RegLab: 75% case-fabrication on court rulings.
- Charlotin database 2026: 1,227 documented court submissions globally.

**AI fiction idiosyncrasies:**
- StoryScope (arxiv 2604.03136): 10,272 prompts × 5 LLMs. Claude flat event escalation; GPT over-indexes on dream sequences; Gemini defaults to external character description. AI stories over-explain themes, favor tidy single-track plots, cluster in shared narrative space; human stories more diverse, morally ambiguous, temporally complex.
- arxiv 2505.01800 (Psycholinguistic Analysis): 31 stylometric features mapped to cognitive processes. "AI models... lack experiential grounding... AI-generated sentiment is based on statistical patterns rather than experiential grounding."

**Narrative-arc gaming:** arxiv 2509.04239: AI stories "unconvincing, repetitive, or misaligned with desired tone or character development."

**Video-LLM hallucination:**
- Moonlight 2026 (Survey on Hallucination in Video LLMs): dynamic distortion + content fabrication driven by statistical priors.
- Artlist 2026: "vague prompts, missing references, or conflicting requests often lead to confident fabrication."

**Hook formulas + algorithm penalties:**
- TikTok 2026 (Socialync May; Napolify July 2025): duplicate-content includes "identical trend templates without adding substantial originality."
- YouTube 2026 (Mohan January letter; eweek; Kapwing): 1 in 5 recommended Shorts is AI-slop; 278 AI-slop channels at 63B views / $117M ad revenue; ~33% of feed AI-generated.
- OpusClip Shorts: 80–90% completion for top performers; below 50% triggers suppression. Silent bold-caption +40% completion; early-CTA +58% conversion.

**Sycophancy / CoT-rationalization (Mode 2 background):**
- BrokenMath (arxiv 2510.04721): CoT enables "rigorous-sounding justifications for the wrong answer."
- arxiv 2603.16643: LLMs sacrifice factual accuracy "to cater to user's perceived beliefs."
- Eidoku (arxiv 2512.20664): hallucination "often a failure of structural consistency rather than low-confidence."

**SB context:**
- `docs/handoffs/2026-05-18-judge-design-step1-storyboard.md` (v0).
- `docs/research/2026-05-15-judges-domain-storyboard.md` (domain — 85% coverage, 3 gaps).
- `docs/research/2026-05-18-ci-ai-failure-modes.md` (sibling; template).
- `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` (CI v3.3 ≤5-ceiling pattern).
- `docs/rubrics/judge-design-guide.md` v2.1 (§5 exception clause).
