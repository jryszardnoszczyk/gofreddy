# Storyboard judge — Phase B research

Calibration corpus for the `storyboard` lane judge. Storyboard produces callable specs (`stories/*.json`, `storyboards/*.json`) that feed fal.ai I2V → composed video. The artifact is a machine-readable plan with three format_modes — narrative (long-form YouTube), educational (TikTok/Reels), brand_authority (LinkedIn). The judge has to grade what an AI video pipeline can actually produce, not what a human filmmaker could imagine.

Mode-agnostic baseline (all three modes share this floor): one move + one action per scene, 20-80 words per scene prompt, 3-5 named colors + named light source + concrete materials, consistency tokens (costume/hair/prop/location) repeated verbatim across scenes because the underlying models have no long-term memory, camera-language fluency (lens + framing + move in cinematography vocabulary). Slop-lexicon ("neon cyberpunk alley", "rain on window", "cinematic", "dramatic lighting") = automatic penalty. Sora 2 and Veo 3.1's own docs ratify this: "think of prompting like briefing a cinematographer who has never seen your storyboard" and "each shot should include only one camera movement and one subject action."

What follows is the per-mode signal taxonomy, the failure modes that separate 9-tier from 5-tier, the Klinika and DWF specifics, the 2026 platform shifts, and the recommendation for how the judge should be restructured.

## 1. Top 9-tier signals — narrative mode

Narrative mode = long-form YouTube. The story plan should generate a video a YouTuber would post unedited, with hook → escalation → climax → resolution. Retention curve and watch-through rate are the ground truth; the judge's job is to grade the *spec* in a way that predicts those outcomes.

**N1. Hook scene is irreplaceable.** Scene 1 contains a frame that could not be lifted from any other video in the same channel without losing meaning. Test: swap scene 1 with scene 1 of any sibling lineage. If the story still parses, the hook is generic. Mechanism: Bilawal Sidhu's high-engagement tweets all start with a specific object (color LiDAR sensor, 3DGS indoor scan, Department of War UFO files) — the object IS the hook. Generic openers ("ever wondered…", "let me tell you about…") fail.

**N2. Camera grammar matches scene intent.** Each scene names lens + framing + move using cinematography vocabulary that maps to real camera behavior in Sora 2 / Veo 3.1: "slow tracking shot following the hiker," "static wide of the workshop, locked tripod, 35mm," "handheld over-shoulder, shallow DoF, 50mm." Sora 2's docs make this load-bearing: "Sora 2 understands 3D space, so specificity here keeps your scene from looking wonky." Test: replace the camera clause with "cinematic shot" — does the model still know what to render? If yes, the grammar was already vacuous.

**N3. Cross-scene consistency tokens repeated verbatim.** Costume/hair/prop/location strings appear verbatim in every scene where the subject appears. Models have no long-term memory; Magic Hour 2026 benchmark weights scene stability at 40% of total quality score, surpassing prompt adherence. Test: diff the subject description across scenes 1, 4, 7. If the descriptions are paraphrases of each other, identity will drift. If they're identical strings, identity holds.

**N4. Emotional map is verified by story beats, not asserted.** The plan's `emotional_map` field (claim) is grounded in the `story_beats` field (evidence): each beat has a concrete action that produces the emotional state, not a label that names it. "Sarah cries" without a beat that earns the cry = unsupported claim. SB-3 already encodes this; for narrative mode it stays essential.

**N5. Pacing grounded in creator's actual videos.** Scene-duration distribution matches the creator's measured cadence (median scene length, hook-to-payoff distance, climax position by % of runtime). Pattern continuation, not invention. SB-7 essential.

**N6. Recontextualizing ending earns the watch.** The final scene reframes the opening — not a twist, a reframe. The viewer rewinds because scene 1 means something different now. SB-4 important-not-essential because not every narrative needs this; comedy and explainer don't.

