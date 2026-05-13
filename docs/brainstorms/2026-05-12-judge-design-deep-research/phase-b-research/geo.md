# Phase B research — `geo` lane

Calibration corpus for the GEO judge. Anchors what 9-tier looks like for a procedure page (Klinika Melitus `/zabiegi/botoks`) in May 2026 against expert consensus, recent large-N studies, and AI-engine grounding behaviour. Goal: judge can score variants against the 2026 citation ceiling, not a generic SEO checklist.

Existing rubric: GEO-1 self-contained quotable answers, GEO-2 verifiable facts, GEO-3 honest competitive positioning, GEO-4 voice/structure fit, GEO-5 citability moat, GEO-6 cross-page coherence, GEO-7 directly answers target queries, GEO-8 technical fixes are real.

## 1. Top 9-tier signals

Each signal: what excellence looks like, source with engagement weight, mechanism, judge test. Graded on the artifact, not on 60–90-day citation outcomes.

### 1.1 Quoted-expert attribution in `"..."` form (name + credential + date)
- **Description:** ≥1 passage where a named expert is quoted verbatim inside quotation marks, attributed by role/credential, dated. Bar: `Dr Anna Kowalska, dermatolog (12 lat stażu), mówi: "Botoks działa średnio 3,4 miesiąca, u 18% pacjentów dłużej niż 5 miesięcy (N=1,247, 2025)" (rozmowa, marzec 2026).`
- **Source:** Prior audit KDD 2024 +41% citation lift. Reinforced by Zyppy's 2026 23-factor study: pages with ≥1 named-source citation are **cited 2.1× more** — `https://signal.zyppy.com/p/ai-citation-ranking-factors`. Aleyda 2026-05-07 (48 likes, 24 bookmarks) retweeting Bing's grounding-index team naming "Factual fidelity, Source attribution quality" as new index-level signals — `https://x.com/aleyda/status/2052300571730714922`.
- **Mechanism:** Quotation marks + proper-noun anchor in the same chunk = a high-confidence "pass-through quote" signal for RAG. Without quotes, the same words look like editorial assertion; the model paraphrases or skips.
- **Judge test:** ≥1 quoted span ≥15 words, attributed to a named individual with role/credential, dated within 18 months. Penalize "experts say"/"studies show" without a name.

### 1.2 Inline citation density to primary sources at the claim
- **Description:** Every quantitative claim hyperlinked to its primary source (peer-reviewed paper, registry, manufacturer datasheet, regulator) at the sentence, not bunched at the bottom. Bar: ≥1 inline citation per 150 words, ≥60% external-primary.
- **Source:** Prior audit KDD 2024 +30%. Aleyda's 2026 e-commerce subvertical study (15 likes, 9 bookmarks, `https://x.com/aleyda/status/2054213512071667740`) — Pattern 3: "the source mix changes according to the evidence AI systems need." Mike King 2026-05-08 700K-page Profound study (`https://x.com/iPullRank/status/2052811818075378089`) — "Visibility isn't possible without eligibility."
- **Mechanism:** AI engines reweight chunks by source-link entropy. Links to UpToDate/ClinicalTrials.gov/EMA/MedDRA raise the page's verifiability score. Pages with no links or only self-links collapse to "marketing copy" in the rerank.
- **Judge test:** count `<a href>` inside `<p>` wrapping a numeric/factual claim; compute ratio. Bar for 9: ≥0.6 with ≥60% external-primary domains.

