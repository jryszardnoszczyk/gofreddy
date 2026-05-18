# GEO Judge Criteria — Domain Research Synthesis

**Date:** 2026-05-15
**Scope:** What makes excellent GEO (Generative Engine Optimization) outputs, grounded in published research and named practitioner observation. Inputs for the geo-lane judge rubric.
**Excludes:** statistical properties, abstract design principles, meta-patterns from other lanes. Excludes specific judge prose (that lands in a separate pass).

---

## 1. What AI engines actually prefer (empirical findings)

The single most-cited piece of academic literature on this question is **Aggarwal et al., "GEO: Generative Engine Optimization"** (arXiv:2311.09735, KDD 2024). The authors built **GEO-bench**, ran 9 candidate optimization methods through it, and measured visibility in generative-engine responses against two metrics: **Position-Adjusted Word Count** (Imp_pwc — citation word-count exponentially decayed by position in the response) and **Subjective Impression** (7-dimension GPT rating: relevance, citation influence, uniqueness, prominence, perceived amount, click probability, material diversity).

Their hierarchy of what worked, ranked by visibility lift:

| Method | Visibility lift | What it does |
|---|---|---|
| Quotation Addition | **+28–40%** | Direct quotes from authoritative sources |
| Statistics Addition | **+30–40%** | Replace qualitative phrasing with quantitative figures |
| Cite Sources | **+30–40%** | Inline citations to credible sources |
| Fluency Optimization | +15–30% | Smoother, more readable prose |
| Easy-to-Understand | +15–30% | Simpler language, same meaning |
| Authoritative tone | +15–30% | More persuasive register |
| Technical Terms | ~+10% | Domain-specific vocabulary |
| Unique Words | ~0 | Lexical novelty — no signal |
| **Keyword Stuffing** | **Negative** | Classic SEO transferred to GEO: counter-productive |

Two findings deserve to land hard in the rubric:

- The three top methods (**quotes, stats, citations**) are all *evidence-injection* tactics. They don't add length, they add verifiability. The lesson is that generative engines treat content like a reviewer treats a paper: claims need support.
- **Citation lift was 115% for rank-5 pages and −30% for rank-1 pages** (Aggarwal §6.2). GEO-style evidence stacking helps weaker pages disproportionately — which directly says first-party landing pages without strong domain authority *must* lean on this lever.

Practitioner studies layered on top largely confirm and extend Aggarwal:

- **Ahrefs (Patel Long, 2025, 75K-brand study):** Brand web mentions correlate with AI Overview visibility at **r = 0.664** — three times stronger than backlinks (r = 0.218). The signal is *unlinked mentions in third-party text*, not link graph.
- **Yext (17.2M citation analysis, 2025):** Sites with original research / first-party data get **4.31× more citation occurrences per URL** than aggregator listings. Same data gets re-cited across query variants.
- **Cyrus Shepard's meta-analysis (Zyppy, "AI Citation Ranking Factors")** consolidated 54 experiments. His top correlation tier was Crawlability → Search Rank → Fan-out Rank → Query-Answer semantic match → Intent-Format match → AI-ready structure → Factually-specific claims → Explicit phrasing → Cites sources → Self-contained passages.
- **Andrea Volpini (WordLift, 2025):** Citations are downstream of retrieval. He frames the architecture as **lexical candidate generation → dense retrieval → reranking → synthesis**, and argues content that *mirrors the query phrasing* gets discounted by Google's task-aware asymmetry (documents and queries live in different vector spaces). The advice is to embody RETRIEVAL_DOCUMENT register: **declarative statements, not echoed questions.**
- **Profound / Search Engine Land (10K-citation passage study, 2025):** Passages of **40–75 words were cited 3.1× more often** than longer ones. Pages with **tables were cited 4.2× more often** than equivalent prose. The unit of competition is the passage, not the page.
- **Perplexity citation behaviour (Skywork, ZipTie 2025):** 78% of complex-research answers tie every claim to a specific source vs. ChatGPT's 62%. **70% of top-cited Perplexity sources have a visible publication or update date within 12–18 months.** **90% answer the core question within the first 100 words** — the BLUF / inverted-pyramid pattern.
- **Backlinko / Ahrefs ranking-overlap studies:** As of Q1 2026, only **38% of AI Overview citations** come from Google's top 10 (down from 76% in July 2025), and only **12% of all AI-cited URLs** overlap with Google's top 10 on the original prompt. AI citation is diverging from organic ranking.