**N7. Audio cues are scene-synchronous.** Sora 2 and Veo 3.1 both generate native audio; the storyboard names diegetic sound per scene ("metal lathe spinning at 200 rpm, oil sizzle on contact") not non-diegetic mood ("tense music"). Sora 2 docs: "Be explicit about what you want to hear." Generic music cues = wasted capacity.

**N8. Surprise mechanism is creator-pattern-continuous.** Bilawal's surprise mechanism is "ordinary technical demo opens onto geopolitical / philosophical consequence" — color LiDAR → autonomous-vehicle thesis; satellite imagery → Iran war transparency. The storyboard's twist mechanism should match the creator's measured surprise style, not generic "and then something unexpected happens." SB-1 + SB-2 read together.

**N9. Visual specificity floor per scene.** 3-5 named colors, named light source, concrete materials. "Brushed-steel lathe under overhead fluorescent, beige cinderblock wall, single red E-stop button" beats "industrial workshop." This is the Sora 2 / Veo 3.1 prompt-ability discipline; below this floor, the model improvises and identity drifts.

**N10. Prompt-ability sweet spot per scene.** Each scene prompt lands at 20-80 words. Below 20: under-specified, model improvises. Above 80: contradicts itself, model averages. Test: word-count the scene prompts; flag any outside the band.

## 2. Top 9-tier signals — educational mode

Educational = TikTok/Reels vertical explainer, 15-60s, viewer learns one specific thing. Success metric is share rate plus completion rate (TikTok 2026 needs 70%+ completion to go viral, up from 50% in 2024). The judge has to grade for knowledge transfer, not narrative arc.

**E1. Single-takeaway test.** The viewer can finish the video and state ONE specific thing they now know in one sentence. Test: read the plan; write the takeaway in 15 words; if you can't, or if there are three competing candidates, the plan is fact-dumping. This replaces N4 (emotional_map verification) for educational.

**E2. First-3-second hook = the takeaway tension.** TikTok 2026 algorithm needs the hook strong enough to keep viewers past the 5-second "Qualified View" mark. Hook format: "Most people think X. Wrong." or "Three myths about Y — number 2 surprised me." The takeaway is named or teased in second 1-3; nothing else gets distribution.

**E3. Visual demonstration over visual decoration.** The single takeaway is *shown*, not narrated over stock B-roll. If the takeaway is "filler swelling peaks at 48 hours not 24," the video shows a calendar with two highlighted dates, not generic clinic footage. Stock B-roll = penalty. This is the educational analog of N9 visual specificity, but tighter — the visual must *carry* the lesson.

