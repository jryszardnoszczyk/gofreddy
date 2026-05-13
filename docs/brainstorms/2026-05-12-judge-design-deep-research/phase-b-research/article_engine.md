# article_engine — Phase B calibration corpus

> Lane purpose: long-form articles in two adaptors — **blog** (`articles/blog/<slug>.md`, SEO meta + JSON-LD Article schema + body-image briefs) and **linkedin_article** (`articles/linkedin_article/<slug>.md`, first-200-char hook + LinkedIn paragraph cadence). Consumes findings-briefs from `geo` (Klinika Melitus procedure-page articles, Polish) and `monitoring` (DWF Poland regulatory explainers under named partner bylines, Polish).
>
> Ceiling target (9-tier): the named expert byline reads it and says "this is what I would have written if I had the time." Citation-grade authority (≥2 sources per load-bearing claim, named experts in `"..."`, freshness markers). Voice-pure to corpus. Compliance precondition (judge cannot score above 5 if the regulatory regime hard-blocks).
>
> **Key divergence call-out:** the two adaptors do not share a ceiling. Blog optimises for AI-search citation + organic search traffic on a 60–90 day horizon, evaluated against a fairly mechanical surface (schema, depth, extractability, source density). LinkedIn Article optimises for B2B buyer trust + the engagement formula `(reactions×1 + comments×3 + shares×5) × exp(-days/14)`, evaluated against a much more political surface (named-buyer follows, profile inbound, dwell time). A judge that grades both identically will overfit blog and underfit LinkedIn, or vice versa. The rubric must branch on adaptor.

---

## 1. Top 9-tier signals — what excellent long-form looks like in 2026

### Blog (SEO + AI-citation target)