The combined story: a citable landing page is **answer-first, evidence-dense, well-chunked, freshness-stamped, mentioned often elsewhere, and written in declarative-document register rather than query-echo register.**

---

## 2. What separates citable from non-citable content (failure modes)

These are concrete failure modes the rubric should be able to call:

1. **Query-mirroring lead.** Page opens with "What is X?" or paraphrases the search query. Volpini's "Matryoshka Paragraph" finding: under Google's asymmetric embedding scheme, this signals "another query" not "an answer," and gets ranked behind sources that lead with a declarative definition. Strong: "GS1 Digital Link is a standards-based URI…" Weak: "What is GS1 Digital Link? GS1 Digital Link is becoming increasingly important…"
2. **Buried answer.** Core claim sits below the fold or in paragraph 4. Shepard's "Answer Near Top" factor; Perplexity's 90/100-words finding; Profound's passage study. Generative engines have retrieval caps per URL — 44% of all AI citations come from the top third of a page.
3. **Prose where a table would do.** Comparison content, pricing, feature differences, spec lists written as flowing paragraphs lose to the same data structured as a table by **4.2×**.
4. **Unsourced specificity.** A number without a source is treated as a claim, not a fact. Aggarwal's Statistics Addition method works only when statistics are presented as verifiable, not as marketing.
5. **Keyword-stuffed claims.** The single most consistent negative-signal finding in the Aggarwal paper. SEO instincts transferred directly to GEO are actively harmful. Vague phrasing like "leading platform" / "industry-best" / "next-generation" trips this as well.
6. **Floating pronouns and orphan passages.** Volpini's "chunk-complete" principle. If a 50-word passage extracted standalone can't be understood without prior context ("This makes it…", "The above shows…"), the retrieval system treats it as low-confidence material.
7. **Vendor self-puffery without third-party signal.** Forrester 2026 data: AI buyers validate vendor claims against external sources before trusting them. Pages that don't acknowledge the competitive landscape (or that quote only the brand's own assets) read as marketing, not reference. The Verge documented Google AI Mode catching and flagging vendor-authored "best of" lists that placed their own products first.
8. **Stale freshness signal.** No visible date, no recent update, no current-year reference. Perplexity's 70% / 12-18 month finding; Ahrefs 17M-citation freshness study showing AI assistants prefer recent content even when the underlying facts haven't changed.
9. **Entity drift.** Calling the product "Acme Pay" in one section, "Acme Payments" in another, "AcmePay" in a third. Kalicube's entity-consistency principle and Shepard's #19 factor. Embeddings cluster these as different entities.
10. **No first-party data of any kind.** All claims are recycled from secondary sources. The Yext 4.31× multiplier disappears entirely — these pages have nothing AI engines can't get elsewhere.
11. **Mismatch between page intent and likely query class.** Shepard's #6 Intent-Format Match: "best X for Y" queries want listicles, "how to X" queries want stepwise structure, "X vs Y" queries want comparison tables. A landing page written as a marketing narrative loses citation slots for question-form queries even when its content is excellent.
12. **No declared target queries.** The author can't say what queries the page should win, so the page hedges across all of them and excels at none.

---

## 3. Industry terminology and frameworks the rubric should adopt

The vocabulary that real GEO practitioners speak in — and that judges should use rather than inventing parallel terms:

- **AEO (Answer Engine Optimization)** — Jason Barnard's term, coined 2017–2018, now the umbrella label for "structure content so answer engines extract and attribute it." Most practitioners use AEO and GEO near-synonymously; Kalicube argues they describe the same practice.
- **Generative Engine** — Aggarwal's term for the class of system: ChatGPT, Perplexity, Google AI Overviews / AI Mode, Claude, Copilot, Gemini.
- **Citation vs. mention** — distinct signals. *Citation* = the engine links/attributes; *mention* = the engine names the brand without linking. RankScience research: brands are 3× more likely to be cited alone than to get both. The page should optimize for both.
- **Citation gap** — Status Labs / ALM Corp: "85% of pages ChatGPT retrieves are never cited." A page can be retrieved into the candidate set and still lose to a better-structured passage.
- **Fan-out queries** — Volpini and Google: a single user query is decomposed into multiple sub-queries that fan out across the knowledge graph and web index. A landing page wins citation slots across the *fan-out set*, not just the literal query.
- **BLUF (Bottom Line Up Front) / Inverted Pyramid** — answer in the first 40–60 words, then context. 3.8× citation lift per the Norg/MintCopy/Claire Broadley body of work.
- **Passage as unit of competition** — Search Engine Land's standing line. A page can have one passage cited and four passages ignored; that's normal, not failure.
- **Self-contained passage / chunk-completeness** — Volpini's principle: every passage stands alone. No floating pronouns, no "as mentioned above," no orphan context.
- **E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)** — Google's Quality Rater framework. Cleveland Clinic, Mayo Clinic, NIH, ScienceDirect get cited because they hit all four. Trust is the most important member — untrustworthy pages have low E-E-A-T no matter how expert.
- **Entity SEO / Semantic Triples** — Kalicube's framework, derived from Bill Slawski's patent analysis. Subject-Predicate-Object statements ("Freddy is an AI agency"; "Freddy specializes in regulated B2B") are how knowledge graphs are populated. Repeated identically across the digital footprint, they stabilize the engine's model of the entity.
- **Knowledge Graph as substrate** — Volpini's argument that KG-grounded reasoning produces "stronger entity centering, cleaner narrative flow, fewer defensive hedges" than pure vector retrieval. Pages that align with a KG entity get cited more reliably across query variants.
- **Retrieval-document register** — Volpini: documents and queries live in different vector spaces in modern asymmetric retrievers. Writing in declarative-statement register positions the content correctly.
- **Citation gravity** — Kalicube's informal term: established entity understanding creates a self-reinforcing pull. Once an engine has cited you, it returns to you across related queries.
- **Brand mention correlation > backlink correlation** — Ahrefs 75K-brand finding: 0.664 vs 0.218. The judge should not reward link-style signals; it should reward signals that drive unlinked mentions elsewhere.
- **Exemplar tier** — the named sites that AI engines treat as default authority: Wikipedia, Mayo Clinic, Cleveland Clinic, NIH, Healthline, Stack Overflow, government .gov resources, Gartner, NerdWallet, Consumer Reports, PCMag, CNET. The rubric should ask "does this page belong in *any* exemplar's vicinity?"

---

## 4. Proposed judge criteria

Seven criteria grounded in the research above. Each maps to a specific empirical finding, not an abstract design principle.

### GEO-A — Answer-First Lead (BLUF compliance)

**Evaluates:** Whether the page's primary claim — what the product/service is, who it serves, what makes it different — lands in the first 40–75 words of meaningful body content, in declarative-document register (not query-echo register).

**Why this is what experts evaluate:** Perplexity's top citations answer the core question in the first 100 words 90% of the time (Skywork 2025); Volpini's Matryoshka Representation Learning argument shows OpenAI's embedding scheme front-loads early dimensions; Profound's 10K-passage study shows 44% of AI citations come from the top third of pages; Norg/MintCopy: BLUF-structured articles got 3.8× more citations.

**Failure modes:** Opens with "What is X?" or paraphrased query. Marketing throat-clearing. Buries the definitional sentence below brand storytelling. Leads with a question rather than a statement.

---

### GEO-B — Evidence Density (Stats, Quotes, Citations)

**Evaluates:** Whether the page injects verifiable evidence — quantitative figures with sources, direct quotations from credible third parties, inline citations to first-party data or external authority — at the density Aggarwal et al. showed correlates with visibility lift.