### 1.3 Answer-first lede in ≤60 words
- **Description:** Opening paragraph (before any subheading) is a direct, complete answer to the page's primary query. For `/zabiegi/botoks` against "ile kosztuje botoks w Warszawie": `Botoks w Warszawie kosztuje 800–1500 zł za jedną strefę. W Klinice Melitus zabieg wykonują certyfikowani lekarze; cena obejmuje konsultację i kontrolę po 14 dniach.`
- **Source:** Search Engine Land 2026 GEO guide + Frase, "Lead with Direct Answers: AI engines frequently extract these opening sentences for citations" — `https://searchengineland.com/what-is-generative-engine-optimization-geo-444418`. Wellows 2026 ChatGPT study: answer-first formatting gets cited 40% more — `https://wellows.com/blog/how-to-rank-in-chatgpt/`. Ekamoira/iPullRank 2026: ChatGPT 5.2 now generates "longer-tail queries and performs minimal fan-outs."
- **Mechanism:** Fan-out narrowing collapses the retrieval window: the first extractable chunk that fully answers the rewritten query wins. Pages that bury the answer below "Wprowadzenie" lose to competitors' ledes.
- **Judge test:** lede contains (a) primary query keyword, (b) numeric anchor (zł/%/min/mg), (c) a complete clause quotable as a standalone answer. All three required for 9.

### 1.4 Query fan-out coverage matrix
- **Description:** Explicit declared fan-out set (≥10 sibling queries for `botoks`: cena, przeciwwskazania, skutki uboczne, czas trwania efektu, ból, lekarz, alternatywy, ciąża, opinie, przed/po, regeneracja, powikłania). Each gets its own H2/H3 with answer-first paragraph. Not buried in FAQ schema only.
- **Source:** iPullRank's Qforia + AI Search Manual — `https://ipullrank.com/ai-search-manual/query-fan-out`. Ekamoira 2026 (`https://www.ekamoira.com/blog/query-fan-out-original-research-on-how-ai-search-multiplies-every-query-and-why-most-brands-are-invisible`): 1,000 KW Planner searches = potentially 15,600 retrieval events at AI Mode. Aleyda 2026-05-10 SEOFOMO references "ChatGPT query fanout top-10 words" study — `https://x.com/aleyda/status/2053571002756477425`.
- **Mechanism:** AI Mode/Perplexity decompose head queries into 8–12 sub-queries; pages covering 3/12 sub-questions are eligible on 3/12, not 12/12. Coverage compounds the citation surface.
- **Judge test:** count H2/H3 sections mapping to documented fan-out nodes, each ≥120 words with answer-first lead. Bar for 9: ≥10 distinct fan-out sections.

### 1.5 Freshness coherence — visible date + dated facts + matching schema
- **Description:** `Zaktualizowano: 10 maja 2026` near the title (not just JSON-LD), body statistics carry data dates (`stan na marzec 2026`), `dateModified` matches visible date ±1 day.
- **Source:** Bing grounding-index team (via Aleyda 2026-05-07, 48 likes): freshness is one of five things the grounding index measures differently. Authority Tech 2026 Perplexity: "content published within last 30 days receives citations at 82% rate." Aleyda 2026-05-08 (`https://x.com/aleyda/status/2052643508196950159`) explicit warning against gaming `dateModified` without real refresh.
- **Mechanism:** Perplexity L3 XGBoost weights recency; ChatGPT Search prefers fresher chunks for pricing/regulation/clinical queries. Stated date contradicting body data dates triggers "stale dressed as fresh" detection and demotion.
- **Judge test:** (a) visible `Zaktualizowano:` within 90 days, (b) ≥3 dated facts in body, (c) JSON-LD `dateModified` matches visible date. All three for 9.

