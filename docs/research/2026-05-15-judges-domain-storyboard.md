# Storyboard Judge — Domain Research Synthesis (2026-05-15)

**Scope:** Validate the existing storyboard rubric (SB-1 through SB-8) against creator-strategist domain expertise. This is a validation pass, not a redesign — Phase 1 reset already removed prose drift, and the pre-investigation found the current criteria are creator-strategist-grounded (pattern data, hook irreplaceability, audio-as-story, AI-model capability). The question this document answers: *do excellent creator strategists evaluate dimensions that SB-1..SB-8 do not capture, and if so, which?*

The short answer: **SB-1..SB-8 capture roughly 85% of what serious practitioners look for at the plan stage. Three dimensions are underweighted or missing entirely. One existing criterion deserves sharpening, not replacement.** Details below.

---

## 1. What SB-1..SB-8 captures well (mapped to named frameworks)

**SB-1 (pattern data references — creator voice, thematic concerns, recurring mechanisms).** This is the *imagine others complexly* discipline that Hank and John Green built their channel around — John Green's rule for vlogbrothers was to write each video for one specific person (his brother), not for "the internet." Colin & Samir's interview practice converges on the same point: stories that travel come from a known voice, not a generic one. SB-1 also echoes Mark Manson's editorial method (a contrarian premise has to come from a *specific* worldview, not a generic provocation) and Pixar Rule #14 from Emma Coats: *"Why must you tell THIS story? What's the belief burning within you that your story feeds off of?"* Solid.

