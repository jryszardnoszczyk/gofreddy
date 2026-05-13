---
date: 2026-05-12
phase: D
lane: storyboard
status: spec — implementer-ready; SB-12 and SB-15 trigger-phrase content gated on Resolve-Before-Planning #2 (legal review)
inputs:
  - phase-a-lane-purposes.md §4 (storyboard, three modes)
  - phase-b-research/storyboard.md (Option C hybrid recommendation)
  - phase-c-variant-ratings.md (mode-conditional fixtures not available; proceed on Phase B)
  - autoresearch/archive/v188/workflows/session_eval_storyboard.py (current SB-1..8 prose)
---

# Phase D — Storyboard rubric spec (3 modes, 15 criteria)

The storyboard lane produces a callable spec — JSON the fal.ai I2V pipeline consumes — under one of three `format_mode` values: `narrative`, `educational`, `brand_authority`. Phase A pinned three different optimization targets per mode. Phase B reviewed the 2026 model landscape (Sora 2, Veo 3.1, Magic Hour scene-stability benchmark) and platform algorithms (TikTok 70% completion, LinkedIn partner-led shift) and recommended Option C: keep SB-1..8 as the mode-agnostic floor, reweight per mode, and add seven mode-conditional criteria.

This spec locks **15 criteria** under **mode-conditional firing**. Narrative fires SB-1..8 only (no behavioural change vs v188). Educational fires SB-1..8 reweighted + SB-9..12. Brand_authority fires SB-1..8 reweighted + SB-13..15. SB-12 (medical_pl) and SB-15 (legal_pl) carry **auto-cap** semantics: a confirmed violation caps the overall fixture score regardless of how the other criteria score.

Two follow-ups remain operator-gated: (a) `format_mode` dispatch needs a single parameter source — frontmatter on the story plan is recommended (§5); (b) SB-12 and SB-15 trigger-phrase lists need legal-review sign-off per the Resolve-Before-Planning #2 gate. This spec defines the *shape* and *evidence model* without inventing rule text.

---

## Section 1 — Three-mode firing table

Tier vocabulary: **essential** (load-bearing for ship-eligibility; failure caps), **important** (drags the score when failed), **optional** (positive when present, neutral when absent), **pitfall** (specific failure mode that caps the score), **skip** (criterion does not fire; the substrate must not include it in the assembled rubric for that mode).

| ID  | Question | narrative | educational | brand_authority |
|-----|----------|-----------|-------------|-----------------|
| SB-1 | Creator-pattern continuation | essential | important | **essential (upweighted)** |
| SB-2 | Hook specific + irreplaceable | essential | essential | essential |
| SB-3 | Emotional_map verified against story_beats | important | **optional (relaxed)** | optional |
| SB-4 | Recontextualizing ending | optional | **skip** | optional |
| SB-5 | Voice-actor performable + silence | important | important | **essential (upweighted)** |
| SB-6 | AI-producible with consistency anchors | important | essential | important |
| SB-7 | Pacing grounded in creator's videos | important | essential (TikTok-speed) | important |
| SB-8 | Cohort diversity (cross-item) | important | important | important |
| SB-9 | Information density (WPS / lecture register) | skip | **essential** | skip |
| SB-10 | Single-takeaway test | skip | **essential** | skip |
| SB-11 | Knowledge-transfer mechanism (show vs tell) | skip | **important** | skip |
| SB-12 | Medical_pl compliance (**auto-cap**) | skip | **essential / pitfall** | skip |
| SB-13 | Authority-anchoring (dated decisions, named cases) | skip | skip | **essential** |
| SB-14 | B2B-trust visual register | skip | skip | **important** |
| SB-15 | Legal_pl compliance (**auto-cap**) | skip | skip | **essential / pitfall** |

**Per-mode totals.** Narrative: 8 (no change vs current). Educational: 8 reweighted + 4 new = 12 active. Brand_authority: 8 reweighted + 3 new = 11 active.

**No fixture fires all 15.** Mode-conditional criteria are replacements, not additions. SB-9..12 do work in educational mode that SB-3 + SB-4 do in narrative (knowledge transfer is the analog of emotional verification). SB-13..15 do work in brand_authority mode that SB-3/SB-4 cannot do at all (authority-anchoring is evidence structure, not emotional structure). Firing all 15 would force the judge to grade narrative arc on a TikTok and authority-anchoring on a YouTube short.