### 1.6 Attribute-rich schema, not generic Article/Service
- **Description:** Strictest applicable type with full attribute coverage. For procedure pages: `MedicalProcedure` with `procedureType`, `bodyLocation`, `preparation`, `followup`, `howPerformed`, `contraindication`, `cost` as `MonetaryAmount`, nested `Physician` entities with `medicalSpecialty`, `affiliation`, `identifier` (PWZ/ORCID).
- **Source:** Prior audit Ahrefs 1885-page cohort: generic schema = 0 lift, attribute-rich = +61.7% — `https://www.searchenginejournal.com/schema-markup-didnt-move-ai-citations-in-ahrefs-test/574568/`. Counter: 50 B2B/ecom domains with FAQPage schema saw 22% median lift. Nature Communications via foglift: GPT-4 fact extraction 16% → 54% with structured fields. Stackmatix 2026: 3+ schema types = 13% more likely to be cited.
- **Mechanism:** Generic schema is noise — every page has it. Attribute-rich schema with `sameAs` (Wikidata/ORCID/PWZ) gives the grounding index discriminating signal at index time, even though SearchVIU showed AI fetchers ignore JSON-LD at retrieval time.
- **Judge test:** ≥2 typed entities, ≥6 populated attributes each, ≥1 external `sameAs` identifier, `cost` as `MonetaryAmount` not free text.

### 1.7 Chunk extractability — 120–180 word self-contained sections
- **Description:** Every H2/H3 section is self-contained. Paragraphs 2–4 sentences. No "as discussed above"/"see section X". First sentence is the answer; rest is evidence.
- **Source:** Frase/SEL 2026: "Passages that retain meaning when read in isolation are more likely to be retrieved and used accurately... 'as mentioned above' tends to lose clarity when extracted." Wellows: pages with 120–180 words between headings get 70% more ChatGPT citations than sections under 50 words. Authority Tech 2026 Perplexity: listicles get highest citation share at 21.9%.
- **Mechanism:** Vector retrieval operates on 256–512-token chunks; the boundary almost always falls at an H2. Chunks referencing "the above" lose context and the rerank penalises ambiguity. Under 50 words = insufficient signal density.
- **Judge test:** ≥80% of H2/H3 sections pass (a) 80–250 words, (b) no anaphoric back-references, (c) first sentence is a standalone answer.

### 1.8 Citability moat — proprietary numbers no competitor can replicate
- **Description:** ≥1 quantitative claim only this clinic could publish — internal patient-outcome data, retention rates, complication frequency from own register, average effect duration measured in own follow-ups. With N and date window.
- **Source:** Existing GEO-5. Cyrus Shepard 2026-04-22 (`https://x.com/CyrusShepard/status/2047044462774563300`, 356 likes, 368 bookmarks) on Danny Sullivan's "Non-Commodity Content" slide; 5 characteristics of winning sites include "Proprietary Assets — Spearman 0.357." Cyrus 2026-04-21 "17 Content Types to Survive Google's Zero-Click Future" — proprietary research, original data, named-source quotes explicitly listed (`https://x.com/CyrusShepard/status/2046629661233553483`, 127 likes, 160 bookmarks).
- **Mechanism:** When AI synthesises an answer from N sources, the chunk with a number no other source has is the chunk that gets quoted. Commodity content collapses to industry averages (UpToDate, NHS); proprietary data cannot be substituted.
- **Judge test:** ≥2 distinct quantitative claims attributed to the clinic's own data, each with N or ≥3-decimal precision and date range.

### 1.9 Honest competitive comparison with explicit losses
- **Description:** Comparison naming ≥2 specific competitors with ≥1 conceded loss each. Bar: `Klinika Aestetic ma niższą cenę za podstawowy zabieg (od 450 zł), my za to obejmujemy kontrolę po 14 dniach i mamy dwóch lekarzy z certyfikatem Allergan Faculty.`
- **Source:** Existing GEO-3. Aleyda's 2026 e-commerce study Pattern 6: "Even category-leading retailers hold a minority share of citations about themselves" — `https://x.com/aleyda/status/2054213512071667740`. Aleyda 2026-05-08: AI engines reward "corroboration" — agreement with what independent sources say, including weaknesses.
- **Mechanism:** AI engines triangulate. Three sources saying competitor X is cheaper + your denial = downrank for factual inconsistency. Conceding the cheaper price and explaining the value differential makes you the "balanced" source the LLM prefers on comparison queries.
- **Judge test:** ≥2 specific named competitors (not "inne kliniki"), ≥1 explicit concession per competitor with a price/duration/method anchor.