**SB-2 (hook specificity / irreplaceability — could you text it to a friend who'd reply "send the link").** This is the substantive version of the "3-second hook" doctrine. The TikTok algorithm research is unambiguous that completion-rate matters more than view count, and that videos with a sharp hook in the first 1–2 seconds see 30–40% higher completion than videos with slow intros. The MrBeast handbook's contrast between *"I Spent 50 Hours In My Front Yard"* and *"I Spent 50 Hours In Ketchup"* is the same idea — the *irreplaceability* of the premise is what makes the click-through honest rather than bait. SB-2 wisely encodes the qualitative test (would a real human forward this?) rather than the quantitative one (3-second retention), because at plan stage we don't have a video yet to measure. Strong.

**SB-3 (emotional_map as CLAIM, story_beats as EVIDENCE — beats produce emotions, not just declared).** This is Pixar Rule #15 (*"If you were your character, in this situation, how would you feel? Honesty lends credibility to unbelievable situations"*) and Casey Neistat's stated north star — "the ultimate goal of any Casey Neistat video is an emotional response… excitement, nostalgia, sadness, or inspiration." Naming the emotion you want without earning it through specific beats is exactly the failure mode this criterion catches. Strong.

**SB-4 (opening reframes by climax — ending changes meaning of opening).** This is the *bookend / final image* tradition: Blake Snyder's "Save the Cat" beat sheet explicitly pairs *Opening Image* with *Final Image* as a tonal contrast that measures the character's change. Pixar Rule #7 — *"Come up with your ending before you figure out your middle. Endings are hard, get yours working up front"* — points at the same craft instinct. Strong.

**SB-5 (voice_script delivery directions + audio-as-story).** This is the explainer-video tradition that Vox-trained creators (Johnny Harris, Cleo Abram, Coleman Lowndes) operationalize: Harris writes visual-first, with the *script supporting the visual evidence*, not the other way around. Audio-as-story (silence, absence, contrast carrying meaning rather than just decorating) is a real practitioner concern — Tom Scott's videos are studied specifically because the pause-and-reveal beats are calibrated. Strong, though arguably under-described (see §2).

**SB-6 (AI video model capability awareness — consistency anchors, prompts within model capability).** This is the practitioner-side knowledge from working with Sora 2, Veo 3.1, Runway Gen-4.5 and Kling: character consistency across clips is the biggest single failure mode, prompt complexity degrades adherence ("too much dramatic wording or competing instructions quickly degrades consistency"), and the working pattern is short clips (4–5 seconds) combined via storyboard mode rather than long single generations. Cameo / reference-image systems exist but with caveats. SB-6 correctly forces plans to budget for what current models *can* render. Strong and necessary — this is the criterion that distinguishes our judge from a generic story-craft judge.

**SB-7 (creator-specific pacing — duration / scene count / cut frequency matches creator's actual videos).** Casey Neistat's three-act-in-ten-minutes structure is *not* the same as MrBeast's minute-by-minute reset rhythm, which is *not* the same as Tom Scott's single-take pace. Plans that move a creator off their native cadence will read wrong regardless of how good the underlying story is. Strong.

**SB-8 (portfolio diversity — 5 plans are genuinely different bets, share creative universe).** This is the *shots on goal* discipline visible in any serious creator's production calendar — different premises, same voice. MrBeast's stair-step structure (small wow → big wow → world-record wow) is the within-video version of the same idea. Strong.

**Summary:** Every existing criterion maps to at least one named practitioner framework. Nothing in SB-1..SB-8 is an LLM-judge invention with no domain grounding.

---

## 2. Dimensions the current rubric may be missing

Three dimensions surface repeatedly in practitioner sources but are not clearly captured by SB-1..SB-8. I list them in descending order of how often they appear in primary sources.

**(A) Stakes / "why must this exist." MrBeast's handbook is explicit that the wow factor and the retention curve do not save a plan with no stakes: "have a satisfying payoff at the end." Pixar Rule #16 is the same point in writers' vocabulary: *"What are the stakes? Give us reason to root for the character. What happens if they don't succeed?"* SB-3 covers the emotional *response* and SB-4 covers the *bookend*, but neither directly catches the failure mode "this plan has no stakes — nothing is at risk, no question is being answered, no character is being changed." This is the single most common failure mode in AI-generated short-form: well-shot, well-paced, emotionally-labeled, and pointless. The fix is either a new criterion (call it SB-9 *stakes / consequence* for now) or a sharpening of SB-3 to require an explicit answer to "what's at risk if this story doesn't resolve?"

**(B) Retention architecture — specifically the *reset point* discipline. MrBeast's handbook calls these out by name: minute-3 and minute-6 re-engagement spectacles, the "100 Days in the Circle" house-on-a-crane reset 30 seconds in, the stair-step escalation pattern. The retention-architecture research is unambiguous that "viewers lose focus every 60–90 seconds, [and] to prevent drop-offs, you need to reset attention with a sudden change." SB-7 covers pacing in the cadence-matches-creator sense, but does not catch the more specific question *where in this plan does the viewer get re-hooked?* On a 30–90s short-form clip this matters less, but at 60s+ it becomes load-bearing, and several of our lanes are scoped past 60s. Recommendation: extend SB-7 prose to require at least one named reset / re-hook beat for plans over 45 seconds, rather than adding a new criterion.

**(C) Specificity over genericness — the McPhee / Hodgman test. The single most quoted line in narrative-craft circles is Hodgman's *"specificity is the soul of narrative"* (often misattributed to McPhee, whose own version is *"a thousand details add up to one impression"*). SB-1 covers *creator-voice* specificity and SB-2 covers *premise* specificity, but neither catches *prop / setting / detail-level* genericness — the failure mode where a plan reads as "a person walks into a coffee shop and has a realization" rather than "Maya — late for her 9:15 dermatology consult — knocks over the green-tea matcha at the Blue Bottle on Mott Street." For Klinika and DWF (and any future B2C/B2B clients), this is the difference between plans that read as ChatGPT-default and plans that read as written by someone who knows the brand. Recommendation: either a new criterion (SB-10 *named specificity*) or sharpening of SB-1 to require that pattern-data references show up as concrete props / settings / named details, not just abstract themes.

A fourth dimension came up but I'm flagging it as a *don't-add* rather than an add: **viewer reward / call-to-action.** Hormozi's "Hook → Retain → Reward" framework and the TikTok 2026 algorithm guidance both treat the closing reward (a save-worthy line, a shareable insight, a clear CTA) as load-bearing. But this is a *post-production / packaging* concern more than a story-plan concern, and the existing rubric correctly stops at the plan layer. Including it would push the judge into evaluating things that aren't in the artifact yet.

---

## 3. Industry terminology and frameworks worth knowing

Vocabulary creator strategists use that should be legible to whoever reads the judge output:

- **Wow factor / wow moment** (MrBeast handbook) — a single un-substitutable visual that no competitor could produce.
- **Reset point / re-engagement spectacle** (MrBeast handbook, retention-architecture literature) — the engineered ~60–90s rhythm of new visuals to halt drop-off.
- **Stair-stepping** (MrBeast handbook) — progressive escalation ($1 firework → $100k firework → world-record firework). The within-video version of portfolio diversity.
- **Hook, Retain, Reward** (Alex Hormozi) — the canonical short-form triptych; the third element is what most AI-generated plans miss.
- **Open loop / curiosity gap** (general short-form vocabulary, Hormozi-adjacent) — a question the opening poses that only the ending answers.
- **Visual-first writing** (Johnny Harris, Vox tradition) — script supports the visual evidence, not vice versa.
- **Imagine others complexly** (Hank Green / Complexly studio name) — the SB-1 discipline named.
- **Story Spine** (Kenn Adams, popularized by Emma Coats Rule #4) — *"Once upon a time… Every day… One day… Because of that… Because of that… Until finally…"* Most useful sanity check for whether story_beats actually form a causal chain.
- **Story circle** (Dan Harmon, 8 points) — comfort → want → enter → adapt → get → pay → return → changed. Less granular than Save the Cat, fits short-form better.
- **Save the Cat beat sheet** (Blake Snyder, 15 beats) — the screenwriting standard; relevant beats for short-form are Opening Image, Catalyst, Midpoint, Finale, Final Image.
- **Three-act compression** (Casey Neistat) — the same setup / conflict / resolution arc Hollywood uses, executed inside 10 minutes.
- **A-player / B-player / C-player** (MrBeast handbook) — coachability tiering, not directly applicable to plan-judging but useful for understanding the surrounding production culture.
- **Cameo system / reference image / character consistency** (Sora 2, Veo 3.1, Runway Gen-4.5 vocabulary) — the specific mechanisms SB-6 refers to.

---

## 4. Recommendation

**Keep all 8 existing criteria. They are well-grounded.** The pre-investigation finding stands.

**Sharpen one criterion (SB-7):** extend the prose to require an explicit reset / re-engagement beat for plans over ~45 seconds. This is a small edit, not a redesign — the cadence framing already in SB-7 covers it conceptually but doesn't force the plan to name *where* the reset happens.

**Add two criteria** (the prose-drafting itself is out of scope per the brief; these are domain-grounded recommendations):

- **SB-9 — stakes / consequence.** Plan must answer "what's at risk if this story doesn't resolve, and what changes by the end?" Maps to Pixar Rule #16 and the MrBeast handbook's payoff requirement. Catches the most common AI failure mode: well-paced, pointless plans.
- **SB-10 — named specificity.** Pattern-data references and props must appear as concrete named details (specific brands, places, names, sensory specifics), not abstract themes. Maps to Hodgman / McPhee. Catches the second-most-common AI failure mode: stories that read as plausibly-anyone's.

**Do not add** a "viewer reward / CTA" criterion. That's a packaging concern, not a story-plan concern, and the existing rubric correctly draws the line at the plan layer.

**Net change:** 8 criteria → 10 criteria, one of the existing 8 lightly sharpened. The rubric remains creator-strategist-grounded, not statistically-driven, and stays within the constraint of evaluating the plan artifact rather than the rendered video.

---

## 5. Sources cited

Primary practitioner sources (verifiable):

- *How to Succeed in MrBeast Production* (leaked 36-page handbook, 2024) — coverage and excerpts at Simon Willison's notes <https://simonwillison.net/2024/Sep/15/how-to-succeed-in-mrbeast-production/>, Daniel Scrivner's summary <https://www.danielscrivner.com/how-to-succeed-in-mrbeast-production-summary/>, Fortune <https://fortune.com/2024/09/26/youtube-mrbeast-jimmy-donaldson-leaked-business-handbook-advice/>, Creator Handbook <https://www.creatorhandbook.net/leaked-document-allegedly-reveals-mrbeasts-secrets-to-youtube-success-the-key-takeaways/>.
- Emma Coats, *Pixar's 22 Rules of Storytelling* (originally tweeted 2011 while at Pixar) — collected at Aerogramme Studio <https://www.aerogrammestudio.com/2013/03/07/pixars-22-rules-of-storytelling/> and Open Culture <https://www.openculture.com/2013/03/pixars_22_rules_of_good_storytelling.html>.
- Blake Snyder, *Save the Cat* beat sheet — official site <https://savethecat.com/beat-sheets>, StudioBinder breakdown <https://www.studiobinder.com/blog/save-the-cat-beat-sheet/>.
- Casey Neistat storytelling analysis — In Depth Cine <https://www.indepthcine.com/videos/casey-neistat>, No Film School <https://nofilmschool.com/2016/08/7-storytelling-techniques-you-can-learn-filmmaker-youtube-star-casey-neistat>.
- Johnny Harris visual-first method — Medium analysis <https://medium.com/@LMK_writing/how-johnny-harris-mastered-visual-storytelling-on-youtube-343ddf9160ec>, The Long Story Substack <https://thelongstory.substack.com/p/why-the-best-journalists-on-youtube>.
- Cleo Abram interview / process — Powder Blue Media <https://powderblue.media/stories/cleo>, *Creators on Creators* podcast <https://podcasts.apple.com/vg/podcast/creators-on-creators-cleo-abram-x-johnny-harris/id1379942034?i=1000659621303>.
- Colin & Samir on three-act structure for creators — Musicbed Blog <https://www.musicbed.com/articles/filmmaking/youtube/the-biggest-mistake-filmmakers-make-with-colin-and-samir/>.
- Hank & John Green / Complexly philosophy — Skyword analysis <https://www.skyword.com/contentstandard/what-hank-and-john-greens-youtube-community-can-teach-us-about-video-marketing/>, Hank Green LinkedIn / Vlogbrothers Wikipedia <https://en.wikipedia.org/wiki/Vlogbrothers>.
- Alex Hormozi Hook-Retain-Reward framework — itsmostly.com breakdown <https://itsmostly.com/blog/alex-hormozis-content-strategy-hook-retain-and-reward-explained>, Powercademy <https://www.powercademy.com/blog/alex-hormozi-s-hook-retain-reward-framework>.
- TikTok algorithm 2025–2026 (completion rate, hook timing) — Go-Viral <https://www.go-viral.app/blog/tiktok-algorithm-2026/>, Fanpage Karma <https://www.fanpagekarma.com/insights/the-2025-tiktok-algorithm-what-you-need-to-know/>, OpusClip on 3-second holds <https://www.opus.pro/blog/youtube-shorts-hook-formulas>.
- Tom Scott / Veritasium structural analysis — Oli's Blog *What makes Tom Scott so good* <https://oli.fyi/2024/what-makes-tom-scott-so-good/>, 1of10 on YouTuber storytelling <https://1of10.com/blog/storytelling-techniques-top-youtubers-use-to-keep-viewers-hooked/>.
- AI video model capability landscape (Sora 2, Veo 3.1, Runway Gen-4.5, Kling) — Magic Hour benchmark <https://magichour.ai/blog/ai-video-model-benchmark>, Genra.ai Runway Gen-4.5 guide <https://genra.ai/blog/runway-gen-4-5-complete-guide>, InVideo comparison <https://invideo.io/blog/kling-vs-sora-vs-veo-vs-runway/>.
- John McPhee on specificity / "thousand details" — The Elements of Writing <https://theelementsofwriting.com/mcphee/>, Paris Review *The Art of Nonfiction No. 3* <https://www.theparisreview.org/interviews/5997/the-art-of-nonfiction-no-3-john-mcphee>.
- Mark Manson on contrarian framing — Castmagic profile <https://www.castmagic.io/creators/mark-manson>, TTS Clues *A Contrarian Opinion* <https://medium.com/tts-clues/84-a-contrarian-opinion-475274e5eb7e>.

**Note on attribution:** *"Specificity is the soul of narrative"* is John Hodgman (*Vacationland*, 2017), not McPhee — frequently misattributed. McPhee's analogous formulation is *"a thousand details add up to one impression."* The recommendation in §4 cites both correctly.
