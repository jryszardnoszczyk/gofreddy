# Phase B research — `monitoring` lane

Calibration corpus for the monitoring judge. Anchors what a 9-tier weekly brand/competitor digest looks like in May 2026 against social-listening industry consensus, rumor-verification research, and the failure modes of Brand24 / Talkwalker / Brandwatch / Sprout Trellis. Goal: judge can score `digest.md` + `stories/*.json` + recommendations against the "Monday-morning paranoid-not-to-read" ceiling, not against a generic mention-count report.

Existing rubric: MON-1 surface DIFFERENT (essential), MON-2 severity defensible (important), MON-3 top development named + prioritized (essential), MON-4 actions have who/when/consequence (important), MON-5 compound narratives (important), MON-6 numbers answer "so what" + flag missing signals (pitfall), MON-7 arc across prior digests (optional), MON-8 word count proportional to importance (pitfall).

Known audit gap: no faithfulness check (hallucinated quotes should auto-cap), no story canonicalization (event-cluster dedup), no author/source weighting.

## 1. Top 9-tier signals

Each: what excellence looks like, source/mechanism, judge test. Graded on the artifact, not 30-day client-action outcomes.

### 1.1 Faithful primary-source quotes with verifiable provenance
- **Bar:** every `"..."` quote ties to URL + author + timestamp; ≥3 verbatim quotes per top-3 story, each round-trippable to the cited URL with byte-exact text. Example: `Tim Soulo (Ahrefs CMO, @timsoulo, 2026-05-09): "32% of organic clicks now reach pages via AI engines, not Google SERPs."` → story JSON has tweet URL, handle, engagement snapshot.
- **Source/mechanism:** Sprout's 2026 Proof-of-Reality Breaking Ground campaign — "When even dancing dog videos turn out to be fake, trust on social gets complicated" (`https://x.com/SproutSocial/status/2019009059052036302`) — exists because this failure is systemic. A digest is derivative: the client can't fact-check 40 mentions in 10 min; they trust the synthesis. One fabricated quote destroys the contract.
- **Judge test:** sample 5 random quotes; confirm (a) URL field present, (b) verbatim match against `monitoring.json`, (c) handle exists. Any failure caps the digest at 2.

### 1.2 Event-cluster canonicalization across syndicating sources
- **Bar:** same event across Verge + TechCrunch + Bloomberg + reposts/reshares collapses to ONE story with `primary_source` (originating reporter), `secondary_sources[]` ranked by author authority not count, `corroboration_count` integer. Weekly: ≥80% of raw mentions resolve to ≤30% as many distinct stories.
- **Source/mechanism:** 80% of articles are duplicates of another article (Newsloth `https://newsloth.com/blog/news-clustering-and-deduplication`, Feedly `https://feedly.com/engineering/posts/reducing-clustering-latency`); MinHash LSH at 85% similarity is the modern baseline. MDPI 2026 review (`https://www.mdpi.com/2076-3417/13/9/5510`) frames canonicalization as solved-but-skipped. Without it, prioritization becomes a count contest: same Verge story retweeted 200× outranks a Bloomberg scoop reported once.
- **Judge test:** any URL repeating across top-5 stories' `secondary_sources[]` = dedup miss. Bar for 9: zero overlap.

### 1.3 Author/source weighting with explicit signal-strength rationale
- **Bar:** each story carries `evidence_strength` (1–5) + `source_weight_rationale` combining author authority (role, prior verified reporting, follower base) and amplification separately. Founder tweet at 10K followers outweighs anonymous 50K-like meme on the same event.
- **Source/mechanism:** Sprinklr 2026 (`https://www.sprinklr.com/blog/brand-monitoring/`): alerting is "threshold-based for volume and sentiment, velocity-based for narrative momentum, and risk-weighted for crisis signals." Sprout's RT (`https://x.com/SproutSocial/status/2050219270546563349`): "71% of directors predict social data will become more influential than traditional market research by 2029" — only if signal is distinguishable from noise. Engagement-only ranking collapses to loudest-wins = meme-economy wins.
- **Judge test:** top-3 each have `source_weight_rationale` ≥1 sentence; numeric `evidence_strength` not engagement-only (rationale must name role/authority).

