# ad_engine judge — calibration corpus (Phase B)

Lane writes 3-5 paid-ad variants per format: Meta Reels + image/carousel (Klinika, aesthetic-medicine consultations); LinkedIn Sponsored Content single-image / document / video (DWF, partner-track inquiries). Each variant ships copy + image/video brief + matched LP hero copy. Compliance gate (medical_pl, legal_pl) runs BEFORE this judge; rubric grades market fit, hook, diversity, and LP coherence on a compliance-clean draft. Foreplay = primary winner-signal source; Adyntel + SerpAPI = Google-side context; GSC + LP analytics close the LP-coherence loop.

---

## 1. Top 9-tier signals — what excellent paid ad creative looks like in 2026

Concrete patterns, source-anchored, judge-able.

### Meta (Reels + image/carousel)

**M1. First-3-seconds hook = tension AND early resolution.**
"If your hook asks a question, answer it. If it teases, reveal it" (Social Media Today). Completion rate is a primary Reels ranking signal; hook+payoff in <3s lifts hook rate ~22% over muted equivalents (Motion App Q1 2026). Test: does the hook contain BOTH tension and an early-resolution element (answer, flip, number, named name) in the first sentence/frame?

**M2. Native handheld beats studio polish on Reels.**
"Ads that look like organic Reels — handheld, natural lighting, lo-fi — consistently achieve lower CPMs and higher completion rates" (AdMove 2026, Reshift). 9:16 vertical is ~90% of Meta inventory. Test: does the brief specify handheld/POV/UGC + vertical + ambient audio, or default to "polished studio"?

**M3. Audio-on with VO or music lifts conversion 13%.**
Meta for Business / AdMove. Audio-on assets running 90+ days had 22% higher hook rate vs muted (Motion App). Test: brief specifies VO script and/or music bed.

**M4. The Dave Trott triangle: Impact + Communication + Persuasion.**
Harry Dry (tweet 1765772001279418404): "Most ads just do communication. 'We're a brand agency.' 'No s***, I just googled that.'" Test: tag each headline line as Impact / Communication / Persuasion — is each represented in the headline + first body line?

**M5. Big figures make fun headers.**
Harry Dry (tweet 1773403909865771338). Specific numbers anchor a claim and pass falsifiability. Test: headline or first 2 lines contain a specific number the LP can substantiate. Vague qualifiers ("dramatically," "many") fail.

**M6. Provocation rooted in the product, not bolted on.**
Bernbach via Harry Dry (tweet 1918381482848014409). "Murder your thirst" works because Liquid Death is canned water; "Don't buy this jacket" works because Patagonia repairs them. Test: remove brand/product — does the provocation still make sense? If yes, untethered (fail).

**M7. Falsifiable copy.**
Harry Dry (tweet 1769762836723466674): "Good copy is falsifiable." "We care about your skin" — every clinic could say it. Test: could a generic competitor swap logos without rewriting? If yes, fail.

### LinkedIn Sponsored Content

**L1. Document ads as gated practical asset.**
"Gating a practical framework or research report inside a Document Ad consistently outperforms standard lead gen forms in B2B" (Funnel.io, Improvado 2026). Test: variant offers a downloadable artifact (memo, checklist, decision-tree, redline) with specific page-count or framework-name promise.

**L2. First 2 lines = entire ad.**
LinkedIn truncates Sponsored Content at ~150 chars before "see more." GrowthSpree 2026: specificity + POV + insights are the 2026 reward. Test: chars 0-149 contain (a) named audience, (b) specific outcome, (c) implicit CTA. <2 of 3 = fail.

**L3. Named outcome + named role.**
"Help your CFO close Q3 without three reforecasts" beats "Better forecasting for finance teams." Improvado 2026: $24 CPCs are economic when the ad self-targets by role+stage. Test: first line contains BOTH a job role (CFO, GC, head of legal ops, COO) AND a measurable outcome (close, reduce, recover, exit).

**L4. POV not summary.**
GrowthSpree 2026: creative quality is now a performance lever, not branding. "Three things every COO gets wrong in cross-border restructuring" beats "Cross-border restructuring services." Test: would every competing firm happily co-sign the text? If yes, no POV.

**L5. Document ad page 1 = the hook, not the cover.**
The in-feed preview frame IS page 1. Title-card with logo = near-100% scroll-past. Spiciest stat or framework diagram = swipe-in. Test: brief explicitly specifies "page 1 is the payoff."

---

## 2. Top 5-tier signals — mediocre ads that run but don't beat benchmark