**E4. Information density without lecture register.** Words-per-second target 2.5-3.5 for educational TikTok (faster than narrative's 2.0-2.5). Below 2: lecture-y, drags. Above 4: viewer can't process. Voice register stays peer-to-peer not professor-to-student. Test: read the VO transcript aloud at TikTok speed; does it still scan? Count filler words ("basically", "essentially", "so", "um equivalents") — more than 5% = lecture pad.

**E5. Compliance-bounded specificity (Klinika).** For aesthetic medicine in Poland, the plan must be useful without: depicting prescription-only medicines (Botox is POM under CAP rules — no branded mentions, no before/after of POM treatments), promising specific results, comparative claims vs other clinics, exploiting body-image insecurity. Useful content stays in: aftercare timelines, recovery-day expectations, terminology clarification, what to ask at a consultation, myths about non-POM treatments (fillers can be discussed; Botox cannot be named). Test: scan the script for the words "Botox," "guaranteed," "best in [city]," "look younger" — any hit = compliance fail.

**E6. Share-worthiness trigger present.** The video gives the viewer a reason to send it to one specific person. TikTok 2026 treats shares as high-intent signal — share velocity is one of the top three ranking inputs after completion rate. Triggers: counterintuitive fact ("filler doesn't migrate, that's a myth"), correction of a common belief, specific timeline ("week 1 vs week 6"), insider language ("what we actually call this in clinic"). Generic informational content rarely shares; specific-correction content shares heavily.

**E7. Vertical-first scene composition.** Every scene is composed for 9:16 with subject in the safe zone (center vertical column, between 20% and 80% of screen height to clear the UI overlay). Talking head bottom-third placement; demo objects in upper-two-thirds. Horizontal compositions in an educational plan = TikTok algorithm penalty per Sprout Social 2026.

**E8. Demonstration scene anchors the share.** The single visual demonstration scene (E3) is the screenshot a sharer pastes into a DM. Test: which scene is the still frame a viewer would screenshot? If the answer is "the talking head," there's no visual moment. The strongest educational TikToks have one frame that works as a static post.

**E9. End-frame loops to hook.** Final 1-2 seconds visually echo the opening frame, creating a rewatch trigger. TikTok 2026 weights rewatches as a positive signal independent of completion. Mechanism: opening shows "calendar with day 1 highlighted," ending shows "calendar with day 1 and day 14 highlighted" — viewer rewinds to confirm the pattern.

**E10. Educator-credibility anchor without authority gesture.** ONE credibility cue (white coat in establishing shot, license plate on wall behind speaker, "Dr. Maria, dermatologist" lower-third) appears once and then never again. Repeated authority signals = lecture register. Single anchor = trust without preachiness.

## 3. Top 9-tier signals — brand_authority mode

Brand_authority = LinkedIn explainer with partner VO ("what KSeF 2026 actually means"). 60-180s, LinkedIn-native vertical or 4:5, captions burnt-in because 73% of LinkedIn video plays start muted. Success metric: LinkedIn engagement formula `(reactions×1 + comments×3 + shares×5) × exp(-days/14)` above partner baseline, plus profile views from named buyer accounts.

**B1. Dated decisions over evergreen platitudes.** The video references at least one specific, dated event: "On 13 March 2026, the Ministry of Finance issued..." Not "recently, there have been changes…" LinkedIn 2026 B2B research (Edelman/LinkedIn Thought Leadership Impact Study) finds 55% of decision-makers vet providers via thought-leadership content; dated specificity is the trust signal. Test: count dated references in the script. Zero = generic content marketing, fail.

**B2. Named cases or named precedents.** "Court ruling K 38/24" or "the recent Allegro VAT dispute" rather than "as we've seen in recent cases." If the partner can't name it, they can't claim authority over it. For DWF specifically: at least one Polish court docket number, statute reference, or named regulatory body action per 60s of runtime.

**B3. Partner-voice fidelity (not creator-voice).** The script reads as written by a senior partner, not by a TikTok-trained content team. Sentence length variance is higher than narrative or educational (Polish senior-counsel register: occasional 30-word sentences, formal connectives — *zatem*, *w konsekwencji*, *natomiast* — used correctly). No emoji in the on-screen text, no "let's talk about" openers, no "guys" or peer-register address. Test: read the script aloud; would a senior partner at the firm sign their name to it? If it sounds like a creator economy explainer in a suit, it fails.

**B4. Counterintuitive-stat-then-actionable structure.** LinkedIn 2026 high-engagement formula is "counterintuitive stat + why it matters + actionable takeaway." Scene 1 = stat, middle scenes = mechanism, final scene = what the viewer should do Monday morning. The takeaway is concrete enough that a CFO could forward it to their controller with a one-line action.

**B5. B2B-trust visual register (not creator aesthetic).** Locked tripod over handheld. Natural office light over ring-light. Sober color palette (navy, grey, white, single accent) over saturated. Speaker in business attire framed waist-up against an actual office wall, not a green-screen backdrop. The visual register signals "this is a partner at a real firm" not "this is a creator's bedroom studio." Test: would this look in-place on the firm's website? If no, register is off.

**B6. Compliance-clean for legal-firm video (DWF: Polish bar rules).** No solicitation language ("contact us today," "we can help with that"), no fee mentions or fee comparison, no comparative claims vs other firms, no client-result promises, no testimonials without consent documentation. Polish bar rules (KIRP / KRRP) constrain advertising; the plan must read as informational/educational content with partner attribution, not as advertising. Test: scan for solicitation verbs and result language; any hit = compliance fail.

**B7. On-screen text reinforces, not duplicates VO.** Burnt-in captions for accessibility + mute-watching. Title cards for proper nouns the model will mispronounce or viewer will mis-spell ("KSeF — Krajowy System e-Faktur"). Title cards for citation references (court docket numbers, statute numbers). On-screen text never just transcribes VO — it adds the receipt.

**B8. Authority-anchored thumbnail / first frame.** First frame is shareable as a static post. Partner in frame + title text + firm wordmark in corner = the unit of LinkedIn distribution. LinkedIn 2026 research finds personal profiles generate 5× engagement vs company pages, so the visual must read "this partner said this," not "this firm produced this."

**B9. Pacing slower than narrative or educational.** Average scene length 8-15s (vs narrative 4-8s, educational 1.5-3s). LinkedIn dwell time is the algorithm signal, not scroll-stopping. Longer scenes signal "serious." Faster scenes signal "creator." Match the register the buyer expects.

**B10. Comment-bait via specific question, not generic CTA.** Final scene ends with one specific question that surfaces buyer-side context: "Has your finance team already mapped the schema changes, or is that still pending?" Not "what do you think?" LinkedIn 2026 algorithm rewards comment velocity in the first 15 minutes; specific question + partner responding to early comments triggers the algorithmic boost.

## 4. What separates 9-tier from 5-tier (per mode)

### Narrative slop (5-tier failures)

- **Vague evocative language**: "stunning cinematic shot," "dramatic lighting," "epic moment." The model defaults to a slop-lexicon visual that looks like every other AI-gen video. Sora 2's docs explicitly call this out: "If you leave out details, they'll improvise."
- **No camera grammar**: scenes describe what's *in* the frame but not how the camera *behaves*. The model picks a default move and the storyboard reads like a slideshow.
- **Identity amnesia**: subject described differently in scenes 1, 4, 7. By scene 7 the protagonist has a different jacket, hair, build. This is the single biggest narrative-mode failure mode in 2026 because the Magic Hour benchmark and every AI-video case study (Higgsfield, Kling, Runway 4) traces "obvious AI-gen" to identity drift.
- **Asserted emotion**: `emotional_map` says "Sarah is heartbroken" but no story beat produces it. The plan tells the model to feel; the model can only show.
- **Slop-lexicon scenes**: "neon cyberpunk alley," "rain on window," "lone figure walks into the sunset," "futuristic cityscape." Automatic 5-tier ceiling.

### Educational slop (5-tier failures)

- **Lecture register**: "Today we're going to discuss…" "It's important to understand that…" "As you can see…" These trigger the TikTok algorithm's drop-off cliff at second 5.
- **Fact-dump without takeaway**: video lists six things; viewer remembers zero. E1 fails — no single-takeaway test.
- **No visual demonstration**: talking head + stock B-roll loop. The lesson is in the audio; the video adds nothing. E3 + E8 fail.
- **Generic stock imagery**: smiling models, soft-focus clinic interiors, hands holding products. The TikTok algorithm treats this as low-novelty; share rate collapses.
- **Compliance-naive aesthetic-medicine content**: names Botox, shows POM packaging, before/after of POM treatments, "guaranteed results," "look 10 years younger." Klinika cannot ship this. Per CAP rules + TikTok healthcare policy, all four are automatic violations.
- **Authority-stacking**: "Dr. Maria, MD, PhD, board-certified, 15 years experience" repeated every scene. One credibility anchor (E10) is trust; repeated anchors are insecurity.

### Brand_authority slop (5-tier failures)

- **LinkedIn-broetry on video**: "Yesterday I learned a lesson. [Pause] About leadership. [Pause] And it changed everything." The motivational-poster register pitched at video pacing. Senior B2B buyers don't share this.
- **Motivational poster**: stock office footage + inspirational quote overlay + uplifting music. Zero authority signal, zero specificity, zero share-to-buyer reason.
- **Fake vulnerability**: "I'll be honest, I struggled with this case." Performed candor without specifics. B1 + B2 fail simultaneously.
- **Generic corporate**: drone shot of glass-tower city, suited people walking down a hallway, handshake close-up, abstract data viz. Looks like every law-firm video ever; signals "we have no specific view."
- **Solicitation veneer**: "Have a question about KSeF? Contact us today." Violates B6 and the implied Polish bar advertising rules; the partner cannot ship this.
- **Creator aesthetic in B2B mode**: ring light, vertical handheld, fast cuts, on-screen captions in a creator font. Triggers register mismatch — senior buyer reads "junior content team," not "senior counsel."

## 5. Klinika + DWF specifics

### Klinika educational mode — aesthetic-medicine non-clinical content

The v1 narrowing rules out depicting clinical procedures. What remains as legitimate Klinika content territory:

- **Aftercare and recovery timelines**: "Day 1 vs Day 7 vs Day 14 after lip filler — what's normal, what's not." Calendar visuals, no clinical-procedure footage.
- **Consultation-prep**: "Three questions to ask before your first filler consultation." Talking-head + on-screen text cards.
- **Terminology clarification**: "Hyaluronic acid vs collagen — what your aesthetician means." Diagram-and-callout demonstration visuals.
- **Myth correction (non-POM only)**: "Three myths about dermal fillers." Crucially, the word Botox is never named. Migration myths, longevity myths, allergy myths — all about fillers, not POMs.
- **What to look for in a clinic**: licensure verification, single-use needle protocol, consultation depth. Generic-good-practice content, no comparative claims.

**Dr. Maria voiceover style examples:**
- "After filler, your lip is going to feel weird for about 48 hours. That's normal. What's not normal is asymmetric swelling on day 4." [calm, peer-to-peer, specific timeline, distinguishes normal from concerning]
- "People ask if fillers migrate. They don't, not in the way TikTok says. Here's what actually happens." [acknowledges the platform, corrects without condescension, sets up demonstration]
- NOT: "At Klinika we use only the highest quality products." [solicitation + comparative]
- NOT: "Get the look you've always wanted." [body-image policy violation + result promise]

### DWF brand_authority mode — Polish-language regulatory explainer

- **Partner-led**: a named partner is on-screen for at least 60% of runtime. Profile lower-third names them and their practice area in Polish ("Anna Kowalska, Partner, Doradztwo Podatkowe").
- **Formal-professional Polish register**: Pan/Pani forms in script direction, formal connectives, no anglicisms when a Polish term exists. The exception is technical terminology where the English term is the legal-canonical reference ("compliance," "due diligence" when they appear in Polish statute or court rulings).
- **Compliance-clean structure**: opens with a dated regulatory event, walks through the mechanism, ends with an informational question (not a CTA). The video is *informational*, not advertising — this is the threshold under Polish bar rules.
- **Citation overlay**: every claim that references a statute, ruling, or ministry communication shows the citation on-screen as a title card (statute number, docket number, MF communication number with date). The visual receipt is what separates DWF authority content from competitor explainers.
- **Pacing 8-15s scenes**: a partner speaking is not a creator; the algorithm boost comes from comment velocity and DM-shares from buyer-side counsel, not from completion rate.
- **End-screen question that surfaces buyer state**: "Czy Państwa zespół finansowy mapował już zmiany schematów, czy to jeszcze przed Państwem?" not "Skontaktuj się z nami." The question is what unlocks the LinkedIn comment-velocity boost in the first 15 minutes.

## 6. 2026 emerging signals

**Sora 2 + Veo 3.1 + Runway 4 / Kling 3 capability shifts.** Three things have changed in the last 6 months that the judge must internalize:

1. **Native audio**. Sora 2 and Veo 3.1 generate synchronized SFX, ambient, and dialogue. The storyboard now has to spec audio per scene (diegetic sound, music cues, dialogue lines) — generic "tense music" gets a generic result. Audio specification is no longer optional.
2. **Scene stability over prompt adherence**. Magic Hour's 2026 benchmark weights scene stability at 40% of total quality — higher than prompt adherence. Consistency tokens repeated verbatim across scenes (SB-6 already, but with much higher weight in 2026) are now the most important single technical discipline.
3. **Storyboard-to-video native modes**. Veo 3.1 has a "storyboard to video" feature that converts a sequence directly. The plan structure is now a *direct* model input, not just human-readable scaffolding. JSON schema discipline matters more.

**Vertical-video algorithm changes (TikTok 2026, IG Reels 2026).**
- TikTok 2026 needs 70%+ completion to go viral (was 50% in 2024). Shorter videos with re-watch loops outperform longer videos with traditional pacing.
- "Qualified View" threshold is now 5 seconds. Hook must hold past second 5 or distribution dies.
- Shares and saves are weighted above likes; comment velocity in the first 30 minutes is a major signal.
- 9:16 is "strongly recommended"; 4:5 and 1:1 take measurable distribution penalty.

**LinkedIn video distribution evolution.**
- Native video 5× engagement of static posts; native vertical 4:5 or 9:16 under 60s outperforms longer.
- 73% of video views from mobile, default sound-off → captions burnt-in mandatory.
- Personal profile 5× engagement of company page → partner-led video is the only sensible format for DWF.
- "Counterintuitive stat + why it matters + actionable takeaway" outperforms narrative structure.
- Responding to early comments within 15 min triggers algorithm boost — the *plan* should anticipate the question the comments will ask.

**AI-video slop fatigue.** Viewers in 2026 identify AI-gen content reliably. What makes AI-storyboard NOT look AI-gen:
- Specific named objects over generic categories ("a brushed-steel Hasselblad H6D on a Manfrotto tripod" > "a camera on a tripod")
- Imperfect framing on purpose (slight handheld jitter, asymmetric composition) over centered-symmetric default
- One light source named with direction ("hard side light from camera-left, 4500K") over "cinematic lighting"
- Diegetic audio specified ("metal grinder, 1.5kHz whine") over mood music
- Continuity tokens that include imperfections (a chipped mug, a specific stain on a shirt) — the imperfections are what break the AI-default "everything is pristine" tell

## 7. Implications for the judge

**Three options on the table:**

**Option A — Rubric reweighting per format_mode (R2's proposal).** Keep SB-1..8, change weights per mode. Educational relaxes SB-3 (emotional_map) and SB-4 (recontextualizing ending); brand_authority upweights SB-1 (creator pattern) and SB-5 (voice register). Lightest-touch; preserves existing calibration corpus.

**Option B — New criteria per mode.** Add educational-specific criteria (information-density, single-takeaway, knowledge-transfer mechanism, compliance-bounded specificity, share-worthiness trigger) and brand_authority-specific criteria (authority-anchoring, B2B-trust visual register, partner-voice-fidelity, compliance-bar-clean). Heaviest; needs new calibration data.

**Option C — Hybrid: reweighting + 2-3 new criteria per mode.** Keep SB-1..8 with mode weights, add the 2-3 highest-leverage NEW criteria per mode for things SB-1..8 cannot express.

### Recommendation: Option C (hybrid)

Rationale: SB-1..8 covers narrative mode well and is partially-applicable to the other two modes, but several signals genuinely don't exist in the current rubric. Information density, single-takeaway, share-worthiness, authority-anchoring, partner-voice fidelity, and compliance-bounded specificity are not reductions of existing criteria — they are net-new dimensions. Reweighting alone (Option A) silently asks SB-3 to do work it wasn't designed for (emotion-verification ≠ knowledge-transfer-verification). Option B throws away the working calibration corpus and over-fits to mode differences that share a common base. Option C keeps the floor (SB-1..8 mode-agnostic baseline) and adds 2-3 mode-specific essentials.

### Mode-specific weight adjustments to SB-1..8

| Criterion | narrative | educational | brand_authority |
|---|---|---|---|
| SB-1 creator pattern continuation | essential | important | essential (upweight) |
| SB-2 hook specific + irreplaceable | essential | essential | essential |
| SB-3 emotional_map verified | important | relaxed-to-optional | optional |
| SB-4 recontextualizing ending | optional | optional | optional |
| SB-5 voice-actor-cold + silence | important | important | essential (upweight) |
| SB-6 AI-producible with consistency anchors | important | essential (upweight) | important |
| SB-7 pacing grounded in creator videos | important | essential (upweight, TikTok-speed) | important |
| SB-8 cohort diversity | important | important | important |

### New criteria — anchors

**SB-9 single-takeaway test (educational mode only, essential).** The viewer finishes the video and can state ONE specific thing they now know in one sentence.
- **Score 1**: plan has no identifiable takeaway, or 3+ competing candidates. Fact-dump.
- **Score 3**: one takeaway identifiable but buried in scene 4+ of 6; viewer drops before it lands. Hook does not tease the takeaway.
- **Score 5**: takeaway named or teased in seconds 1-3, demonstrated visually in middle scene, echoed in end-frame. A 15-word takeaway sentence is recoverable from the plan.

**SB-10 information-density and lecture-register check (educational, essential).** Words-per-second 2.5-3.5, peer-to-peer register, no lecture pads.
- **Score 1**: WPS < 1.8 or > 4.5; lecture-pad fraction > 10% ("basically," "essentially," "so," "today we're going to," "as you can see"). Professor-to-student register.
- **Score 3**: WPS in band but register slips on 1-2 lines ("it's important to understand"). Mostly peer-to-peer.
- **Score 5**: WPS in 2.5-3.5 band, < 5% lecture pads, peer-to-peer throughout, sentence-length variance natural.

**SB-11 share-worthiness trigger (educational, important).** The plan gives the viewer a reason to send the video to one specific person.
- **Score 1**: generic informational content, no counterintuitive correction, no specific timeline, no insider-language reveal. Nothing to forward.
- **Score 3**: one share-trigger present but buried, or the trigger is interesting-not-actionable.
- **Score 5**: counterintuitive correction or specific-timeline or insider-language reveal lands in the first 10 seconds and is the visual peak (E8 anchor).

**SB-12 compliance-bounded specificity (educational, essential, pitfall).** Content is useful while staying within ad/healthcare/bar compliance for the lane domain.
- **Score 1**: at least one explicit violation — POM brand name, before/after of POM treatment, result promise, comparative claim, body-image exploitation, solicitation language. Blocking-fail; this criterion can override others.
- **Score 3**: no explicit violation but content is so cautious it loses informational value. "We can't talk about X" said three times.
- **Score 5**: useful, specific, compliance-clean. Names what can be named (fillers, hyaluronic acid, post-procedure timelines), avoids what cannot (POMs, results, comparisons), and the avoidance doesn't show — content stays peer-useful.

**SB-13 authority-anchoring (brand_authority, essential).** Dated decisions, named cases, named precedents.
- **Score 1**: zero dated references; "recently," "lately," "in modern practice." Generic evergreen.
- **Score 3**: one dated reference but no named case; or named case but no date.
- **Score 5**: at least one dated regulatory event + at least one named case/docket/statute per 60s of runtime. Citation overlays visible.

**SB-14 partner-voice fidelity (brand_authority, essential).** Script reads as written by a senior partner, not by a content team.
- **Score 1**: TikTok register on B2B mode — "let's talk about," emoji punctuation, peer-address ("guys," "folks"), or motivational-poster cadence.
- **Score 3**: mostly formal but slips into creator register in 1-2 places; sentence-length variance feels engineered not natural.
- **Score 5**: passes the "would the named partner sign their name to this" test. Formal-professional register, natural sentence-length variance, no anglicisms where Polish exists, no solicitation verbs.

**SB-15 B2B-trust visual register (brand_authority, important).** Visual choices match senior-counsel context, not creator aesthetic.
- **Score 1**: ring light + handheld + fast cuts + saturated palette + green-screen backdrop. Creator aesthetic in a suit.
- **Score 3**: locked framing but lighting too even (looks rendered), or color palette too saturated, or pacing too fast for B2B dwell-time.
- **Score 5**: locked tripod, natural office light, sober palette (navy/grey/white + single accent), real office wall, 8-15s scene pacing, partner waist-up framed for LinkedIn share-as-static-frame.

### What the judge does NOT need

- A new "narrative" criterion. SB-1..8 with N-tier signal anchoring already covers narrative mode well; the 9-tier signals N1..N10 sharpen interpretation of existing criteria, they don't add new ones.
- A new "audio specification" criterion. Native audio in Sora 2 / Veo 3.1 is now an input *to* SB-6 (AI-producibility). The judge should grade audio specification as part of the existing AI-producibility check, not as a separate axis.
- Separate criteria for slop-lexicon detection. This is a deterministic pre-check (regex on the plan: "cinematic," "dramatic," "neon cyberpunk," "rain on window," "epic," "stunning" → automatic SB-2 + SB-9 cap). The judge does not need to learn it.

The judge becomes 8 + 7 = 15 criteria total: SB-1..8 mode-agnostic with mode-specific weights, plus SB-9..15 mode-conditional (SB-9..12 fire only in educational mode, SB-13..15 fire only in brand_authority mode). Narrative mode uses SB-1..8 only — the existing rubric works.

Sources:
- [Sora 2 Prompting Guide | OpenAI Cookbook](https://cookbook.openai.com/examples/sora/sora2_prompting_guide)
- [Sora 2 Prompting Guide: Tips for Better AI Video Generation in 2026 | WaveSpeed](https://wavespeed.ai/blog/posts/sora-2-prompting-tips-better-videos-2026/)
- [Veo 3.1 Google Video API: Complete Developer Tutorial (2026)](https://ofox.ai/blog/veo-3-1-google-video-api-english-tutorial-2026/)
- [Google Veo 3.1 4K Guide: Master the "Ingredients to Video"](https://studio.aifilms.ai/blog/google-veo-31-official-release-january-2026)
- [How the TikTok Algorithm Works in 2026 | Sprout Social](https://sproutsocial.com/insights/tiktok-algorithm/)
- [TikTok 70% Retention Rule: Why Views Stop in 2026 | Socialync](https://www.socialync.io/blog/tiktok-viral-retention-rate-2026)
- [LinkedIn Algorithm 2026: What Works Now](https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now)
- [LinkedIn Video in 2026: What's Working and How to Make It](https://www.visla.us/blog/guides/linkedin-video-in-2026-whats-working-and-how-to-make-it/)
- [AI Video Generation Scene Stability: 2026 Evolution Guide](https://resource.digen.ai/ai-video-generation-scene-stability-2026/)
- [AI Multi-Shot Video: How to Create Consistent Characters and Scenes](https://www.aimagicx.com/blog/ai-multi-shot-video-character-consistency-2026)
- [10 Dos and Don'ts: Social Media for Aesthetics Practitioners | Harley Academy](https://www.harleyacademy.com/aesthetic-medicine-articles/10-dos-and-donts-social-media-for-aesthetics-practitioners/)
- [Healthcare and Pharmaceuticals | TikTok Advertising Policies](https://ads.tiktok.com/help/article/tiktok-ads-policy-healthcare-pharmaceuticals)
- [10 High-Impact Law Firm Marketing Strategies for B2B Growth in 2026](https://www.cloudpresent.co/blog/law-firm-marketing-strategies)
