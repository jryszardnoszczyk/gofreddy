---
date: 2026-05-12
phase: D
lane: article_engine
status: spec — implementer-ready; NEW lane (no v188 predecessor); ART-8 rule-file content gated on Resolve-Before-Planning #2 (legal review)
inputs:
  - phase-a-lane-purposes.md §8 (article_engine, two adaptors)
  - phase-b-research/article_engine.md (8 candidate criteria, blog-vs-LinkedIn ceiling divergence, voice-fidelity-as-biggest-gap)
  - phase-c-variant-ratings.md (no existing fixtures — NEW lane; proceed on Phase B research strength)
---

# Phase D — article_engine rubric spec (2 platforms, 8 criteria)

`article_engine` is new in v1. It ships long-form articles in two adaptors — **blog** (`articles/blog/<slug>.md` with SEO meta + JSON-LD Article schema + body-image briefs) and **linkedin_article** (`articles/linkedin_article/<slug>.md` with first-200-char hook + LinkedIn paragraph cadence). It consumes findings-briefs from `geo` (Klinika Polish procedure-page articles) and `monitoring` (DWF Poland Polish regulatory explainers under named partner bylines).

Phase B fixed two non-negotiables. (1) **The two adaptors do not share a ceiling**: blog optimises for AI-search citation + organic search on 60-90 days against a mechanical surface (schema, depth, extractability, source density); LinkedIn Article optimises for B2B buyer trust + engagement formula `(reactions×1 + comments×3 + shares×5) × exp(-days/14)` against a political surface (named-buyer follows, dwell). A judge that grades both identically overfits one. (2) **Voice fidelity at long-form scale is the biggest 9-vs-5 gap** — articles are 8-15× longer than tweets, so 8-15× more chances to slip; mid-article drift to neutral LLM register is what most separates 5-tier from 9-tier and what opener/closer-only checking systematically misses.