Runs without rejection, doesn't scale.

- **5a. Hook is a category statement.** "Looking for a great Warsaw aesthetic clinic?" Reader's answer: "no, scrolling." No tension, no number.
- **5b. CTA is "Learn more."** Default Meta button. CTR sits at category-median (Klinika ~0.8%, legal LinkedIn ~0.4%) but never breaks through.
- **5c. Body lists features, not the outcome bought.** "We use HArmonyCa filler" vs "Two follow-ups in your first month, doctor on WhatsApp."
- **5d. One concept, five wordings.** Five variants run "Stop wasting money on X" with different X. Meta's Creative Entity ID (Dataally) clusters as one concept, starves four.
- **5e. Stock-photo bland.** Smiling model + white teeth + neutral background. Native-style is the 2026 reward (AdMove).
- **5f. LP hero is generic welcome.** Ad: "Skin tightening 18mo, Warsaw." LP: "Welcome to [Clinic]." Cross-asset eval (wetracked) downranks.
- **5g. LinkedIn ad fills 600 chars.** Hook buried at line 4, cut by truncation.
- **5h. Document ad page 1 is the cover.** Foreplay competitor-set shows page-1-as-hook variants 3-5× swipe-in rate.

---

## 3. Slop patterns (1-tier)

Auto-fails regardless of other strengths.

- **S1. "Learn more" CTA, no specific offer.**
- **S2. Stock-photo bland / generic studio shot.** Fatal on Reels (M2).
- **S3. Feature-explanation body.** "We offer HArmonyCa and Sculptra with US-trained doctors using HD ultrasound." Reader buys the outcome, not the brand-names.
- **S4. Five wordings of one bet.** Five "Stop wasting [X]" or five patient testimonials about one procedure. Meta clusters as one concept. Hardest-to-catch slop pattern.
- **S5. LP hero says different thing than ad headline.** Bait-and-switch. Cross-asset eval downranks (wetracked); reader CVR collapses regardless.
- **S6. AI-copy tells.** Em-dashes everywhere; "tapestry," "elevate," "unlock," "navigate the complexities of"; uniform 12-14-word rhythm; "isn't just X — it's Y" cadence; lists of three with parallel verbs.
- **S7. Provocation untethered from product.** "We hate marketing agencies too." But you ARE one. Fails M6.
- **S8. Falsifiability fail.** "Trusted by Warsaw professionals" — every clinic could write this.
- **S9. Klinika prohibited word.** "Best," "guaranteed," "permanent results," "cure," "transform." Compliance should catch; if leaks, quality judge auto-fails.
- **S10. DWF solicits / names fees.** "Hire us." "Starting at PLN X/hr." Violates Polish bar rules.
- **S11. Reel brief specifies "cinematic" / "high production value."** Inverse of M2.
- **S12. Document ad page 1 is the cover.** Failure mode of L5.

---

## 4. What separates 9-tier from 5-tier

**Meta image/Reels.** 9-tier wins on visual+audio hook stop-power + provocation-product fit + falsifiable claim. 5-tier loses by being competently boring. Gap is largely Impact (Trott triangle, M4). Reels: native-style beats studio (M2) — a 2026 inversion of older "high-quality = better" intuition and the easiest way for AI-generated copy to fail.

**LinkedIn Sponsored Content.** 9-tier wins on first-150-chars specificity (L2) + named role + outcome (L3) + POV (L4). 5-tier loses by being category-correct, position-less, over-long. Gap is POV. "We help GCs reduce litigation risk" is 5-tier. "Three things every GC of a Polish manufacturer gets wrong in cross-border IP (and a 4-page memo)" is 9-tier — number + role + outcome + POV + asset (L1).

**Variant-diversity is the trickiest separator.** A copywriter can produce 5 truly different bets or 5 wordings of one bet, and to a human they often look similar in the editor. "5 wordings of 1 bet" (S4) is the most common high-effort failure: time spent, all 5 competent, none will break through because they all chase one lever. 5 hooks all anchored to "save time" with different verbs (cut, slash, recover, reclaim, free up) is ONE bet. 5 hooks where one anchors to time, one to compliance risk, one to peer reputation, one to closing speed, one to total cost is FIVE bets. Needs a cohort-level diversity check — see C5.

---

## 5. Klinika + DWF specifics

### Klinika — Meta Reels ad scripts, aesthetic-medicine compliance-bounded

Polish aesthetic medicine is the hardest paid-media environment in the EU. Layered constraints:

1. **2023 Polish Art. 14 / device-advertising ban** (All 4 Comms, JLSW): no advertising specific devices to the public — lasers, ultrasound, carboxytherapy, peels, fillers, implants. No images of doctors in ads.
2. **Meta health-vertical policy** (Transparency Center, AdAmigo): no "best," "guaranteed," "instant," "clinically proven" without backing; no before/after; no second-person personal-attribute language; semantic evaluation reads implied meaning (wetracked 2026).
3. **Cross-asset enforcement** (wetracked): ad + LP + image reviewed together. Compliant ad + non-compliant LP = rejected.

What works inside these walls:

- **Educational POV from the clinic (NOT the doctor).** First-person plural, no doctor image, no procedure photo, no outcome promise. "Most Warsaw clinics get filler consults wrong. Here's what we ask new patients before going near a syringe."
- **Founder / operations POV.** Owner talks about WHY the clinic exists — brand narrative, not service advertisement.
- **Anonymous patient story, no procedure named.** "I came in confused. Three appointments later I had a plan I trusted." Procedure-name vacuum is intentional — drives consult inquiry, not price-shopping.
- **Process and trust signals, not outcomes.** "Two follow-ups in the first month. Your doctor's WhatsApp. No portal." Falsifiable (M7), not an outcome claim.
- **CTA = "Book a consultation," never "Book this treatment."** Consultation is information-exchange; specific-treatment ad would breach Art. 14.

What does NOT work: before/after carousels, doctor-on-camera Reels, specific-procedure ads, comparison ads.

### DWF — LinkedIn Sponsored Content, partner-track inquiry

Polish bar rules: solicitation prohibited, fee/scope disclosure restricted. Substitute structure for "Hire us":

- **Expertise-sharing, not retainer-sale.** "A short memo on Article 102 GCJ enforcement risk for Polish exporters, prepared by our trade team." Drives "send me the memo," not "engage us." Document ad (L1) is built for this.
- **Named outcome bound to decision-maker stage.** "If you're a GC of a Polish manufacturer with cross-border IP exposure in 2026, three things you should already have answers to." Self-targets at GC + stage.
- **POV / disagreement signal.** "Most M&A advisors will tell you to redomesticate before holding consolidation. We've done five where the opposite move saved 30%+ in stamp duty." Falsifiable, partner-track POV (adjust numbers to what DWF can substantiate).
- **Document ad with page-1-as-hook** (L5).
- **No fee mentions, no "engage us," no "schedule a consultation."** Substitute: "Reply with your jurisdiction and we'll send the relevant section."

5 angle-buckets that don't violate solicitation rules: regulatory-deadline memo, cross-border tax/IP framework, anonymized restructuring case, opinion-piece on a recent court decision, partner-authored research drop.

---

## 6. 2026 emerging signals

**Foreplay-based winners.** 10M+ ads, 200k+ brands; Spyder surfaces new ads from tracked brands in real time. 2026 archetypes for our verticals: founder-on-camera-at-desk Reels for healthcare; document/carousel "framework reveal" for legal/B2B. Reliability caveat: Foreplay shows IN-MARKET, not WORKING — cannot verify spend or ROAS. Drop the market-signal criterion if Foreplay reliability fails (Phase A note). Fallback: use Foreplay only to penalize variants that look NOTHING like in-market winners (high deviation = warning, not quality signal).