### 1.10 Multi-modal anchors — alt-text + comparison table
- **Description:** ≥1 explanatory image with alt-text that is itself an extractable answer (not "botoks-warszawa.jpg"); ≥1 comparison table with semantic `<th>` headers and ≥3 rows.
- **Source:** Wellows 2026: multi-modal content integration = +156% selection rate. YouTube is now #1 cited domain in AI Overviews, +34% in 6 months — `https://wellows.com/blog/google-ai-overviews-ranking-factors/`. Mike King 2026-05-09 (`https://x.com/iPullRank/status/2053095345039532038`): "Markdown is hitting its limits... HTML as the new default output format (tables, SVG, diagrams)." Aleyda 2026-05-06 on Google AI Mode updates (87 likes, 61 bookmarks): more UGC, more inline link previews — `https://x.com/aleyda/status/2052079983762276425`.
- **Mechanism:** Comparison tables extract as tables (preserved in answers). Alt-text becomes a retrievable chunk. Tables differentiate from prose-only competitors.
- **Judge test:** ≥1 `<img>` with alt-text ≥10 words containing a fact, ≥1 `<table>` with `<th>` headers and ≥3 rows of comparison data.

### 1.11 URL accessibility / crawl eligibility for AI agents
- **Description:** Page returns 200 to GPTBot, PerplexityBot, ClaudeBot, Google-Extended, Bingbot. `robots.txt` permits. No Cloudflare challenge. TTFB ≤500ms.
- **Source:** **Zyppy 2026: URL accessibility (9.5) is the single top factor of 23** — `https://signal.zyppy.com/p/ai-citation-ranking-factors`. Mike King 2026-05-08: "Slow pages may never be eligible for AI citations"; 700K-page Profound study on the undocumented status code making content invisible to ChatGPT/Perplexity (`https://x.com/iPullRank/status/2052811818075378089`, 27 likes, 33 bookmarks).
- **Mechanism:** Before content-quality signals matter, the crawler has to fetch within the budget. Cloudflare's default verified-bot challenge blocks many AI fetchers. Slow TTFB times out the agent; the page never enters the candidate pool.
- **Judge test:** `robots.txt` permits AI agents, 200 response on a `User-Agent: GPTBot` probe, TTFB ≤500ms documented in artifact's audit.

### 1.12 Entity identifiers — `sameAs` to authoritative graphs
- **Description:** Named entities (clinic, doctors, conditions, drugs) carry explicit IDs: Wikidata QID for the clinic, ORCID + PWZ for doctors, ChEMBL/DrugBank for drugs, ICD-10 + SNOMED for conditions. JSON-LD `sameAs` for each.
- **Source:** Wellows 2026: 15+ connected entities = 4.8× boost. Authority Tech 2026: Perplexity's L3 XGBoost quality gate filters sources without entity clarity.
- **Mechanism:** AI engines build answers on entities, not strings. Linked entities resolve to single graph nodes; ambiguous strings are dropped by the L3 rerank.
- **Judge test:** ≥4 entities with ≥1 external authoritative identifier each.

## 2. Top 5-tier signals — mediocrity that ships but doesn't get cited

What median Polish-market `/zabiegi/botoks` content looks like. Publishable, indexable, gets organic traffic. Not extracted.

### 2.1 Generic answer-first lede with zero numbers
"Botoks to popularny zabieg medycyny estetycznej, który skutecznie redukuje zmarszczki. Nasi doświadczeni lekarze gwarantują bezpieczeństwo." Hits answer-first structurally, ~95% vector-similar to 500 other clinic intros. **Bar to fail:** no number, no named individual, no source.