**B1. One thesis answers one specific question, stated within the first 100 words.**
- *Source:* "The future of SEO is not about ranking higher. It is about becoming the answer" ([Adobe 2026](https://business.adobe.com/uk/blog/seo-in-2026-fundamentals)); decision-makers ask AI to summarise/recommend "often before they ever visit a website" ([MarketingProfs](https://www.marketingprofs.com/articles/2026/54596/ai-search-b2b-content-strategy)).
- *Mechanism:* AI extractors (Perplexity, ChatGPT, Google AI Overviews, Claude) pull one canonical answer per query. Bury the answer and the synthesiser cites a competing page that didn't.
- *Judge-able test:* Does `<h1>` + first paragraph contain a complete declarative answer to the brief's SEO topic? Or "In today's fast-paced world..."?

**B2. ≥2 distinct, named, dated sources per load-bearing factual claim.**
- *Source:* For YMYL, "rigorous fact-checking and source verification" is the minimum entry, not a quality booster ([River Editor 2026](https://rivereditor.com/blogs/write-health-articles-pass-strict-2026-google-medic-update)); for AI citation, "content depth and readability matter most" while "traditional SEO metrics like traffic and backlinks have little impact" ([LLMrefs](https://llmrefs.com/generative-engine-optimization)).
- *Mechanism:* AI engines triangulate before citing. Single-source claims read as opinion and get filtered out. Two named sources is the minimum that survives the synthesiser's confidence threshold.
- *Judge-able test:* For each numeric claim, brand name, regulatory date, or clinical figure, ≥2 named sources reachable via in-text link or footnote. Ground-truthable from the rendered link graph.

**B3. JSON-LD `Article` schema with `author.@type=Person`, dated `datePublished` + `dateModified`, named `medicalSpecialty` or `legalArea`.**
- *Source:* Schema is the machine-readable E-E-A-T signal across all 2026 YMYL guides ([Healthus](https://healthus.ai/eeat-seo-healthcare-content/), [Koanthic](https://koanthic.com/en/ymyl-content-guidelines-complete-guide-for-2026/), [SEL YMYL](https://searchengineland.com/guide/ymyl)).
- *Mechanism:* Crawlers (Google, GPTBot, ClaudeBot, PerplexityBot) parse schema before NLP. A `Physician`/`Lawyer`-typed `Person` author with specialty bypasses the NLP "who is qualified" guess.
- *Judge-able test:* Emitted `.md` frontmatter compiles to valid JSON-LD with all five fields. `author.@id` matches the persona's `@id` in the byline registry.

**B4. Skimmable hierarchy — H2 every ~300 words, one H3 question per section that an AI engine could extract verbatim.**
- *Source:* "Clear heading hierarchies with one topic per section" ([Grafit](https://www.grafit.agency/blog/the-llm-seo-guide-how-to-optimize-a-b2b-website-for-ai-search-in-2026)); answer "why, when, how, and what" because AI relies on "context and relationships between concepts" ([SEL GEO](https://searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142)).
- *Mechanism:* AI engines chunk on H2/H3 boundaries. A 2,000-word article with 6–7 well-formed H2s gets 6–7 citation slots; the same content as wall-of-text gets 1.
- *Judge-able test:* Words-per-H2 in [200, 400]. Each H3 phraseable as a search query.

**B5. Named-expert quotation in `"..."` with attribution + credential + date.**
- *Source:* AI "rewards" "original insights, lived experience, and nuanced opinions" because they're hard to replicate ([Typeface](https://www.typeface.ai/blog/content-marketing-statistics)); "Information Gain" from named SMEs ([Reachlane](https://www.reachlane.com/ai-search-for-b2b-how-companies-stay-visible/)).
- *Mechanism:* Verbatim quotes from credentialed humans are the unit-of-citation AI engines preferentially attribute. A paraphrased claim loses source; a direct quote keeps your URL.
- *Judge-able test:* ≥1 verbatim quote per 800 words, each ≥15 words, each followed by `— [Name], [Credential], [Date or Org]`.

### LinkedIn Article (B2B engagement + named-buyer trust target)

**L1. First 200 characters carry a specific, falsifiable, counter-intuitive claim.**
- *Source:* Lenny's Eric Ries summary opens "There's a force that pulls organisations toward mediocrity and corruption — 'the force no one controls but everyone obeys.'" — 4,151 likes / 490K views on a quote that *is* the hook ([tweet](https://x.com/lennysan/status/2053965154845634615)). LinkedIn 2026 penalises engagement-bait openers ~60% and rewards dwell ([digitalapplied](https://www.digitalapplied.com/blog/linkedin-algorithm-2026-engagement-strategy-guide), [socialboostdigital](https://www.socialboostdigital.com/blog/linkedin-dwell-time-factor-2026)).
- *Mechanism:* LinkedIn collapses Articles after ~3 lines on mobile. The visible portion must earn the "see more" tap and keep the reader. Counter-intuitive + falsifiable triggers both comments (controversy) and dwell (need to confirm it).
- *Judge-able test:* Strip everything after char 200. Specific number, named entity, or contrarian claim? Or throat-clear ("In this article we'll explore...")?

**L2. Numbered, scannable structure with one tactical takeaway per section.**
- *Source:* Same Lenny/Ries tweet — 8 numbered takeaways, each with specific number + named example (Cloudflare, Anthropic, Vectura/Philip Morris) + actionable verb. LinkedIn document/PDF posts lead engagement at ~6.60% ([dataslayer](https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now)) because they're inherently numbered.
- *Mechanism:* B2B users bookmark numbered lists to send to their team. Bookmarks weight higher than likes in the 2026 dwell-time formula.
- *Judge-able test:* Numbered structure (1./2./3. or equivalent markers) visible in first screen. Each item compresses to one tweet.

**L3. Named-buyer-resonant case examples (companies the reader recognises).**
- *Source:* Eric Ries cites Anthropic/Cloudflare/Patagonia/Costco/Vectura — names a Series B+ founder verifies on sight. Lenny's Anthropic org-chart tweet (4,151 likes, [tweet](https://x.com/lennysan/status/2052439125538873516)) works the same way: every named PM/eng leader is independently verifiable.
- *Mechanism:* B2B buyers follow accounts that keep name-dropping the same orbit the buyer lives in. Each named case is a chance the reader has been in a room with that org.
- *Judge-able test:* ≥3 named orgs per 1,000 words; ≥1 named person per 500 words.

**L4. Paragraph cadence: 1–2 sentence paragraphs, frequent line breaks, hard return between every shift.**
- *Source:* Dwell time is "the algorithm's most powerful behavioural signal" ([dataslayer](https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now)); posts that "hold attention for longer periods receive exponentially greater distribution" ([stackmatix](https://www.stackmatix.com/blog/linkedin-algorithm-how-it-works)).
- *Mechanism:* Long paragraphs on LinkedIn read as walls and get scrolled past. Each line break is a micro-commitment to keep going.
- *Judge-able test:* Average paragraph ≤3 sentences. None >5. Empty lines between every paragraph.

**L5. Closes with a specific question that resolves to comments, not "what do you think?"**
- *Source:* LinkedIn 2026 explicitly penalises "Comment YES if you agree" bait ([digitalapplied](https://www.digitalapplied.com/blog/linkedin-algorithm-2026-engagement-strategy-guide)); Lenny's Tony Fadell prompt — "what would you love to hear from him?" — drew 38 replies on 16K views ([tweet](https://x.com/lennysan/status/2053920807928332573)).
- *Mechanism:* Generic CTAs get suppressed; specific named-process questions pull comments, which weight 3× reactions in the engagement formula.
- *Judge-able test:* Final paragraph = one question referencing a named entity, decision, or timeframe ("What did you do at your last board review?" not "Thoughts?").

### Cross-platform (both)

**X1. Voice fidelity at scale — the byline could have written it.**
- *Source:* Jason Fried's Basecamp 5 long tweet (1,800+ words, May 7 2026) — "I can't stress enough just how incredible it is to work this way... In the 27 years I've been running this company..." ([tweet](https://x.com/jasonfried/status/2052462355137871934)). Unmistakeable Fried: first person, calendrical anchor, low-jargon emphatic, no buzzwords. Test: remove the byline and still know it's him.
- *Mechanism:* A long-form article is 8–15× longer than a tweet → 8–15× more chances to break voice. Breaks come from (a) mid-article slip to LLM register, (b) jargon imported from a source the byline would never use, (c) abstraction-level shift mid-paragraph.
- *Judge-able test:* Cross-reference `voice_persona.corpus_path`. Score lexical overlap of distinctive bigrams, sentence-length distribution, first-person/imperative/declarative ratio across rolling 200-word windows. Flag any window whose voice-distance exceeds threshold.

**X2. Freshness marker tied to a verifiable event in the last 90 days.**
- *Source:* Dwarkesh's David Reich thread — "He and collaborator Ali Akbari just published a paper that overturns a long-standing consensus..." (May 8 2026, 1,962 likes, [tweet](https://x.com/dwarkesh_sp/status/2052798237828960334)). "Just published" + named co-author + date-able event. Without that anchor: >50% engagement loss.
- *Mechanism:* AI engines preferentially cite content with explicit dates (that's how they reason about freshness). LinkedIn surfaces news-tied content in newsletters. Both adaptors reward now-ness.
- *Judge-able test:* Reference to a dated event (regulation effective date, court ruling, study publication, product launch) within 90 days of `datePublished`. Verify against brief's `findings_freshness`.

**X3. Specific named case example within compliance bounds.**
- *Source:* Eric Ries's Vectura/Philip Morris reference — specific company, outcome ("destroying it within three years"), and mechanism (acquisition). For Klinika: "patient X (consented, anonymised)" or a published case series; for DWF: a public administrative ruling.
- *Mechanism:* Generic ("clinics see results in 4–6 weeks") reads as content-farm. Specific ("23 of 27 patients in Q1 2026 reached full clearance by week 8") reads as written-by-the-person-doing-the-work. AI engines extract specifics; humans trust specifics.
- *Judge-able test:* ≥4 concrete numeric-or-named claims per 1,000 words = 9-tier; ≤1 = 1-tier.

---

## 2. Top 5-tier signals — mediocre long-form that ships

- **M1. Topic-correct but thesis-absent.** On-topic, no position. Reads as a Wikipedia summary. Ranks for long-tail keyword but won't be cited by AI engines (no extractable answer) and won't drive LinkedIn engagement (nothing to react to).
- **M2. One source per claim, all generic** (Wikipedia, topic's own homepage, "studies show"). Passes casual fact-check, fails GEO citation triangulation.
- **M3. Generic case examples** — "a major Polish law firm," "one aesthetic clinic in Warsaw." Reads as compliance-cautious *and* as did-not-do-the-work. Misses both the trust signal and the extractable-specifics signal.
- **M4. Adequate H2 structure but no H3 questions.** Skimmable, not extractable. The chunker finds sections; the answer-engine can't find Q&A pairs.
- **M5. Voice "in the neighbourhood" but not exact.** No howling LLM tells; also no unmistakeable byline tics. Reads like an associate wrote it after one coaching session with the partner — polished, voice-flat. Fails the "byline would have written this" test by ~15%.
- **M6. Closes on a generic CTA** ("Book a consultation," "Contact us"). Acceptable on a service page, median on thought-leadership.
- **M7. LinkedIn Article: first 200 chars are a setup, not a hook.** "Last week I was at a conference and someone asked me a question..." — accurate, fails dwell-time because the reader doesn't yet know if the article is worth tapping.

---

## 3. Slop patterns (1-tier)

- **S1. The Three-Pillars opener.** "In today's rapidly evolving [industry] landscape... three key pillars: X, Y, Z." Unmistakeable LLM tell.
- **S2. The "Let's explore..." transition.** "Let's dive deeper..." "Before we get into specifics..." LLM scaffolding that survived editing.
- **S3. Empty Polish calque vocabulary.** Articles machine-translated from English then sprinkled with "innowacyjny," "kompleksowy," "holistyczny," "synergia," "transformacja cyfrowa." Native Polish experts use verb-driven, concrete language.
- **S4. "Key Takeaways" bullets that compress no information.** "Patient safety is paramount." "Compliance is essential." Adjective-form restatements of the topic.
- **S5. The "Conclusion: In conclusion..." section.** Section literally headed "Conclusion" opening with "In conclusion." Schoolbook structure imported by the LLM.
- **S6. Hyperlinks to nothing.** `[study](https://example.com/study)` resolving to homepage, paywall, or 404. AI extractors downweight pages with broken link graphs. Common because LLMs hallucinate plausible-shaped URLs.
- **S7. Body-image briefs describing stock photography.** "Doctor in white coat smiling at patient." 9-tier brief is anatomically/instructively specific ("annotated skin cross-section, microneedle depth indicators at 0.5/1.0/1.5mm").
- **S8. LinkedIn Article that's three blog paragraphs pasted in.** No line breaks, no first-200-char hook, no named cases. Detectable from paragraph-length distribution.

---

## 4. What separates 9-tier from 5-tier (per platform)

**Blog — gap is citation-density × extractability × voice retention through the long middle.**
- Source triangulation. 9-tier ≥2 named sources per claim, ≥1 primary within 24 months. 5-tier 0.5–1 source per claim, most secondary, undated.
- Extractable Q&A structure. 9-tier H3s read as search queries answered in the next 200–400 words. 5-tier H3s are topic labels ("Background," "Considerations") that engines can't extract Q&A from.
- **Voice retention through the long middle is the hardest gap and the biggest.** A 5-tier article opens in voice, drifts to neutral LLM register by paragraph 4 (~600 words in), never recovers. The 9-tier article holds voice across 1,500–2,500 words. **Voice fidelity at long-form scale is harder than at tweet scale because there are 8–15× more sentences to slip in.** The judge needs voice-distance scoring across rolling 200-word windows, not opener/closer-only.

**LinkedIn Article — gap is first-screen hook × named-case density × dwell-time architecture.**
- First 200 chars. 9-tier compresses counter-intuitive specific claim. 5-tier wastes the real estate on setup. With 2026's dwell-time weighting, this matters more than in 2024.
- Named-buyer surface area. 9-tier names 3+ orgs + 1+ person the audience recognises; 5-tier says "a large enterprise" / "one PM I worked with." Named version generates inbound from people who know the entities; generic version generates nothing.
- Cadence + close. 9-tier = sequence of micro-claims with line breaks, specific named-process question at close. 5-tier = 3–4 medium prose paragraphs ending on "Thoughts?" Cadence alone moves engagement 2–3×.

Voice fidelity is a gap on LinkedIn too but narrower than on blog because LinkedIn Articles are shorter (800–1,500 vs 1,500–2,500 words). Drift is bounded by length.

---

## 5. Klinika + DWF specifics

### Klinika Melitus — Polish procedure-page blog article (Dr. Maria byline)

**9-tier shape:**
- **Title** specific cohort + timeframe + mechanism. Not "Mezoterapia w Warszawie" (commodity SEO) but "Mezoterapia igłowa po 40-tce: co realnie zmienia się w skórze w pierwszych 8 tygodniach."
- **Lede** answers the title in 2–3 sentences — what change, in what tissue layer, over what timeframe — and notes when it would *not* work (claim falsifiable + bounded).
- **Author block.** Full credentials (specialisation registered with Naczelna Izba Lekarska, PWZ number, society memberships), photo, link to PWZ register entry. JSON-LD `Person` with `medicalSpecialty: "Dermatology"`.
- **Body.** 5–7 H2s posed as patient questions ("Jak długo utrzymuje się efekt?" / "Jakie są realne przeciwwskazania?"). 200–400 words per H2. H3 questions extractable verbatim.
- **Sources.** ≥2 per claim, one primary (PubMed paper, EMA monograph, Polish Society of Dermatology guideline) + one practitioner perspective. Dated, ≤5 years.
- **Specific case within compliance bounds.** "W naszej praktyce, w grupie 27 pacjentów leczonych w Q1 2026, 23 osoby osiągnęły..." — anonymised, consented, specific. Not "większość pacjentów obserwuje."
- **Body-image brief.** Anatomically specific: "Cross-section diagram of skin with microneedle depth indicators at 0.5/1.0/1.5mm, labeled in Polish: naskórek, skóra właściwa, tkanka podskórna."
- **Close** routes to consultation request with the specific concern named, not generic "umów wizytę."
- **Voice = Dr. Maria's.** First-person clinical ("U moich pacjentek widzę…"), measured, no superlatives, willing to say "tego nie wiemy jeszcze na pewno." Anchors: "obserwuję," "zalecam," "w mojej praktyce."

**Compliance hard-blocks (judge ≤5):** superlative vs other clinics; efficacy claim without bounding; competitor reference or off-label use; missing PWZ-verifiable credential; treatment without contraindications section. Polish Medical Chamber Code of Ethics art. 63–65 binds.

### DWF Poland — Polish regulatory explainer LinkedIn Article (partner byline)

**9-tier shape:**
- **First 200 chars** carry regulatory fact + deadline + cost of missing it. Example: "KSeF 2.0 wchodzi obowiązkowo dla firm >200 mln zł obrotu od 1 lutego 2026 — kary za nieprzesłanie faktury w terminie sięgają 100% kwoty VAT. Trzy rzeczy, które trzeba zrobić przed grudniem, których nikt nie robi." (KSeF dates per [Meridian](https://meridianglobalservices.com/four-new-regulations-finalised-for-e-invoicing-framework-in-poland/), [RTC Suite](https://rtcsuite.com/ksef-2-0-implementation-in-poland-four-regulations-now-define-the-2026-operating-model/), [EDICOM](https://edicomgroup.com/blog/poland-will-make-b2b-electronic-invoicing-mandatory).)
- **Numbered structure**, 5–8 takeaways. Each item: specific fact + named company/regulator + specific action. Mirror the Eric Ries 8-point template ([Lenny tweet](https://x.com/lennysan/status/2053965154845634615)).
- **Named cases.** Polish companies that have implemented (consent or public reporting), MoF regulations by number, named clauses from the four December 2025 executive regulations.
- **Author block.** Named partner, photo, bar number (numer wpisu na listę radców prawnych / adwokatów), DWF Poland affiliation. JSON-LD `Person` with `knowsAbout: ["KSeF", "Polish VAT law", "B2B e-invoicing"]`.
- **Cadence.** ≤3 sentences per paragraph. Line break between claims. Bold on dates + numeric thresholds.
- **Voice = the named partner.** Formal Polish legal register, third-person institutional ("nasza kancelaria obserwuje"), punctuated with 1–2 first-person observations to signal the partner actually wrote it. Avoids "innowacyjne rozwiązanie," "kompleksowa obsługa," "holistyczne podejście" — those are junior-marketing voice, not partner voice.
- **Sources.** ≥2 named regulatory citations per fact: Ustawa or Rozporządzenie by number + date + public commentary (MoF press release, Sejm transcript, ECJ ruling).
- **Close.** Specific named-process question. Not "co Państwo o tym sądzą?" Instead: "Czy Państwa dział księgowości testował już wysyłkę przez API w środowisku przedprodukcyjnym?"

**Compliance hard-blocks (judge ≤5):** unauthorised client-matter disclosure; pending-litigation prediction stated as fact; superlative vs other firms; Ustawa cite without Dz.U. number; missing author bar number.

---

## 6. 2026 emerging signals — what a fresh-built rubric must grade for

- **E1. Long-form AI-search citation pattern.** Per [LLMrefs](https://llmrefs.com/generative-engine-optimization) and [SEL GEO](https://searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142), AI engines preferentially cite deep, specific pages over shallow ones. A 2,500-word piece with 12 sources gets cited; a 500-word service page with 2 gets cited 5× less. Reward depth + source density.
- **E2. LinkedIn 2026 algorithm: dwell time > raw engagement, document/PDF outperform native articles in some windows, external links penalised ~60%** ([digitalapplied](https://www.digitalapplied.com/blog/linkedin-algorithm-2026-engagement-strategy-guide), [dataslayer](https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now)). Reward self-contained articles; penalise external links in first half (final CTA OK); consider PDF/document export as parallel output.
- **E3. Personal profile dominates feed: company pages ~5%, personal ~65%** ([dataslayer](https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now)). LinkedIn Article must be byline-strong (named partner, not "DWF Poland"). Penalise firm-marketing register.
- **E4. YMYL bar risen — E-E-A-T is the floor, not the ceiling** ([River Editor 2026](https://rivereditor.com/blogs/write-health-articles-pass-strict-2026-google-medic-update), [Koanthic 2026](https://koanthic.com/en/ymyl-content-guidelines-complete-guide-for-2026/)). For Klinika: author credential must be schema-machine-verifiable, sources must be primary medical literature, `dateModified` is ranked separately from `datePublished`, patient testimonials flagged as such.
- **E5. Polish-language quality bar above auto-translation.** Polish morphology and clause structure that machine translators flatten. Native readers (and Polish-language engines like Bielik) detect translated-from-English text within 2 paragraphs. Grade Polish syntactic naturalness, not just "Polish words present": penalise calque vocabulary; reward verb-driven structure; penalise nominal-style ("przeprowadzenie analizy" vs "analizujemy").
- **E6. Compliance-as-precondition replaces compliance-as-checklist.** 2026 enforcement is shifting from "did you put a disclaimer" to "did the article materially mislead." Rubric needs a hard-block gate (judge ≤5 if violated), not a deductible point.

---

## 7. Implications for the judge — 8 candidate criteria

Each criterion below ties to a 9-tier signal from §1, has 1/3/5 anchors in plain prose, suggested tier, and a ground-truth verification hook where applicable.

### C1. Thesis specificity (essential) — anchors B1, L1
*Does the article open with a single specific falsifiable answer to the brief's topic question?*
- **1:** Buries the answer past the first 100 words ("In today's…" / "As organisations navigate…").
- **3:** On-topic, competent setup, answer deferred to §2 or §3.
- **5:** First 100 words contain a complete specific falsifiable answer. A reader who stops there has the answer.
- *Ground truth:* compare lede against brief's `topic_question` field; LLM extractor for answer-completeness.

### C2. Source triangulation (essential) — anchors B2, X2
*Source density + primary/secondary mix per load-bearing claim.*
- **1:** Claims unsupported, or hyperlinks-to-homepages, or single secondary sources.
- **3:** ≥1 source per claim, mostly secondary, dated within 5 years.
- **5:** ≥2 named sources per claim with ≥1 primary (study, register, official doc) within 24 months. All hyperlinks resolve.
- *Ground truth:* parse link graph, HEAD-check each URL, cross-reference dates against `findings_freshness`. 404/login-redirects auto-deduct.

### C3. Extractable structure (essential, blog-weighted) — anchors B4
*H2/H3 hierarchy for AI-engine extractability.*
- **1:** Wall of text or H2-only with topic-label headings ("Background," "Considerations").
- **3:** H2+H3 present but H3s are topic labels not extractable questions.
- **5:** Each H2 owns a sub-thesis; each H3 phraseable as a search query the next 200–400 words answer.
- *Ground truth:* markdown AST parse; classify H3s as question-shaped via `?` or interrogative regex; words-per-H2 in [200, 400].

### C4. Voice fidelity at long-form scale (essential) — anchors X1
*Could the named byline have written it — measured across rolling 200-word windows?*
- **1:** LLM register throughout, or opens in voice and drifts to LLM register by paragraph 4 (~600 words) and never returns.
- **3:** Opener + closer in voice; middle 60% drifts to neutral. Corpus lexical overlap ≥30% but <60%.
- **5:** Voice-distance to corpus stays within threshold across every 200-word window. Distinctive lexical/syntactic patterns (first-person frequency, sentence-length distribution, signature phrases) match corpus.
- *Ground truth:* cross-reference `voice_persona.corpus_path`; rolling-window voice-distance; surface threshold-exceeding windows for human review.

### C5. Named-case density (important, LinkedIn-weighted, applies to both) — anchors B5, L3, X3
*Specific named orgs, people, and concrete numeric claims per 1,000 words.*
- **1:** Zero named cases; generic placeholders ("a major client").
- **3:** 1–2 named orgs per 1,000 words; cases industry-generic.
- **5:** ≥3 named orgs + ≥1 named person per 500 words; cases named, dated, specific, compliance-bounded.
- *Ground truth:* NER pass; cross-reference compliance allowlist (no client-matter disclosure for DWF; consented anonymisation for Klinika); reject on compliance fail.

### C6. Platform-adaptor fit (essential, branches on adaptor) — anchors B3, L1, L2, L4, L5

**Blog:**
- **1:** Missing JSON-LD; missing `dateModified`; missing schema-machine-readable author credential.
- **3:** JSON-LD minimal; author in body only, not schema.
- **5:** Full `Article` schema with `Person` author typed `Physician`/`Lawyer`; both `datePublished` + `dateModified` fresh; `medicalSpecialty`/`legalArea` populated; body-image briefs instructive (not stock-photo descriptors).

**LinkedIn:**
- **1:** First 200 chars are setup; paragraphs avg >5 sentences; no numbered structure; generic CTA close.
- **3:** Soft hook; mixed cadence; non-specific question close.
- **5:** First 200 chars = counter-intuitive specific claim; numbered structure visible first screen; paragraphs avg ≤3 sentences; close = specific named-process question.
- *Ground truth:* JSON-LD validator (blog); char-count + paragraph-length distribution + question-detection regex (LinkedIn).

### C7. Polish-language naturalness (important when `brief.lang == "pl"`) — anchors E5
*Reads as native Polish or as machine-translated?*
- **1:** Multiple calque words per paragraph (innowacyjny, kompleksowy, holistyczny, synergia, transformacja cyfrowa); nominal-style dominates; English rhythm in Polish vocabulary.
- **3:** Competent non-specialist Polish; some calque; rhythm acceptable.
- **5:** Native expert Polish in domain; verb-driven; idiomatic constructions; <1 calque per 500 words.
- *Ground truth:* per-lane calque-word frequency list; nominal-vs-verbal sentence-style ratio; native-Polish bigram model on legal/medical corpora.

### C8. Compliance precondition (hard ceiling — judge ≤5 if violated) — anchors §5, E6
*Hard-block, not deduction.*
- **1:** Violates compliance (unauthorised disclosure, superlative comparison, off-label claim, missing required credential).
- **3:** Meets compliance but over-cautious (no specifics where compliance permits them — collapses to 5-tier mediocrity).
- **5:** Meets compliance AND uses full permitted latitude (specific anonymised Klinika cases, specific public DWF regulatory citations). Compliance *enables* specificity within bounds, not *erases* it.
- *Ground truth:* per-lane compliance rule registry (PWZ verifiable for Klinika; bar number for DWF; no client-matter disclosure; no superlative comparison; no off-label efficacy; no pending-litigation prediction). **Any rule failure caps score at 5 regardless of C1–C7.**

---

## Summary table of criteria

| # | Name | Tier | Adaptor weighting | Ground truth |
|---|---|---|---|---|
| C1 | Thesis specificity | essential | both | brief.topic_question vs lede |
| C2 | Source triangulation | essential | both | link-graph + HEAD checks |
| C3 | Extractable structure | essential | blog-weighted | markdown AST |
| C4 | Voice fidelity at long-form scale | essential | both | corpus rolling-window distance |
| C5 | Named-case density | important | LinkedIn-weighted | NER + compliance allowlist |
| C6 | Platform-adaptor fit | essential | branches on adaptor | JSON-LD validator (blog); para/hook detector (LinkedIn) |
| C7 | Polish-language naturalness | important when pl | both | calque-list + style-ratio + native bigrams |
| C8 | Compliance precondition | pitfall (caps at 5) | both | per-lane rule registry |

**Weighting:** C1/C2/C4 weight equal across adaptors. C3 weights heavier for blog. C5/C6 weight heavier for LinkedIn. C7 fires only when `brief.lang == "pl"`. C8 hard-caps regardless.

**Why C4 (voice fidelity) is non-negotiable:** per §4, mid-article drift is what most separates 5-tier from 9-tier on blog. Opener/closer-only checking misses it systematically. Rolling-window distance is the only test that catches a writer in voice for the first 600 words and LLM-register for the next 1,500.

**Why C8 is a precondition not a deduction:** compliance violations in medical/legal regimes are categorical, not gradient. An article that misleads on dosage isn't "mostly good with one gap" — it's not shippable. The score must reflect that.

---

## Sources

- [MarketingProfs — Redefining B2B Content Strategy for AI Search](https://www.marketingprofs.com/articles/2026/54596/ai-search-b2b-content-strategy)
- [Adobe Business — SEO in 2026](https://business.adobe.com/uk/blog/seo-in-2026-fundamentals)
- [LLMrefs — Generative Engine Optimization 2026 Guide](https://llmrefs.com/generative-engine-optimization)
- [Search Engine Land — Mastering GEO in 2026](https://searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142)
- [Grafit Agency — LLM SEO Guide for B2B 2026](https://www.grafit.agency/blog/the-llm-seo-guide-how-to-optimize-a-b2b-website-for-ai-search-in-2026)
- [Reachlane — AI Search for B2B 2026](https://www.reachlane.com/ai-search-for-b2b-how-companies-stay-visible/)
- [Typeface — Content Marketing Statistics 2026](https://www.typeface.ai/blog/content-marketing-statistics)
- [Varn — Gated Content + AI Search 2026](https://varn.co.uk/insights/gated-content-ai-search-strategy-2026/)
- [Digital Applied — LinkedIn Algorithm 2026 Engagement Guide](https://www.digitalapplied.com/blog/linkedin-algorithm-2026-engagement-strategy-guide)
- [Dataslayer — LinkedIn Algorithm Feb 2026](https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now)
- [SocialBoost Digital — LinkedIn Dwell Time Factor 2026](https://www.socialboostdigital.com/blog/linkedin-dwell-time-factor-2026)
- [Stackmatix — LinkedIn Algorithm Data-Driven Breakdown 2026](https://www.stackmatix.com/blog/linkedin-algorithm-how-it-works)
- [River Editor — 2026 Google Medic Update Guide](https://rivereditor.com/blogs/write-health-articles-pass-strict-2026-google-medic-update)
- [Koanthic — YMYL Content Guidelines 2026](https://koanthic.com/en/ymyl-content-guidelines-complete-guide-for-2026/)
- [Healthus AI — Healthcare E-E-A-T SEO](https://healthus.ai/eeat-seo-healthcare-content/)
- [Search Engine Land — YMYL Guide](https://searchengineland.com/guide/ymyl)
- [Meridian — KSeF Four Regulations](https://meridianglobalservices.com/four-new-regulations-finalised-for-e-invoicing-framework-in-poland/)
- [RTC Suite — KSeF 2.0 Four Regulations](https://rtcsuite.com/ksef-2-0-implementation-in-poland-four-regulations-now-define-the-2026-operating-model/)
- [EDICOM — Poland Mandatory B2B E-Invoicing](https://edicomgroup.com/blog/poland-will-make-b2b-electronic-invoicing-mandatory)
- [Papers Guru — Structuring Long Papers Coherence](https://papers.guru/2025/11/10/structuring-long-papers-managing-coherence-across-sections/)
- Tweets (verbatim quotation):
  - [Jason Fried — Basecamp 5 long tweet (May 7 2026)](https://x.com/jasonfried/status/2052462355137871934)
  - [Lenny Rachitsky — Eric Ries 8 takeaways (May 11 2026)](https://x.com/lennysan/status/2053965154845634615)
  - [Lenny Rachitsky — Anthropic org chart (May 7 2026)](https://x.com/lennysan/status/2052439125538873516)
  - [Lenny Rachitsky — Tony Fadell question prompt (May 11 2026)](https://x.com/lennysan/status/2053920807928332573)
  - [Dwarkesh Patel — David Reich + Ali Akbari paper (May 8 2026)](https://x.com/dwarkesh_sp/status/2052798237828960334)