**Why this is what experts evaluate:** Aggarwal et al.'s top three methods (Quotation Addition +28–40%, Statistics Addition +30–40%, Cite Sources +30–40%) are all evidence injection. Yext's 17.2M-citation study: first-party data drives 4.31× more citation occurrences. Shepard's "Factually Specific" (8.3) and "Cites Sources" (8.0) factors.

**Failure modes:** Vague qualitative claims ("leading," "industry-best," "trusted by thousands") without numbers. Numbers without attribution. Self-citation only — every linked source is a sibling page on the same domain. Marketing copy where stats would do the work.

---

### GEO-C — Passage Self-Containment

**Evaluates:** Whether each substantive passage (heading + paragraph or list block) stands alone when extracted. The judge should be able to lift any 40–75-word block and have it read as a complete claim with named entities, no floating pronouns, no "as mentioned above," no orphan context.

**Why this is what experts evaluate:** Volpini's "chunk-complete" principle; Shepard's #13 "Self-Contained Passages" (8.0); Search Engine Land's "passage is the unit of competition"; Profound's 40–75-word sweet-spot finding. AI engines retrieve and cite passages, not pages.

**Failure modes:** "This makes it..." "The above shows..." "As we saw earlier..." Headings that don't restate the entity. Pronouns that resolve only by reading prior paragraphs. Lists where items 2–5 require item 1 for context.

---

### GEO-D — Entity Consistency and Semantic Triples

**Evaluates:** Whether the page presents the brand/product/service as a stable entity via consistent canonical naming and repeated subject-predicate-object statements that a knowledge graph could ingest. Same name everywhere. Same predicate-style claims ("Freddy is a content engine for regulated B2B"). Disambiguation early.

**Why this is what experts evaluate:** Kalicube's Entity SEO / Semantic Triple framework (Jason Barnard, derived from Bill Slawski's analysis of Google entity patents); Shepard's #19 Entity Consistency (5.8); Volpini's argument that KG-grounded retrieval produces stronger entity centering. Embeddings cluster name variants as separate entities — drift fragments citation signal.

**Failure modes:** Calling the product "Acme Pay" in hero, "AcmePay" in body, "Acme's payment platform" in footer. Missing one-sentence entity definition near the top. No clear category placement ("an X for Y who need Z"). Predicate drift — page describes the product as multiple incompatible things.

---

### GEO-E — Third-Party Validation and Competitive Acknowledgment

**Evaluates:** Whether the page treats the competitive landscape as something that exists — naming alternatives, citing third-party comparisons or analyst coverage, quoting external voices — rather than presenting itself in a vendor-vacuum. Vendor-neutral framing increases citation odds because answer engines validate vendor claims against external sources.

**Why this is what experts evaluate:** Forrester 2026 research: AI buyers validate vendor claims against external sources before trusting them. Status Labs / RankScience "Citation Gap" research: pages that present themselves in isolation fail to earn citations because they read as marketing not reference. The Verge documented Google AI Mode discounting vendor "best of" lists that placed their own products first. Ahrefs' brand-mention correlation (r = 0.664) is driven by *external* text, which only happens when the brand engages a real ecosystem.

**Failure modes:** Zero mention of alternatives or category. "Trusted by [logo wall]" without source for any logo. Self-comparison only (us-vs-old-us). Cites zero external voices. Claims category leadership without an analyst, journalist, or comparison-site reference. Acknowledges competitors only to attack them.

---

### GEO-F — Search-Intent and Format Match for Declared Target Queries

**Evaluates:** Whether the page's structure matches the format AI engines prefer for its declared target query class. "Best X for Y" → comparison structure with at least one table or list. "How to X" → ordered, stepwise structure. "X vs Y" → side-by-side table. "What is X" → definition lead + structured detail. The page must declare its target queries, and the format must match.