This spec locks **8 criteria**: 5 essential, 2 important, 1 pitfall. ART-1 (hook) and ART-6 (platform fit) branch anchors on `platform_target ∈ {blog, linkedin_article}`. ART-7 fires only when `brief.lang == "pl"`. ART-8 is a **compliance precondition** with auto-cap: a confirmed violation caps overall fixture at 4. ART-4 carries a separate **HARD FLOOR**: any rolling 200-word window exceeding 2σ voice-distance caps ART-4 at 2. Two follow-ups remain operator-gated: `platform_target` dispatch source (frontmatter recommended, §3); ART-8 rule-file content (legal-review per Resolve-Before-Planning #2).

---

## Section 1 — Summary table

Tier vocabulary: **essential** (load-bearing for ship-eligibility), **important** (drags score when failed), **pitfall** (specific failure caps the score).

| ID | Quality | Tier | Platform branching |
|----|---------|------|--------------------|
| ART-1 | Hook strength — extractable falsifiable answer in first attention unit | essential | **branches** (blog: first 100 words; linkedin_article: first 200 chars) |
| ART-2 | Argument coherence — one specific thesis defended across every section | essential | shared anchors |
| ART-3 | Citation density + verifiability — ≥2 named-dated-resolving sources per load-bearing claim; ≥12 for ≥2,500-word blog | essential | weight upweighted for blog |
| ART-4 | Voice fidelity at long-form scale — rolling 200-word-window distance vs `voice_persona.corpus_path` | essential, HARD FLOOR | shared anchors |
| ART-5 | Specificity — named entities + numbers + dated decisions per 1,000 words, brief-grounded | important | shared anchors |
| ART-6 | Platform-adaptor fit — form that the target platform actually rewards in 2026 | important | **branches** (blog: JSON-LD + H2/H3; linkedin_article: cadence + numbered + close-as-question + no first-half external links) |
| ART-7 | Polish-language naturalness — native expert Polish vs auto-translation | important (fires when `lang == "pl"`) | shared anchors |
| ART-8 | Compliance precondition — `medical_pl` (Klinika) / `legal_pl` (DWF) per byline | pitfall, **auto-cap** | regime branches on byline |

All 8 fire on both adaptors; only ART-1 / ART-6 *anchors* branch and ART-3 *weight* differs. Branching ART-2 / ART-4 / ART-5 / ART-7 / ART-8 would silently fork the calibration corpus and make blog/LinkedIn scores incomparable.

**ART-4 is essential and HARD FLOOR** because mid-article voice drift is what most separates 5-tier from 9-tier on blog; opener/closer-only checking misses it; the rolling 200-word-window mechanism (§4) is the only test that catches a writer in voice for the first 600 words and LLM-register for the next 1,500. **ART-8 is a precondition not a deduction** because YMYL compliance violations are categorical: an article that misleads on dosage is not "mostly good with one gap" — it is not shippable.

---

## Section 2 — Final criterion prose

### ART-1 — Hook strength (essential, **platform-branched**)

**Evaluate this article for ONE quality:** Does the opening land an extractable, falsifiable, on-topic answer in the first attention unit — first 100 words for blog, first 200 chars for linkedin_article?

Blog readers arrive from search or AI-citation: the first 100 words must confirm "yes, this answers that, here is the answer" — otherwise AI extractors cite a competing page that did. LinkedIn Articles collapse after ~3 lines on mobile; the visible portion must earn the "see more" tap. Counter-intuitive + falsifiable + specific is what triggers both comments and dwell.

**Blog anchors:**
- **Score 1:** Buries the answer past the first 100 words. Throat-clear opener ("In today's rapidly evolving landscape…"). Or topic-correct but thesis-absent — reads as Wikipedia summary.
- **Score 3:** On-topic, competent setup, answer deferred to §2 or §3.
- **Score 5:** First 100 words contain a complete specific falsifiable declarative answer to `brief.topic_question`. `<h1>` matches the brief's topic; lede names when the claim would *not* hold (falsifiable + bounded).

**LinkedIn Article anchors:**
- **Score 1:** First 200 chars are setup or generic frame ("Last week I was at a conference…"). No specific number, no named entity, no contrarian claim. 2026 LinkedIn penalises engagement-bait openers ~60%; setup openers fall in the same bucket.
- **Score 3:** Soft hook — on-topic, specific-ish, missing one of {counter-intuitive, specific number, named entity}.
- **Score 5:** First 200 chars carry a counter-intuitive specific falsifiable claim. Specific number OR named entity OR contrarian framing of a load-bearing brief claim. Strip everything after char 200 and the reader still has the headline takeaway + reason to tap "see more."

**Ground truth.** Cross-reference `brief.topic_question`. Blog: LLM extractor on first 100 words — can it produce a one-sentence answer? LinkedIn: char-count + check first 200 chars for ≥1 of {number, named entity, contrarian-framing marker}. Substrate pre-computes; judge cross-references.

Provide your reasoning, quote the first 100 words (blog) or first 200 chars (LinkedIn), then give your score.

### ART-2 — Argument coherence (essential)

**Evaluate this article for ONE quality:** Does one specific thesis carry across every section of the body, defended with evidence in each section rather than re-asserted as decoration?

Long-form has a middle, and the middle is where the thesis is tested — each H2 either advances the argument or fails it. 5-tier articles have a strong opener and closer with orthogonal topic-correct paragraphs between, re-orderable without loss. 9-tier articles have a body where §3 builds on §2 and §4 closes the loop opened in §1.

- **Score 1:** No identifiable through-line, OR reader can state two competing theses, OR opener thesis never reappears in body. Sections re-orderable without loss.
- **Score 3:** Identifiable thesis. Most sections gesture at it; 1-2 orthogonal asides. Reader at end cites mostly opener/closer when asked to defend (middle didn't carry).
- **Score 5:** One specific thesis. Every H2 advances it — §2 establishes mechanism, §3 demonstrates with named case, §4 addresses obvious objection, §5 bounds the claim, closer routes to consequence. Reader can defend the thesis citing any section. Sections not re-orderable without breaking the argument.

**Ground truth.** Judge writes the candidate thesis sentence in evidence *before* scoring, then maps each H2 to one of {advances, bounds, addresses objection, demonstrates with case, orthogonal aside}. ≥1 aside in ≤6 H2s = 3-tier; ≥2 = 1-tier. Cross-reference `brief.thesis_hypothesis` if upstream provided.

Provide your reasoning, write the candidate thesis sentence, classify each H2, then give your score.

### ART-3 — Citation density + verifiability (essential; weight upweighted for blog)

**Evaluate this article for ONE quality:** Are load-bearing factual claims defended with ≥2 distinct named-dated-link-resolving sources, with named experts in verbatim `"..."` quotation, and (for ≥2,500-word blog) with ≥12 sources overall?

AI extractors triangulate before citing — single-source claims get filtered as opinion. Two named sources is the minimum that survives the synthesiser's confidence threshold; for YMYL it is the *floor*. The 2026 GEO research is unambiguous: long-form depth pays — ≥12 named sources on ≥2,500 words is the working threshold. Verbatim `"..."` from credentialed humans is the unit-of-citation that loses provenance under paraphrase.

- **Score 1:** Claims unsupported, OR hyperlinks resolve to homepages/paywalls/404s, OR single-secondary sources (Wikipedia, "studies show"), OR `"..."` attributed to "an expert" without name + credential + date. ≥2,500-word blog: <6 distinct sources. Hallucinated-shape URLs are auto-1.
- **Score 3:** ≥1 source per claim, mostly secondary, dated within 5 years. Some `"..."` with name but no credential or date. Long-form blog: 6-11 sources. Link graph mostly resolves; 1-2 dead links.
- **Score 5:** ≥2 named sources per load-bearing claim with ≥1 primary (peer-reviewed paper, official register, regulatory document) within 24 months. All hyperlinks resolve (HEAD 200). ≥1 `"..."` verbatim quote per 800 words, each ≥15 words, each followed by `— [Name], [Credential], [Date or Org]`. ≥2,500-word blog: ≥12 distinct sources, ≥4 primary. Sources cluster around load-bearing claims.

**Ground truth.** Parse markdown link graph; HEAD-check each URL (substrate pre-check); cross-reference quoted experts against `brief.findings`. Quotes attributed to names not in the brief = inflation flag — judge cannot ground-truth invented experts.

Provide your reasoning, count load-bearing claims and sources, list dead links or unverifiable quotes, then give your score.

### ART-4 — Voice fidelity at long-form scale (essential; **HARD FLOOR**)

**Evaluate this article for ONE quality:** Could the named byline — Dr. Maria for Klinika, the named DWF partner — have written this article, measured across every rolling 200-word window of the body?

A long-form article is 8-15× longer than a tweet → 8-15× more chances to slip. Failure modes: (a) opener in voice, drift to neutral LLM register by paragraph 4, never recovers; (b) jargon imported from cited source the byline would never use; (c) abstraction-level shift mid-paragraph. Opener/closer-only checking does not catch these; the rolling 200-word-window mechanism (§4) does. Ground truth = the operator-recognition test: would the named expert, reading out of context, recognise it as theirs?

- **Score 1:** LLM register throughout, OR drifts to LLM register by paragraph 4 and never returns, OR any window > 2σ from corpus baseline (HARD FLOOR — §4). Median window distance > corpus 75th percentile. Signature phrases absent.
- **Score 3:** Opener + closer in voice. Middle 60% drifts to neutral. Corpus lexical overlap ≥30% but <60%. 1-2 windows close to but not exceeding HARD FLOOR.
- **Score 5:** Voice-distance within threshold across every window. Distinctive lexical patterns match corpus (signature phrases — "obserwuję" / "zalecam" / "w mojej praktyce" for Dr. Maria; "nasza kancelaria obserwuje" / "warto przy tym zauważyć" for DWF partner). Median ≤ corpus median. Worst ≤ corpus 90th percentile. Operator-recognition test: byline would say "yes, that's mine."

**HARD FLOOR.** If *any* window exceeds corpus 2σ voice-distance, ART-4 caps at 2 regardless of qualitative read. Different mechanism from ART-8's overall-fixture auto-cap; this caps only ART-4. A single window reading as somebody-else-wrote-this is enough for operator-recognition to fail.

**Ground truth.** Cross-reference `voice_persona.corpus_path`. Substrate computes rolling-window distances deterministically (§4) and passes `voice_distance.{median,worst,window_count,hard_floor_triggered,signature_phrase_rate}` to the judge. Judge does not recompute — grades against numbers + qualitative dimension.

Provide your reasoning, name worst-window and median-window distances, identify HARD FLOOR triggers, then give your score.

### ART-5 — Specificity (important)

**Evaluate this article for ONE quality:** Are named entities, specific numbers, and dated decisions present per 1,000 words at a density consistent with "the byline did the work," sourced from `brief.md` rather than invented?

Generic ("clinics see results in 4-6 weeks," "many firms struggle") reads as content-farm. Specific ("23 of 27 patients in Q1 2026 reached full clearance by week 8"; "the four December 2025 executive regulations under Dz.U. nr 412/2025") reads as written-by-the-person-doing-the-work. The catch: specifics must be *real*. Invented numbers ("a 2024 study found 67%…" with no citation) are fabrications and trip ART-3. Specifics absent from the brief that the article cannot back with a citation are a downgrade, not an upgrade.

- **Score 1:** Zero named entities; zero specific numbers; generic placeholders ("a major Polish law firm," "one aesthetic clinic in Warsaw"). OR specifics present but unsourced — fabrication-shaped.
- **Score 3:** 1-2 named entities per 1,000 words; some specific numbers, most "many/often/generally." Specifics mostly sourced. Cases industry-generic.
- **Score 5:** ≥4 concrete numeric-or-named claims per 1,000 words. Each specific traceable to `brief.findings` or to a cited resolving source. Klinika cases anonymised + consented + specific; DWF cases public + named (Dz.U., komunikat MF, sygn. akt).

**Ground truth.** NER + number-regex (substrate pre-check). Cross-reference each named entity against `brief.findings` — specifics in the brief get credit; specifics absent require a resolving in-text citation. Compliance allowlist: Klinika anonymised; DWF public (no client-matter disclosure).

Provide your reasoning, count specifics, list unverifiable ones, then give your score.

### ART-6 — Platform-adaptor fit (important; **platform-branched**)

**Evaluate this article for ONE quality:** Does the article land the form that its target platform actually rewards in 2026?

Blog rewards machine-readable structure (JSON-LD, extractable H2/H3 with H3s phraseable as search queries, named credentials in schema, fresh `dateModified`, instructive body-image briefs). LinkedIn Article rewards 2026 algorithm signals: dwell over raw engagement, paragraph cadence, numbered structure, close-as-question, and critically *no external links in the first half* (~60% engagement penalty). Same content on the wrong adaptor underperforms badly.

**Blog anchors:**
- **Score 1:** Missing JSON-LD, OR JSON-LD missing `author.@type=Person` / `medicalSpecialty` / `legalArea` / `datePublished` / `dateModified`. H2 hierarchy absent or wall-of-text. H3s are topic labels ("Background," "Considerations," "Conclusion"), not extractable questions. Body-image briefs describe stock photography.
- **Score 3:** JSON-LD minimal — present but fields missing or stale. H2 hierarchy present; H3s mixed. Body-image briefs adequate but not instructive.
- **Score 5:** Full `Article` schema, `Person` author typed `Physician` (Klinika) / `Lawyer` (DWF), `medicalSpecialty` / `knowsAbout` / `legalArea` populated, `datePublished` + `dateModified` fresh (≤90 days for AI-citation). H2 every 200-400 words. Every H3 phraseable as a search query the next 200-400 words answers verbatim. Body-image briefs anatomically specific ("annotated skin cross-section, microneedle depth indicators at 0.5/1.0/1.5mm, labels in Polish"). Author `@id` matches byline registry.

**LinkedIn Article anchors:**
- **Score 1:** Paragraphs average >5 sentences. No numbered structure visible in first screen. External links in first half. Close = "Thoughts?" / generic CTA. Reads as three blog paragraphs pasted into LinkedIn.
- **Score 3:** Cadence mixed. Numbered structure present but not visible in first screen. 1 external link in first half. Close is a specific question but not platform-native ("How does this play out in your industry?").
- **Score 5:** ≤3 sentences per paragraph, none >5, empty line between every paragraph. Numbered structure visible in first screen with one tactical takeaway per item. Zero external links in first half (final CTA OK). Close = one specific named-process question referencing a named entity / decision / timeframe ("Czy Państwa dział księgowości testował już wysyłkę przez API w środowisku przedprodukcyjnym?"). Bold on dates + numeric thresholds. Suitable for parallel PDF/document export.

**Ground truth.** Blog: JSON-LD validator; markdown AST for H2/H3; interrogative regex on H3 text; words-per-H2 count. LinkedIn: char-count + paragraph-length distribution + external-link position + question-detection regex on closing paragraph. All deterministic; judge grades against parsed structure.

Provide your reasoning, cite platform-specific evidence, then give your score.

### ART-7 — Polish-language naturalness (important; fires when `brief.lang == "pl"`)

**Evaluate this article for ONE quality:** Does the Polish read as native expert in the domain, or as English-then-translated with calque vocabulary papered over?

Polish morphology and clause structure differ from English in ways machine translators flatten and English-first LLMs reproduce. Native readers (and Polish engines including Bielik) detect translated-from-English text within 2 paragraphs. Failure signature: calque vocabulary (innowacyjny, kompleksowy, holistyczny, synergia, transformacja cyfrowa) where native experts use verb-driven concrete language; nominal-style dominance ("przeprowadzenie analizy ryzyka") where Polish prefers verbal-style ("analizujemy ryzyko"); English bigram rhythm in Polish vocabulary. The bar is *native expert in the relevant domain*.

- **Score 1:** Multiple calque per paragraph. Nominal-style >60%. English bigram rhythm. Reads as machine-translated then word-edited by non-native speaker.
- **Score 3:** Competent non-specialist Polish. 1-2 calque per page. Nominal/verbal mixed (40-60% nominal). Native general-reader would not flag; native domain expert would notice register mismatch.
- **Score 5:** Native expert Polish in domain. Verbal style >70%. Idiomatic constructions appropriate to register. <1 calque per 500 words. Native bigram distribution on appropriate corpus (medical for Klinika; legal for DWF).

**Ground truth.** Per-lane calque-frequency list (operator-loaded); nominal-vs-verbal style ratio (POS pre-check); native-Polish bigram model on domain corpora — distance score vs expected distribution. All deterministic; judge grades against scores.

Provide your reasoning, cite calque hits, name nominal-vs-verbal ratio + register, then give your score.

### ART-8 — Compliance precondition (pitfall, **auto-cap**)

**Fires per byline:** `medical_pl` for Klinika (Dr. Maria byline); `legal_pl` for DWF (named partner byline).

**Evaluate this article for ONE quality:** Is the article useful and specific while staying inside the Polish medical-advertising rule set (Polish Medical Chamber Code of Ethics art. 63-65, pharmaceutical advertising statute) or the Polish bar advertising rule set (KIRP / KRRP)?

YMYL compliance violations are categorical, not gradient. The pre-publish human gate catches violations as a backstop; the in-loop judge catches them earlier so the loop regenerates. Over-caution kills value: "we cannot discuss specifics" said three times produces compliance-clean but useless content. Phase B ceiling: "compliance enables specificity within bounds; the avoidance doesn't show."

**Cross-reference (gated on Resolve-Before-Planning #2).** Rules at `configs/compliance/{medical_pl,legal_pl}/rules.yaml`. Rule text operator-loaded after legal review. This spec defines categories and auto-cap semantics, not rule text.

**`medical_pl` categories (Klinika):** (a) POM-name blocklist (Botox, Dysport, Vistabel, Azzalure); (b) result-promise patterns ("guaranteed results," "look 10 years younger"); (c) comparative claims ("best clinic in Warsaw"); (d) off-label use; (e) missing PWZ-verifiable credential; (f) missing contraindications section.

**`legal_pl` categories (DWF):** (a) solicitation verbs ("contact us today," "skontaktuj się z nami"); (b) fee mentions; (c) comparative claims ("better than other firms"); (d) client-result promises; (e) pending-litigation prediction as fact; (f) unauthorised client-matter disclosure; (g) Ustawa / Rozporządzenie citation without Dz.U. number; (h) missing partner bar number / firm affiliation.

**Auto-cap.** Confirmed regex/pattern match against any category triggers **auto-cap at score 2** for ART-8 AND **caps overall fixture at 4**. Deterministic — match triggers cap regardless of qualitative read. Multiple-category match does not lower further; cap is binary. Evidence requires the quoted string + location; vague evidence ("the article mentions Botox") does not trigger the cap.

- **Score 1:** Confirmed violation quoted. Auto-cap fires; overall fixture capped at 4.
- **Score 3:** No explicit violation but content so cautious it loses informational value. "We cannot discuss specific brands" said three times.
- **Score 5:** Compliance-clean AND uses full permitted latitude. Klinika: specific anonymised consented case ("our practice, Q1 2026, 27 patients, 23 reaching full clearance by week 8"), filler chemistry named where compliant (hyaluronic acid), post-procedure timelines specific, contraindications section present, PWZ on byline. DWF: dated regulatory citations with Dz.U. numbers, named statute articles, public administrative rulings, no solicitation, close = buyer-side question not CTA, bar number on byline.

Provide your reasoning, scan against each rule category, quote any violations + identify category, then give your score.

---

## Section 3 — Platform-adaptor dispatch

The article carries `platform_target` in frontmatter. The substrate reads frontmatter, assembles the per-platform rubric from the 8-criterion superset, passes only branched anchors to the judge. LaneSpec stays platform-agnostic — the lane is `article_engine`; per-fixture frontmatter declares the adaptor.

Frontmatter schema:

```yaml
---
platform_target: blog                          # blog | linkedin_article
compliance_regime: medical_pl                  # null | medical_pl | legal_pl
voice_persona: klinika/byline/maria-kowalska   # path under configs/voice_persona/
lang: pl                                       # ISO; ART-7 fires when pl
brief_path: briefs/klinika/mezoterapia-po-40.md  # upstream geo/monitoring brief
---
```

**Default dispatch:**
- `platform_target` absent → fixture rejected at structural gate (no platform default for this lane).
- `compliance_regime` absent → ART-8 fires in shape-only mode (confirms cross-reference path exists, abstains scoring). Failure-loud rather than silently scoring against empty rules.
- `lang` absent → ART-7 does not fire.

**Per `platform_target`:**
- **blog** → ART-1 blog anchors (first 100 words); ART-6 blog anchors (JSON-LD + H2/H3 extractability); ART-3 weight upweighted (≥12 sources for ≥2,500-word for AI-citation depth).
- **linkedin_article** → ART-1 linkedin_article anchors (first 200 chars); ART-6 linkedin_article anchors (cadence + numbered + close-as-question + no first-half external links); ART-3 weight standard.

ART-2, ART-4, ART-5, ART-7, ART-8 use shared anchors. Branching them would silently fork the calibration corpus.

---

## Section 4 — Voice fidelity at long-form: the rolling-window mechanism

Voice fidelity is the biggest 9-vs-5 gap on blog. Opener/closer-only checking does not catch mid-article drift; the rolling 200-word-window mechanism does. This section specifies what implementers wire.

**Windows.** Size **200 words** (matched to paragraph cluster; smaller is too noisy on signature-phrase frequency; larger masks drift). Stride **100 words** (50% overlap). Body only — skip frontmatter, title, author block, source list, JSON-LD.

**Per-window voice-distance.** Weighted sum of four components (weights operator-loaded per `voice_persona`; defaults equal):
1. **Distinctive bigram overlap.** Cosine distance on top-200 corpus-distinctive bigrams (corpus frequency ≥3× general-Polish-or-English baseline).
2. **Sentence-length distribution.** KL divergence or EMD on window mean / variance / max vs corpus.
3. **Signature-phrase frequency.** Each `voice_persona` declares `signature_phrases`. Window rate normalised to corpus baseline. Absent = high distance.
4. **First-person / imperative / declarative ratio.** Clause-type distribution vs corpus.

**Scoring anchors.** Median window distance = primary signal (score 5 requires median ≤ corpus median). Worst window distance = secondary (score 5 requires worst ≤ corpus 90th percentile). **HARD FLOOR**: any window > corpus 2σ (≈98th percentile) caps ART-4 at 2. A single window reading as somebody-else-wrote-this is enough for operator-recognition to fail. HARD FLOOR forces the loop to regenerate those windows; does not by itself cap the overall fixture (ART-8 does that).

**Corpus calibration.** `voice_persona.corpus_path` must be ≥5,000 words of verified-authored writing (Dr. Maria's prior blog posts; DWF partner's prior articles + court filings + sanitised memos). Corpus is split into windows on first load; corpus's own window-distance distribution computed once and cached. Per-fixture distances compared against cached distribution.

**Judge interface.** Substrate computes distances and passes `voice_distance.{median,worst,window_count,hard_floor_triggered,signature_phrase_rate}` to the judge. Judge does not recompute — grades against numbers + qualitative dimension.

**Non-platform-specific.** LinkedIn Articles (800-1,500 words) are shorter than blog (1,500-2,500+); same failure mode, same threshold, only window count differs (~10-15 for LinkedIn, ~25-35 for blog). Median/worst handles length naturally.

---

## Section 5 — Implementation notes

**Lane is NEW.** No v188 predecessor. Calibration corpus must be built from the first 10 fixtures (5 Klinika blog + 5 DWF LinkedIn, §7) before evolution can be trusted.

**`lane_registry.py`.** Lane registers as `article_engine` with two adaptors (`blog`, `linkedin_article`) declared as `platform_target`. Consumes findings-briefs from `geo` (Klinika SEO topics) + `monitoring` (DWF regulatory events). Brief contract R21 from v1 brainstorm: frontmatter declares `topic_question`, `findings`, `findings_freshness`, `thesis_hypothesis`, `language`.

**Rubric ID convention: ART-1..8.** Three-letter prefix + single digit. Matches storyboard SB-1..15. No ambiguity with existing IDs (MA, MON, GEO, CMP, SB).

**`voice_persona` directory:**

```
configs/voice_persona/klinika/byline/maria-kowalska/
  corpus.md              # ≥5,000 words verified-authored writing
  voice_rules.yaml       # signature_phrases, register, calque_blocklist
  style_anchors.yaml     # POS-style targets, sentence-length, first-person rate
  metadata.yaml

configs/voice_persona/dwf/partners/<partner-slug>/
  corpus.md
  voice_rules.yaml       # Polish legal signature phrases, formal connectives
  style_anchors.yaml     # nominal-vs-verbal target, first-person rate
  credentials.yaml       # bar number, practice areas, named-case authority (cross-ref ART-5 + ART-8)
```

`voice_rules.yaml` + `style_anchors.yaml` parameterise the rolling-window computation. `credentials.yaml` cross-references for ART-5 (authority) and ART-8 (partner bar number on byline).

**Compliance regime integration.** ART-8 lives here; trigger phrase content lives in `configs/compliance/{medical_pl,legal_pl}/rules.yaml`. Same files referenced by storyboard SB-12 / SB-15 + x_engine / linkedin_engine / image_engine / ad_engine. Resolve-Before-Planning #2 covers rule-file content. Until populated, ART-8 fires in shape-only mode.

**RUBRIC_VERSION hash invalidates on:** (1) ART-1..8 text changes; (2) ART-1 / ART-6 anchors change; (3) `configs/compliance/{medical_pl,legal_pl}/rules.yaml` content hash changes; (4) `voice_persona.corpus_path` content hash changes (active-fixture bylines); (5) `voice_rules.yaml` / `style_anchors.yaml` change; (6) rolling-window parameters change. Without (3)-(5), score cache could return stale verdicts after rule or corpus updates and ship voice-drifted or violating content.

**Two-gate compliance design preserved.** In-loop judge drives evolution toward compliance-clean output; pre-publish human reviewer catches the rest. Auto-cap at ART-8 = 2 + overall fixture cap at 4 keeps violations below ship-eligibility.

**Deterministic pre-checks fed to the judge.** Slop-lexicon detection ("In today's rapidly evolving," "Let's dive deeper," "Three key pillars," "synergia," "transformacja cyfrowa," "Conclusion: In conclusion"); link-graph HEAD-check; JSON-LD validation; first-200-char extraction; paragraph-length distribution; H2-words count; H3 interrogative classification; voice-distance window computation; calque-frequency count; nominal-vs-verbal ratio; named-entity + specific-number count. All run in substrate's structural gate. Judge does not recompute.

---

## Section 6 — Klinika + DWF demo specifics

### Klinika blog — Polish procedure-page (Dr. Maria byline)

**Frontmatter:** `platform_target: blog`, `compliance_regime: medical_pl`, `voice_persona: klinika/byline/maria-kowalska`, `lang: pl`.

**Load-bearing criteria:** ART-1 (first 100 words answer the procedure question); ART-3 (≥12 sources for ≥2,500-word procedure deep-dives; ≥1 primary PubMed / EMA / Polish Society of Dermatology per claim); ART-4 (Dr. Maria's first-person clinical voice — "obserwuję," "zalecam," "u moich pacjentek," "w mojej praktyce"; corpus = prior blog posts); ART-6 (full JSON-LD `Person.Physician` + `medicalSpecialty: Dermatology` + `dateModified` ≤90 days; H2 every 200-400 words; H3s phraseable as patient questions — "Jak długo utrzymuje się efekt?", "Jakie są realne przeciwwskazania?"; body-image briefs anatomically specific); ART-7 (native Polish clinical register; verb-driven; <1 calque per 500 words); ART-8 (POM blocklist, no result promises, no comparatives, no off-label, PWZ on byline, contraindications section present). Polish Medical Chamber Code of Ethics art. 63-65 binds.

**Voice anchors:** First-person clinical, measured, no superlatives, willing to say "tego nie wiemy jeszcze na pewno." Verbal-style >70%. Avoids junior-marketing register ("kompleksowa opieka," "innowacyjne rozwiązania," "holistyczne podejście").

### DWF linkedin_article — Polish regulatory explainer (named partner byline)

**Frontmatter:** `platform_target: linkedin_article`, `compliance_regime: legal_pl`, `voice_persona: dwf/partners/<partner-slug>`, `lang: pl`.

**Load-bearing criteria:** ART-1 (first 200 chars carry regulatory fact + deadline + cost of missing it); ART-4 (partner's formal Polish legal register with measured first-person observations; corpus = prior articles + court filings + sanitised memos); ART-5 (Dz.U. numbers, sygn. akt court dockets, komunikat MF numbers, MoF press releases per 500 words; cross-reference `credentials.yaml` for partner's standing-to-speak); ART-6 (≤3-sentence paragraphs; numbered structure visible first screen; zero external links first half; close = specific named-process question); ART-7 (native Polish legal register; formal connectives — zatem / w konsekwencji / natomiast — used correctly; no calque); ART-8 (no solicitation, no fee mentions, no comparatives, no client-result promises, no pending-litigation prediction, Dz.U. numbers on all statute citations, partner bar number on byline). KIRP / KRRP bar advertising rules bind.

**Voice anchors:** Formal third-person institutional ("nasza kancelaria obserwuje," "w kontekście") punctuated with 1-2 first-person observations ("warto przy tym zauważyć," "moim zdaniem"). Sentence-length variance higher than Klinika (accommodates 30-word sentences).

---

## Section 7 — Validation plan

**V1. Voice fidelity rolling-window catches mid-paragraph drift.** Take a Dr. Maria blog fixture scoring ART-4 = 5. Construct a synthetic-drift variant: keep first 600 words verbatim; replace next 1,000 words with LLM-paraphrased content (no voice prompt). Expected: window mechanism flags windows 4+ as exceeding 2σ HARD FLOOR; ART-4 caps at 2; overall fixture drops ≥1.5 points. If the drift variant scores ART-4 ≥3, window mechanism not configured correctly — inspect per-window distance output. Repeat against DWF partner LinkedIn fixture.

**V2. Compliance precondition auto-fires on synthetic violations.**
- *medical_pl:* take Klinika blog (1); insert "Botox" in two paragraphs; append "guaranteed permanent results"; add "the best dermatology clinic in Warsaw." Expected: ART-8 = 1; overall capped at 4; judge quotes "Botox" (rule a), "guaranteed permanent results" (rule b), "the best dermatology clinic in Warsaw" (rule c).
- *legal_pl:* take DWF LinkedIn (1); append "Skontaktuj się z naszym zespołem — pomożemy w pełnej implementacji"; insert "Nasze stawki są konkurencyjne" in §3; replace closing question with "Zadzwoń do nas dziś." Expected: ART-8 = 1; overall capped at 4; judge quotes violating strings + categories.
- Any violating fixture scoring above 4 means auto-cap not wired correctly. Cap must be deterministic (regex match → cap), not judgment-driven.

**V3. Per-platform anchor discriminates blog vs linkedin_article.** Take one underlying article ("KSeF 2.0 — three things before December") and render twice: blog (full JSON-LD, H2/H3, ≥12 sources, 2,500 words) and linkedin_article (first-200-char hook, numbered, ≤3-sentence paragraphs, close-as-question, ~1,200 words). Expected: ART-1 and ART-6 score differently. If both score the same on ART-1 and ART-6, platform dispatch firing wrong anchors.

**V4. Klinika blog demo — 5 fixtures, calibration corpus.** "Mezoterapia igłowa po 40-tce"; "Hialuronowy filler ust: dzień 1 vs 7 vs 14"; "Botulina w gabinecie estetycznym"; "Lifting nici"; "Pierwsza wizyta u dermatologa estetycznego." All blog / medical_pl / pl. Expected: all 5 fire ART-1..8; ≥4 of 5 score ≥4 on ART-8; ≥4 of 5 ≥4 on ART-3 (≥12 sources, ≥4 primary); ≥3 of 5 ≥4 on ART-4. A fixture scoring 5 across the board on first run is almost certainly inflation — spot-check rolling-window output + source list.

**V5. DWF LinkedIn demo — 5 fixtures, calibration corpus.** "Co naprawdę zmienia KSeF od 1 lutego 2026"; "Polish Grid Act 2026 vs dyrektywa UE"; "Wyrok TK K 38/24 a praktyka compliance"; "Nowa Ordynacja Podatkowa — Q3"; "Implementacja CSRD w polskim prawie spółek." All linkedin_article / legal_pl / pl. Expected: all 5 fire ART-1..8; all 5 ≥4 on ART-8; all 5 ≥4 on ART-1; ≥4 of 5 ≥4 on ART-6; ≥3 of 5 ≥4 on ART-4.

**V6. Brief-grounding check.** For each of 10 calibration fixtures, verify ≥80% of named entities and ≥80% of specific numbers in the article are present in `brief.findings` OR sourced via a resolving citation. If the judge's ART-5 evidence never flags any unground-able specifics, ART-5 is not cross-referencing the brief and the rubric is silently inflating.

**V7. Cross-platform same-thesis consistency.** Pick one thesis ("KSeF 2.0 enforcement timeline is shorter than firms assume") and produce both blog (2,500 words) and linkedin_article (1,200 words). Expected: ART-2 scores within ±0.5 across both renderings — thesis is the same, only form differs. If ART-2 diverges ≥1, one has a coherence problem the other doesn't.
