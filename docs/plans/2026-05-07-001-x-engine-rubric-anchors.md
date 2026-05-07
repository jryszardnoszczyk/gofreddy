# X-1..X-6 + LI-1..LI-6 Rubric Anchors

Companion to `2026-05-07-001-x-engine-autoresearch-port-master-plan.md` §4.4.

12 prose anchors authored at L2 in `src/evaluation/rubrics.py` (`_X_1`..`_X_6` + `_LI_1`..`_LI_6`). 1/3/5 anchor format mirroring `_GEO_1`..`_GEO_8`. All `scoring_type='gradient'`. X-6 + LI-6 are `is_cross_item=True`.

JR's pre-L0 F4 task scores these against 10-20 reference posts (emulation set + 5 external triangulation posts). If any score ≤6, anchor is wrong — rewrite before L2 prose-block authoring locks them.

## X-1..X-6 (x_engine; rendered into `scorer_templated.md` via `_render_criteria_for_domain("x_engine")`)

| ID | Anchor (50-100 words each) |
|---|---|
| X-1 | JR's voice — first-person, opinionated, plain-language register accessible to a non-engineer founder/marketer. Jargon without inline plain-English context caps this dimension. AUTOMATIC ≤4 if 2+ unexplained technical terms; AUTOMATIC ≤6 if any jargon without plain-English follow-up. |
| X-2 | Factual specificity. SOURCE claims must verify against source_text. INTERPRETIVE claims framed as JR's view ('my read', 'in our work') OK. **HARD FLOOR:** any first-person specific lived-work claim ('when I built X for client Y') REQUIRES the named entity to appear in `programs/references/voice.md` (shared substrate, loaded into source_data). Unnamed-client claims → ≤3. |
| X-3 | Hook strength. SHARP brackets — first 8-12 words carry the punch. BUILD/CASE-STUDY — first 1-2 sentences earn line two (beat the show-more cutoff). Generic openers and rhetorical-question hooks ≤4. |
| X-4 | Slop-freeness. Zero AI-tells. Banned phrases per `slop_gate.py` regex are a deterministic floor; this dimension judges what slips through. |
| X-5 | Structural richness. Bracket-aware: SHARP earns 10 with one sharp claim+support pair; BUILD earns 10 with prose intro + structural pivot + 3-5 substantive bullets + authority anchor + outcome metric; CASE-STUDY earns 10 with multi-paragraph narrative + sensory detail + numbers timeline + implication close. Pad-to-length = ≤4. |
| X-6 | Cross-item: across drafts in this cohort, no two use the same primary differentiator, source, or hook archetype. The variant should spread across `voice_pillars` listed in angle metadata. (geometric mean across `drafts/*.md`.) |

## LI-1..LI-6 (linkedin_engine; rendered via `_render_criteria_for_domain("linkedin_engine")`)

| ID | Anchor (50-100 words each) |
|---|---|
| LI-1 | JR's LinkedIn voice — first-person, story-led, professional register accessible to B2B buyers + agency operators + C-suite. Plain language still required (jargon caps voice score) but tone is noticeably less contrarian than X. AUTOMATIC ≤4 if it reads as bait-y, hot-take-y, or "Twitter-translated"; AUTOMATIC ≤6 if jargon without plain-English follow. The lever is *thoughtful authority*, not *contrarian punch*. |
| LI-2 | Factual specificity. Same SOURCE/INTERPRETIVE split as X-2. **HARD FLOOR:** lived-work claims REQUIRE the named entity to appear in `programs/references/voice.md` (shared substrate, loaded via load_source_data). Specific claims about unnamed clients/projects → ≤3. LinkedIn audience punishes vague claims harder than X audience does — score ceiling capped at 7 for any first-person specific claim that doesn't name the entity. |
| LI-3 | Hook strength. LinkedIn rewards story-led openings ("Last quarter I learned X.") + concrete-result openings ("47 hours of agent debugging led to one config change.") + before-the-fold tension. PUNISHES contrarian hot-takes that work on X ("Most marketers don't realize..." → ≤3 on LinkedIn even though it works on X). First 1-2 sentences earn line two (beat the show-more cutoff at ~210 chars on web LinkedIn). Generic openers ≤4. |
| LI-4 | Slop-freeness. Zero AI-tells AND zero LinkedIn-AI-tells. Banned phrases include the deterministic regex floor (`slop_gate.py --platform linkedin`) PLUS LinkedIn-specific tells: "Game-changer.", "Here's what I learned." (alone), "Thoughts? 👇", "Agree? 🤔", excessive line breaks for whitespace inflation, fake "Hot take:" framings. This dimension judges what slips through the deterministic gate. |
| LI-5 | Structural richness + hashtag-count quality. Bracket-aware: SHORT_TAKE (500-900) earns 10 with story-opening + 1 substantive paragraph + closing thought; THOUGHT_LEADER (1500-2500) earns 10 with story → frame → 3-5 numbered points → implication close; CASE_STUDY (2500-3000) earns 10 with multi-paragraph narrative + numbers timeline + named characters + implication close. Pad-to-length, "I'm sharing this because..." filler, motivational-poster generality = ≤4. **Hashtag-count component:** 3-5 targeted hashtags = ideal (no penalty); 1-2 = suboptimal (cap dimension at 7); 0 = ≤4 (zero-tag posts get less LinkedIn distribution). Spam guardrail (count > 5) hard-fails at structural_gate, never reaches this rubric. |
| LI-6 | Cross-item: across drafts in this cohort, narrative archetype varies (story-led vs lesson-led vs comparison) and drafts spread across `voice_pillars`. PUNISHES same-tone-same-format streak. (geometric mean across `drafts/*.md`.) Note: hashtag-set diversity is NOT scored here — same-pillar drafts may legitimately share signature 3-tag combos for brand consistency; per-draft hashtag count ∈ [3,5] is enforced deterministically by structural_gate, not by judge. |