### 2.2 Self-published FAQ without quoted experts
"Czy botoks jest bezpieczny? Tak, gdy wykonywany przez certyfikowanego lekarza." Cyrus Shepard 2026-05-09 (169 likes, 77 bookmarks): "LEAVE THE CONTENT IF IT'S HELPFUL. Consider answering additional questions" — the shift is from FAQ schema to actually-helpful Q&A. Templated FAQ that adds no information is 5-tier. **Bar to fail:** FAQ answers <30 words AND no inline citation AND no quoted expert.

### 2.3 Generic JSON-LD Service/Article with required-only attributes
`{"@type":"Service","name":"Botoks","provider":"Klinika Melitus"}` — valid, parseable, useless. Ahrefs 1885-page cohort: 0 citation lift. **Bar to fail:** schema validates but <3 typed entities or <4 attributes per entity.

### 2.4 Single-citation pattern — links only to own domain
~80% of inline links point to other pages on the same domain. Internally well-linked, signals "closed garden" to grounders that can't triangulate. **Bar to fail:** external-link-to-total-link ratio <0.2.

### 2.5 Fan-out coverage stuck at 3–4 sub-questions
H2s for "Co to", "Jak wygląda zabieg", "Cena", "Przeciwwskazania" — misses regeneracja, alternatywy, opinie, ciąża, powikłania, porównanie, kontrola. Eligible for retrieval on 3/12, citation ceiling ~30% of addressable surface. **Bar to fail:** distinct fan-out sections ≤6 against a 10–12-node fan-out tree.

### 2.6 Ornamental freshness — `dateModified` only
CMS bumps `dateModified` nightly, no visible date, body content last edited 18 months ago. Aleyda 2026-05-08 explicit warning against this exact tactic. **Bar to fail:** no visible "Zaktualizowano:" OR body data dates >12 months.

## 3. Slop patterns — 1-tier explicit failures

### 3.1 Pure marketing copy with zero verifiable claims
"Nasz zespół najlepszych specjalistów dba o Twój komfort." No numbers, names, sources. Fails GEO-1, GEO-2, GEO-5 simultaneously.

### 3.2 LLM-written hedge content
"Botoks może być skuteczny u niektórych pacjentów. Wyniki mogą się różnić." Structurally fluent, factually vacuous. AI engines down-rank high-hedging-density content because it adds no information to the synthesis.

### 3.3 Keyword-stuffed alt-text and headings
`<img alt="botoks warszawa cena tani najlepszy lekarz">`. Triggers spam-pattern detection in grounder retrieval; the page drops out of the candidate pool entirely.

### 3.4 Comparisons against unnamed "inne kliniki"
"Klinika Melitus 100% | Inne kliniki 60%." Fabricated comparisons trip authenticity heuristics. Aleyda 2026-05-08: "Buying domains... artificially inflate perceived popularity... systems eventually catch up."

### 3.5 Schema-content mismatch
JSON-LD says `cost: 600 zł`, page says `od 1500 zł`. Triggers Google's structured-data inconsistency penalty AND Perplexity's L3 entity-clarity gate. Silently excluded from retrieval.

## 4. What separates 9-tier from 5-tier

**Numbers attached to identities vs floating free.** Biggest single gap. 5-tier: "botoks działa około 3–4 miesięcy" — true, generic, unciteable. 9-tier: `Dr Anna Kowalska, dermatolog, marzec 2026: "Botoks działa średnio 3,4 miesiąca u 82% naszych pacjentów (obserwacja N=1,247, 2025)."` Same fact, pinned to a named individual with credentials, date, and N. Zyppy 2.1× citation lift on named-source citation measures exactly this. Floating numbers compress to "industry average" and the model picks the aggregator over the clinic.

**Fan-out coverage breadth as a citation-surface multiplier.** 5-tier optimises for the head query, answers 3 sub-questions. 9-tier treats the head query as a 10–12-node tree, each node with a self-contained section. Not "long content" — structured breadth. Ekamoira: 1,000 Keyword Planner searches = 15,600 retrieval events at AI Mode. 5-tier captures ~4,000; 9-tier captures ~13,000. After ChatGPT 5.2's narrowing, generic "side effects" coverage loses to specifically titled "ile trwa siniak po botoksie." The judge needs to grade against a declared fan-out matrix, not against "is this comprehensive."