**Why this is what experts evaluate:** Shepard's #6 Intent-Format Match (9.0) and #5 Query-Answer Match (9.2); Profound's table-vs-prose finding (4.2× citation rate for tables on comparison content); Aggarwal's domain-specific finding that different methods work in different domains (Statistics Addition wins for Law & Government and Opinion; Quotation Addition wins for People & Society and History; Fluency wins for Health and Business). Format-intent fit is domain-specific.

**Failure modes:** No declared target queries. Declared targets but page is a flowing narrative when comparison or stepwise was required. Comparison content written as prose without tables. "How to" pages without ordered steps. Wrong domain register (technical-debate tone on a Health page, casual-explanation tone on a Law page).

---

### GEO-G — Freshness and Citable Specifics

**Evaluates:** Whether the page provides AI engines with the freshness signals they preferentially weight — visible publication or update date, current-year references in body content, dated data points, recent third-party citations — and whether its specific claims are time-stamped and verifiable rather than evergreen-vague.

**Why this is what experts evaluate:** Ahrefs 17M-citation freshness study (AI assistants prefer fresher content even when underlying facts are stable); Search Engine Land 8K-citation analysis: 44% of AI Overview citations are from current-year content, 85% from the last few years; Perplexity 70% / 12-18 months freshness finding (Skywork 2025); Volpini's "verifiable citation triggers — concrete numbers, dates, standards, primary sources."

**Failure modes:** No visible date anywhere on the page. Last-updated stamp from prior year on a page making current-state claims. Stats without years ("studies show 80%..."). Generic evergreen tone where specifics would land harder ("modern", "today's", "the latest"). Third-party citations all undated.

---

## 5. Sources