### 1.4 Severity classification anchored to a defensible scale
- **Bar:** each story tagged `critical|high|medium|low` with explicit triggering clause: critical = legal/regulatory/safety/exec-named; high = competitor strategic move OR sustained negative narrative ≥3 distinct authors; medium = product mention with measurable demand signal; low = passing reference. Zero "high" without a cited clause.
- **Source/mechanism:** Marketing Juice 2026 (`https://themarketingjuice.com/competitive-intelligence-monitoring/`): "1=noise, 2=interesting, 3=actionable, only escalate 3's." Severity without a stated scale is vibes — unfalsifiable, uncorrectable, drifts. A scale lets the client disagree with a specific call rather than the whole digest.
- **Judge test:** every `critical`/`high` story has `severity_reason` naming a clause; sample 3, verify the clause applies.

### 1.5 Stance-tagged mentions for contested stories
- **Bar:** for rumor-flavoured/breaking-event stories, each mention carries `support|deny|query|comment`. Story `verification_status` derives from distribution: high deny+query → `unverified_rumor`, not asserted as fact.
- **Source/mechanism:** ACM TIST 2026 (`https://dl.acm.org/doi/10.1145/3716856`); ScienceDirect stance review (`https://www.sciencedirect.com/science/article/abs/pii/S0952197622007916`); arXiv 2512.13559 stance-aware structural modeling. Consensus: misinformation greeted with skepticism (denials, queries) is more likely to turn out false. Stance distribution is the strongest early-warning predictor.
- **Judge test:** rumor-tagged stories carry mention-level `stance`; story `verification_status` derived. Acceptable: explicit "no rumor-flavoured stories this week."

### 1.6 Action items with owner/timing/consequence-of-inaction
- **Bar:** ≥3 actions, each with action verb + named owner + concrete deadline (this-Friday / before-launch) + consequence-if-skipped clause. ≥1 with deadline ≤Friday EOD. Disqualifiers: "team", "soon", "continue monitoring", "keep an eye on."
- **Source/mechanism:** ReachReport 2026 (`https://www.reachreport.io/en/guide/media-monitoring-report/`): execs want "What happened? Why it matters? What to do next?" Adata.pro (`https://adata.pro/blog/crafting-an-effective-media-monitoring-report-for-your-c-suite/`): summary ≤10% of length but decision-ready. Vague actions are unfalsifiable and skipped.
- **Judge test:** all four fields populated, non-trivial. Pitfall flag on "missed opportunity" consequence or "ongoing" deadline.

### 1.7 Compound narrative — weak signals forming a strong story
- **Bar:** ≥1 cross-story "convergent signal" naming ≥3 independent low-severity mentions suggesting a pattern. Pattern statement + mechanism + forward hypothesis + confidence (low/med/high).
- **Source/mechanism:** Sprout's 2026 Bieberchella post — "Is it your algo, or is #Bieberchella actually all anyone's talking about? You need signals beyond your own timeline" (`https://x.com/SproutSocial/status/2046327841353052378`) — captures the discipline. Single signals everyone sees; the compound pattern is what only the close reader notices. The client pays for synthesis they can't do in 10 min.
- **Judge test:** `compound_narratives[]` ≥1 entry with `pattern_statement`, `supporting_stories[]` (≥3 IDs), `forward_hypothesis`, `confidence`. Generic "lots of AI chatter" fails.

### 1.8 Cold-start surfacing — what's DIFFERENT this week
- **Bar:** ≥3 specific "first-time-seen-in-corpus" callouts naming the entity (handle, outlet, framing) and the reasoning ("not in last 4 weeks" / "first time brand appears on r/sysadmin").
- **Source/mechanism:** Existing MON-1. Sprinklr 2026: "social listening surfaces early signals about risks, opportunities, and changing expectations so leaders aren't making decisions in the dark." Difference is signal; sameness is noise. A digest that recaps the same 4 themes weekly becomes background; the client trains themselves to skim.
- **Judge test:** ≥3 entries in `whats_different_this_week[]` with named entity + reasoning. Generic "interest is growing" fails.

