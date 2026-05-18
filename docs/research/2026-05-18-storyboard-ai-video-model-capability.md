# Storyboard Judge — AI-Video-Model Capability Awareness (2026-05-18)

**Scope.** AI-video-model capability axis for the storyboard lane. Goes beyond `2026-05-15-judges-domain-storyboard.md` (which validated SB-1..SB-8 generically and noted Sora 2 / Veo 3.1 / Runway Gen-4.5 / Kling as the practitioner reference set) by mapping the *current as of May 2026* capability boundaries across the live model fleet, the failure mode where a plan demands shots the model can't render, and what `structural_gate` can verify deterministically versus what the LLM judge must reason about. Companion to `docs/handoffs/2026-05-18-judge-design-step1-storyboard.md` SB-4 ("Within current AI-video-model capability").

**Hard constraints respected.** Outcome questions, binary anchors, no σ-widening / anti-gaming / framework-name embedding, route verifiables to `structural_gate`, reference-free, defend per failure mode. No overlap with the creator-voice-fidelity axis (separate research, `2026-05-18-storyboard-creator-voice-fidelity.md`), the pattern-data cold-start axis (`2026-05-18-storyboard-pattern-data-cold-start.md`), or the generic AI-failure axis (CI / MA siblings).

---

## TL;DR

1. **The fleet rotated under us between Jan and May 2026, and the SB-4 anchor list in the v0 spec is partially stale.** Sora 2 shipped Sep 30 2025; Veo 3.1 shipped Oct 16 2025; Runway Gen-4.5 shipped Dec 1 2025; Kling 3.0 (multimodal, multi-shot-native) shipped in Q1 2026; Luma Ray 3 / Dream Machine 2.0 shipped March 2026; Pika 2.5 shipped early 2026; Veo 4 shipped late April 2026. **OpenAI sunset the Sora consumer product on April 26 2026** (API continues until September 2026 for partners). The spec's "Sora 2, Veo 3.1, Runway Gen-4.5, Kling" anchor list is correct for what fixtures were rendered against in Q1 2026, but the *current* available fleet is Veo 4 / Kling 3.0 / Runway Gen-4.5 / Luma Ray 3 / Pika 2.5 — Sora is gone.

2. **There is no single "current capability" — there is a fleet with overlapping but non-identical envelopes, and the storyboard has to specify against whichever model the workflow will actually call.** Native clip length runs from 4-5 s (Pika 2.5 default, Runway base) to 15 s (Kling 3.0) to 25 s (Sora 2 historical, Pika via Pikaframes). Multi-shot continuity is native-multi-shot in Kling 3.0 (up to 6 cuts in one generation) and Veo 3.1+ (Scene Extension / Ingredients), versus stitch-and-pray for everything else. **Specifying "smooth dolly through 4 rooms with the same actor" — the canonical fail case — fails on every model in the May 2026 fleet.**

3. **Five capability boundaries persist across the fleet in May 2026 and are unlikely to clear within 6 months.** (a) Legible long text on signs / screens, (b) sustained character-consistent multi-character interaction in one shot, (c) precise lip-sync to externally-authored dialogue across cuts, (d) multi-constraint camera moves ("dolly while orbiting and panning"), (e) sub-second-precise timing of named beats ("at 0:35 the back door opens"). Each is a documented failure mode in 2026 benchmark coverage. Storyboards that demand any of these without a fallback path waste production money.

4. **Three failure modes for capability-blind storyboards.** (i) Wasted credit spend on regenerate-loops with 15-25% rejected output (industry-reported credit waste rate); on a 60-second AI-generated piece costing $4-36 in raw model time, brand-grade output averages $75-175 once rejection is accounted for. (ii) Visible AI-rendering artifacts ship into the final cut because the team didn't have budget or time for another regen pass — viewers see warping faces, drifting clothing, illegible product names. (iii) Fallback to traditional shoot mid-production — the plan becomes a partial spec, the original premise gets distorted to whatever the live-action crew can salvage in the window.

5. **The judge's job is "feasibility given the named model" — not "rate the model."** The storyboard does NOT have to bound itself to the *most conservative* model in the fleet; it has to bound itself to the model the workflow declares it will use, plus a stated fallback for shots that exceed that model's envelope. SB-4 (v0) already says this implicitly via "Sora 2, Veo 3.1, Runway Gen-4.5, Kling" — but the criterion needs to *name the declared model* as the input to feasibility judgment, not assume a canonical fleet floor that won't survive the next quarter's model rotation.