**Verifiable freshness vs ornamental freshness.** 5-tier bumps `dateModified` nightly. 9-tier aligns visible "Zaktualizowano: 10 maja 2026" + body "cennik aktualny na maj 2026" + regulator "URPL 2026-Q1" + matching schema. Bing's grounding team names "Contradictions / conflict" as a new index signal — dates that contradict body content are now actively detected.

**Honest competitive framing as citation magnet.** Counterintuitive and the most-missed gap on Polish clinic pages. 5-tier asserts category leadership. 9-tier concedes: "Klinika Aestetic tańsza (450 zł), Klinika La Perla większy zespół. My: dwóch lekarzy Allergan Faculty + kontrola po 14 dniach." Aleyda Pattern 6: even category leaders hold a minority share of citations about themselves. The AI engine will cite a competitor in answers about you regardless; pre-empting the framing is what gets quoted on comparison queries.

**Attribute-rich entity graph vs validating schema.** Most important calibration of 2026: Ahrefs 1885-page null result on generic schema vs +61.7% on attribute-rich. 5-tier mistake = treating GEO-8 as "is there valid JSON-LD?" 9-tier = treating schema as Knowledge-Graph contribution with `MedicalProcedure`+`Physician`+`MedicalCondition`, ICD-10/SNOMED for conditions, ORCID/PWZ for doctors, `cost` as `MonetaryAmount`, `sameAs` to Wikidata. SearchVIU's "AI fetchers don't read JSON-LD at retrieval time" is not a counter — schema feeds the indexer layer (Knowledge Graph, Bing grounding) that decides which pages enter the candidate pool.

## 5. 2026 emerging signals not in the current rubric

**Crawl eligibility as hard prerequisite.** Mike King's 700K-page Profound study: an undocumented status code makes content invisible to ChatGPT/Perplexity. Cloudflare's verified-bot challenge blocks AI fetchers. Current GEO-8 doesn't grade fetchability by `GPTBot`/`PerplexityBot`/`ClaudeBot`. Zyppy ranks URL accessibility #1 (9.5/10) — the highest-weighted concern is currently ungraded.

**Fan-out coverage matrix as structured signal.** GEO-7 grades "directly answers target queries" (singular). 2026 reality is a 10–12-node tree per query. Needs a separate criterion grading coverage of a declared fan-out matrix.

**ChatGPT 5.2 longer-tail behaviour.** Ekamoira/iPullRank: 5.2 generates longer-tail queries with minimal fan-out. Shifts "answer-first" semantics — the lede must win on a 5-word compound query, not a 2-word head term. Current GEO-1 doesn't distinguish.

**Reddit/UGC anchoring.** Aleyda 2026-05-06 (87 likes): Google AI Mode adds previews of "perspectives from public online discussions, social media." Authority Tech: Reddit citations in Perplexity +450% Mar→Jun 2025. 9-tier 2026 pages reference relevant Reddit/forum discussions by name.

**Multi-modal extraction.** Mike King 2026-05-09 on HTML > markdown: "richer info density (tables, SVG, diagrams)." YouTube #1 cited domain in AI Overviews. Current rubric is text-only.

**Entity identifiers (`sameAs`) as new authority signal.** Wellows: 15+ connected entities = 4.8× boost. Perplexity L3 actively filters entity-ambiguous pages. Objectively countable, unlike "domain authority."

**Citation velocity / cross-engine coverage.** Authority Tech: pages cited across Perplexity + AIO + Brave score higher than single-engine. Not measurable from the artifact alone, but the rubric should tighten "verifiable" to mean "verifiable against ≥2 independent external sources."