### 1.9 Channel diversity — no single-platform echo
- **Bar:** top-3 stories collectively triangulate ≥4 distinct platform-classes (X + Reddit + news + LinkedIn / podcast / forum / review). At most 1 top story is single-channel.
- **Source/mechanism:** Hootsuite 2026 (`https://blog.hootsuite.com/social-listening-business/`): differentiator is "holistic view... expanded social media monitoring across forums, reviews, and multimedia content." Trigify B2B guide flags channel-coverage gaps as the #1 vendor weakness. Single-channel echo correlates with viral-tweet bias: conversation looks bigger from inside X because X is loudest; the actual analyst on LinkedIn is buried.
- **Judge test:** distinct platform-classes across top-3 `channels[]` ≥ 4.

### 1.10 Forward hooks — explicit watch-next-week items
- **Bar:** ≥3 hooks with conditional trigger + expected signal + monitoring target. Example: "If Competitor Y posts earnings Wed, expect AI-margin-pressure narrative spike — check r/investing + Stratechery."
- **Source/mechanism:** Sprinklr 2026 emphasizes "trajectory" not "snapshot." Cassidy AI brief (`https://www.cassidyai.com/solutions/weekly-competitor-news-brief`) lists forward hooks as the stickiest feature in customer feedback. Retrospective-only digest reports yesterday; forward hooks pre-organize next Monday.
- **Judge test:** `forward_watch[]` ≥3 entries with `trigger` + `expected_signal` + `monitoring_target`. "Continue monitoring AI sentiment" disqualifies.

### 1.11 Volume-decoupled prioritization
- **Bar:** ≥1 of top-3 stories has below-median volume but above-median strategic importance (founder named + dollar named + new entity).
- **Source/mechanism:** Studio North (`https://www.studionorth.com/brand-visibility-metrics-are-your-new-growth-signal/`): "growth signal" is decoupled from volume. Sprout's RT (`https://x.com/SproutSocial/status/2046957885708493264`): "AI can process the volume, but it can't replace your judgment." Engagement is power-law; mention-count rankings always surface the same loud accounts. A one-line CFO tweet outweighs 800 Reddit UI comments.
- **Judge test:** ≥1 top-3 story has volume rank > median.

### 1.12 Word count proportional to story importance
- **Bar:** word-count ratio between top-1 and rank-10 ≥ 3:1; zero `critical` stories under 60 words.
- **Source/mechanism:** Existing MON-8. Adata.pro 2026: executive summary ≤10% of full report, but within the summary, weight is proportional to consequence. Equal-length items signal equal importance — if your critical story and your meme-retweet are both 80 words, the client reads them the same. Length is a load-bearing editorial signal.
- **Judge test:** compute `word_count` per story; verify rank-by-words ≈ rank-by-severity (Spearman ≥0.7). Penalize `critical` <60 words.

### 1.13 Missing-expected-signal callouts (negative space)
- **Bar:** ≥1 named absence with stated basis: "Competitor X had a launch Tuesday; absent from community channels — unusual" + hypothesis.
- **Source/mechanism:** Rivalsense 2026 (`https://rivalsense.co/intel/the-real-world-benefits-of-competitive-intelligence-software-and-how-to-actually-use-it/`): "absence of an alert is also information." arXiv 2603.23568v1 on sparse-news signal reconstruction underscores the diagnostic value of expected-but-missing signals. Surfacing absences requires the synthesizer to hold a model of "what should be" against "what is" — exactly the judgment the client pays for.
- **Judge test:** `expected_but_missing[]` ≥1 entry with `expected_topic` + `expectation_basis` + `hypothesis_for_absence`. Generic "didn't see much about pricing" fails.

## 2. Top 5-tier signals — mediocrity that ships but doesn't drive action

Median Brand24/Mention/Meltwater-free output. Read once. Filed. Not returned to.