**Meta algorithm 2026.** Andromeda + Creative Entity ID (Dataally, Y'all): Meta clusters ads by latent concept, not surface variation. Five "different" ads with one underlying concept = one entity competing against itself, four get starved. This is the variant-diversity enforcement engine. Cross-asset compliance evaluation (wetracked, AdAmigo) treats text + LP + image as one unit. 47 ad-policy changes in March 2026 (AuditSocials), trending stricter on health-vertical semantics.

**LinkedIn Sponsored Content evolution.** Document ads = strongest single format for senior-decision-maker top-of-funnel (Funnel.io, Improvado, GrowthSpree). Conversation Ads + Message Ads less effective post-2025 (oversaturated InMail). Audience floor 50k for Sponsored Content delivery (StackMatix). 2026 CPC $8-24 for legal/finance roles, justified by LTV.

**iOS 18 measurement.** Attribution decay continues; CAPI + LP-side conversion APIs are table-stakes. Implication for the judge: a great ad whose LP lacks event wiring looks worse than it is. Out of scope for v1 rubric (operations, not creative), but flag in brief if LP isn't wired.

---

## 7. Implications for the judge

Six candidate criteria; mix of per-variant and cohort. Anchors 1-3-5 (1 = slop, 3 = median, 5 = ceiling).

### C1. Hook stop-power (per-variant)
**Grades.** Does the first 3 seconds (Reels) / first 150 chars (LinkedIn) / headline + first body line (image) contain a tension AND an early-resolution element (number, named name, specific verb, contrast flip)?
- **1.** Hook is a category statement or vague question. "Looking for a Warsaw aesthetic clinic?" "Better forecasting for finance teams." No tension, no resolution.
- **3.** Hook has tension OR resolution but not both. "Most aesthetic clinics in Warsaw get filler patients wrong." (Tension, no resolution yet.) Resolves eventually but past the truncation/scroll point.
- **5.** Tension + resolution both present in the first frame/line. "Two follow-ups in your first month. Your doctor on WhatsApp. No portal." (Falsifiable, concrete, resolution-in-place.)

Tier weight: high (hook is the single highest-leverage variant feature on both platforms).

### C2. Specificity & falsifiability (per-variant)
**Grades.** Could a generic competitor substitute their logo and run the exact same copy truthfully? If yes, fail. Look for specific numbers, named roles, named outcomes.
- **1.** Generic competitor swap is undetectable. "We care about your skin." "Trusted by Polish business leaders."
- **3.** One specific element (a named role, a number, or a named outcome) but two of three slots are generic.
- **5.** Named role + named outcome + at least one specific number or named name. Competitor swap would require rewriting the copy.

Tier weight: high. Anchors the M5/M7 Harry Dry signals.

### C3. Platform compliance & format fit (per-variant)
**Grades.** Format-correct, compliance-clean, native-style. (Compliance gate has passed by this point; criterion checks soft-compliance + format adherence.)
- **1.** Stock-photo bland visual, generic "Learn more" CTA, body copy listing features. Klinika: any tempt toward outcome promise. DWF: any solicitation language.
- **3.** Format-correct, no compliance-leakage, but visual brief defaults to studio-glossy and CTA is generic.
- **5.** Native-style production brief (handheld, ambient audio, VO script), CTA carries a specific promise ("Get the memo," "Book a 20-min consult"), Reels has audio-on with VO/music. Document ad page 1 is the hook, not the cover.

Tier weight: medium-high.

### C4. LP coherence (per-variant, CROSS-ARTIFACT)
**Grades.** Does the matched LP hero copy deliver on the ad headline's promise? Specifically: is the named outcome from the ad reused in the LP hero? Does the LP hero promise the same artifact (consult / memo / framework)?
- **1.** LP hero is generic welcome ("Welcome to DWF") or names a DIFFERENT outcome than the ad. Bait-and-switch.
- **3.** LP hero references the same domain but rewords the outcome. Reader has to translate.
- **5.** LP hero uses the ad's named outcome verbatim or a close synonym, names the same artifact (consult / memo), and the offer matches.

Input format for this criterion: judge receives BOTH the ad creative AND the matched LP hero copy as a paired artifact. Spec:
```yaml
variant_id: klinika-reels-v2
ad:
  hook: "Two follow-ups in your first month..."
  body: "..."
  cta: "Book a 20-min consult"
  visual_brief: "..."
lp_hero:
  headline: "Two follow-ups, your doctor's WhatsApp, no portal."
  subhead: "Aesthetic-medicine consultations in Warsaw..."
  cta: "Book your 20-min consult"
```

Tier weight: high. This is the cross-artifact check that prevents the most common silent failure mode.

### C5. Cohort variant diversity (COHORT-LEVEL)
**Grades.** Count distinct underlying bets across the 3-5 variants — NOT distinct wordings. A bet is the (angle, hook-lever, persona-stage) triple:
- **angle** = claim category (process / outcome / cost / risk / peer-reputation / regulatory-deadline)
- **hook-lever** = lever pulled (loss-aversion / curiosity / authority / social-proof / specificity-as-credibility / contrarian-POV)
- **persona-stage** = buyer-journey position (unaware / problem-aware / solution-aware / vendor-comparison)

Anchors:
- **1.** 1 distinct bet across all variants. Five "save time" wordings or five testimonials about one procedure (S4).
- **3.** 2-3 distinct bets across 5 variants. Some diversity, but pairs collapse.
- **5.** Each variant occupies a distinct (angle, lever, stage) tuple. 5 variants = 5 tuples.

Score = `min(distinct_tuples, cohort_size) / cohort_size` mapped to 1-5. To avoid handwaving, judge MUST emit the explicit (angle, lever, stage) tuple per variant in its rationale — operator can read tuples and override.

Tier weight: very high — most likely criterion to differentiate a thoughtful variant set from a high-effort one-bet set.

### C6. POV / non-genericity (per-variant)
**Grades.** Does the copy take a position a competing firm/clinic would disagree with, or could every competing operator co-sign the text?
- **1.** Every competitor could co-sign. Pure category language.
- **3.** Has POV implicitly but doesn't surface a disagreement. Hints at a position.
- **5.** Explicitly takes a position. "Most M&A advisors will tell you X. We've done five where Y saved 30%+." Names a contrarian stance + evidence.

Tier weight: medium (LinkedIn-weighted; Meta weights this less because visual hook can carry without explicit POV).

### Optional / market-signal (drop-if-unreliable)
**C7. Foreplay-alignment.** Does the variant resemble (in concept-tagging, not literal copy) ads currently in-market from Foreplay's library for the same vertical? Penalize ONLY high-deviation outliers (where every Foreplay winner is doing X and this variant does anti-X with no rationale). Default to scoring 3 when Foreplay reliability is uncertain. Per Phase A note: drop entirely if Foreplay reliability fails the dimension-test.

---

### Composite
Per-variant = weighted mean of C1-C4, C6 (drop C7 if disabled). Cohort = mean(per-variant) × C5/5 (diversity multiplier prevents high-diversity-but-mediocre from beating low-diversity-but-excellent and vice versa). Ship-eligibility: cohort ≥ 3.5 AND C5 ≥ 3 AND no variant has C1 < 2 or C4 < 2 (no broken hooks, no broken LP coherence).

Audit-ability: judge MUST emit per-variant the C5 (angle, lever, stage) tuple AND the C4 ad-headline-promise / LP-hero-promise pair quoted side-by-side. These two emissions keep the rubric auditable.

---

**Sources.**
- Harry Dry corpus (raw/ad_engine.json): tweets 1918381482848014409 (Bernbach provocation), 1765772001279418404 (Trott triangle), 1769762836723466674 (falsifiability), 1773403909865771338 (big figures).
- Meta creative 2026: [Social Media Today](https://www.socialmediatoday.com/news/meta-shares-tips-on-reels-hooks-creative-diversification-in-ads-and-threa/808182/), [AdMove](https://www.admove.ai/blog/meta-advantage-creative-best-practices-for-2026), [Motion App](https://motionapp.com/blog/creative-diversity-ad-volume-performance), [Reshift](https://www.reshiftmedia.com/meta-advertising-creative-diversity/).
- LinkedIn Sponsored Content 2026: [Funnel.io](https://funnel.io/blog/linkedin-advertising-2026), [Improvado](https://improvado.io/blog/linkedin-advertising-guide), [GrowthSpree](https://www.growthspreeofficial.com/blogs/linkedin-sponsored-content-vs-messaging-vs-conversation-ads-b2b-2026), [StackMatix](https://www.stackmatix.com/blog/linkedin-ads-best-practices).
- Meta healthcare compliance: [Transparency Center](https://transparency.meta.com/policies/ad-standards/restricted-goods-services/health-wellness/), [AdAmigo](https://www.adamigo.ai/blog/meta-ads-policy-unapproved-health-claims-explained), [wetracked.io](https://www.wetracked.io/post/meta-ads-new-sensitive-categories-restrictions), [AuditSocials March 2026](https://www.auditsocials.com/blog/meta-ad-policy-updates-2026-guide).
- Polish aesthetic medicine: [All 4 Comms](https://all4comms.com/how-to-legally-promote-aesthetic-medicine-online-in-poland/), [JLSW](https://jlsw.pl/en/news/zakaz-reklamy-medycyny-estetycznej/), [Digital Dot](https://digitaldot.com/metas-advertising-policies-a-guide-for-aesthetic-clinics/).
- Law-firm LinkedIn: [Mile Mark](https://www.milemarkmedia.com/lawyer-linkedin-marketing/), [Rankings.io](https://rankings.io/blog/tips-and-tricks-for-linkedin-marketing-a-law-firm/), [Good2BSocial](https://good2bsocial.com/the-law-firm-guide-to-linkedin-advertising/).
- Diversity + Andromeda + Foreplay: [Superads](https://www.superads.ai/blog/creative-diversity-in-ads), [Dataally](https://www.dataally.ai/blog/metas-creative-entity-id-why-creative-diversification-is-essential), [Y'all](https://www.yall.co/post/why-creative-diversity-is-the-only-way-to-win-with-metas-andromeda-algorithm), [Foreplay.co](https://www.foreplay.co/).