## 6. Implications for the judge — mapping to GEO-1..8

| Section 1 signal | Existing criterion | Action |
| --- | --- | --- |
| 1.1 Quoted-expert attribution | GEO-1 + GEO-2 | **Split out new GEO-9 Named-expert quotes**. 2.1× citation lift justifies dedicated criterion. |
| 1.2 Inline citation density | GEO-2 | **Strengthen** with explicit density bar: ≥1 inline external-primary link per 150 words, ≥60% external. |
| 1.3 Answer-first lede ≤60w | GEO-7 | **Strengthen**: require (a) primary query keyword, (b) numeric anchor, (c) standalone clause in lede. |
| 1.4 Fan-out coverage matrix | GEO-7 | **Split GEO-7 → GEO-7a head-lede + GEO-7b fan-out coverage**. Fan-out is structurally distinct. |
| 1.5 Freshness coherence | none | **New GEO-10 Freshness coherence**: visible date + body data dates + JSON-LD alignment within 90 days. |
| 1.6 Attribute-rich schema | GEO-8 | **Strengthen**: grade attribute density (≥6/entity), type specificity, external `sameAs` count. |
| 1.7 Chunk extractability | GEO-1 | **Strengthen GEO-1**: ≥80% sections pass 80–250 words + no anaphora + first-sentence-answer. |
| 1.8 Proprietary numbers | GEO-5 | **Tighten**: ≥2 distinct claims with N or ≥3-decimal precision. |
| 1.9 Honest competitive | GEO-3 | **Keep unchanged**. Aleyda Pattern 6 reinforces criterion as written. |
| 1.10 Multi-modal anchors | none | **New GEO-11 Multi-modal anchors**: ≥1 image with citable alt-text, ≥1 comparison table with `<th>`. |
| 1.11 Crawl eligibility | GEO-8 | **Split GEO-8 → GEO-8a schema richness + GEO-8b crawl eligibility**. Zyppy's #1 factor currently ungraded. |
| 1.12 Entity identifiers | GEO-8 | **Roll into strengthened GEO-8a**: ≥4 entities with external IDs. |

### Proposed rubric

| Code | Name | Status |
| --- | --- | --- |
| GEO-1 | Chunk extractability (tightened) | strengthen |
| GEO-2 | Inline citation density (tightened) | strengthen |
| GEO-3 | Honest competitive positioning | keep |
| GEO-4 | Voice/structure fit | keep |
| GEO-5 | Citability moat (proprietary numbers) | strengthen |
| GEO-6 | Cross-page coherence | keep |
| GEO-7a | Answer-first head-query lede | strengthen |
| GEO-7b | Fan-out coverage matrix | new |
| GEO-8a | Attribute-rich schema + entity IDs | strengthen |
| GEO-8b | Crawl eligibility for AI agents | new |
| GEO-9 | Named-expert quotes in `"..."` | new |
| GEO-10 | Freshness coherence | new |
| GEO-11 | Multi-modal anchors | new |

### Calibration anchors

Judge prompt for each criterion should include three reference artifacts: 9-anchor (e.g. the Dr Anna Kowalska quote with credential + date + N), 5-anchor (the generic "popularny zabieg" paragraph), 1-anchor (pure marketing or schema-content mismatch). Each criterion prompt ends with: "Compared to the 9-anchor, where does this artifact fall on 1–9? Quote the phrases/structures that move it up or down."

### Source-confidence note

Strongest 2026 evidence base: Cyrus Shepard's Zyppy 23-factor study (54 experiments synthesised), corroborated by Aleyda's e-commerce subvertical study via Semrush Enterprise AIO, and Mike King's iPullRank/Profound 700K-page eligibility analysis. The Ahrefs 1885-page null result on generic schema is the most important calibration against overrating schema. Authority Tech and Wellows percentage lifts are directional, not load-bearing — many vendor numbers are not independently reproduced.