**Academic:**
- Aggarwal, Murahari, Rajpurohit, Kalyan, Narasimhan, Deshpande. "GEO: Generative Engine Optimization." [arXiv:2311.09735v3](https://arxiv.org/abs/2311.09735) (KDD 2024). Full text: [arXiv HTML v3](https://arxiv.org/html/2311.09735v3). GitHub: [GEO-optim/GEO](https://github.com/GEO-optim/GEO).

**Practitioner / industry research:**
- Cyrus Shepard, "AI Citation Ranking Factors Analysis," [Zyppy Signal](https://signal.zyppy.com/p/ai-citation-ranking-factors) — meta-analysis of 54 experiments.
- Andrea Volpini (WordLift), "Why AI Cites Some Pages and Ignores Others," [WordLift Blog](https://wordlift.io/blog/en/embeddings-search-visibility/).
- Andrea Volpini (WordLift), "Retrieval Evolution For Large Language Models," [WordLift Blog](https://wordlift.io/blog/en/retrieval-evolution-for-large-language-models/).
- Andrea Volpini (WordLift), "Query Fan-Out: A Data-Driven Approach to AI Search Visibility," [WordLift Blog](https://wordlift.io/blog/en/query-fan-out-ai-search/).
- Jason Barnard / Kalicube, "Semantic Triple" entity definition, [Kalicube](https://kalicube.com/entity/semantic-triple/).
- Jason Barnard / Kalicube, "Entity SEO" framework, [Kalicube](https://kalicube.com/entity/entity-seo/).
- Jason Barnard / Kalicube, "AIO, GEO, LLMO, AEO: industry renaming," [Kalicube](https://kalicube.com/learning-spaces/faq-list/generative-ai/aio-geo-llmo-aeo-the-industry-keeps-renaming-the-methodology-jason-barnard-coined-in-2017/).

**Citation-pattern studies:**
- Profound, "AI Platform Citation Patterns: ChatGPT, Google AI Overviews, Perplexity," [Profound](https://www.tryprofound.com/blog/ai-platform-citation-patterns).
- Profound, "How ChatGPT Sources the Web," [Profound](https://www.tryprofound.com/blog/chatgpt-citation-sources).
- Search Engine Land, "How to get cited by AI: SEO insights from 8,000 AI citations," [Search Engine Land](https://searchengineland.com/how-to-get-cited-by-ai-seo-insights-from-8000-ai-citations-455284).
- Search Engine Land, "How to write for AI search: A playbook for machine-readable content," [Search Engine Land](https://searchengineland.com/ai-search-playbook-machine-readable-content-472412).
- Ahrefs, "76% of AI Overview Citations Pull From the Top 10" (Jul 2025) and follow-up "Update: 38% of AI Overview Citations Pull From The Top 10" (Q1 2026), [Ahrefs](https://ahrefs.com/blog/ai-overview-citations-top-10/).
- Ahrefs, "Only 12% of AI Cited URLs Rank in Google's Top 10," [Ahrefs](https://ahrefs.com/blog/ai-search-overlap/).
- Ahrefs (Patrick Stox / Chris Long), 75K-brand mention-correlation study showing brand mentions r=0.664 vs backlinks r=0.218.
- Ahrefs, "AI Assistants Prefer to Cite Fresher Content (17M Citations Analyzed)," [Ahrefs](https://ahrefs.com/blog/do-ai-assistants-prefer-to-cite-fresh-content/).
- Yext, 17.2M-citation analysis showing first-party data → 4.31× citation occurrences.

**BLUF / passage-structure research:**
- MintCopy, "BLUF: The 'Ski Ramp' Content Strategy," [MintCopy](https://mintcopy.com/content-marketing-blog/content-strategy-for-ai-attention-put-the-bluf-first/).
- Norg, "How to Structure Content for Maximum AI Citation," [Norg](https://home.norg.ai/ai-search-answer-engines/answer-engine-architecture-citation-mechanics/how-to-structure-content-for-maximum-ai-citation-a-step-by-step-optimization-guide/).
- Claire Broadley, "Passage-First Workflow + BLUF," [clairebroadley.com](https://www.clairebroadley.com/passage-optimization/).
- Am I Cited, "Answer-First Content: The BLUF Technique for AI Visibility," [amicited.com](https://www.amicited.com/blog/answer-first-content-bluf-ai-visibility/).

**Citation gap / failure-mode research:**
- ALM Corp, "Why 85% of Pages ChatGPT Retrieves Are Never Cited," [ALM Corp](https://almcorp.com/chatgpt-retrieval-fanout-google-serps-citations/).
- Status Labs / Retail Tech Innovation Hub, "Citation Gap: why ChatGPT cites your competitors but not you," [retailtechinnovationhub.com](https://retailtechinnovationhub.com/home/2026/2/4/experts-at-status-labs-explain-the-citation-gap-why-chatgpt-cites-your-competitors-but-not-your-firm).
- RankScience, "AI Citations vs Mentions: Why AI Picks Competitors Over You," [rankscience.com](https://www.rankscience.com/blog/ai-citations-brand-mentions-visibility-gap).

**E-E-A-T and Google Quality Rater context:**
- Search Engine Land, "Google quality raters now assess whether content is AI-generated," [Search Engine Land](https://searchengineland.com/google-quality-raters-content-ai-generated-454161).
- Geneo, "Why E-E-A-T Matters in AI Search," [geneo.app](https://geneo.app/blog/e-e-a-t-ai-search-2025/).

**Perplexity-specific:**
- Skywork, "Perplexity Accuracy Tests 2025: Sources & Citations," [Skywork](https://skywork.ai/blog/news/perplexity-accuracy-tests-2025-sources-citations/).
- ZipTie, "How Perplexity AI Answers Work: Retrieval, Ranking, and Citation Pipeline," [ZipTie](https://ziptie.dev/blog/how-perplexity-ai-answers-work/).

**Exemplar sources AI engines consistently cite:** Wikipedia (ChatGPT's #1 source, 7.8% of all citations; 47.9% of top-10 share), Reddit (Perplexity's #1, 46.7% of top-10 share; Google AI Overviews' #1 community source), YouTube (~23.3% across industries per Surfer), Mayo Clinic / Cleveland Clinic / Healthline / WebMD (health domain authority tier), NIH / ScienceDirect (research authority tier), Stack Overflow (technical Q&A — 58M+ Q&A entries), Gartner (B2B analyst), NerdWallet / Consumer Reports / PCMag / CNET (third-party review tier), .gov / .edu (institutional tier).