---

## Section 2 — SB-1..8 disposition

**Criterion prose stays identical to v188.** Only the tier mapping changes per mode. Rewriting the criterion text per mode would silently fork the calibration corpus; the floor is mode-agnostic by design, and only the weights move.

Per-criterion notes on what changes:

- **SB-1.** Brand_authority **upweighted to essential**: DWF partner-voice fidelity is the load-bearing buyer-trust signal (Phase B B3). If the script reads like a content team wrote it, the video fails. Educational drops to important because SB-10 and SB-12 dominate the educational ship-gate.
- **SB-2.** Essential in all three modes. Mode emphasis differs: narrative tests hook against channel lineage (N1); educational tests hook against the 5-second TikTok "Qualified View" plus second 1-3 takeaway tease (E2); brand_authority tests hook against counterintuitive-stat-then-actionable (B4).
- **SB-3.** Educational **relaxed to optional**: educational TikToks need takeaway recall, not emotional arc. Forcing SB-3 penalises good explainer content. SB-10 + SB-11 carry the verification load. Brand_authority drops to optional for the same reason (evidence structure ≠ emotional structure).
- **SB-4.** Educational **skips**: 30-second explainers don't recontextualize; the end-frame loop (E9) is a rewatch trigger, not a reframe — folded into SB-10. Brand_authority stays optional (some long explainers do reframe).
- **SB-5.** Brand_authority **upweighted to essential**: Polish-language senior-counsel register (Pan/Pani forms, formal connectives *zatem* / *w konsekwencji* / *natomiast* used correctly, no anglicisms where Polish exists) must be performable by the named partner without rewriting.
- **SB-6.** Educational **upweighted to essential**: Magic Hour 2026 weights scene stability above prompt adherence; educational TikToks have 8-20 cuts in 30-60s — every cut is a drift chance. Consistency tokens (Dr. Maria's coat, the calendar prop, the name card) must repeat verbatim.
- **SB-7.** Educational **upweighted to essential** with TikTok-speed anchor (WPS 2.5-3.5, scene length 1.5-3s). Brand_authority anchors at LinkedIn-dwell (8-15s scenes).
- **SB-8.** Stays important across all three. Cohort variance per mode: narrative = different premises within the creative universe; educational = different *takeaways* (not five myths about one procedure); brand_authority = different *regulatory mechanisms* (not five framings of one case).

---

## Section 3 — New criteria SB-9..15

Each new criterion follows the SB-1..8 template: one concrete question, why-before-what where load-bearing, 1/3/5 anchors or 4 YES/NO sub-questions, mode-firing, ground-truth cross-reference, CoT closing.

### SB-9 — Information density (educational, essential)

**Evaluate this story plan for ONE quality:** Does the words-per-second rate land in the 2.5-3.5 band that TikTok/Reels educational content requires, with peer-to-peer register and zero lecture-pad fraction above 5%?

TikTok 2026 distribution gates on the 5-second "Qualified View" plus 70%+ completion. Density below 2.0 WPS reads as lecture and triggers the second-5 drop-off cliff; above 4.0 WPS the viewer cannot process and shares collapse. The Phase B failure signature ("Today we're going to discuss…", "As you can see…") is detectable from the script alone.

- **Score 1:** WPS < 2.0 OR WPS > 4.0. Lecture-pad fraction > 10% (count of: "basically", "essentially", "so today", "as you can see", "it's important to understand", "what we're going to talk about" / total spoken words). Professor-to-student register.
- **Score 3:** WPS in 2.0-2.5 or 3.5-4.0 (in-band-adjacent). Lecture-pad 5-10%. Mostly peer-to-peer; slips on 2-3 lines.
- **Score 5:** WPS in 2.5-3.5 (verifiable: `voice_script` word count / `duration_target_seconds`). Lecture-pad < 5%. Peer-to-peer throughout — addresses viewer directly without "guys/folks" gestures, natural sentence-length variance, no warmup. Script reads aloud at TikTok speed without losing meaning.

**Ground-truth verification.** WPS = `voice_script` word count / `duration_target_seconds` (deterministic). Lecture-pad fraction = regex against a fixed phrase list (deterministic). Judge cross-references both before scoring.

**Closing.** Think step by step. Compute WPS first, count lecture pads, then score. If WPS is out of band, that determines the score regardless of qualitative register.

### SB-10 — Single-takeaway test (educational, essential)

**Evaluate this story plan for ONE quality:** Can the viewer finish the video and state ONE specific thing they now know, in 15 words or fewer?

Educational content that fails this test is fact-dumping, and fact-dumps have near-zero share rate. TikTok 2026 weights shares above likes; share is the heaviest distribution lever. If the rubric can't write the takeaway sentence from the plan, the viewer won't either.

**Sub-questions (YES/NO; 4 YES = 5; 3 = 4; 2 = 3; ≤1 = 1):**
1. Can a 15-word takeaway sentence be recovered from the plan? ("Filler swelling peaks at 48 hours, not 24 — don't panic on day 2.")
2. Is the takeaway named or teased in seconds 1-3 of voice_script (the hook scene)?
3. Is the takeaway visually demonstrated in at least one middle scene (not just narrated)?
4. Is there exactly ONE takeaway, not three competing candidates?

- **Score 1:** No recoverable takeaway, OR three competing candidates ("here are five myths"), OR generic takeaway ("filler can be safe"). Fact-dump.
- **Score 3:** One takeaway identifiable but buried in scene 4+ of 6. Hook does not tease it.
- **Score 5:** Takeaway named or teased in seconds 1-3, demonstrated visually in a middle scene, echoed in the end-frame (E9 rewatch trigger). A 15-word sentence is recoverable and matches the demonstrated content.

**Ground-truth verification.** Judge writes the candidate takeaway sentence in its evidence string *before* scoring. If it cannot write the sentence, score 1 is mandatory. Cross-reference against `findings.md` (Creative Intent) to confirm the takeaway matches the intended educational angle.

**Closing.** Write the takeaway sentence first. Then check whether the hook teases it and a scene demonstrates it.

### SB-11 — Knowledge-transfer mechanism (educational, important)

**Evaluate this story plan for ONE quality:** Is the takeaway *shown* visually, or only *told* in voiceover with decorative B-roll?

Phase B E3 anchors the educational ceiling on visual demonstration carrying the lesson. Stock B-roll (smiling models, soft-focus clinic interiors, hands holding products) is the AI-video-slop signature of educational mode — visual adds nothing to audio, and TikTok 2026 treats this as low-novelty. Share rate collapses. The strongest educational TikToks have one frame that works as a static post (E8 demonstration-anchor).

- **Score 1:** Talking head + stock B-roll. Lesson entirely in audio. No scene visually demonstrates the takeaway.
- **Score 3:** One demonstration scene present, but generic (a calendar with day numbers but no specific timeline marked; "before/after" without a specific dimension). Most scenes are talking-head.
- **Score 5:** At least one scene visually demonstrates the takeaway with specific, prop-anchored detail. The demonstration scene works as a static post — someone could screenshot it and the post would still make sense. Visual specificity matches the Phase B N9 floor (3-5 named colors, named light source, concrete materials).

**Ground-truth verification.** For each scene in `scene_plan`, ask: does this scene's visual content advance the SB-10 takeaway, or is it decorative? At least one scene must advance, and it must be non-talking-head.

**Closing.** Identify the demonstration scene (or note its absence). Check specific vs generic.

### SB-12 — Medical_pl compliance (educational, essential, pitfall, **auto-cap**)

**Fires when** `compliance_regime = medical_pl` is set on the story plan.

**Evaluate this story plan for ONE quality:** Is the content useful and specific while staying inside the Polish medical-advertising rule set (CAP-equivalent under Polish law, pharmaceutical-advertising statute, TikTok healthcare ads policy)?

Educational content that violates compliance cannot ship — Klinika's human reviewer rejects it at the pre-publish gate. Catching it in the loop saves a regeneration cycle. But over-caution kills educational value: "we can't talk about X" said three times produces compliance-clean but useless content. The Phase B E5 ceiling is "useful, specific, compliance-clean; the avoidance doesn't show."

**Cross-reference (gated on Resolve-Before-Planning #2).** Judge cross-references the script against the medical_pl rule list at `configs/compliance/medical_pl/rules.yaml` — path is normative; file content is operator-loaded after legal review. Rule categories: (a) POM-name blocklist (Botox, Dysport, Vistabel, Azzalure — prescription-only medicines that cannot appear in advertising); (b) result-promise patterns ("guaranteed results," "look 10 years younger"); (c) comparative claims ("best in [city]," "cheaper than competitors"); (d) body-image exploitation ("finally feel beautiful," "fix your insecurity").

**When the cap fires.** Confirmed regex match against any pattern in (a)-(d) triggers **auto-cap at score 2** for SB-12 and **caps overall fixture score at 4** (below ship-eligibility). Deterministic — match triggers the cap regardless of qualitative read.

**Verifiable evidence.** Judge must quote the violating string from voice_script or scene text in its evidence field and identify which rule category matched. Vague evidence ("the script mentions Botox" without quoted string) does not trigger the auto-cap; the cap requires concrete evidence the human reviewer could verify in 5 seconds.

- **Score 1:** Confirmed violation quoted from the script. Auto-cap fires; overall fixture capped at 4.
- **Score 3:** No explicit violation but content is so cautious it loses informational value. "We can't talk about specific brands" said three times.
- **Score 5:** Useful, specific, compliance-clean. Names what *can* be named (filler chemistry, hyaluronic acid, post-procedure timelines, what to ask at consultation). Avoids what cannot (POMs, results, comparisons, body-image). The avoidance doesn't show — content stays peer-useful at Dr. Maria's register.

**Closing.** Scan voice_script against each rule category. If any match, quote the violating string and trigger the auto-cap. Only then assess the qualitative dimension.

### SB-13 — Authority-anchoring (brand_authority, essential)

**Evaluate this story plan for ONE quality:** Does the plan reference at least one dated regulatory event AND at least one named case / docket / statute per 60 seconds of runtime?

Phase B B1+B2: senior B2B buyers vet providers via thought-leadership content (Edelman/LinkedIn 2026: 55% do this); dated specificity is the trust signal. "Recently, there have been changes…" reads as content marketing; "On 13 March 2026, the Ministry of Finance issued komunikat MF nr 7/2026…" reads as partner authority. The brand_authority ceiling — "senior buyer DMs to a colleague with 'you should watch this'" — requires evidence the buyer can cite back to their team.

**Sub-questions (YES/NO; 4 YES = 5; 3 = 4; 2 = 3; ≤1 = 1):**
1. Is at least one specific date (day-month-year, or month-year for the broadest claims) referenced in the script?
2. Is at least one named case, court docket number, statute reference, or regulatory-body action named per 60s of runtime?
3. Are the citations shown on-screen as title cards (consistency_anchors include text-overlay specs for citations)?
4. Is the partner naming the citation in VO (not just on-screen overlay) — the authority is *spoken* by the named partner?

- **Score 1:** Zero dated references. "Recently," "lately," "in modern practice." Generic evergreen — could be a content team's blog post.
- **Score 3:** One dated reference, OR named cases but no dates. Partial authority signal.
- **Score 5:** Dated regulatory event + named case/docket/statute per 60s of runtime. Citations appear on-screen. Partner names them in VO. Plan reads as the partner's *own* knowledge of the regulatory record.

**Ground-truth verification.** Cross-reference against the partner credential list at `configs/voice_persona/dwf/partners/<partner_slug>/credentials.yaml`. The credential file declares practice area, named-case history, and regulatory bodies the partner has standing to speak about. A partner declared in `compliance.dwf.podatkowe` (tax) citing a labor-law docket is an authority failure — the partner doesn't speak with authority on labor law. This is the criterion that *can't be argued with* by an inflating judge.

**Polish-language anchor.** Statute references in Polish naming convention ("ustawa z dnia 13 marca 2026 r." not "the March 13 act"); court dockets in Polish convention ("K 38/24" or "sygn. akt I CSK 123/24"); ministry communications ("komunikat MF nr 7/2026"). English-translated citations are an authority failure — the partner works in Polish primary sources.

**Closing.** List the citations the script makes. Check each against the partner credential list. Confirm dated + named-case per 60s.

### SB-14 — B2B-trust visual register (brand_authority, important)

**Evaluate this story plan for ONE quality:** Do the visual choices (lighting, framing, palette, pacing, set) signal "senior partner at a real firm" rather than "creator producing content in a bedroom studio"?

Phase B B5: register mismatch is the load-bearing visual failure for brand_authority. A partner on a ring-light + green-screen setup with fast cuts reads as "junior content team with a partner's face attached" — senior B2B buyers screen this out instantly. The ceiling tests against "would this look in-place on the firm's website."

**Sub-questions (YES/NO; 4 YES = 5; 3 = 4; 2 = 3; ≤1 = 1):**
1. Camera move per scene is locked tripod (no handheld, no walking shots, no rapid-zoom)?
2. Lighting is natural office light or sober studio (not ring-light, not saturated key/fill, not green-screen)?
3. Color palette is sober (navy / grey / white / single accent), not creator-saturated?
4. Scene pacing matches B2B dwell-time (8-15s average scene length, not 1.5-3s TikTok-speed)?

- **Score 1:** Ring light + handheld + fast cuts + saturated palette + green-screen backdrop. Creator aesthetic in a suit. Partner reads as performing for the camera, not speaking from authority.
- **Score 3:** Locked framing but lighting too even (looks rendered), OR palette too saturated, OR pacing too fast for B2B dwell-time. Mixed signal.
- **Score 5:** Locked tripod, natural office light, sober palette + single accent, real office wall (not green-screen, not stylised backdrop), 8-15s scene pacing, partner waist-up framed for LinkedIn share-as-static-frame (B8 thumbnail anchor).

**Ground-truth verification.** Cross-reference scene specs against the DWF visual brand pack at `configs/brand/dwf/visual_pack.yaml` — declared palette tokens, framing constraints, approved backdrop set. The judge does not invent the register; it grades against the declared brand pack.

**Closing.** For each scene, check lighting / framing / palette / pacing against the brand pack. Score against the count of in-spec scenes.

### SB-15 — Legal_pl compliance (brand_authority, essential, pitfall, **auto-cap**)

**Fires when** `compliance_regime = legal_pl` is set on the story plan.

**Evaluate this story plan for ONE quality:** Is the content informational under Polish bar advertising rules (KIRP / KRRP) — no solicitation, no fee mentions, no comparative claims, no client-result promises, no testimonials without consent?

Phase A flags `legal_pl` as a hard-block precondition. Polish bar rules constrain what attorneys can say in advertising — even informational content can cross the line if it solicits, compares, or promises. DWF partners cannot ship video that violates KIRP / KRRP; the regulatory liability is the firm's. The judge catches violations in the loop so the human gate doesn't have to.

**Cross-reference (gated on Resolve-Before-Planning #2).** Rules at `configs/compliance/legal_pl/rules.yaml`. Categories: (a) solicitation verbs ("contact us today," "skontaktuj się z nami," "we can help"); (b) fee mentions ("our fees," "competitive rates," "affordable representation"); (c) comparative claims ("better than other firms," "the leading firm"); (d) client-result promises ("we win cases," "guaranteed outcomes"); (e) testimonials without consent metadata. Rule text is operator-loaded.

**When the cap fires.** Confirmed regex match against (a)-(e) triggers **auto-cap at score 2** for SB-15 and **caps overall fixture score at 4**. Deterministic — match triggers cap regardless of qualitative read.

**Verifiable evidence.** Judge quotes the violating string and identifies the rule category. Cross-references back to the brief: brand_authority mode produces *informational* content under partner attribution. Any solicitation-shaped language — even subtle ("if your team has questions about KSeF, we're here") — is a violation. Polish bar enforcement is character-of-content driven, not just literal-keyword driven.

- **Score 1:** Confirmed violation quoted from the script. Auto-cap fires; overall fixture capped at 4.
- **Score 3:** No explicit violation, but content is so cautious it loses authority value (the final scene CTA is so vague it doesn't even ask the question).
- **Score 5:** Informational throughout. Final scene asks a buyer-side-context question per Phase B B10 ("Czy Państwa zespół finansowy mapował już zmiany schematów?" — not "skontaktuj się z nami"). Closing is a question, not a CTA. Partner is recognisable as a partner of the firm without the firm soliciting business through the artifact. On-screen text never includes phone numbers, email addresses, "contact" buttons, or fee references; partner lower-third names the partner + practice area only.

**Closing.** Scan voice_script and on-screen text against each rule category. If any match, quote the violation and trigger the auto-cap. Only then assess the qualitative dimension.

---

## Section 4 — Klinika + DWF v1 anchors

**Klinika educational.** R1 narrowing rules out clinical-procedure depictions. Anchor scene set: calendar visuals (day-1/day-7/day-14 timelines), talking-head with on-screen text cards, diagram-and-callout (terminology), myth correction restricted to non-POM treatments. Anchor language is Polish-language educational TikTok / IG Reels at Dr. Maria's register: calm, peer-to-peer, specific timelines, distinguishes normal from concerning, acknowledges TikTok-as-platform without condescension. Voice exemplar: "Po fillerze warga będzie czuła się dziwnie przez około 48 godzin. To normalne. Niepokojąca jest asymetria opuchlizny w 4. dobie." Failure-mode mapping: lecture register → SB-9; fact-dump → SB-10; talking-head + stock B-roll → SB-11; POM names / result promises / comparatives → SB-12 auto-cap; authority-stacking → SB-1 + SB-5.

**DWF brand_authority.** Polish-language LinkedIn explainer under named partner byline. 60-180s vertical or 4:5. Partner on-screen ≥60% of runtime; lower-third names partner + practice area in Polish; citations on-screen as title cards; final scene closes with a buyer-side question, not a CTA. Anchor language is Polish senior-counsel register: formal-professional Pan/Pani forms, formal connectives (*zatem* / *w konsekwencji* / *natomiast*) used correctly, sentence-length variance higher than narrative or educational (accommodates 30-word sentences), no anglicisms where Polish exists (exception: legal-canonical "compliance," "due diligence" inside statute/court contexts). Failure-mode mapping: broetry-on-video → SB-5 + SB-14; motivational poster → SB-1 + SB-13; fake vulnerability → SB-13; generic corporate → SB-14; solicitation veneer → SB-15 auto-cap; creator aesthetic → SB-14.

---

## Section 5 — Implementation notes

**Mode dispatch — recommendation: frontmatter on the story plan.** The substrate reads frontmatter, assembles the per-mode rubric from the 15-criterion superset, and passes only the active subset to the judge. LaneSpec stays mode-agnostic — the lane is "storyboard"; per-fixture frontmatter declares the mode + regime. This matches the cross-lane pattern Phase A flagged for compliance regimes (`medical_pl` + `legal_pl` are applied across content-for-publish lanes).

Frontmatter schema:

```yaml
---
format_mode: educational    # narrative | educational | brand_authority
compliance_regime: medical_pl    # null | medical_pl | legal_pl
voice_persona: dwf/partners/anna-kowalska    # path under configs/voice_persona/
visual_brand_pack: dwf/visual_pack    # path under configs/brand/
---
```

Default dispatch: if frontmatter is absent, `format_mode: narrative` and `compliance_regime: null`. Preserves backward compatibility with the existing storyboard corpus (fires SB-1..8 as today).

**Compliance regime integration.** SB-12 and SB-15 criteria live in this spec; their trigger phrase lists live in `configs/compliance/medical_pl/rules.yaml` and `configs/compliance/legal_pl/rules.yaml`. Other content-for-publish lanes (article_engine, image_engine, ad_engine, x_engine, linkedin_engine) reference the same rule files. Resolve-Before-Planning #2 covers rule-file *content*; this spec covers *shape*. Until rule files are populated, SB-12 and SB-15 fire in shape-only mode — judge confirms the cross-reference path exists, declares "not yet scoring," abstains. Failure-loud rather than silently scoring against an empty rule list.

**Two-gate design preserved.** In-loop judge drives evolution toward compliance-clean output; pre-publish human reviewer catches the rest. Auto-cap at 2 + overall-cap at 4 keeps violation fixtures below ship-eligibility, so the loop regenerates them automatically.

**RUBRIC_VERSION hash invalidates on:** (1) SB-1..15 criterion text changes; (2) the mode-firing table changes; (3) `configs/compliance/{medical_pl,legal_pl}/rules.yaml` content hash changes; (4) voice_persona files referenced by SB-1/SB-5/SB-13 change; (5) visual brand pack referenced by SB-14 changes. Without (3)-(5), the score cache could return stale "no violation" verdicts after rule updates and ship violating content.

**Cross-item criterion (SB-8).** Stays as v188: glob `stories/*.json`, `max_items=4`. Cohort diversity is mode-agnostic; fires once per cohort.

**Deterministic pre-checks.** Slop-lexicon detection ("cinematic," "dramatic," "neon cyberpunk," "rain on window," "epic," "stunning") and lecture-pad detection are deterministic pre-checks in the structural gate, not judge criteria. They feed the SB-2 / SB-6 / SB-9 caps. Judge's prose carries the *ceiling*; regex carries the floor.

---

## Section 6 — Validation plan

**V1. Narrative regression.** Run the existing narrative corpus from v188 against the updated rubric assembly (frontmatter default: `format_mode: narrative`, `compliance_regime: null`). Expected: scores within ±0.1 of v188 for the same fixtures. Drift > 0.2 means the dispatch logic accidentally fired a mode-conditional criterion — inspect the assembled rubric.

**V2. Klinika educational demo.** Produce 5 fixtures: "Three myths about dermal fillers"; "Day 1 vs Day 7 vs Day 14 after lip filler"; "Three questions before your first filler consultation"; "Hyaluronic acid vs collagen"; "What to look for in a clinic." Frontmatter: `format_mode: educational`, `compliance_regime: medical_pl`. Expected: all 5 fire SB-1..8 (reweighted) + SB-9..12; all 5 score ≥4 on SB-12 (no POM names, no result promises, no comparatives); ≥3 of 5 score ≥4 on SB-10 (recoverable 15-word takeaway); cohort SB-8 ≥4 (five different takeaways). A fixture scoring 5 across the board on first run is almost certainly inflation; spot-check the takeaway sentence and WPS.

**V3. DWF brand_authority demo.** 5 Polish-language fixtures: "Co naprawdę zmienia KSeF od 1 lutego 2026"; "Polish Grid Act 2026 vs dyrektywa UE"; "Wyrok TK K 38/24 a praktyka compliance"; "Nowa Ordynacja Podatkowa — działy finansowe"; "Implementacja CSRD w polskim prawie spółek." Frontmatter: `format_mode: brand_authority`, `compliance_regime: legal_pl`. Expected: all 5 fire SB-1..8 (reweighted) + SB-13..15; all 5 score ≥4 on SB-15 (no solicitation, closing question not CTA); all 5 score ≥4 on SB-13 (≥1 dated event + ≥1 named case per 60s, citation overlays specified); cohort SB-8 ≥4. Fixtures scoring high on SB-13 without partner-credential cross-reference firing are a silent failure — confirm by inspecting evidence strings.

**V4. Auto-cap on synthetic violating storyboards.**
- *medical_pl violation:* take Klinika fixture (1) and replace "filler" with "Botox" in two scenes, add "guaranteed results" to closing VO, add "the best clinic in Warsaw" as comparative. Expected: SB-12 = 1; overall capped at 4; judge evidence quotes "Botox" (rule a), "guaranteed results" (rule b), "the best clinic in Warsaw" (rule c).
- *legal_pl violation:* take DWF fixture (1) and append "Skontaktuj się z naszym zespołem — pomożemy w pełnej implementacji" to closing VO; insert "Nasze stawki są konkurencyjne" in scene 3; replace closing buyer-side question with "Zadzwoń do nas." Expected: SB-15 = 1; overall capped at 4; judge quotes the violating strings.

Any violating fixture scoring above the cap indicates the auto-cap logic is not wired correctly. The cap must be deterministic (regex match → cap fires), not judgment-driven.

**V5. Mode dispatch correctness.** Score one fixture three times with three different `format_mode` values on the same underlying JSON. Expected: three different rubric assemblies, three different score sets, three different evidence strings. SB-9..12 fire only on the educational pass; SB-13..15 fire only on the brand_authority pass; SB-3/SB-4 are present-not-relaxed only on the narrative pass. Same criterion firing across all three passes = dispatch logic is broken.