- **2.1 Volume cosplay opening.** "247 mentions, +34% WoW." Total count predicts neither sentiment nor consequence; Brand24 Capterra reviews note "filters can let irrelevant or incorrect content through" — inflated totals are default. **Fail:** count+delta opener with no decision-relevant claim in first 40 words.
- **2.2 Generic sentiment ratio, no quote.** "62% positive, 28% neutral, 10% negative." Unfalsifiable without anchors. Brand24 noted weaknesses: sarcasm-blind, off on industry language (`https://combinat.net/brand24-review-2026-complete-social-listening-brand-monitoring-tool-guide/`). **Fail:** ratio without ≥1 quoted negative + ≥1 quoted positive mention.
- **2.3 Equal-severity alphabetical list.** Every story "medium," 80 words, sorted by topic. Trigify flags this as the #1 reason teams stop reading vendor digests. **Fail:** ≥80% same severity, or sort order independent of severity.
- **2.4 "Continue monitoring" recommendation.** Literal opposite of an action — synthesizer admitting no judgment. **Fail:** recommendation containing "continue monitoring"/"keep an eye on"/"stay aware of" without follow-up trigger.
- **2.5 Single-channel feed dump.** 90%+ from X (or LinkedIn-only). Reflects tool affordance, not brand's actual conversational surface. **Fail:** ≥90% mentions from one platform-class.
- **2.6 Source-count as authority proxy.** "Mentioned by 7 sources including Bloomberg, Verge, TechCrunch..." — all paraphrasing the same Bloomberg piece. Canonicalization failure dressed as breadth. **Fail:** "N>3 sources" without `primary_source` distinguished.
- **2.7 Templated competitor count-table.** "Anthropic 34; OpenAI 89; Google 142." Raw data, useless as digest. **Fail:** competitor section is count-table with <50 words of interpretation.
- **2.8 Vague forward-look.** "AI continues to dominate conversations." Past dressed as forward-look. **Fail:** no conditional ("if X happens") and no named entity to watch.

## 3. Slop patterns — 1-tier auto-rejects

**3.1 Fabricated quotes (load-bearing → auto-cap at 1).** Quote attributed to author/outlet where source contains no such text or no such handle exists. Sprout's whole Proof-of-Reality positioning targets this systemic failure mode.

**3.2 Duplication inflation.** Same Verge article counted as 7 mentions via syndication/reposts. Newsloth+Feedly: 80% of articles are duplicates. Any tool not dedup'ing is producing slop.

**3.3 Reddit-volume overweight.** 200-comment meme thread ranked above Bloomberg byline. Engagement-only ranking collapses to "loudest wins" = meme-economy wins.

**3.4 Vibes sentiment.** "Sentiment trending negative" with no quote, no count, no named stakeholder. Brand24's documented sarcasm-blindness makes vendor-generated vibe-sentiment particularly dangerous.

**3.5 Single-channel echo (90% X).** Synthesizer used the X API and called it monitoring. Reddit/HN/Substack/podcasts/news APIs absent.

**3.6 "Continue monitoring" recommendations.** Concentrated form (≥50% of recommendations) = synthesizer laundering uncertainty as advice.

**3.7 Number without "so what".** "Brand mentions up 43% WoW." Why? Correlated with what? Good or bad? Number without decision is filler.

**3.8 Hallucinated authors/outlets.** "As reported by *TechFinance Weekly*..." — outlet doesn't exist. "Tweet by @marketinguru2025" — handle doesn't exist. Confident citation of non-existent sources = LLM-monitoring baseline. Auto-cap.

## 4. What separates 9-tier from 5-tier

Three dimensions where the gap is widest and the judge has the most leverage.

**Faithfulness vs vibes.** 9-tier: every quoted span round-trips to URL + author + timestamp, sample-verifiable. 5-tier: percentages and "trending" without a single anchor. A fabricated quote sent to the CEO is a career-affecting event. The judge should treat faithfulness as binary-with-cap, not graded: any verifiable fabrication caps the digest at 1 regardless of other strengths. Sprout's 2026 Proof-of-Reality bet is that this gap is widening as AI summaries proliferate.