6. **The structural_gate / judge split for SB-4 is sharper than the v0 spec suggests.** `structural_gate` can deterministically check: (a) declared model name is in the supported list, (b) every scene declares a duration ≤ that model's native clip length OR a stitch-strategy field, (c) consistency-anchor section is present with required fields, (d) no scene contains a banned-construct phrase (long legible text, externally-authored dialogue with lip-sync requirement, etc.) without a fallback flag. The LLM judge then evaluates: does this plan, *given those structural facts*, actually produce a video the creator could ship — or is it structurally compliant but semantically over-ambitious?

7. **The 6th-criterion question (per design guide §5 exception): does AI-video-model capability deserve its own criterion (SB-6 in original numbering), or absorb into SB-4 / SB-5?** Current v0 spec absorbs it into SB-4 already. Recommendation: KEEP the absorption — capability awareness is structurally testable enough that the SB-4 outcome question "can the model render this at usable quality" carries the load with structural_gate doing the heavy lifting. A separate SB-6 only earns its keep if the redundancy check shows SB-4 collapsing semantic and capability-awareness signals — flag for the empirical redundancy pass per design guide §5.

---

## Key questions answered

### Q1 — What are the CURRENT (May 2026) capability boundaries per top-fleet model?

The fleet has rotated meaningfully since the Jan 2026 baseline. Live-as-of-May-2026 state:

**Sora 2 (OpenAI) — SUNSETTED for consumer April 26 2026, API ending September 2026.** Historic capability: 4-20 second clips (default 4, max 25 with storyboard mode), 1080p, multi-shot storyboard with 3-12 named shots maintaining character/lighting/scene continuity in one generation, native synchronized dialogue + sound effects, ~95% subject-consistency retention with proper prompting (per OpenAI's October 2025 system card), Cameo system for 2 reference characters. The Sora 2 prompting guide explicitly required dialogue in a code block so the model distinguished visual description from spoken lines. **In May 2026, fixtures that ran against Sora 2 are historical — any new generation has to route to a different model.** This is a material change since the v0 spec was authored.

**Veo 3.1 (Google DeepMind) — released October 16 2025.** Up to 60-second 1080p clips with native audio. Scene Extension generates new clips conditioned on the last second of the previous clip — extends to ~1 minute with maintained visual continuity. "Ingredients to Video" takes up to 3 reference images for character / object / style. "Frames to Video" takes start + end frame and generates the transition. Character consistency in short sequences is competent but drifts in longer-form; Kling 3.0 outperforms it on cross-shot character identity per multiple 2026 head-to-head benchmarks.

**Veo 4 (Google DeepMind) — released late April 2026.** Up to 30 seconds native (longer via stitch), 4K output, zero-shot avatar creation, scene-aware multi-shot generation where consecutive shots share lighting and subject consistency, ~70% reduction in common AI-video artifacts versus Veo 3.1 (per Google's published comparison). Access via Google Flow, Gemini, AI Studio API tier. This is the new ceiling for character continuity through camera motion.

**Runway Gen-4.5 — released December 1 2025.** Currently #1 on the Artificial Analysis text-to-video leaderboard (1,247 Elo as of latest benchmark). Native audio generation, multi-shot sequencing with arbitrary-duration editing (consistent transformations across multiple shots), up-to-1-minute character-consistent long-form video, physics-emphasis training (weight / inertia / cloth / fluids / collisions). Strongest model for emotion-on-face and faces-staying-stable-through-motion in production benchmarks.

**Kling 3.0 (Kuaishou) — Q1 2026 release.** Native multimodal: video + audio + images in one architecture. Clips 5-15 seconds (default range), native 4K, 60 FPS. Multi-shot mode generates up to 6 named camera cuts in ONE generation maintaining character consistency across cuts (the closest to Sora 2's storyboard mode now that Sora is sunset). Native lip-sync in 5 languages. Best price-performance leader in the fleet at ~$0.07 / second of output.

**Luma Ray 3 / Ray 3.14 / Dream Machine 2.0 — March 2026 (Ray 3), January 2026 (Ray 3.14 1080p 4× speed upgrade).** Cinematic camera moves are the marketing axis: dolly / crane / orbit / handheld specified via visual timeline. World-first studio-grade HDR with native high-dynamic-range output exportable to 16-bit EXR for pro post pipelines. Physics-informed loss term during fine-tuning — fluid dynamics, cloth, rigid-body collisions reportedly pass blind-evaluator tests at higher rates than alternatives. Ray 3 Modify enhances real-actor performances rather than generating from scratch.

**Pika 2.5 — early 2026.** Layered motion control with prompt-level direction of camera / subject / environmental motion independently. Native clip 3-5 seconds default, extendable to ~15 seconds via Scene Extension and ~25 seconds via Pikaframes (iterative chained extension). The first release positioning camera language as a "first-class citizen" — i.e., the camera-direction parameters route to a different subsystem than scene description.

**The fleet's overlapping envelope.** All models in May 2026 can do: 4-15 second 1080p clips, single-character continuity within one clip, basic camera motion (dolly / pan / orbit when specified cleanly), text-to-video and image-to-video. None reliably do: legible long text on signs, externally-scripted dialogue with cut-to-cut lip-sync, sub-second-precise timing of named beats, smooth multi-room continuity with stable character through environmental change, complex multi-character choreography with both characters consistent.

### Q2 — For a storyboard intended for AI-video generation, what specifications MUST NOT exceed model capability?

The set of "MUST NOT exceed" specifications, mapped to the current fleet:

**(a) Per-scene duration > native clip length.** Veo 3.1's Scene Extension and Pikaframes mitigate this by stitching, but each stitch boundary is a continuity risk. A scene specified as "20 seconds, single shot, continuous motion" on a model with 5-second native clip means 4+ stitch boundaries — and per Veo 3.1 documentation, the extension conditions only on the *last second* of the previous clip, so subject pose, lighting, and prop positions can drift at every boundary. Storyboards should specify continuous motion within native-clip duration or explicitly call the cut.

**(b) Externally-authored dialogue requiring lip-sync.** Native dialogue authored in-prompt (described in the Sora 2 / Kling 3.0 convention as dialogue-in-code-block) lip-syncs better than dialogue authored externally and dubbed onto AI-rendered video. For storyboards where the dialogue is load-bearing (a creator's monologue, a brand spokesperson), AI generation is currently the wrong tool — fall back to traditional shoot for those scenes. Veo 3.1 and Kling 3.0 native lip-sync is "competent in short clips" but a tracked failure mode in rapid-motion sequences.

**(c) Legible product names / brand text / on-screen UI text.** Across the fleet in May 2026, on-screen text is the most reliable model failure mode — letters morph, words are unreadable, brand names degrade into similar-looking glyph soup. Storyboards specifying "logo visible on the cup" or "phone screen shows 'Tinder match'" should treat that text as either non-load-bearing (model can fail and the scene still works) OR plan to composite the text in post.

**(d) Complex multi-character interaction in one shot.** Two characters with named consistent appearance, both maintained through interaction, both lip-synced if speaking. The fleet handles this poorly; Veo 4's scene-aware multi-shot is the strongest implementation and still has measurable drift. Storyboards that put 3+ named characters in one shot are mostly unfeasible at usable quality.

**(e) Multi-constraint camera moves in a single prompt.** "Dolly in while orbiting and panning right while the subject walks left" overspecifies the geometric solution. The model produces mush. Even Pika 2.5's first-class camera-language treatment cannot satisfy 3 simultaneous geometric constraints plus subject motion plus style. Storyboards should specify ONE primary camera move per shot, with secondary motion either implicit or absent.

**(f) Sub-second-precise beat timing.** "At 0:35 the camera pans to the door" presumes the model can hit a frame-accurate timestamp. Native generation doesn't expose that level of timing control. The beat has to either survive being off by ±15-20% of the named timestamp OR live in a separately-generated cut whose duration is the model's degree of freedom.

**(g) Smooth continuous environmental change across one shot.** "Walk through 4 rooms with the same actor" requires lighting, set, prop, and clothing all maintained through environmental transitions. The fleet does not do this reliably at any duration. Each environmental change should be its own shot with explicit cut.

**(h) Specific physical actions outside the training distribution.** Fine motor work (hands manipulating small objects, instrument fingering, sign-language), specific sport-form (precise martial-arts technique, surgical hand motion), animal behavior beyond the most common species. Even Sora 2's "Olympic gymnastics + cat on shoulders" demo was a calibrated showcase — the long tail of fine-motor accuracy remains a fleet-wide weakness.

### Q3 — What is the failure mode when storyboards demand impossible shots?

Three documented failure modes, ordered by frequency in the storyboard-to-AI-render pipeline:

**Failure mode 1 — Wasted credit spend on regenerate-loops.** Industry-reported credit waste rate is 15-25% across all production AI-video workflows in 2026 — meaning the listed per-second cost ($0.06-0.75 depending on model) understates real spend by ~20%. The waste concentrates on shots that should have been flagged as out-of-envelope at the plan stage: long legible text, multi-character lip-sync, multi-room continuity. A creator working a $200/month subscription pipeline against a Veo 3.1 budget loses 20-50 credits to regenerates per project specifically when the plan exceeds capability. At higher-spend tiers (a 3-minute brand short at $75-175 total raw cost), the proportion holds — and the unrecoverable hours of creator review time on rejected gens are the real cost.

**Failure mode 2 — Visible AI-rendering artifacts ship into the final cut.** When budget and time run out and the team can't afford another regen pass, the gen-with-artifacts ships. Viewers see: faces warping between frames, hands with the wrong finger count, drifting clothing patterns through motion, product labels degraded into glyph soup, backgrounds melting at the edge of camera motion. The 2026 benchmark literature catalogs this as the dominant "lossy-handoff" failure — the team trusted the plan, the plan exceeded the model envelope, the model produced an artifacted output, and the editing team couldn't recover it without a reshoot they couldn't afford.

**Failure mode 3 — Mid-production fallback to traditional shoot.** The most expensive failure mode. Plan was designed for AI render, half the shots regenerate cleanly, half don't. The team commissions a live-action shoot for the remaining shots — but the live-action crew can't replicate the AI-generated character (no real-world actor matches the synthetic look), so the plan distorts to whatever combination of AI and live-action the team can salvage. The original premise erodes through compromise. This is the failure mode where capability blindness in the plan causes the deepest cost — the salvage operation costs more than a from-scratch live-action shoot would have.

### Q4 — How does the judge score "shot list realism" given the AI-video model in use?

The judge's question is NOT "is the model capable of this in the abstract" but "given the workflow has declared model X as the renderer for this plan, does each scene specification stay within model X's envelope, or does the plan flag the out-of-envelope scenes with an explicit fallback strategy?"

This decomposes into the structural_gate / judge split per design guide §2:

**`structural_gate` (deterministic pre-check) handles:**

- Declared model field present and matches a supported model (Veo 3.1 / Veo 4 / Runway Gen-4.5 / Kling 3.0 / Luma Ray 3 / Pika 2.5)
- Every scene declares duration; sum of durations ≤ declared total runtime
- For scenes with duration > declared model's native clip length, an explicit `stitch_strategy` field is present (values: `scene_extension`, `pikaframes`, `manual_cut`, `multi_shot_native` for Kling 3.0)
- Consistency-anchor section is present with required fields: subject name, appearance markers, lighting key, prop list, environment markers
- No scene contains banned-construct phrases without a fallback flag: "legible text reading [content]", "lip-sync dialogue to [external audio]", "complex multi-character interaction" (>2 named characters speaking)
- For multi-character scenes, the `character_continuity_anchor` field names the reference image(s) used
- Per-scene camera-move count ≤ 2 simultaneously specified motions
- Banned-phrase list includes "smooth continuous motion through [N>1] rooms / environments / locations"

These are factual checks. They live in `structural_gate` because they are deterministic — a judge LLM scoring them adds Goodhart surface without adding signal.

**LLM judge (SB-4) evaluates:**

- Given the named model and the scene specifications, would the creator who reads this plan have confidence the rendered output will look professional — or do they have to mentally flag scenes as "this one is going to need 5 regens"?
- Are the consistency anchors functional engineering decisions (specific named appearance markers, specific lighting key, specific prop continuity rules) — OR decorative restatement ("the character looks consistent" without specifying what stays identical)?
- For scenes that exceed model envelope, does the fallback strategy actually resolve the gap — or is it pro forma flagging without a real plan?

The judge's CoT for SB-4 should walk:

1. Identify the declared rendering model (from the plan metadata).
2. List every scene specification.
3. For each scene, map specification against the model's published capability envelope (durations, multi-character, text, camera moves, beat timing).
4. Flag in-envelope vs out-of-envelope; out-of-envelope scenes require a usable fallback.
5. Evaluate consistency anchors for functional engineering vs decorative restatement.
6. Emit verdict: would the creator ship this plan to render OR send it back for capability-aware rework?

### Q5 — What changed Jan-2026 to May-2026 in the AI-video fleet?

Five material changes that affect the SB-4 anchor list:

**(1) Sora 2 sunset for consumer April 26 2026.** OpenAI cited "unsustainable economics, significant drop in active users, cancellation of a major partnership" in their announcement; API access continues until September 2026 for existing partners but new fixtures should not be planned against Sora. The v0 SB-4 anchor list naming Sora 2 is correct for historical fixture interpretation but stale for forward-looking renders.

**(2) Veo 4 release late April 2026.** New ceiling for character continuity through environmental motion and zero-shot avatar creation. Plans that previously had to fall back to live-action for "this exact face through this exact arc of motion" can now route to Veo 4. The judge must know this is now an option.

**(3) Kling 3.0 multimodal architecture Q1 2026.** Native multi-shot mode (6 cuts in one generation maintaining character) is the closest replacement for Sora 2's storyboard mode, which had been the practitioner default for multi-shot plans. Kling 3.0 is now the multi-shot-native default and the SB-4 judge has to treat Kling-rendered plans differently from single-clip Runway plans.

**(4) Luma Ray 3 / Dream Machine 2.0 March 2026.** Camera-move-first positioning, HDR native output. For storyboards where camera language is load-bearing (cinematic brand work, narrative shorts with deliberate camera grammar), Luma Ray 3 is now the strongest renderer in the fleet.

**(5) Runway Gen-4.5 December 2025.** Took the #1 position on Artificial Analysis text-to-video leaderboard. Strongest face-stability-through-motion (the historical Runway weakness) is now a strength. Multi-shot sequencing arrives with arbitrary-duration consistent transformations.

**Implications for SB-4:** The criterion prose should NOT enumerate fixed model names (they will rotate again by Q3 2026). Instead, the criterion references the workflow-declared model field and depends on the structural_gate to enforce that the declared model is in the supported list. The supported-list is a configuration parameter that the operations team updates as the fleet rotates — not embedded in judge prose.

---

## Synthesis — what this means for SB-4

The v0 SB-4 spec ("Within current AI-video-model capability") is structurally correct but mis-anchored against a Jan-2026-vintage fleet. The judge's job is feasibility-given-declared-model, not feasibility-against-a-canonical-fleet-floor. Three design moves follow:

**Move 1 — Route the model-name anchor out of judge prose into structural_gate.** The criterion does NOT hardcode "Sora 2, Veo 3.1, Runway Gen-4.5, Kling" in its prose. Instead, the prose references "the declared rendering model" and the structural_gate enforces that the declared model is in the operations-team-maintained supported list. The supported list is a config file (`configs/storyboard/supported_models.yaml`) updated quarterly as the fleet rotates. **This decouples judge stability from fleet rotation.** When Veo 5 ships and Kling 4 launches, the rubric prose does not change — only the config.

**Move 2 — Treat capability awareness as a structurally testable property where possible, and a judgment call only for the residual.** The list of structural_gate checks in Q4 above is the durable layer. The judge's residual is "consistency anchors as functional engineering vs decorative restatement" and "would the creator ship this plan or send it back" — both of which require reading the plan with creator-empathy and judging the gap between specification and probable render. These are genuine judgment calls.

**Move 3 — Defend specifically against the three failure modes named in Q3.** The SB-4 score-1 anchor should require evidence in the plan that the failure modes are addressed. Score 0 should match "plan contains banned constructs without fallback flags" OR "consistency anchors are decorative restatement" OR "scenes specify fine-motor / multi-character / multi-room continuity without acknowledged risk." Score 0.5 is the way-out when the plan is borderline-feasible and the judge can't commit without knowing the renderer's specific recent track record on this specific shot type.

The v0 SB-4 prose largely does this, with one gap: it does not explicitly require the *declared model* as a plan-level field. Adding that field unlocks both the structural_gate check (model is in supported list) and the judge check (specifications match THIS model's envelope, not a generic floor).

---

## Recommendations — structural_gate vs judge

### What `structural_gate` can verify deterministically (move OUT of judge attention)

1. **Plan declares `rendering_model` field with value in supported list.** Operations-team-maintained list updated quarterly; current as of May 2026: Veo 3.1, Veo 4, Runway Gen-4.5, Kling 3.0, Luma Ray 3, Pika 2.5. Sora 2 historical-only.
2. **Every scene declares `duration_sec` numeric field.** Sum across scenes equals declared total runtime.
3. **For scenes where `duration_sec` > declared model's native clip length, `stitch_strategy` field is present** with a value in {`scene_extension`, `pikaframes`, `manual_cut`, `multi_shot_native`}. The native clip length per model is a config table — Veo 3.1 = 60s with extension, Veo 4 = 30s native, Kling 3.0 = 15s, Runway Gen-4.5 = 60s extended, Luma Ray 3 = ~10s base, Pika 2.5 = 5s base.
4. **`consistency_anchor` block is present once per plan** with required fields: `subject_name`, `appearance_markers` (≥3 specific items), `lighting_key`, `prop_list`, `environment_markers`. Missing fields = structural fail.
5. **Banned-construct lint per scene.** Scene description contains any of these phrases without a `fallback_strategy` field: `"legible text reading"`, `"lip-sync to external"`, `"3 named characters speaking"`, `"smooth continuous motion through 2"` (rooms / environments / locations), `"specific text on (the / a) sign"`, `"fine-motor"` (without a closeup-frame budget noted).
6. **Per-scene `primary_camera_move` field** is a single-value enum: `static`, `dolly`, `pan`, `tilt`, `orbit`, `crane`, `handheld`, `tracking`. Multiple values in this field = structural fail. Secondary motion may be implicit but a `secondary_camera_move` field, if present, may not coexist with `primary_camera_move` other than `static`.
7. **Per-scene `beat_timing_tolerance_sec` field** if any named beat references a specific timestamp; tolerance ≥ 0.3s.
8. **Banned-phrase list extension.** AI-slop tells specifically for storyboard prose: em-dash density > 1 per 100 words, "let me explain why", "moreover" / "furthermore", "the perfect (shot|scene|moment)", "stunning visuals", "captivating imagery".

These checks are deterministic. They live in `structural_gate` per OpenRubrics design principle (Hard Rules → structural_gate, Principles → judge). Routing any of these through the LLM judge adds Goodhart surface without adding signal.

### What the LLM judge (SB-4) evaluates

After structural_gate passes:

1. **Are consistency anchors functional engineering, or decorative restatement?** Engineering: specific named appearance markers (brown hair tied back, navy hoodie, no makeup, cool-key from camera-left), specific lighting key with directional anchor, specific prop continuity rules. Decorative: "the character looks consistent", "consistent lighting", "consistent props" — same words, no information.
2. **For scenes with declared stitch_strategy, does the fallback actually resolve the gap, or is it pro forma flagging?** Pro forma: scene description specifies "30-second smooth dolly through 4 rooms" with stitch_strategy = `scene_extension`. Real fallback: scene description specifies "30 seconds total, 4 cuts, one per room, character continuity anchor noted at each cut" with stitch_strategy = `manual_cut`.
3. **For shots that are in-envelope but ambitious for the declared model, does the plan acknowledge the regen-risk?** Ambitious for Veo 3.1: a 15-second multi-character scene with both characters lip-synced. The plan should either flag this as "expect 2-5 regenerates" OR route the shot to a more capable model OR redesign the shot.
4. **Are out-of-envelope scenes accompanied by a usable plan?** Either route the shot to a different renderer ("this scene is shot live-action, AI render is for B-roll only") OR redesign to fit the envelope. A "we'll figure it out in post" is not a usable plan.
5. **Does the named model match the shot grammar?** Cinematic camera-language plan → Luma Ray 3 is the strongest fit. Multi-shot narrative plan → Kling 3.0 or Veo 4. Single-shot character-stable physics-heavy plan → Runway Gen-4.5. Generic-fits-anything plan → the declared model is a tell about whether the workflow understood its own scope.

The judge does NOT score: model preference in the abstract (any in-list model is acceptable); number of regenerates a real production would take (can't predict from plan alone); whether the model is "the best" for this kind of work (relative ranking would tie the judge to fleet specifics that rotate).

### Open question on criterion count

The v0 spec compresses original SB-6 (AI-model capability) into SB-4 alongside voice-script delivery. With the structural_gate moves above, SB-4's judge-residual is small enough that absorption holds — the LLM judge layer is evaluating 2-3 semi-orthogonal things (anchor-engineering quality, fallback usability, regen-risk acknowledgement) which is on the boundary of what a single criterion should do.

**Recommendation: KEEP the absorption in v1.** Run the redundancy check per design guide §5 across SB-4 and SB-5 specifically — if SB-4 starts correlating tightly with SB-5 (creator pacing + portfolio diversity), redesign the absorption. If SB-4 stays independent but its variance is unusually high across re-runs, that is the signal to split out a separate capability-awareness criterion (SB-6 in the v0 numbering). Variance instrumentation per design guide §11.5 will catch this within 3 generations.

---

## Open questions

1. **Fleet rotation cadence vs supported-list maintenance.** The supported-list (`configs/storyboard/supported_models.yaml` proposed above) needs an owner and a refresh cadence. The fleet rotated 4 major model releases between Jan and May 2026; if that rate holds, quarterly updates are the floor. Who owns this in the ops loop?

2. **Per-model envelope as config vs as judge knowledge.** The native-clip-length table per model is currently spread across vendor documentation. Either (a) the structural_gate config table is canonical and the judge prompt does NOT contain per-model envelope details, OR (b) the judge prompt includes a compact envelope table to reason about fallback usability. Option (a) is cleaner but loses the "would the creator ship this" residual judgment that depends on knowing model-specific weaknesses. Recommend (b) with the table itself referenced rather than re-stated each call — but the table travels with the judge prompt, not in rubric prose, so it doesn't trigger the framework-name-embedding anti-pattern.

3. **Multi-renderer plans (the most realistic production case).** A storyboard for a 3-minute piece might use Kling 3.0 for multi-shot scenes, Luma Ray 3 for the establishing crane shot, and Pika 2.5 for the closing reaction beats — each routed by shot type. The current SB-4 spec presumes one declared renderer per plan. Multi-renderer plans require either (a) per-scene `rendering_model` overrides, or (b) the plan declares a primary model and per-scene exceptions. Defer to v2.

4. **How to score plans for AI rendering when the team has not yet committed to a renderer.** Some early-stage plans are renderer-agnostic on purpose — they specify shots and the team will route them. SB-4's strict "declared rendering model" requirement may be too strict for that pre-commitment stage. Possibly a separate `lane_stage` field: `pre_commitment` (judge evaluates against fleet floor) vs `committed` (judge evaluates against declared model). Defer to v2.

5. **First-cohort overfitting.** Current Klinika + DWF clients do not have heavy AI-video-rendering use cases — Klinika is image-led (clinical before/after, denied per content_denylist) and DWF is text-led. The first real storyboard fixtures with serious AI-video render targets will likely be media-native B2C clients (creator-economy, DTC, entertainment). When those onboard, re-validate the SB-4 capability envelope against their actual production constraints — they may need stricter envelopes (4K delivery, specific platform aspect ratios) or different fallback strategies (in-house compositing, specialist render farms).

6. **Cost-aware envelope: does the storyboard need a budget annotation per shot?** Production realism on a $200-1000/month creator budget differs from a $5K-50K brand-spot budget. Higher budgets justify regen-loops on ambitious shots; lower budgets require the plan to bound to the model envelope. SB-4 currently treats envelope as binary (in or out); cost-awareness would make it a continuous variable. Defer — likely belongs in a separate `production_constraints` block rather than in SB-4 judge prose.

7. **Latency between model release and SB-4 anchor update.** Veo 4 shipped April 30 2026; this research lands May 18 2026; the next time the spec is reviewed against Veo 4-rendered fixtures may be Q3 2026. There is a window of 2-3 months where the spec lags the live capability. Mitigation: the supported-list config makes the lag less painful (operations team updates config without touching judge prose) but the empirical validation lag remains.

---

## Citations

Primary release-note sources (verified against vendor sites where possible):

- **Sora 2 (OpenAI), September 30 2025.** OpenAI Sora 2 announcement: <https://openai.com/index/sora-2/>. Sora 2 system card: <https://openai.com/index/sora-2-system-card/>. Sora 2 prompting guide (developers): <https://developers.openai.com/cookbook/examples/sora/sora2_prompting_guide>. Sunset notice April 26 2026: Sora release notes <https://help.openai.com/en/articles/12593142-sora-release-notes>.
- **Veo 3.1 (Google DeepMind), October 16 2025.** Google blog announcement: <https://blog.google/technology/ai/veo-updates-flow/>. Google Developers Blog: <https://developers.googleblog.com/introducing-veo-3-1-and-new-creative-capabilities-in-the-gemini-api/>.
- **Veo 4 (Google DeepMind), late April 2026.** Veo product page: <https://deepmind.google/models/veo/>. Veo 4 release notes (third-party summary): <https://www.veo3ai.io/blog/veo-4-release-everything-you-need-to-know-2026>.
- **Runway Gen-4.5, December 1 2025.** Runway research announcement: <https://runwayml.com/research/introducing-runway-gen-4.5>. Runway changelog: <https://runwayml.com/changelog>. AI Business coverage: <https://aibusiness.com/generative-ai/runway-releases-gen-4-5-video-model>.
- **Kling 3.0 (Kuaishou), Q1 2026.** Kling 3.0 capabilities deep-dive: <https://higgsfield.ai/kling-3.0>. Bonega comparison: <https://bonega.ai/en/blog/kling-3-ai-4k-multimodal-video-generation-2026>. Morphic Kling 3.0 docs: <https://morphic.com/resources/how-to/kling-3.0>.
- **Luma Ray 3 / Dream Machine 2.0, March 2026 (Ray 3); Ray 3.14 upgrade January 2026.** Luma announcement: <https://lumalabs.ai/ray>. Ray 3 Modify press release: <https://lumalabs.ai/press/luma-ai-announces-ray3-modify>. Flowith analysis: <https://flowith.io/blog/luma-ray-3-dream-machine-2-0-hollywood-quality-generative-video-2026/>.
- **Pika 2.5, early 2026.** Pika Labs product page: <https://pikaslabs.com/pika-2.5/>. Pika 2.5 guide: <https://genra.ai/blog/pika-2-5-complete-guide-review>.

Capability boundary / failure-mode sources:

- **AI Multiple text-to-video benchmark 2026** (motion, object permanence, fluid interaction, lighting, composition, multi-motion-source coverage): <https://research.aimultiple.com/text-to-video-generator/>.
- **Atlas Cloud State-of-AI-Video-APIs 2026** (camera movement control, dolly / orbit / tracking shot limitations): <https://www.atlascloud.ai/blog/case-studies/the-state-of-ai-video-apis-in-2026-from-text-to-video-to-cinematic-directing>.
- **Cliprise February 2026 state-of-the-art analysis**: <https://medium.com/@cliprise/the-state-of-ai-video-generation-in-february-2026-every-major-model-analyzed-6dbfedbe3a5c>.
- **Lip-sync error catalog 2026** (rapid-motion failure mode, native vs external dialogue handling): <https://percify.io/blog/fix-ai-lip-sync-errors-a-troubleshooting-guide-for-2025>.
- **Magic Hour AI Video Model Release Tracker 2026** (quarterly fleet rotation patterns): <https://magichour.ai/blog/ai-video-model-release-tracker-2026>.
- **Pricing / credit-waste rate (15-25%)**: Atlas Cloud cheapest API guide <https://www.atlascloud.ai/blog/guides/cheapest-ai-video-generation-api-2026>, SoloAI cost-per-second 2026 <https://soloa.ai/blog/ai-video-generation-cost-per-second-2026>, MindStudio AI filmmaking cost breakdown <https://www.mindstudio.ai/blog/ai-filmmaking-cost-breakdown-2026>.
- **Veo 3.1 vs Sora 2 head-to-head** (multi-shot continuity, character drift): <https://www.glbgpt.com/hub/veo-3-1-vs-sora-2/>. Skywork multi-prompt best practices: <https://skywork.ai/blog/multi-prompt-multi-shot-consistency-veo-3-1-best-practices/>.
- **Runway Gen-4.5 character emotion / face-stability claims**: DataCamp tutorial <https://www.datacamp.com/tutorial/runway-gen-4-5>, Artificial Analysis Elo position (1,247) referenced via TechNow <https://tech-now.io/en/blogs/runway-gen-4-5-the-next-frontier-in-ai-video-generation>.
- **Seedance / Kling / Veo benchmark comparison 2026**: <https://aijourn.com/seedance-2-0-vs-kling-3-0-vs-veo-3-1-ai-video-benchmark-test-for-2026/>.

Companion gofreddy research used as input baseline:

- `docs/research/2026-05-15-judges-domain-storyboard.md` — generalist domain pass naming Sora 2 / Veo 3.1 / Runway Gen-4.5 / Kling as the practitioner reference fleet, recommending SB-6 stays as capability-aware criterion.
- `docs/handoffs/2026-05-18-judge-design-step1-storyboard.md` v0 — current 5-criterion compression, with SB-4 absorbing original SB-5 (voice-script) + SB-6 (AI-model capability).
- `docs/rubrics/judge-design-guide.md` v2.1 — design constraints applied throughout.

**Attribution note on Sora sunset framing.** OpenAI's April 26 2026 sunset of the Sora consumer product is the most material fleet change since the v0 spec was authored. Multiple sources confirm; the most authoritative is the Sora release notes page itself (OpenAI Help Center).