**Canonicalization vs source-count theater.** 9-tier: 247 mentions resolve to 18 stories with named `primary_source` and corroboration count. 5-tier: 247 mentions presented as 247; "trending topics" by keyword frequency. Newsloth/Feedly engineering blogs show the algorithms are commodity — the gap is product-level laziness. A judge that doesn't check canonicalization rewards tools that pad source counts.

**Prioritization fidelity vs volume.** 9-tier: top-3 includes ≥1 below-median-volume but high-strategic-importance story with explicit weighting rationale. 5-tier: top-3 = top-3 by raw count = whatever went viral = what the client already saw on Twitter. If the digest only surfaces what the client already saw, it's redundant — they stop opening it.

Secondary high-leverage gaps: compound narratives (synthesis vs aggregation); negative space (expert behavior aggregators can't replicate); forward hooks (next-week pre-organization turns one-shot report into tracker).

## 5. 2026 emerging signals

**Stance detection moves from research to product.** ACM TIST 2026 joint rumor/stance work and arXiv 2512.13559 stance-aware structural modeling signal that stance-tagging is now cheap enough at inference to attach per-mention. Tools that don't are leaving the strongest rumor-verification signal on the floor. Judge: stance distribution becomes first-class, not curio.

**AI-summary slop is documented in incumbent tools.** Brand24 Capterra/Gartner reviews flag sarcasm-blindness and industry-language errors. Talkwalker's "Blue Silk AI understands context and nuance that simpler tools miss" pitch exists because baseline is bad. Sprout's Trellis agent (`https://x.com/SproutSocial/status/2001354487017988511`) positioned to make "messy social data actually make sense" — explicit acknowledgment default state is unusable noise. Judge must assume upstream tool may have hallucinated; verification can't be deferred.

**Cross-platform aggregation gap widens.** Sprout's Bieberchella post captures the operational problem: teams over-indexed on their own timeline. Platforms most predictive of business outcomes (niche subs, industry Substacks, podcasts, private Discord/Slack) are hardest to API-scrape. Tools that don't cover them go invisible to early narrative formation. Judge: reward ≥3 platform-classes/week; penalize X-only.

**Compound-narrative synthesis is the AI-native moat.** arXiv 2603.23568v1 on sparse-news causal reconstruction frames the gap: aggregators dedup/count/sort; synthesizers name 3-weak-signal patterns no single source flagged. 9-tier behavior is no longer "comprehensive coverage" (commoditized by API access) but "the synthesizer noticed what no individual analyst would have time to notice."

**"Proof of reality" as product positioning.** Sprout's repeated 2026 Breaking Ground events (`https://x.com/SproutSocial/status/2019087402690633794`, `https://x.com/SproutSocial/status/2019009059052036302`) target trust-crisis caused by AI-generated content. Buyer's question shifted from "do you cover all platforms?" to "can I trust the cited quotes?" Regression in baseline expectations, and it's now the bar.

## 6. Implications for the judge — keep/strengthen/add for MON-1..8

### Audit of existing criteria

- **MON-1 (DIFFERENT, cold-start).** Keep. Strengthen: require ≥3 named first-time-seen elements with reasoning (§1.8).
- **MON-2 (severity defensible).** Strengthen with explicit clause taxonomy (critical=regulatory/safety/exec-named; high=strategic-competitor or sustained-negative; medium=product+demand; low=passing), cited per story (§1.4).
- **MON-3 (top development named + prioritized).** Split. "Named" (entity, dollar, timing) is one check; "prioritized" (volume-decoupled, §1.11) is another. Forces failing digests where everything is correctly named but ranked by volume.
- **MON-4 (who/when/consequence).** Strengthen. Add fourth field "consequence-of-inaction" with specific risk/opportunity (§1.6); add disqualifiers ("continue monitoring," "team," "soon").
- **MON-5 (compound narratives).** Keep, tighten anchor: ≥3 supporting signals + forward hypothesis + confidence (§1.7).
- **MON-6 ("so what" + missing signals).** Split. "So what" stays as pitfall (§3.7); "missing expected signals" becomes its own positive criterion (§1.13).
- **MON-7 (arc of prior digests).** Keep optional. Add forward-hooks (§1.10) as a separate optional.
- **MON-8 (word count ∝ importance).** Keep. Calibrate with 3:1 ratio between top-1 and rank-10 (§1.12).

### NEW criteria

**MON-9 Source faithfulness (essential, auto-cap).** Grades: quoted spans and cited URLs verifiably correspond to cited author/timestamp. 1: quote attributed to author/outlet that didn't say them or doesn't exist (digest capped at 1). 3: quotes real but timestamps/follower counts/engagement don't match source state. 5: all sampled quotes round-trip — verbatim text, correct handle, real timestamp, raw mention in source corpus. Verification: deterministic substring match against `monitoring.json` + URL resolution + handle existence.

**MON-10 Event canonicalization (essential).** Grades: same-event mentions collapse to one story with explicit primary/secondary. 1: same event as 4+ stories, count inflated by syndication, no `primary_source`. 3: partial clustering, URL overlap across top stories, ranking driven by count. 5: single story with `primary_source`, authority-ranked `secondary_sources[]`, `corroboration_count`, zero URL overlap across top-5. Verification: URL overlap check; MinHash ≥0.85 flags semantic dedup misses.

**MON-11 Author/source weighting (important).** Grades: stories carry weight rationale combining authority + amplification, not engagement alone. 1: engagement-only ranking; founder tweet at 50 likes below anon meme at 5K; no rationale. 3: `evidence_strength` numeric exists but reduces to engagement. 5: per-top-3 `source_weight_rationale` names role/authority + amplification separately; ≥1 below-median-volume story makes top-3. Verification: rationale fields + volume-rank check.

**MON-12 Stance-tagged contested stories (important).** Grades: mentions in rumor/breaking stories carry stance; verification status derives. 1: rumor as fact, no stance. 3: stance counted at story level only. 5: mention-level stance + derived `verification_status`; "no rumor-flavoured stories" acceptable. Verification: `stance` field on rumor-tagged mentions.

**MON-13 Channel diversity (important).** Grades: top stories triangulate platform-classes. 1: ≥90% mentions one class; top-3 all single-channel. 3: corpus multi-channel, top-3 skews to one. 5: top-3 touch ≥4 distinct classes; at most 1 single-channel top story. Verification: distinct values in top-3 `channels[]`.

**MON-14 Forward hooks (optional).** Grades: watch-next-week items with trigger + expected signal + target. 1: none, or "continue monitoring AI sentiment." 3: topics named, no triggers/targets. 5: ≥3 hooks with conditional triggers + named expected signals + specific monitoring targets. Verification: shape of `forward_watch[]`.

**MON-15 Missing-expected-signal callouts (optional).** Grades: surfacing expected-but-absent topics. 1: none. 3: generic absences without basis. 5: ≥1 named absence with expectation basis + hypothesis. Verification: shape of `expected_but_missing[]`.

### Calibration anchors

Each criterion's prompt references three anchor digests: 9-anchor (faithful quotes + canonicalized events + weighted sources + stance-tagged rumors + named compound narrative + named absences + forward hooks); 5-anchor (volume-cosplay opener + 62/28/10 sentiment + alphabetical-medium-list + "continue monitoring" recs); 1-anchor (single fabricated quote or non-existent outlet).

### Source-confidence note

Strongest evidence for faithfulness: Sprout's Proof-of-Reality product framing + Brand24's Capterra/Gartner sentiment-accuracy limitations. For canonicalization: Newsloth/Feedly engineering reports + MDPI event-detection review. For stance detection: ACM TIST 2026 + arXiv 2512.13559. Author/source-weighting and channel-diversity lean on industry consensus (Sprinklr, Hootsuite, Trigify), directionally established not laboratory-validated. Sprout tweets cited are low-engagement (300–1500 views typical) but the product-positioning content captures the articulated bar precisely.
