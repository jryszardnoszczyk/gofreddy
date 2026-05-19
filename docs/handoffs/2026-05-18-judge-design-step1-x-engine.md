---
date: 2026-05-19 v3.1
type: judge-design Step 1 — x_engine optimal-output spec
status: DRAFT v3.1 — post-verification surgical fix per `docs/handoffs/2026-05-19-x-engine-v3-verification.md`. §8 Q6 numerical-weight leak closed (the leak that v3 stripped from §5 had persisted verbatim in §8 Q6 of the same file). Spec-wide audit also strips remaining verbatim numerical weights from §3c CUTS list and §3d ADDS list. Zero verbatim numerical weights remain in the spec. All v3 architecture preserved (12-component bundle, 10 per-cycle increments, substrate-readiness gate, 5-criterion ceiling, X-1..X-5 criterion prose).
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
companions:
  - docs/research/2026-05-19-x-engine-comprehensive-scope.md (LOAD-BEARING — 30 surfaces, 12-component first-engagement bundle, 10 per-cycle increments, bundle-coherence judge BC-1..BC-5 sketch)
  - docs/handoffs/2026-05-19-x-engine-v2-spot-check.md (v3 surgical-edit source — adversarial audit findings)
  - docs/research/2026-05-18-judges-domain-x-engine.md (generalist x_engine domain research)
  - docs/research/2026-05-18-x-engine-algorithm-jan-2026.md (algorithm-signals axis)
  - docs/research/2026-05-18-x-engine-hook-discipline.md (hook discipline axis)
  - docs/research/2026-05-18-x-engine-voice-screenshot-test.md (voice / screenshot axis)
  - docs/research/2026-05-18-x-engine-ai-slop-detection.md (AI-slop detection axis)
revision_history:
  - 2026-05-18 v0 — initial 5-criterion skeleton with numeric algorithm weights in wrapper, em-dash/moreover/tricolon enumeration in X-5 score-0
  - 2026-05-18 v1 — Path-A iteration grounded in 4 deep-research deliverables. Stripped numerical weights from §5 wrapper → direction-of-effect language. Strengthened X-1 with 3-axis CoT. Reworked X-5 with gestalt-stack language, X-vs-LinkedIn register check, explicit cold-start sub-anchor. Routed em-dash / banned-phrase / tricolon / "Stop X. Start Y." / listicle-parallelism / link-suppression / hashtag enumeration OUT of judge into 6 structural_gate checks. Added 3 sample-and-flag telemetry signals. 5-criterion ceiling held.
  - 2026-05-18 v1-surgical — restored X-2 voice.md HARD FLOOR + X-5 jargon-gloss rule from live code at `fc99d64` per cross-check audit. Bracket-aware scoring and X-6 cross-cohort intentionally NOT restored at criterion layer; flagged §8.
  - 2026-05-19 v2 — School-B restructure per JR locked decision. **Judge layer UNCHANGED** at v1's 5 criteria (X-1..X-5) over the locked single-post or 3-12-thread artifact shape ("Component A"). **Lane scope EXPANDED** per `docs/research/2026-05-19-x-engine-comprehensive-scope.md`: lane v2 ships a 12-component first-engagement bundle (Component A judge-scored; Components B-L `structural_gate`-validated) plus 10 per-cycle increments after first engagement. §1 reader broadened beyond founder/indie to SaaS / AI lab / agency / service firm / finance / e-commerce + indie hacker; US-primary. §3 expanded with 20 cuts (modern-lever bias OFF old-school plays) and 24 adds (modern-lever bias ON 2026 platform surfaces — reply-discovery, Spaces, Communities, Articles, bookmark engineering, series-arc, etc.). §8 adds sibling-fork triggers (x_spaces / x_articles when demand crosses 3+ clients) and bundle-coherence-judge BC-1..BC-5 candidate (deferred to v3 candidate; only promote if first-engagement bundle coherence becomes load-bearing failure). Modern-lever bias throughout. Hard constraints preserved: 5-criterion ceiling held, no numerical weights, no AI-detector classifier output, X-1..X-5 prose unchanged, jargon-gloss + voice.md HARD FLOOR + 3-axis CoT preserved.
  - 2026-05-19 v3 — Option D surgical edits per spot-check audit (`docs/handoffs/2026-05-19-x-engine-v2-spot-check.md`). X-2 voice.md HARD FLOOR specified Component L as PREREQUISITE for first-engagement judging (cold-start undefined-behavior closed); cold-start sub-anchor at X-2 score-0.5 + CoT Step 3 emits 0.5 + "voice substrate not provisioned" when voice.md absent. §5 wrapper "do not re-add numerical weights" note softened to remove information leak (specific reconstructed numerals stripped from in-spec prose; direction-of-effect rationale retained). §1.5 Substrate-Readiness Gate added — 12-component bundle is SPEC TARGET; client-side shipping gated on substrate emission readiness, Component A ships at substrate-current, B-L ship as substrate emission catches up. §1 first-cohort overfitting clause: Polish + regulated-vertical first-cohort (Klinika, DWF) does NOT apply Components F/G/H as core deliverables. §8 I3 reply-judging deferred to v3.1 (>50% lane output un-judged at criterion layer accepted for v3; observe via variance instrumentation). §8 X-6 90% threshold reframed to falsifiable variance trigger (Axis C variance vs design-guide §11.5 redesign threshold). §3 modern-lever framing note added — CUTS/ADDS are LANE PRODUCT DNA expressing failure/success modes, not roadmap items. All v1 surgical-restoration content preserved. 5-criterion ceiling held. No new criteria. No scope reductions. No numerical weights re-added. No AI-detector classifier integration.
  - 2026-05-19 v3.1 — post-verification surgical fix. §8 Q6 numerical-weight leak closed (relocated leak from §5 to §8 stripped; operator-reconstructed action-class weight estimates referenced by name not number; same direction-of-effect discipline as §5 wrapper). Spec-wide audit confirms zero verbatim numerical weights remain.
---

# X Engine — Optimal-Output Spec (DRAFT v3)

Conforms to `docs/rubrics/judge-design-guide.md`. v3 supersedes v2 with **Option D surgical edits** per spot-check audit (`docs/handoffs/2026-05-19-x-engine-v2-spot-check.md`) — substrate-readiness gate, voice.md PRE-REQ for first-engagement judging, wrapper info-leak softened, first-cohort exemption for F/G/H, I3 judge-coverage deferral documented, X-6 promotion threshold reframed, §3 lane-DNA framing note. All v2 scope and v1 surgical-restorations preserved. v2 restructure from v1 was a **School-B restructure**: judge layer stays atomic at v1's 5 criteria (X-1..X-5) over the locked single-post-or-3-12-thread artifact shape (designated "Component A"); the lane's broader program components (profile audit, content strategy, reply-target list, DM templates, Spaces brief, Communities map, series-arc storyboard, measurement plan, 30/60/90 roadmap, cross-platform syndication rules, brand voice substrate — "Components B-L") are validated by `structural_gate` and optionally by a deferred bundle-coherence judge (BC-1..BC-5 candidate, §8). v1's load-bearing decisions are preserved without change: 5-criterion ceiling, direction-of-effect wrapper, 3-axis CoT on X-1, regime-aware X-5, jargon-gloss rule, voice.md HARD FLOOR on X-2, no AI-detector classifier output, no numerical algorithm weights in the wrapper, no anti-gaming clauses. Frameworks (Welsh, Cole/Bush, Naval, Bloom, Mack, Veerasamy, Hormozi, Schneider, Koe) inform the reader/success/failure spec and the judge's private reasoning toolkit; they do NOT appear by name in criterion prose.

v2 closes the v1 gap that lane scope was confined to a single ≤280-char post or 3-12-tweet thread — correct *for the judge* (shape-drift Goodhart is real) but incorrect *for the lane* (an X workflow that ships only those two shapes in 2026 leaves 80% of program value on the table per `docs/research/2026-05-19-x-engine-comprehensive-scope.md`). v2 expands the lane's deliverable architecture without expanding the judge's scope. The judge keeps scoping Component A atomically; `structural_gate` validates the broader program; the optional bundle-coherence judge (BC-1..BC-5) is held in reserve for v3 only if cross-component drift becomes a measured failure mode.

---

## 1. Reader (LOCKED 2026-05-18, REAFFIRMED 2026-05-19 v2 with broadened substitute set)

**Primary reader.** A power-user on X with Premium subscription, scrolling the For-You feed on a phone with ~0.5 seconds of attention per post: a topical-niche scroller (US-primary by default — B2B SaaS founder, AI lab researcher, agency principal, service firm partner, finance operator, e-commerce operator, or indie hacker) arriving via interest-graph fanout. About 50% of any For-You feed is out-of-network content surfaced by SimClusters + Grok-based candidate retrieval (per xai-org/x-algorithm Jan + May 2026 open-source release). Commitment to expand / reply / repost / bookmark / profile-click happens inside the first 400–700ms based on first-fixation lexical features; full-post read happens only if the opening earned that commitment. They are slop-aware — by mid-2026 most active power-users pattern-match AI-generated content and hit "not interested" (negative-signal cluster) on recognizable slop before the third line.

**Secondary reader: the algorithm.** Phoenix (Grok-1-derived transformer, candidate-isolated scoring per the open-source release) reads the post as semantic content — no separate hashtag-lookup table, no keyword-multiplier pipeline. It outputs ten action probabilities (favorite, reply, repost, quote, click, profile_click, video_view, photo_expand, share, dwell) combined via positive-and-negative-weighted summation. Reply, repost, bookmark, and long-dwell are heavily-positive; mute, block, "not interested," and report are heavily-negative. Phoenix also reportedly factors tone-of-voice via Grok-tone analysis (constructive / curious / positive distribution > combative / aggressive / negative). Primary and secondary readers align by design: the algorithm rewards what the scroller actually does, so a post that earns substantive scroller engagement earns algorithmic out-of-network fanout.

**Substitute readers the same post should also serve (broadened from v1's founder/indie-only set; US-primary defaults):** a peer practitioner in the niche who would substantively reply, quote-tweet with a real add, or want to disagree publicly; a 100k+-follower creator in the niche who would repost or copy-link to DM; an interest-graph adjacent scroller surfaced via SimClusters fanout (US-East / US-West tech-Twitter / AI-Twitter / DTC-Twitter / FinTwit / LegalTwitter / IndieHackers communities); an AI-aware reader who would recognize "generic founder voice" within one fixation and bail; a Communities-feed reader inside a topic-specific Community surfaced regardless of follower-count; a Premium-tier scroller (Premium-account fanout has +4× in-network / +2× out-of-network multiplier per Glitchwire May 2026 reconstruction). The substitute readers cover the 7 verticals enumerated in §4 of the comprehensive scope research — same artifact-shape Reader spec across SaaS / AI lab / agency / service firm / finance / e-commerce / indie. Vertical-specific reply-target graphs and Communities maps shift at the *strategy* layer (Component B-L); the *artifact* Reader spec stays universal.

**NOT the reader.** Bot accounts (negative signal source, not target); engagement-farming peers (artificial signal, not target); the author's first-degree network alone (golden-hour kick, not the goal — fanout requires winning second-and-third-degree out-of-network); a long-form reader from a blog (different commitment regime — they've already committed; the X scroller has not); a LinkedIn scroller (different platform register — authority-positioned broadcast, slower-tempo, lesson-extracting conclusive tone; X is peer-not-broadcast, punchy-not-narrative, contrarian-not-conclusive); a comms director (different decision shape — see monitoring lane).

**First-cohort overfitting watch.** The reader spec is research-grounded against English-language Anglosphere founder/operator/researcher voice (Naval, Bloom, Mack, Welsh, Schneider, Veerasamy, Graham, Andreessen, Karpathy, Husain, Levels, Vassallo, Lou as exemplars per §7 of the comprehensive scope research). gofreddy's first-cohort includes Polish-language operators (DWF lawyers, Klinika dermatology) where the architectural shape applies (peer-not-broadcast, punchy-not-narrative, schema-violation-as-hook) but specific lexical anti-patterns (em-dash conventions, discourse markers) need separate calibration. The criteria below test mechanisms that are language-universal at the cognitive-load level; the lexical surface enforcement in `structural_gate` is English-calibrated and needs a Polish-language fixture pass before locking. See §8 open-question 7.

**First-cohort overfitting — explicit Polish + regulated-vertical exemption (NEW in v3).** Polish + regulated-vertical first-cohort (Klinika, DWF) does NOT apply Components F (Spaces brief), G (Communities map), or H (series-arc storyboard) as core deliverables — these components ship for SaaS/AI/agency/indie clients where they apply. For Klinika (medical_pl rule set, b2c_aesthetics archetype) and DWF (legal_pl rule set, b2b_regulated archetype): Spaces hosting is regulatorily ambiguous (no settled professional-conduct guidance for live-audio public commentary in either vertical); Communities participation in English-language Build-in-Public / Indie Hackers / ML Twitter Communities is off-vertical; series-arc-as-public-build-in-public ("$5K to $20K MRR in 8 weeks") is structurally inapplicable to clinical and partnership-track legal practices. The bundle for Polish + regulated-vertical clients ships A + B + C + D (vertical-appropriate reply-target list) + E (warm-only DM templates) + I + J + K + L; Components F + G + H are marked N/A in the per-client bundle manifest with rationale captured per Component for portability when later clients in other verticals adopt the bundle. **Component A judging applies to all clients regardless of cohort** — the artifact-judge layer (X-1..X-5) is language-universal at the cognitive-load level per the previous paragraph, and the criteria below stay invariant across cohorts.

---

## 1.5. Artifact shape (LOCKED 2026-05-18, REAFFIRMED 2026-05-19 v2 at judge layer; LANE SCOPE EXPANDED at workflow layer)

**Judge-layer artifact shape is LOCKED at v1.** The judge scopes ONE of two artifact shapes for Component A — and only Component A — per practitioner literature converging on Veerasamy unit-of-consideration + Cole/Bush 1-3-1 rhythm + Naval thread-as-essay:

1. **Single X post** — one tweet, ≤280 chars, exactly one coherent claim that resolves within the post.
2. **Thread of 3–12 tweets** — opening tweet promises a trajectory; each subsequent unit instantiates one beat and reveals something the prior unit did not (Rate of Revelation per unit). Veerasamy's 3–7 typical, up to ~12 max.

**Locked because shape-drift Goodhart is a documented failure mode.** Under 50-generation selection pressure the workflow would learn that dense-single-post outputs score well on X-2 while expansive-thread outputs score well on X-4, producing Frankenstein artifacts (wall-of-text "threads" of 2 dense tweets; padded single-posts that should have been threads). The lock prevents this at the judge layer.

**LANE SCOPE EXPANDED at workflow layer (NEW in v2, per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §5).** The judge keeps scoping Component A at the locked single-post-or-3-12-thread shape. Beyond Component A, the lane v2 ships a broader **multi-component deliverable bundle** that captures the full surface of valuable X workflow activities in 2026. The lane produces:

**Substrate-readiness gate (NEW in v3).** The 12-component first-engagement bundle (A 5 sample posts/threads [judge core] + B profile audit + C content strategy + D reply-target list + E DM templates + F Spaces brief + G Communities map + H series-arc storyboard + I measurement plan + J 30/60/90 + K cross-platform syndication rules + L voice substrate) + 10 per-cycle increments (I1-I10) describes the COMPREHENSIVE workflow target. Component A ships at substrate-current — `session_eval_x_engine.py` reliably emits 5 sample posts/threads. Components B-L ship as substrate emission catches up: B (profile audit) when profile-shape extractor exists; C (content strategy) when pillar-extraction substrate exists; D (reply-target list) when target-account research substrate exists; E-L similarly require their own workflow tooling. Until each component's substrate emits, structural-gate validates Component A only. Per-cycle increments I3 (substantive replies), I7 (DM template instances), I10 (monthly measurement reports) emit at sustained-engagement phase, NOT first-engagement. Comprehensive scope is the SPEC TARGET; client-side shipping gated on substrate readiness.

### 1.5.1. First-engagement bundle — 12 components (delivered once per client at onboarding)

The first time the lane engages a client, it ships a bundle of 12 components. Component A is the judge's atomic scope (5 sample posts / threads judged per the locked 5 criteria); Components B-L are validated by `structural_gate` for shape + provenance + completeness, not by the artifact judge.

| # | Component | Judge route |
|---|-----------|-------------|
| A | 5 sample posts/threads (the current v1 judge scope — single post ≤280 chars OR thread 3-12 units; per-artifact independent scoring) | 5-criterion judge per artifact (X-1..X-5 below) |
| B | Profile audit — bio (≤160 chars, niche-claim + credibility marker + forward expectation), pinned tweet (3 candidate rotations), banner (1500×500, niche-reinforcing), profile photo (recognizable face for personal / clean logo for brand — personal-account-first default per A23), custom URL / handle consistency | `structural_gate` |
| C | Content strategy doc — 3-5 topic pillars (Welsh content-matrix grid: pillars × formats), voice plan (declarative-not-hedging, peer-not-mentor, lived-experience-not-summary, contrarian-not-conclusive), cadence + posting times (3-6 posts/day; 9 AM-1 PM Tue/Wed/Thu in ICP timezone), format mix (5-10 single posts + 1-2 threads + 5-15 substantive replies + 1-3 QTs + 0-1 Article per fortnight Premium+) | `structural_gate` |
| D | Reply-target list — 10-30 accounts in the client's niche meeting (a) >1 post/day cadence, (b) follower-count ≥10× client, (c) topically aligned, (d) reply-receptive; populated per vertical from §4 of the comprehensive scope research; per-account context (what they post about, what tone is welcomed, what reply-shape works) | `structural_gate` |
| E | DM templates — 5-7 use-case templates (cold outbound with warm-conversation-first prerequisite per §A15 / §1.16; warm inbound: thanks-for-following / response-to-question / response-to-collab-request / response-to-sales-pitch); each carries voice-substrate provenance | `structural_gate` |
| F | Spaces strategy brief — host decision (yes/no/co-host), cadence (weekly same-time recommended where applicable), format (founder Q&A / day-in-the-life / technical deep-dive / panel with 2-3 guests rotating from D), guest list draft, first month's 4 Space topics | `structural_gate` |
| G | Communities map — 5-10 X Communities the client should join + per-Community posting plan (typically 1-2 posts/week per active Community, <20% promotional per NealSchaffer 2026) + own-Community-creation decision if no existing Community covers the exact niche | `structural_gate` |
| H | Series-arc storyboard — first month's multi-post arc spanning 4-12 weeks (e.g., "$5K to $20K MRR in 8 weeks" for SaaS; "launching X over 6 weeks" for e-commerce; "research-thread-arc per paper" for AI lab); arc premise, weekly cadence commitment, arc-resolution promise | `structural_gate` (per arc-storyboard shape); per-post artifacts within the arc pass through judge as Component A |
| I | Measurement plan — 5-7 KPIs (profile clicks, substantive replies, bookmarks per thread, follower growth net of unfollows, DM inbound count, engagement velocity in first 30 min, Premium-tier-confound tracking per Q3), monthly report cadence, rotation thresholds (e.g., pillar X's posts hit 50% lower engagement than pillar Y over a fortnight → rotate pillar mix) | `structural_gate` |
| J | 30/60/90 execution roadmap — week-by-week deliverable cadence + founder-time commitment negotiation (engagement-velocity-first design per §A21 requires founder online for first 5-10 replies within 30 min of posting; non-delegable) | `structural_gate` |
| K | Cross-platform syndication rules — LinkedIn → X adaptation (extract 5-7 key beats from a LI essay, restructure as units-of-consideration thread, rewrite voice to peer-register, drop LinkedIn lesson-extracting conclusive tone); blog → X threads; X thread → LinkedIn carousel; per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §1.20 (repurpose-the-idea-not-the-text per PostBridge 2026) | `structural_gate` |
| L | Brand voice substrate — written record of voice posture + signature rhetorical moves + named entities the operator is licensed to reference first-person (operator-provided; stored at `programs/references/voice.md`; loaded as `source_data` parents[2] for the X-2 HARD FLOOR check) | `structural_gate` (voice.md provenance + completeness; X-2 HARD FLOOR fires judge-side off this substrate) |

### 1.5.2. Per-cycle increments — 10 categories (delivered after first engagement, steady-state cadence)

After the first-engagement bundle ships, the lane shifts into per-cycle increments — the steady-state stream of artifacts the lane produces against the strategy doc + measurement plan over weeks/months. Component A (sample posts/threads in the bundle) becomes per-cycle single posts + threads at the prescribed cadence; the other increment categories operationalize the broader program.

| # | Increment | Cadence | Judge route |
|---|-----------|---------|-------------|
| I1 | Single post drafts | 5-10/week | 5-criterion judge (Component A scope) |
| I2 | Thread drafts (3-12 units) | 1-2/week | 5-criterion judge (Component A scope) |
| I3 | Substantive replies — DH3-DH5 zone per Graham's "How to Disagree" hierarchy (DH3 contradiction-with-reasoning / DH4 counterargument-with-evidence / DH5 refutation); DH0-DH2 (name-calling / ad hominem / responding-to-tone) NEVER ship | 10-20/week | `structural_gate` (DH-zone deterministic check); reply shape gated by X-3 outcome-equivalence (substantive disagreement test) |
| I4 | Quote-tweet drafts with substantive add — of someone else's post (counter-take / extension / specific-knowledge reframe) or of own post (continuation arc / "X weeks later" / specific result update) | 1-3/week | `structural_gate` (QT-parent-context check) |
| I5 | Spaces recap thread (after each hosted Space) — 5-7 key takeaways from the conversation | weekly if hosting | 5-criterion judge (treated as a thread per Component A; lived-experience source is the Space itself, anchoring X-2) |
| I6 | Article drafts (Premium+ accounts only) — long-form prose up to 25k chars, X Articles surface, Google-discoverable | 0-2/fortnight | `structural_gate` (Article shape + headline anatomy + paragraph structure); same 5-criterion judge applies at the Article-shape-adjusted scope — X-1 hook operates on article-headline + first-paragraph level not first-7-words; X-2 carries extra weight (longer surface lets author go deeper); X-4 "form matches function" interpreted at Article scope |
| I7 | DM template instances (use-case specific instantiations of E) | on-demand | `structural_gate` (DM provenance + recipient-specificity check) |
| I8 | Pinned tweet rotation candidates | every 2-4 weeks | 5-criterion judge per candidate (Component A scope); rotation selection deterministic (best-performer-of-fortnight or specific-positioning-update or seasonal-relevance) |
| I9 | Series-arc per-post updates (within active arc from H) | weekly | 5-criterion judge per post (Component A scope); arc-coherence handled at `structural_gate` (post belongs to declared arc, advances arc by one beat) |
| I10 | Monthly measurement report (telemetry rollup per I from B-L bundle) | monthly | `structural_gate` (report shape + KPI coverage) |

### 1.5.3. Why this split (School-B locked decision)

The judge-vs-structural_gate split follows OpenRubrics' "Hard Rules → `structural_gate`. Principles → judge" formalization (arxiv 2510.07743) per design guide §1.2:

- **Component A (sample posts / threads / reply drafts / QT drafts / Spaces recaps / Article drafts / pinned-tweet candidates / series-arc per-post updates)** are subjective-quality outcome artifacts where the reader either does or doesn't tap / reply / repost / bookmark / dwell. These pass through the **5-criterion judge** at the locked single-post-or-3-12-thread artifact shape (Articles get shape-adjusted thresholds within the same 5 criteria).
- **Components B-L (profile audit / strategy doc / reply-target list / DM templates / Spaces brief / Communities map / series-arc storyboard / measurement plan / 30/60/90 roadmap / cross-platform syndication rules / brand voice substrate)** are workflow-doc deliverables with verifiable structure (does the bio fit 160 chars; does the strategy doc enumerate 3-5 pillars; does the reply-target list have 10-30 entries with per-account context; does the voice substrate trace to the operator). These pass through **`structural_gate`** for shape, completeness, provenance, vertical-appropriateness — not through the artifact judge.

Out-of-scope shapes for v2 (lane will NOT produce, judge will NOT score):
- Long-form essay or article cross-posted from blog (X-native register differs; X Articles via I6 covers Premium+ long-form natively)
- Screenshot-of-text post (photo_expand-dominant ranking regime; separate calibration needed)
- Image carousel
- Native video draft under 60s — video_view + 50%-completion signal lives in `structural_gate` if/when video drafts enter scope; out of judge scope for v2

**Shape enforcement lives in `structural_gate`, NOT in judge criteria.** Judge tests outcomes (X-1..X-5) on Component A only; `structural_gate` tests artifact-shape conformance (character count, thread unit-count band, thread reply-chain continuity) plus Components B-L bundle shape/completeness/provenance. Per design guide §11.1, this preserves outcome-question-not-feature-check discipline at the judge layer while still defending against shape-drift and bundle-incompleteness.

**Empirical validation scope.** Two-shape spec (Component A) is research-grounded against English-language Anglosphere founder/operator/researcher content. When fixtures from differently-shaped registers appear (Polish-language conversational, multi-language thread, post-with-quote-tweet-add), re-validate the form factor. 12-component bundle architecture (Components A-L) is research-grounded against the 7 verticals enumerated in §4 of the comprehensive scope research; vertical-specific bundle calibration (reply-target lists, Communities maps, Spaces briefs, DM templates) is per-vertical configurable.

**Sibling-fork triggers, not v2 scope (§8).** If Spaces hosting demand crosses 3+ clients with weekly cadence, fork an `x_spaces` sibling lane that scopes Spaces-as-primary-surface (title hook + description + co-host pairing + recap-thread bundle). If Articles long-form demand crosses 3+ clients with weekly Premium+ cadence, fork an `x_articles` sibling lane that scopes long-form X-Articles separately with shape-adjusted criteria. v2 keeps Articles + Spaces inside x_engine as I5 / I6 increments.

---

## 2. Success — what the reader DOES (LOCKED 2026-05-18, EXPANDED 2026-05-19 v2 with program-execution success)

### 2.1. Artifact-level success (Component A — unchanged from v1)

After ~0.5 seconds the scroller stops; after ~3 seconds they take an action: tap to expand, reply substantively, repost with conviction, bookmark, profile-click, or pause long enough for dwell-time to fire (long-dwell ≥2 minutes per the open-source release). The post earns a substantive reply (not "Great post!") from at least one relevant peer in the first 90 minutes (the engagement-velocity window Phoenix shrunk to 30 minutes per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §A21); that early substantive engagement drives algorithmic out-of-network fanout, which is where viral reach lives in 2026.

The post survives the screenshot test in the gestalt sense documented in the voice axis research: if a regular reader of this account encountered it in their feed without seeing the avatar, they would attribute it to this account specifically — not to "some founder." Generic founder voice (earnest, slightly conspiratorial, prescriptive, "what nobody tells you" framing) fails this test even when it earns first-day likes, because the second-fixation pattern-match by an AI-aware scroller recognizes the centroid voice and hits "not interested." Wang et al. EMNLP 2025 (arxiv 2509.14543) measures the mechanism: frontier LLMs default to an average generic tone under voice-imitation tasks, and few-shot demonstrations beyond ~10 give diminishing returns.

A peer in the niche would either repost without comment, quote-tweet with a substantive add, or want to disagree publicly. Posts that earn engagement-bait clicks ("Like if you agree," "Drop a 🔥") trigger Grok's `engagement_arbitrage` detector and the negative-signal cascade — these are NOT success even if they earn high impressions in the first 30 seconds.

**Sleep test.** If the scroller bookmarked and re-encountered the post 24 hours later, they would still find it worth their attention — the post's claim survives reflection, not just momentum. Posts that work on adrenaline but disappoint on re-read produce the bounce-after-hook gap that Phoenix's `engagement_arbitrage` penalizes.

**Bookmark-as-engagement-signal (NEW emphasis from v2 modern-lever bias).** Bookmarks carry materially-higher algorithmic weight than likes (direction-of-effect; specific operator-reconstructed coefficient deliberately not surfaced — same Goodhart-vector discipline as §5 wrapper; rationale lives in internal design notes per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §1.12). "Would a reader save this for later" is a first-class success axis. Bookmark-shaped artifacts: reference frameworks, dated playbooks, screenshot-survivable checklists, data tables, decision trees. Strategy doc (Component C) pre-commits ~20-30% of content mix to bookmark-shaped artifacts; the artifact judge X-2 (specific knowledge) partially captures bookmark-worthiness via the lived-experience anchor.

### 2.2. Program-level success (Components B-L + per-cycle increments — NEW in v2)

A v2 bundle is a success if, when the client takes it and runs it themselves for 30/60/90 days, the bundle gives them a defensible program to operate against — not just a stack of templates. Specifically:

- The client's **profile** (Component B) ships with niche-claim-plus-credibility bio + rotating pinned tweet (3 candidates) + niche-reinforcing banner; profile-click → follow conversion measurably uplifts vs prior state (XPatla 2026: well-optimized profile → 20-30% follow conversion uplift; Tweet Archivist 2026: 2× follow rate from the same content).
- The **strategy doc** (Component C) commits to 3-5 pillars the client can credibly own for 6-12 months before exhaustion, voice plan articulated explicitly, cadence calendar specific to ICP timezone, format mix that respects the 70/30 reply-to-original ratio (per §A4 / `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §1.6).
- The **reply-target list** (Component D) names 10-30 vertical-appropriate accounts the client can substantively reply to weekly; the client recognizes these as the accounts they themselves would target — not generic founder-Twitter accounts. The reply-discovery growth lever (500 → 12,000 followers in 6 months on 70/30 reply-to-original ratio per Teract 2026) is operationalized.
- **Spaces brief** (Component F) declares hosting cadence + format + first-month topics if Spaces is on-strategy for the vertical (HIGH for SaaS / AI / indie; MEDIUM for agency / finance; LOW for service firm). Single most-underused growth tool per NealSchaffer 2026; weekly cadence trains audience.
- **Communities map** (Component G) names 5-10 Communities + posting cadence; Communities are the pre-fanout discovery surface — topic-graph reach regardless of follower count.
- **Series-arc storyboard** (Component H) declares the first 4-12-week arc with explicit premise + cadence + resolution promise — the compounding-attention engine documented across Pieter Levels / Daniel Vassallo / Marc Lou exemplars per SOTA-9 / SOTA-10 / SOTA-11.
- **Measurement plan** (Component I) creates a closed feedback loop: artifacts ship → metrics measure → strategy updates → next artifacts ship. KPIs include the Premium-tier confound tracking so substrate doesn't misread distribution as quality (§8 Q3 per `docs/research/2026-05-19-x-engine-comprehensive-scope.md`).
- **30/60/90 roadmap** (Component J) explicitly negotiates founder time-commitment for engagement-velocity-first design — founder online for first 5-10 replies within 30 min of posting is non-delegable; bundle must surface this constraint.
- **Cross-platform syndication rules** (Component K) prevent voice-register mismatch when LinkedIn essays get repurposed to X (catches X-5 voice failure mode at upstream layer).

If the client takes a bundle and after 90 days has shipped 5-10 single posts/week + 1-2 threads/week + executed 10-20 substantive replies/week + run 4 Spaces + participated in 5-10 Communities + executed a 4-12-week series arc + iterated against the measurement plan — that is program-level success. Bundle that requires gofreddy operating it indefinitely is not hand-off-able and fails the differentiation lever (BC-5 candidate per §8).

### 2.3. World-class real-world exemplars (quality anchors, NOT templates to copy)

- **Naval Ravikant** — *How to Get Rich (without getting lucky)* canonical thread-as-essay (230k+ likes). Specific-knowledge claims compressed to 6-word declarative reframings. Voice signature recognizable across 200+ posts. Reference for X-2 + X-5.
- **Sahil Bloom** — Paradox / razor / framework one-liner pattern. 400k+ followers in 36 months; 700k+ by 2026. Uses tricolons + em-dashes substantively as foundational rhetoric. Reference for X-1 hook discipline + X-3 paradox-as-falsifiable-claim.
- **George Mack** — *High Agency* counter-stereotype framing. Schema-violation as primary hook shape. Reference for X-1 Axis B + X-3.
- **Visakan Veerasamy** — Prolific threader. Unit-of-consideration thread theory: 3-7 units typical, up to ~12 max; each unit a distinct move. Reference for X-4 (thread form-matches-function; Rate-of-Revelation per unit).
- **Justin Welsh** — Content Matrix framework (pillars × formats grid). 1M+ followers across X / LinkedIn. Reference for Component C strategy doc.
- **Dickie Bush + Nicolas Cole** — *Ship 30 for 30* curriculum. 1 Chip Rule + 1-3-1 Rhythm + Rate of Revelation. Reference for hook discipline (private reasoning toolkit, not in rubric prose).
- **Alex Hormozi** — Curiosity gap + hook-promise-deliver structure. Single-instance "Stop X. Start Y." rhetoric (the slop is reflexive density, NOT the construction itself). Reference for hook discipline + clickbait-avoidance.
- **Cody Schneider** — Documented 5,000 follows in 30-60 days via reply-strategy. "Expect ~20% follow-back from substantive replies on bigger-account threads." Reference for Component D + I3.
- **Pieter Levels (@levelsio)** — 600k followers over 10 years; $40-60M net worth; multi-product portfolio (Nomad List $3M ARR, Photo AI $132K MRR by month 18). Canonical build-in-public exemplar. Reference for Component H series-arc + indie hacker vertical.
- **Daniel Vassallo (@dvassallo)** — Small Bets portfolio in public. Build-in-public exemplar. Reference for indie / SaaS vertical.
- **Marc Lou** — TrustMRR + multi-product micro-SaaS in public. Newer-cohort (2024-2026) build-in-public exemplar.
- **Paul Graham (@paulg)** — Essay-shape on X Articles. Sentence-length distribution: 15-25-word essayistic with periodic 5-word punctuation. Reference for X-5 voice (specific-founder-idiolect signature) + I6 Articles.
- **Hamel Husain** — Domain-expert credibility on technical content. Specific-knowledge from lived ML/AI engineering. Reference for X-2 + AI lab vertical.
- **Andrej Karpathy (@karpathy)** — Technical-deep-dive thread shape; research-explainer Articles. Reference for AI lab vertical.

What ties these together: forward-vector hook in the first 7 words; specific knowledge from lived experience; falsifiable claim inviting substantive disagreement; form matched to claim density; voice that survives screenshot with attribution stripped; **bundle-of-program-execution** (Naval's thread-as-essay sits inside an essay arc; Bloom's one-liners sit inside the Framework Handbook; Levels's posts sit inside the Nomad List build-in-public arc; Welsh's posts sit inside the Content Matrix).

---

## 3. Failure — mediocre, Goodhart-collapse, and modern-lever cuts (LOCKED at v1 mediocre/Goodhart core; EXPANDED 2026-05-19 v2 with 20 cuts + 24 adds and 4 X-specific AI-slop families)

### 3a. Mediocre — four failure modes the judge must discriminate against (unchanged from v1)

**Generic founder advice.** Reads as competent X content — has a hook, a specific number, ends with a question — but every claim is the centroid of "founder advice" prose. No named entities the author was present for; no dated specifics; no first-person details that survive Naval's specific-knowledge test. Reader recognizes template within 0.5 seconds and scrolls.

**Hot take without evidence.** Strong claim ("Most founders are wrong about X") earns instant likes (low weight) but no substantive replies (high weight), and triggers high mute rate among readers who recognize provocation without substance. Net algorithmic value: negative. Mack falsifiability test catches this — the hot take is unfalsifiable because the underlying claim is too vague to be wrong on substance.

**Catalog / clip dump.** List of niche facts ("Acme raised $40M; Beta hired a CRO"). No claim, no implication, no forward-vector — competitor-monitoring log re-shaped as content. Nothing earns the next tap.

**Vulnerability theater.** "I failed at X. Here's what I learned." / "Last year I almost went bankrupt. Three lessons." Carefully calibrated admission of failure that feels authentic but isn't threatening; followed by exactly-3 numbered lessons where the failure is non-specific (no named entity, dollar amount, or date) and the lessons are platitudes. Reader's parasocial filter catches it within two fixations. "Performative pathless path" failure per Millerd / Stoddart.

### 3b. Goodhart-collapse — four named AI-slop families (per AI-slop deep research; unchanged from v1)

**Structural broetry.** "Stop X. Start Y." imperative-pair constructions stacked across a thread; every other tweet opens with negation-then-replacement antithesis. Endemic to AI-generated founder-advice content. Hormozi teaches the single-instance version; the slop variant is the *rhythm* — three of these in a 5-tweet thread is past any thoughtful operator's natural rate.

**Surface signature stack.** Em-dash density above account baseline + signature transitions ("moreover," "furthermore," "delve into," "in conclusion," "let me explain," "here's the thing") + three-element parallel constructions used reflexively + tricolons in every other paragraph. Any single tell is high-FPR against real operators (Naval uses em-dashes substantively; Bloom uses tricolons as foundational rhetoric); the slop fingerprint is the *stack* — 3+ co-occurring in a single post.

**Affective flatness.** Smooth, gradeless prose with no rough edges, no specific names, no dated claims, no commitments-with-cost. Cadence collapse — sentence-length variance compresses toward the 18–24-word AI-cadence plateau (Wang et al. EMNLP 2025 + 2026 burstiness stylometry consensus). Simulates authority but has not used a product or survived a failed launch.

**Algorithmic-affinity templating.** Phase 4 pathology rolled back at `c76f051`. Workflow learns to slot-fill surface markers: every post opens with a number or counter-intuitive declaration regardless of substance; every post namechecks a person with a fabricated quote; every thread is exactly 5 units; every post ends with a planted question to extract reply count; em-dashes get replaced with parentheticals (different surface, same model-collapse). Surface markers compliant, content underneath empty.

**Historical context.** This lane shares root pathology with the lanes that triggered three prior rollbacks: `2ce99bb` (σ-widening), `ca4a256` (v2 contract-prose), `698e658` (Phase 4 feature-checking → `c76f051`). Criteria below are designed to resist re-creating any of them AND to defend against the four AI-slop families above.

**Framing note (NEW in v3 per spot-check audit).** The 20 CUTS and 24 ADDS below are LANE PRODUCT DNA, not roadmap items. They appear in score-0 (CUTS) and score-1 (ADDS) anchors via the verifiable failure/success modes they describe, NOT as roadmap aspirations. The judge tests whether the artifact produces what an ADD describes or avoids what a CUT describes. CUTS routed to `structural_gate` are deterministic shape-checks the lane's gate filters upstream; CUTS absorbed into outcome criteria (X-2, X-3, X-4, X-5) are the failure shapes those criteria score against; ADDS that are product/strategy decisions (Component C/D/E/F/G/H/I/J cadence + targeting + format choices) inform the bundle's structural-gate shape checks, not judge prose. Treat §3c + §3d as the lane's articulated taste, not as a feature checklist for the judge to count.

### 3c. Modern-lever CUTS — 20 old-school plays that now backfire (NEW in v2 per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §2)

Each is explicitly suppressed by the 2026 algorithm + AI-slop pattern recognition. Most live in `structural_gate`; a few are gestalt judgments the artifact judge catches.

- **C1. Engagement-bait CTAs** — "Like if you agree," "RT if X," "Drop a 🔥," "Comment YES if," "Follow me for more." Grok-flagged as `engagement_arbitrage`; strongly-negative cascade per single negative reaction (direction-of-effect; specific operator-reconstructed coefficient deliberately not surfaced — same Goodhart-vector discipline as §5 wrapper). `structural_gate` literal-string match.
- **C2. Fake-vulnerability bait** — "I lost everything last year. Here's what I learned." / "I almost went bankrupt. 3 lessons." Composed-engineer voice; AI-slop Tier-2 structural signature. Artifact judge X-2 catches if no specific entity/dollar/date; `structural_gate` catches if confessional-opener + exactly-3 numbered bullets + abstract-failure shape.
- **C3. "Stop X. Start Y." imperative-pair rhythm** — endemic AI-generated founder-advice rhythm. Single instance is Hormozi rhetoric; 2+ in a 5-tweet thread is the slop signature. `structural_gate` regex.
- **C4. Em-dash density above account baseline** — GPT-4-family 3.28× human baseline (Goedecke 2025). >5 em-dashes per 100 words is the slop signature. `structural_gate` density check.
- **C5. Slop-transition phrase stack** — "moreover / furthermore / delve into / in conclusion / let me explain / here's the thing / let's be clear / it's worth noting / navigate the complexities / tapestry of / transformative / unleash / harness the power of / leverage (as verb)." `structural_gate` literal-string match (>2 phrases triggers).
- **C6. Reflexive tricolons** — three-element parallel constructions every other paragraph. Naval and Bloom use tricolons as foundational rhetoric; the slop is reflexive density. `structural_gate` syntactic-uniformity density check (>2 tricolons per thread).
- **C7. Hot takes without evidence** — "Most founders are wrong about X" with no falsifiable substance underneath. Mack falsifiability test catches. Artifact judge X-3.
- **C8. Generic motivational quotes** — "Consistency beats intensity." "Done is better than perfect." Centroid-voice platitudes. Fail X-2 + X-3 + X-5 simultaneously. Artifact judge.
- **C9. Hollow tricolons / parallel-listicle inflation** — "Build. Ship. Iterate." stacked without substance. Listicle syntactic uniformity >0.85. `structural_gate`.
- **C10. Throat-clearing openers** — "I've been thinking a lot lately about..." "There's something I want to share..." "Today I want to talk about consistency." First-7-words wasted on meta. Artifact judge X-1 Axis B + anti-pattern flag.
- **C11. Link-in-body posts** — 94% reach reduction for non-Premium since Q1 2026 (PPC.land); near-zero median engagement since March 2026. Workaround: link in first reply. `structural_gate` auto-rewrite.
- **C12. Multiple hashtags** — 3+ hashtags = ~40% reach reduction; 5+ = spam flag. `structural_gate` hashtag-count cap.
- **C13. Brand-account voice on personal account** — "At Acme, we believe in..." Personal accounts get materially-higher engagement than brand accounts (Conbersa 2026; direction-of-effect — specific multiplier not surfaced). Fail X-5 voice check. Strategy doc (Component C) defaults to personal-account-first.
- **C14. Quote-tweet-of-own-post-for-amplification only** — Grok-flagged as manipulation. Legitimate QT-of-self with new substantive context is allowed and encouraged (§I4); the cut is the *only*-pattern. Operator behavior, not artifact-level.
- **C15. Posting cadence over 10/day from a single personal account** — triggers spam-detection. Strategy doc caps at 6 posts/day; bursts allowed during launch / news events.
- **C16. Long-form essays cross-posted verbatim from blog / LinkedIn** — voice register mismatch. LinkedIn broadcast voice on X reads as imported and fails X-5. Cross-platform syndication ruleset (Component K) requires platform-adaptive rewriting.
- **C17. Numbered-list inflation** — "Here are 7 things..." with items 4-7 being restatements. Promise-inflation; bounce-after-hook gap fires. Artifact judge X-1 Axis C catches; `structural_gate` listicle-uniformity catches.
- **C18. Quote-tweet without substantive add** — a QT that just retweets-with-attribution. Adds no value; fails X-2 + X-3. Artifact judge.
- **C19. Cliffhanger that doesn't pay** — "The result will surprise you." Followed by ordinary content. Artifact judge X-1 Axis C.
- **C20. Bookmark-this CTAs** — "Bookmark this thread." Flagged manipulation. `structural_gate` literal-string match.

### 3d. Modern-lever ADDS — 24 surfaces worth pulling (NEW in v2 per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §3)

Each lever is grounded in 2026 algorithm signals OR 2025-2026 named-practitioner evidence. The lane bakes these into the strategy doc / artifact production / bundle composition. ADD count > CUT count by design (modern-lever bias toward 2026 platform surfaces).

- **A1. First-7-words discipline** — forward-vector hook with first-fixation-survivable tokens (named entity / specific number / concrete noun / schema-violation). Already in X-1.
- **A2. Specific-knowledge claims from lived experience** — Naval / Mack / Bloom / Schneider exemplars. X-2 anchor. Voice substrate (Component L → `programs/references/voice.md`) loads operator-specific anchors.
- **A3. Falsifiable claims peers can substantively disagree with** — X-3 anchor. Strategy doc commits 30-40% of original posts to falsifiable claims.
- **A4. Reply-discovery as primary growth lever** — 70/30 reply-to-original ratio (Teract 2026). Component D + I3. **Highest-ROI lever in 2026** — operationally more impactful than any single-post optimization.
- **A5. Quote-tweets with new substantive context** — §I4. 4-of-top-10 highest-performing posts per OpenTweet 2026 case data come from QT-of-self with new context. Distinct artifact shape.
- **A6. Bookmark-engineering — reference / playbook / checklist content** — §2.1 NEW emphasis. Materially-higher algorithmic weight than likes (direction-of-effect; specific coefficient not surfaced). Strategy doc commits 20-30% of content mix to bookmark-shaped artifacts. Lane learns which formats earn the most bookmarks per client across generations.
- **A7. Build-in-public weekly cadence** — Pieter Levels / Daniel Vassallo / Marc Lou exemplars. Component H + I9. Vertical-conditional (HIGH for SaaS / AI / indie / e-commerce; MEDIUM for agency; LOW for service firm / finance).
- **A8. Series-arc threading over 4-12 weeks** — Component H. Compounding-attention engine. Series premise must be compelling, cadence must hit, resolution must deliver. **Bundle-coherence-judge candidate** (BC-1..BC-5 §8) would score arc separately from per-post.
- **A9. Spaces hosting on weekly cadence** — Component F + I5. Single most-underused growth tool per NealSchaffer 2026 + KickoffLabs 2026. Co-hosting with larger guests pulls their audience.
- **A10. Communities participation (5-10 active per client)** — Component G. Topic-graph fanout regardless of follower count. The pre-fanout discovery surface.
- **A11. Premium subscription for any client targeting >100 impressions/post** — operator-action document (per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §1.9). +4× / +2× structural multiplier. ROI-positive at $8/month.
- **A12. Premium+ + Articles for any client where long-form is on-strategy** — I6. $1M X Writing Contest signals platform priority. Articles get Google discoverability.
- **A13. Public-list relationship-building** — "Best [Industry] Voices" list named publicly; each add notifies the account; some follow back. Low-effort high-leverage.
- **A14. Pinned tweet / thread rotation every 2-4 weeks** — I8. Best-performer-of-fortnight pins.
- **A15. DM warm-up sequence before outbound** — Component E. 2-3 weeks of substantive replies → DM. 30-50% reply-rate uplift founder-led vs SDR-led.
- **A16. Cross-platform adaptive rewriting (not verbatim)** — Component K. LinkedIn → X requires voice register conversion.
- **A17. ICP-timezone-aware posting calendar** — Component C cadence section. 9-11 AM Tue/Wed/Thu in client's ICP timezone, not operator's.
- **A18. Reciprocity calendar with 5-10 peer-creator accounts** — Component D adjacent. Engagement reciprocity effect documented across all 6 major platforms (Buffer 2026).
- **A19. Topic Authority 6-month roadmap** — Components C + H + D align. Pillar consistency + lived-experience + peer-engagement + bookmark-by-niche-readers. Measurable at 6 months.
- **A20. Constructive-tone band ("contrarian-not-combative")** — Grok-tone analysis rewards constructive distribution; substantive falsifiability is fine; combative-empty hot takes are suppressed.
- **A21. Engagement-velocity-first design** — Phoenix shrunk post-evaluation window to 30 minutes. Strategy doc commits operator to engage with first 5-10 replies within 30 minutes; founder-led; not delegable. Component J explicitly negotiates.
- **A22. Long-form Articles with Google-search discoverability** — I6. Long-form is the 2026 inflection point. X is becoming a search-and-discovery surface (Econsultancy 2026).
- **A23. Founder-account-first over brand-account** — Personal accounts carry materially-higher engagement than brand accounts (Conbersa 2026; direction-of-effect — specific multiplier not surfaced). Brand account as secondary aggregator, not primary.
- **A24. Measurement-driven pillar rotation** — Component I. Each pillar's posts tracked; bottom-performing pillars rotated out at 6-week marks.

### 3e. Deterministic AI-slop checks live in `structural_gate`

Em-dash density >5/100w, signature-phrase blocklist, tricolon density, "Stop X. Start Y." regex, listicle-syntactic-uniformity above 0.85, external-link-in-body suppression flag (94% reach reduction per Q1 2026 PPC.land A/B data), >2 hashtag count. Per OpenRubrics (Hard Rules → `structural_gate`, Principles → judge): deterministic verification belongs in `structural_gate` because (a) the judge cannot enumerate features without inviting feature-checking, (b) deterministic checks fail closed with low FPR against real operator voice, (c) workflow has to evade all 7 checks simultaneously to game the gate, (d) gestalt judge catches the residual stack. **AI-detector classifier output (GPTZero, Originality.ai, BERTweet) is NOT integrated** — Dawkins et al. 2025 (arxiv 2506.09975) measures 54% detection on fine-tuned voice models; 15.6–17.6% FPR disproportionately penalizes non-native English writers (core to first-cohort).

---

## 4. Criteria — outcome questions (5, judge layer UNCHANGED from v1)

The 5 criteria below scope **Component A only** — single X post (≤280 chars) or thread of 3–12 tweets. Components B-L of the bundle are validated by `structural_gate` (§1.5.3), not by these criteria. Per-cycle increments I1-I9 (single posts, threads, replies, QTs, Spaces recaps, Article drafts within shape-adjusted thresholds, pinned-tweet candidates, series-arc per-post updates) all pass through these same 5 criteria at the Component A scope; I7 (DM templates) and I10 (monthly measurement reports) route to `structural_gate`, not the artifact judge.

Modern-lever bias additions appear only as score-1 anchor expansions or examples — never as feature checks. The criterion prose itself is unchanged from v1.

### X-1 — Earns the next tap from a relevant scroller (hook discipline, 3-axis CoT)

**Outcome question (binary):**
Would a relevant X power-user — scrolling For-You at 0.5s/post, first-fixation commitment in 400–700ms — stop on this post and tap to expand, reply, repost, bookmark, or pause for dwell? And does the body deliver the specific gap the opening promised, rather than over-promising and producing the bounce-after-hook cliff?

**Score 1 (yes)** — The opening (first 1–2 sentences for a single post; opening tweet for a thread) opens a specific, bounded, finitely-closeable information gap the reader's brain commits to closing. It anchors first-fixation via ≥1 named entity, specific number, concrete noun, or schema-violating juxtaposition — and does NOT instantiate the topic-statement anti-pattern ("Today I want to talk about X") or the throat-clearing anti-pattern ("I've been thinking lately about Y"). The body delivers the gap: for single post, gap closes within the post; for thread, opening promises a trajectory and each subsequent unit instantiates one beat.

Example A (do not optimize toward this): "Seek wealth, not money or status." Six words; three named referents; forward-vector is the bounded question "what's the difference?" Body delivers by re-defining wealth as "assets that earn while you sleep" — gap closes specifically.

Example B (do not optimize toward this): "Pinsent Masons pulled 6 partners from CMS in May." Named entity + specific number + dated event; forward-vector is "what does this mean for our practice?" Thread delivers the lateral-flight analysis its first tweet promised.

**Score 0 (no)** — Opening instantiates topic-statement, throat-clearing, vague-promise ("Here's something that changed my life"), or cliché closed-loop ("Most people don't realize how important consistency is"). OR opening anchors first-fixation correctly but body fails to deliver the promised gap: hollow superlative (ordinary advice underneath); fake-revelation tease (contrarian framing was a vehicle for conventional content); numbered-list inflation (items 4–7 are restatements); cliffhanger-that-doesn't-pay; vulnerability bait. Bounce-after-hook gap fires.

**Score 0.5 (unknown)** — Opening framing depends on context not in the artifact (reply to unseen post, quote-tweet of unseen context). Emit 0.5 + "unknown" + one sentence on what context would resolve it.

**Required CoT (3 axes):**
- Step 1 (Axis B — first-fixation-survivable opening): Identify the opening (first ~7 words ±2 for single post; opening tweet for thread). Tag tokens as first-fixation-survivable (named entity, specific number, concrete noun, mid-narrative action verb, schema-violating juxtaposition) or abstract (motivational noun, hedge, topic-statement framing, throat-clearing). Flag topic-statement and throat-clearing anti-patterns.
- Step 2 (Axis A — forward-vector presence): Determine whether sentence two / tweet two is (a) predictable from the opening (cliché — fail), (b) unconstrained (vague promise — fail), or (c) bounded-but-unresolved (working hook — pass). Gap must be specific, bounded, finitely closeable (~3–15 words of resolution).
- Step 3 (Axis C — hook-body alignment): Identify what specific gap the opening promised. For single post, does the body close that specific gap? For thread, do subsequent units instantiate the promised trajectory (Rate of Revelation per unit)? Flag clickbait: hollow superlative, fake revelation, numbered-list inflation, cliffhanger that doesn't pay, vulnerability bait.
- Step 4: Emit verdict + one-sentence justification. Score 1 only if all three axes pass.

Do not score: hashtag count, emoji, formatting, exact character count (those live in `structural_gate`). Do not score literal first-7-words as a threshold — it's a working approximation the CoT applies as private reasoning.

### X-2 — Carries specific knowledge only this author could write

**Outcome question (binary):**
Would a relevant practitioner reading this post recognize it as written by someone with lived experience — not summarized from secondary sources, not regenerable from public-internet summarization?

**Score 1 (yes)** — Contains ≥1 specific detail (named person, dated event, specific number with provenance, unique anecdote, named project, specific failure with named context, dollar amount with attribution) demonstrating the author was present for the underlying experience. Claim cannot be regenerated by an LLM reading the public internet — required first-hand exposure.

Example A (do not optimize toward this): "Cody Schneider's '5,000 follows in 30–60 days, expect ~20% follow-back' is specific because he ran the experiment on his own account and published the result with numbers."

Example B (do not optimize toward this): "When I rolled out our SOC2 prep flow last quarter, 7 of the 12 customers said 'finally — the BambooHR compliance bundle requires us to do this manually'." Named entity + specific number + first-person observation.

**Score 0 (no)** — Every claim could appear in any productivity-niche post. No named entities the author was present for; no dated specifics; no first-person details. Generic platitude framed as wisdom. OR specific-looking details that are confabulated: fabricated quotes, made-up "Stanford 2023 study," conflated entities, dated events that don't exist (documented LLM failure mode). **HARD FLOOR (substrate-provenance gate):** any first-person specific lived-work claim REQUIRES the named entity (person, project, client, dated event, specific number's source) to appear in the voice substrate at `programs/references/voice.md` loaded into `source_data`. Lived-work claim with a named entity that does not trace to the voice.md substrate scores 0 even if the claim is plausible — provenance must be in-substrate, not LLM-generated. This is a JR-iterated structural gate carried over from live code (`load_source_data` loads `programs/references/voice.md` as `parents[2]` specifically so this check can fire judge-side). The Component L brand voice substrate in the bundle (§1.5.1) is where this substrate is authored; `structural_gate` verifies provenance + completeness of Component L at bundle level; the judge fires the HARD FLOOR off the substrate at scoring time.

**Score 0.5 (unknown)** — Single-line aphorism where lived-experience claim is ambiguous (could be quote-tweet, could be generic platitude, could be earned reframing). Emit 0.5 + "unknown" + one sentence. **Voice substrate not provisioned (NEW in v3, Component L PRE-REQ gate):** if `programs/references/voice.md` is absent from `source_data` or empty, emit 0.5 + "unknown" + "voice substrate not provisioned — judge cannot score lived-experience claims against ground truth." This closes the cold-start chicken-and-egg: Component L (voice substrate) is a PREREQUISITE for first-engagement Component A judging at X-2; if the substrate doesn't exist, X-2 abstains rather than scoring 0 by default (which would force the workflow to strip lived-work specifics) or scoring 1 without verification (which would invite confabulation). The bundle's internal ordering is: Component L populates first (operator-provided substrate authoring), THEN Component A's 5 sample posts are judged against the populated substrate.

**Required CoT:**
- Step 1: List every specific entity, number, date, named project, or first-person anecdote.
- Step 2: For each, test whether the claim is non-regenerable from public-internet summarization. Flag specific-looking details reading as confabulated (no attribution, no resolvable provenance, conflated entities, non-existent dated events).
- Step 3: For any first-person specific lived-work claim, verify the named entity appears in the voice substrate (`programs/references/voice.md` segment of `source_data`). **PRE-REQ check (NEW in v3):** if voice.md is absent or empty in `source_data`, emit 0.5 + "unknown" + "voice substrate not provisioned — judge cannot score lived-experience claims against ground truth" for the whole criterion; do NOT apply HARD FLOOR in this state. If voice.md is populated AND a lived-work claim names an entity that is NOT in the voice substrate, score 0 — HARD FLOOR fires regardless of whether the claim is plausible elsewhere.
- Step 4: Emit verdict + one-sentence justification.

Do not score: total word count, presence of "I" pronouns, claim accuracy (judge can't verify; confabulation flagging is pattern recognition, not fact-checking).

### X-3 — Asserts something falsifiable a peer could substantively disagree with

**Outcome question (binary):**
Could a thoughtful peer in this niche say "I disagree, and here's why" — substantively, not stylistically? Is the claim wrong in at least one knowable way a peer could articulate?

**Score 1 (yes)** — Position contradicts at least one widely-held belief in its niche, OR claims a specific causal relationship the reader could test against their own experience, OR makes a falsifiable forward prediction. Claim is wrong in at least one knowable way — peer could write a substantive counter-thread, not just a stylistic complaint. Disagreement would be about substance (causal model, empirical claim, strategic prescription), not surface (tone, formatting, example choice).

Example A (do not optimize toward this): "Low-agency people are passengers in their own lives" — testable against any reader's autobiography; peer could substantively disagree by arguing low agency is structural rather than dispositional.

Example B (do not optimize toward this): "Most B2B newsletters that hit 1,000 subscribers got there by reposting LinkedIn content to email, not by building from email-first." Specific causal claim; peer could disagree by citing email-first newsletters that grew without LinkedIn repurposing.

**Score 0 (no)** — Unfalsifiable: tautology, generic platitude, claim so hedged no one could substantively disagree, manufactured controversy where the "disagreement" invited is stylistic. Earns likes, earns no substantive replies. Triggers high mute rate among readers who recognize provocation without substance.

**Score 0.5 (unknown)** — Falsifiability cannot be evaluated without knowing the account's prior positions (claim might be radical for this author and conventional for others); OR post is reply/quote-tweet where the parent context carries the load. Emit 0.5 + "unknown" + one sentence.

**Required CoT:**
- Step 1: Identify the central claim.
- Step 2: Test whether a thoughtful peer could substantively disagree on substance — not stylistically, not on tone, not by criticizing example choice, but by arguing the underlying causal model or empirical claim is wrong.
- Step 3: Emit verdict + one-sentence justification.

Do not score: claim controversy level, "controversial opinion" markers, presence of "what do you think?" CTA (engagement-bait CTAs routed to `structural_gate`), whether the claim is actually true.

### X-4 — Form matches function — single post or 3–12-unit thread, no padding

**Outcome question (binary):**
Does the post's structure (single post vs thread) match the density of its claim? Does each unit earn its place — would removing any unit degrade the post?

**Score 1 (yes)** — Either (a) a single post under ~280 chars containing exactly one coherent claim that resolves within the post, OR (b) a thread of 3–12 tweets where each tweet reveals something the prior tweet did not (Rate of Revelation per unit). Removing any unit would degrade the post or break the promised trajectory.

Example A (do not optimize toward this): A 6-word Naval-style declarative reframing that condenses a 5000-word essay; single-post form earned because expansion would dilute.

Example B (do not optimize toward this): A 7-unit Veerasamy thread on courage where each unit is a distinct move (define, exemplify, counter, anchor, generalize, test, close); removing unit 4 breaks the trajectory.

**Score 0 (no)** — Either (a) single dense post burying a multi-claim argument no scroller will parse — wall-of-text without 1-3-1 rhythm; OR (b) thread padding one insight across 8+ tweets with restated points and connective tweets that reveal nothing (promise-inflation). Padded threads produce the dwell-completion drop documented in Phoenix's `engagement_arbitrage` detector.

**Score 0.5 (unknown)** — Intended distribution (single post vs thread, X-native vs cross-post) ambiguous from artifact. Emit 0.5 + "unknown" + one sentence.

**Required CoT:**
- Step 1: Identify the post's form (single post / thread of N units).
- Step 2: For single posts, test whether claim density fits 280 chars (no buried multi-claim argument). For threads, walk each unit and test whether it reveals something the prior unit did not — Rate of Revelation applied per-unit, not as a sum.
- Step 3: Emit verdict + one-sentence justification.

Do not score: specific unit-count as target (always-5, always-7 templating fails this), exact character count, thread-length conventions.

### X-5 — Survives the screenshot test in the account's voice (gestalt, regime-aware)

**Outcome question (binary):**
If the avatar and handle were stripped, would a regular reader of this account — encountering the post in their feed — recognize it as the author's voice and attribute it to this account specifically (not "some founder")? Or does it read as machine-finished prose anchored in the generic-niche-attractor cadence — the centroid of "founder X voice" belonging to no specific person?

**Score 1 (yes)** — In **data-rich regime (≥30 prior posts in `source_data`)**: voice consistent with the account's established empirical register (cadence, vocabulary mode, posture, joke-to-seriousness ratio, signature rhetorical moves) AND no AI-slop signature stack triggers (no 3+ co-occurring Tier-1/2 tells — em-dash density past account baseline + signature transitions + reflexive tricolons + "Stop X. Start Y." + listicle parallelism + false-vulnerability shape). Draft reads as in-the-X-conversation (peer-to-peer, in-the-moment, punchy) rather than imported from a different register (LinkedIn broadcast, blog narrative, "lesson-extracting" conclusive tone). Post would be screenshottable with author's name re-attributed and still read as theirs.

In **cold-start regime (<30 prior posts)**: prose is not recognizable as machine-finished to an AI-aware reader (no centroid-voice cadence collapse, no slop-stack triggers) AND draft is consistent with the account's stated positioning in `source_data` (bio, declared niche, stated topic focus). Slop-absence + positioning-consistency replaces empirical voice-match. Addresses Wang et al. EMNLP 2025 plateau finding (few-shot beyond ~10 gives diminishing returns) and the `linkedin_engine v040 cold-start mutation` precedent.

**"Looks like slop but isn't" defense.** Real operators legitimately use the surface markers that AI-slop detection enumerates. Naval uses em-dashes substantively (his "Seek wealth, not money or status" is a tricolon). Bloom uses paradox-and-tricolon as foundational rhetoric. Mack uses counter-stereotype + antithesis as core moves. The slop signal is the *stack* — 3+ Tier-1/2 tells co-occurring — NOT any single tell in isolation. A post with one em-dash, one antithesis, and one substantive claim is not slop; a post with em-dash-every-line + "Stop X. Start Y." + reflexive tricolons + "moreover" + parallel-listicle is slop. Judge tests gestalt, not feature presence.

Example A (do not optimize toward this): Naval's 6-word openings where rhythm + lexical mode + posture (declarative-reframing, lower-status, peer-not-mentor) all match across 200+ posts. New draft in that pattern with substantive content scores 1.

Example B (do not optimize toward this): Bloom's paradox-as-headline with tricolon — uses three slop-adjacent features substantively. Score 1 because the stack is rhetoric not template.

**Score 0 (no)** — Voice mismatches account's prior register (sober technical account posting Hormozi-style heat); reads as LinkedIn-shape imported to X (authority-positioned, narrative, "the lesson is X" conclusive framing rather than peer-not-broadcast, punchy-not-narrative); OR reads as machine-finished (generic-niche-attractor cadence, 18–24-word sentence-length plateau, no specific person's idiolect surface); OR triggers 3+ AI-slop signature stack tells co-occurring (the gate filters most upstream — if the judge sees a draft with this stack, the gate missed a residual and the judge catches it); OR opens with template phrases anchoring a known LLM register ("Here's the thing nobody tells you about," "Most people get this wrong," "Stop X. Start Y." rhythm); OR uses jargon without inline plain-English context. **Jargon-gloss rule (JR-iterated accessibility floor, carried over from live code):** technical jargon (acronyms, niche terminology, insider shorthand) appearing without inline plain-English gloss caps this dimension — the JR voice anchor is "accessible to a non-engineer founder/marketer," and unglossed jargon breaks that contract regardless of whether the rest of the voice register matches. A post can mention SOC2, ARR, ICP, MEDDIC, or RAG, but the first use must carry enough surrounding context that a non-engineer founder/marketer reading the screenshot understands what's being claimed.

**Score 0.5 (unknown)** — Data-rich: voice consistency borderline and slop-absence ambiguous from artifact alone. Cold-start: stated positioning itself absent from `source_data` AND prose is borderline. Emit 0.5 + "unknown" + one sentence.

**Required CoT:**
- Step 1: Identify the account's register from prior posts in `source_data` (cadence, vocabulary mode, posture, signature rhetorical moves). If <30 prior posts, switch to cold-start: identify stated positioning from `source_data` bio/niche/topic-focus. Form a one-sentence private description; do NOT enumerate features as a checklist.
- Step 2: Test whether the draft reads as in-the-X-conversation (peer-to-peer, in-the-moment, punchy, contrarian-not-conclusive) versus imported from a different register (LinkedIn broadcast, blog narrative, "lesson-extracting" mentor tone). X-vs-LinkedIn discriminator defends against the most-common cross-platform voice failure in repurposed founder content. Also apply the jargon-gloss check: identify any technical jargon (acronyms, niche terminology, insider shorthand); for each first use, verify inline plain-English context exists. Unglossed jargon caps this dimension — JR's voice anchor is accessible-to-non-engineer-founder/marketer, and unglossed jargon breaks that contract.
- Step 3: Test the draft for AI-slop signature *stack* — ≥3 of the named tells (em-dash density past account baseline, signature transition phrases, reflexive three-element parallel rhythm, "Stop X. Start Y." imperative-pair, false-vulnerability shape, listicle syntactic parallelism, cadence collapse toward 18–24-word plateau) co-occurring. NOT presence-of-any-single-tell. Apply "looks like slop but isn't" defense — sparse use of em-dashes / antithesis / tricolons is rhetoric.
- Step 4: Emit verdict + one-sentence justification.

Do not score: emoji in isolation, formal vs casual register on its own, any specific punctuation in isolation, AI-detector classifier output (not integrated — see §3e rationale).

---

## 5. Shared judge-prompt wrapper (direction-of-effect language, NO numerical weights — UNCHANGED from v1)

```
You are scoring an X (Twitter) post draft for a power-user
scrolling the For-You feed in 2026. The reader has roughly 0.5
seconds of attention per post; they commit to expanding,
replying, reposting, bookmarking, or profile-clicking inside
the first 400–700ms based on first-fixation lexical features,
then read the full post only if the opening earned that
commitment. They are slop-aware — they recognize generic
founder voice within two fixations and hit "not interested."

The post must work for the scroller (would they tap, reply,
repost, bookmark, dwell, profile-click?) AND for the algorithm,
which rewards substantive replies, conviction-level reposts,
save-for-later bookmarks, and long-dwell — and heavily
penalizes mutes, blocks, "not interested," and reports. These
align by design: the algorithm rewards what the scroller
actually does, so a post that earns substantive scroller
engagement earns algorithmic out-of-network fanout.

The draft is the lane's locked artifact shape: a single X post
(≤280 chars, one coherent claim that resolves within the post)
or a thread of 3–12 tweets where each tweet reveals something
the prior tweet did not. This is "Component A" of the lane's
broader bundle deliverable; only Component A is in scope for
this judge. Other bundle components (profile audit, strategy
doc, reply-target list, DM templates, Spaces brief, Communities
map, series-arc storyboard, measurement plan, 30/60/90 roadmap,
cross-platform syndication rules, brand voice substrate) are
validated by structural_gate, not by this judge.

Score each criterion independently with 0, 0.5, or 1 plus a
one-sentence rationale following the per-criterion CoT steps.
Do not blend criteria. Do not infer criteria not stated. If a
criterion's condition is ambiguous from the draft alone, emit
0.5 + "unknown" + one sentence on what context would have to
be present to commit to 1.

A relevant practitioner in the account's niche should
recognize this as written by someone with lived experience.
The post should earn a substantive reply (not "Great post!")
from a peer; it should survive the screenshot test with the
avatar stripped and handle re-attributed. Score for OUTCOMES
on the scroller and the algorithm — not for the presence of
named frameworks, specific punctuation, template opener
shapes, or named surface markers.

Emit per-criterion JSON:
{"criterion_id": "X-N", "rationale": "...", "score": 0 | 0.5 | 1}.
```

**Note on stripping numerical weights (carried over from v1, REAFFIRMED in v3 with information-leak softening).** Numerical algorithm weights are stripped from this wrapper as documented elsewhere; do not re-add. Direction-of-effect language provides the judge with sufficient orientation. The rationale, kept lightweight to avoid pointing at unscored-but-predictive signals: operator-community reconstructions of action-probability coefficients are not official, anchoring on them invites Goodhart template-fitting against the named numerals, and the formula template (ten-action probability set + positive-and-negative-weighted summation) is sufficient for the judge to evaluate outcomes without coefficient anchoring. Detailed rationale lives in internal design notes (`docs/research/2026-05-19-x-engine-comprehensive-scope.md` §1.12 captures the reconstructed numerics for reference; that file is NOT load-bearing for criterion design and should not be ingested as substrate by the lane's workflow prompts).

**Note on Component A scoping in the wrapper.** v2 adds one sentence to the wrapper making explicit that only Component A (single post or 3-12 thread) is in the judge's scope. This protects against scope-drift where the workflow might attempt to feed bundle components B-L through the judge — which would invite the feature-checking pathology the design guide explicitly prohibits. The judge's scope is artifact-atomic; the bundle is structural_gate-validated.

---

## 6. Goodhart-resistance verification

Each criterion resists a specific Goodhart-collapse mode named in §3:

- **X-1**: "Templated specific-number + counter-intuitive declaration opener" doesn't pass — Axis B catches the opening as anchored, Axis A catches the body if the gap is closed-loop or unbounded, Axis C catches the body if it over-promises or under-delivers (clickbait failure). All three axes must pass.
- **X-2**: Fabricated specifics don't pass — lived-experience claim must be non-regenerable; CoT tests for confabulation patterns. **HARD FLOOR via Component L voice substrate** prevents named-entity confabulation: any first-person specific lived-work claim must trace to `programs/references/voice.md` (loaded as `parents[2]` of `session_dir` via `load_source_data`).
- **X-3**: Manufactured controversy doesn't pass — falsifiability requires the claim could actually be wrong on substance. Hot-takes-without-evidence fail because the disagreement invited is stylistic, not substantive.
- **X-4**: Always-5-units, always-7-units thread templating doesn't pass — Rate of Revelation is per-unit, not summed. Unit-count is incidental.
- **X-5**: Avoiding em-dashes by replacing with parentheticals doesn't pass — AI-slop is a *stack*, not a single tell; judge tests gestalt at 3+ co-occurring. LinkedIn-shape voice imported to X doesn't pass — X-vs-LinkedIn discriminator in CoT step 2 catches the broadcast-not-peer register mismatch. Cold-start void doesn't collapse to feature-checking — regime-aware sub-anchor switches to slop-absence + positioning-consistency.

Workflow that learns to slot-fill each criterion still has to produce content with the right outcome to score 1. Slot-fill alone scores 0 — and the structural_gate checks (§3e + §8 expansion list) gate the surface markers upstream, so the workflow has to evade all of them simultaneously AND produce content the gestalt judge can't dismiss.

**v2-specific Goodhart-resistance posture for the broader bundle.** Components B-L of the bundle are validated by `structural_gate` for shape/completeness/provenance — they are NOT scored by the artifact judge. This is structurally important: if the bundle's strategy doc (Component C), reply-target list (Component D), Spaces brief (Component F), etc., were fed to the judge, the workflow would learn to template-fill bundle prose for judge approval, which is exactly the Phase-4 pathology the design guide prohibits. By keeping the judge scope atomic at Component A, the bundle's structural quality (does it have 10-30 reply targets, does it specify ICP timezone, does the voice substrate trace to operator-provided sources) becomes a `structural_gate` matter — deterministic checks the workflow cannot evade by clever prose alone. The optional bundle-coherence judge (BC-1..BC-5 candidate, §8) would be a separate workflow-layer judge with its own outcome questions — deferred to v3 unless first-engagement bundle coherence becomes a measured failure mode.

**3 sample-and-flag telemetry signals** (variance instrumentation per design guide §11.5, NOT criteria — these run alongside the judge, generate telemetry, trigger redesign rather than score):

- **Grok-tone proxy.** Sample 10% of drafts; run a lightweight tone classifier (constructive / neutral / combative-empty). If a generation shows ≥30% combative-empty, flag. Catches workflow learning to mimic edgy-takes-without-substance even when X-3 passes on surface read.
- **Reply-bait CTA detector.** Sample drafts for end-of-post bait patterns ("what do you think?", "agree or disagree?", "drop your thoughts below"). Track per-generation rate. Rising rate = workflow templating toward reply-bait; flag for redesign.
- **AI-slop signature density across generations.** Count em-dashes, tricolons, "moreover/furthermore/delve" tokens, "Stop X. Start Y." imperative-pairs across the generation's corpus. If density rises monotonically across 3 generations, flag — even if X-5 passes per-fixture, the workflow may be drifting toward slop on average.

**v2 NEW telemetry candidates (deferred to plan-author / operator triage before wiring):**

- **Bundle-component-coherence variance.** Across a generation's bundle outputs, measure voice consistency between Component B (profile audit's bio voice) + Component C (strategy doc's voice plan articulation) + Component A (sample posts) + Component E (DM templates) + Component H (series-arc storyboard's per-post arc voice). If variance rises monotonically, flag — workflow may be ghostwriting each component in a different voice register. (Only fires if bundle-coherence judge BC-1..BC-5 candidate is promoted per §8.)
- **Premium-tier confound tracking.** Across a generation's per-fixture metrics, track Premium vs non-Premium impression baselines. If Premium drafts hit median 6× non-Premium impressions but score same on judge, the substrate may misread that as quality signal during evolution.
- **Vertical-mix coverage.** Across the calibration set, track which of the 7 verticals (SaaS / AI lab / agency / service firm / finance / e-commerce / indie) are represented; flag if a vertical falls below 10% representation as the lane scales. Defends against first-cohort overfitting at the substrate-evolution layer.

---

## 7. Verification — conforms to design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples ✓
- §5 criterion count: **5** (5-criterion ceiling held; no documented exception. X-1 absorbs hook-discipline + clickbait failure via 3-axis CoT rather than promoting Axis C to a 6th criterion — see §8 open-question 1. Bundle-coherence BC-1..BC-5 is a SEPARATE judge layer if/when promoted in v3, not a 6th artifact criterion.) ✓
- §5 isolation: per-criterion rationale, no blending ✓
- §6 structured per-criterion CoT (3–4 steps each) ✓
- §7 reference-free: examples hedged with "do not optimize toward this" ✓
- §11 Goodhart-resistance verification with 3 sample-and-flag telemetry signals + 3 v2 candidate signals ✓
- §13 specimen criterion template followed ✓

**Note on the 5-criterion ceiling (REAFFIRMED in v2).** Unlike the CI lane's CI-6 evidence-chain criterion (a documented justified-breach per design guide §5 v2.1, justified by 19.9% GPT-4o citation-fab and 37% Perplexity confabulation effect sizes), x_engine v2 does NOT promote a 6th criterion at the artifact layer. The hook-discipline deep research identified a potential X-6 "hook-body alignment" that would catch the clickbait failure mode — v2 folds hook-body alignment into X-1's Axis C CoT step rather than promoting. Rationale: X-1 (with 3-axis CoT) + X-2 (specific knowledge — most clickbait fails X-2 because the body is generic) together should catch ≥90% of seeded clickbait fixtures. If the redundancy check shows <90%, the §5 documented-exception path opens and X-6 hook-body alignment becomes a 6th criterion. Until then: 5.

**Note on bundle-coherence judge BC-1..BC-5 (NEW in v2).** The optional bundle-coherence judge sketched in `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §5.3 is held in reserve as a SEPARATE workflow-layer judge — not a 6th artifact criterion. If promoted, it would score the bundle's coherence across components on 5 outcome questions (voice coherence, pillar-to-artifact alignment, vertical-appropriateness, measurement-plan feedback loop, hand-off-ability). Per design-guide §5, the bundle-coherence judge would have its own 5-criterion ceiling, its own redundancy check, its own Goodhart-resistance verification. **v2 defers promotion to v3** unless first-engagement bundle coherence becomes a measured failure mode in v2 fixtures (see §8 sibling-fork triggers).

Length per criterion ≈ 250–350 words (longer than the design guide's 150-word target due to 3-axis CoT on X-1 and regime-aware sub-anchors on X-5; absorbable). Total spec body ≈ 9000-10000 words including v2 expansions (§1.5 bundle architecture, §3c/d cuts/adds, §8 sibling-fork + BC-1..BC-5 candidate).

---

## 8. Open questions

**v2 restructure note (2026-05-19).** v1 surgical-restoration items from `fc99d64` cross-check audit (`docs/handoffs/2026-05-18-judge-design-v1-cross-check.md`) are PRESERVED unchanged: X-2 voice.md HARD FLOOR (CoT Step 3 + Score 0 score-cap); X-5 jargon-gloss rule (CoT Step 2 + Score 0 score-cap). Bracket-aware scoring (SHARP/BUILD/CASE-STUDY) remains INTENTIONALLY NOT restored at criterion layer (open-question 11 below). X-6 cross-cohort criterion remains INTENTIONALLY NOT promoted (preserves 5-criterion ceiling; workflow-level `cross_item_criteria` survives; open-question 12 below).

Reader / Artifact-shape (Component A judge scope) / Success (artifact + program level) / Failure (mediocre + Goodhart + 20 cuts + 24 adds) / 5 Criteria / wrapper-strip / structural_gate routing for Components B-L + per-cycle increments I3/I7/I10 / sibling-fork triggers are LOCKED at v2. Remaining:

1. **X-6 hook-body alignment promotion — falsifiable variance trigger (REFRAMED in v3 per spot-check audit).** The hook-discipline deep research identified a potential 6th criterion targeting the clickbait failure (high impression / low dwell-completion / high negative-signal cascade). v1 + v2 + v3 fold hook-body alignment into X-1's Axis C CoT. **X-6 hook-body alignment promotion criteria: if X-1 + X-2 + structural_gate combined catch <90% of seeded clickbait test fixtures across 3 generations OR if X-1's Axis C anchor shows variance exceeding judge-design §11.5 redesign threshold, promote X-6 per design-guide §5 documented-exception path** — LLM-specific failure surface is documented (xai-org/x-algorithm `engagement_arbitrage` detector + Phoenix bounce-after-hook penalty). The 90% catch-rate threshold is calibrated against the seeded clickbait sub-population (specific seeding methodology lives in the §8 Q8 fixture-validation plan); the Axis C variance trigger uses the design-guide's standing redesign threshold (§11.5 variance instrumentation) so X-6 promotion has two independent decision rules rather than a single performative threshold.

2. **Redundancy check pending (urgent).** Per design guide §5, run pairwise correlation across re-runs of 5 fixtures × 5 criteria × 3 panel models = ~75 calls (~$30). Drop any criterion correlating >0.7 with another. Most-likely-to-merge pairs: X-2 (specific knowledge) ↔ X-3 (falsifiability) — specific lived-experience claims are often falsifiable; X-2 ↔ X-5 (voice) — composed-engineer voice tends to make claims simultaneously unfalsifiable AND off-voice, forcing co-variance on slop-positive cases.

3. **Phoenix retraining cadence — quarterly algorithm-axis re-run (carried over from v1).** Phoenix is iterated regularly (May 2026 release shipped an architectural refresh). The 5-criterion outcome-question shape is durable; underlying weight reconstructions and operator-data triangulations are not. Re-run algorithm-axis research quarterly; track whether `reply > like > repost > bookmark > profile_click` ordering still holds, whether `engagement_arbitrage` still fires on the same bounce-after-hook patterns, whether external-link suppression cohort thresholds shift.

4. **Cold-start handling for X-2 and X-5 — fixture-stratify the calibration set.** When the account has <30 prior posts (working data-rich threshold), X-2 and X-5 both lose their account-history reference. X-5 has an explicit cold-start sub-anchor (slop-absence + stated-positioning-consistency); X-2 still scores because lived-experience is about claim specificity not voice. Recommend: 100-fixture calibration set stratify across cold-start (≤10), mid-data (10–30), data-rich (≥30) regimes, ~33 fixtures each, so X-5 regime branches are independently calibratable.

5. **Premium vs non-Premium accounts — no spec effect at criterion layer; track confound in telemetry.** Premium accounts receive +4× in-network and +2× out-of-network ranking bonus on Phoenix output. Draft quality is invariant to tier; distribution is not. Judge scores quality, so spec does not condition on Premium. Open: if Phase-3 telemetry shows Premium drafts hitting median 600 impressions vs non-Premium 100, the substrate may misread that as quality signal during evolution. Track for the first 3 generations post-deployment (§6 NEW telemetry candidate).

6. **Wrapper numerical-weight strip — decision documented (this lane done, REAFFIRMED v2, leak-closed v3.1).** v0 named reply/repost/bookmark/dwell/negative numerical weights; v1 stripped; v2 reaffirms strip. Operator-reconstructed action-class weight estimates (QT, profile-click, reply-with-author-response) that surface in third-party community sources are NOT to be re-added to the spec, even though the comprehensive-scope research deliverable surfaced them. Same Goodhart vector applies: anchoring on named numerals invites template-fitting against them. Revisit if the open-source release publishes official numerical weights (currently the repo publishes the formula template + ten-action probability set but NOT coefficients).

7. **First-cohort overfitting watch — Polish-language fixture risk.** v1+v2 are research-grounded against English-language Anglosphere founder/operator voice. The 6+ structural_gate checks (em-dash density, signature-phrase blocklist, tricolon density, "Stop X. Start Y." regex, listicle uniformity, hashtag count, link suppression) are English-calibrated. Polish-language clients (DWF lawyers, Klinika dermatology) may show different Tier-1 tell frequencies — Polish em-dash conventions, Polish discourse markers, Polish parallel-construction baselines. Judge criteria (X-1..X-5) test mechanisms that are language-universal at the cognitive-load level (forward-vector, gestalt voice, falsifiability, specific knowledge) so the criterion prose should generalize. Structural_gate thresholds need a Polish-language fixture pass before locking. v2-specific: Components B-L (strategy doc, reply-target list, Communities map, DM templates) also need Polish-language calibration before DWF/Klinika launch — vertical adjustment is harder when language register also shifts.

8. **Fixture validation.** Run 5 existing X-engine fixtures (current archive `v007-curated` + any Polish-language fixtures available) through the locked criteria; eyeball judge rationales. If rationales don't match human reasoning about quality, the prose is wrong, not the design. Surface findings before propagating. **v2-specific:** also dry-run the bundle-shape `structural_gate` against an existing fixture's `programs/references/voice.md` to verify Component L provenance check fires correctly.

9. **`structural_gate` expansion (before spec ships to v006/workflows)** — Component A deterministic checks (~120 LOC) PLUS Components B-L bundle shape checks (~150 additional LOC). Each defends a specific named failure surface with real-operator FPR below 5%:

   **Component A deterministic checks (carried over from v1):**
   - **Em-dash density gate** — reject drafts with >5 em-dashes per 100 words. ~20 LOC.
   - **Signature-phrase blocklist** — hard-reject on appearance of conversational tells. ~15 LOC + curated list (the 14-phrase list per §3c C5).
   - **Three-element parallel-construction density** — detect tricolons via syntactic-uniformity scoring; reject if >2 per thread. ~30–40 LOC.
   - **"Stop X. Start Y." structural detector** — regex or parse-tree match for two immediately-adjacent imperative sentences. >1 instance per post fails. ~15 LOC.
   - **Listicle syntactic-uniformity gate** — cosine similarity of bullet POS-tag sequences. Reject if >0.85. ~40 LOC.
   - **External-link-in-body suppression flag** — auto-rewrite `https?://` URLs in body to first-reply form. ~20 LOC.
   - **Hashtag count gate** — reject if >2 hashtags. Already in `slop_gate`; confirm coverage. ~0 LOC.
   - **Engagement-bait CTA blocklist (NEW in v2 per §3c C1, C20)** — literal-string match on "Like if you agree," "RT if X," "Drop a 🔥," "Bookmark this thread," etc. ~10 LOC.
   - **Confessional-bait-shape detector (NEW in v2 per §3c C2)** — opening pattern "I [failure verb] [object]" + exactly-3 numbered bullets + abstract-failure shape. ~25 LOC.

   **Components B-L bundle structural checks (NEW in v2):**
   - **B (profile audit) shape check** — bio fits ≤160 chars; pinned tweet has ≥3 rotation candidates; banner specs match 1500×500.
   - **C (strategy doc) shape check** — enumerates 3-5 pillars; voice plan section present; cadence calendar specifies ICP timezone; format-mix percentages sum to 100%.
   - **D (reply-target list) shape check** — 10-30 entries; each entry has per-account context block (what they post about, what tone is welcomed, what reply-shape works).
   - **E (DM templates) shape check** — 5-7 use-case templates; each carries voice-substrate provenance reference.
   - **F (Spaces strategy brief) shape check** — host decision binary + cadence + format + first-month 4 topics if hosting.
   - **G (Communities map) shape check** — 5-10 Communities enumerated; per-Community posting plan.
   - **H (series-arc storyboard) shape check** — arc premise + weekly cadence + arc-resolution promise; first month populated.
   - **I (measurement plan) shape check** — 5-7 KPIs; monthly report cadence; rotation thresholds named; Premium-tier confound tracking included.
   - **J (30/60/90 roadmap) shape check** — week-by-week deliverable cadence; founder-time commitment block present.
   - **K (cross-platform syndication rules) shape check** — at least one LI→X rule + one blog→X rule + one X→LI rule.
   - **L (brand voice substrate) provenance + completeness check** — `programs/references/voice.md` non-empty; contains named-entity index for X-2 HARD FLOOR enforcement.

   AI-detector classifier output (GPTZero, Originality.ai, fine-tuned BERTweet) is NOT added — see §3e rationale (54% detection on fine-tuned voice models per Dawkins et al. 2025; 15.6–17.6% FPR disproportionately penalizes non-native English writers).

10. **Propagation to other 7 lanes.** Once x_engine v2 validates on real fixtures, propagate per-lane — NOT mechanical 4-question repeat. The 4 x_engine deep-research questions (algorithm, hook discipline, voice screenshot test, AI-slop detection) were lane-specific; LinkedIn engine needs a partially-overlapping but distinct deep-research set (algorithm differs; voice register differs — broadcast vs peer; AI-slop ghostwriter regime differs). **v2-specific:** LinkedIn engine should also expand to bundle-shape (LI profile audit + LI strategy doc + LI carousel templates + LI Newsletter cadence + ...) if the multi-component-deliverable pattern proves load-bearing on x_engine.

11. **Bracket taxonomy vs locked artifact shape — resolve before spec ships to v006/workflows.** Live code's `structural_gate` enforces a three-bracket taxonomy (SHARP 250–300 chars / BUILD 500–900 / CASE-STUDY 1000–1500) via the `length_bracket` frontmatter field. v1 §1.5 + v2 §1.5 locked artifact-shape (Component A) to single post (≤280) or thread of 3–12 units — which fits SHARP-as-single-post and BUILD/CASE-STUDY-as-thread, but is not identical to the live taxonomy. v2 recommendation: (c) restore the bracket-aware per-shape prescription as a `structural_gate` check (not a judge criterion — outcome-question-not-feature-check discipline holds). The bracket field is shape-validation, not content-validation. **v2 extension:** with the 12-component bundle, the BUILD bracket might be the natural home for Component C (strategy doc) shape; CASE-STUDY might be the home for Component J (30/60/90 roadmap). Operationalize before locking.

12. **X-6 cross-cohort: workflow-level only, or surface to judge?** Live code wires `cross_item_criteria={"X-6": CrossItemCriterion(glob="drafts/*.md", max_items=10, words_per_item=400)}` in `SessionEvalSpec`. v1 + v2 drop X-6 as a judge criterion (preserves 5-criterion ceiling) but the workflow-level diversity check still fires across multi-draft sessions. v2 recommendation: (a) keep cross_item_criteria active at workflow level only — diversity violations surface as workflow-level telemetry, judge scores each draft independently per X-1..X-5; promote X-6 only if redundancy-check (§5 v2.1 documented-exception path) shows multi-draft sessions overfitting on same-archetype hooks. **v2 extension:** if the bundle-coherence judge BC-1..BC-5 candidate is promoted (next open question), BC-3 (vertical-appropriateness) absorbs the cross-cohort diversity check at bundle-layer.

13. **Bundle-coherence judge BC-1..BC-5 promotion — DEFER to v3 candidate, promote only if first-engagement-bundle coherence becomes load-bearing failure (NEW in v2).** Per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §5.3, the bundle-coherence judge has 5 outcome questions:
    - **BC-1.** Does the bundle's voice carry coherently across all components? Would a reader of the strategy doc, then the sample posts, then the DM templates, find them attributable to the same person?
    - **BC-2.** Do the strategy doc's pillars actually appear in the sample posts + sample threads + series-arc + reply-target choices? Or is the strategy doc decoupled from the artifacts?
    - **BC-3.** Is the reply-target list and Communities map vertical-appropriate? Would a peer in the client's vertical recognize these as the accounts and Communities they themselves would target — not generic founder-Twitter accounts?
    - **BC-4.** Does the measurement plan have a closed feedback loop to strategy updates? Or is it a list of metrics that never feeds back into pillar / format / cadence rotation?
    - **BC-5.** Does the bundle work as a starting point for a client running the workflow themselves — or does it require gofreddy operating it indefinitely? Hand-off-ability differentiation test.

    These are SEPARATE from the artifact judge (X-1..X-5 stays atomic at Component A). The bundle-coherence judge would be its own workflow-layer judge with its own 5-criterion ceiling, redundancy check, Goodhart-resistance verification, calibration set.

    **v2 posture:** DEFER to v3 candidate. The artifact judge already does the load-bearing work (X-2 HARD FLOOR catches named-entity coherence between Component L voice substrate and Component A artifacts; X-5 catches voice register drift). `structural_gate` already validates Components B-L for shape and provenance. The bundle-coherence judge is only needed if, after v2 fixtures run, BC-1..BC-5-shaped failures appear that the artifact judge + `structural_gate` did NOT catch. Promote BC-1..BC-5 in v3 only if measured.

14. **Sibling-fork triggers — when to fork x_spaces / x_articles as siblings (NEW in v2).** v2 keeps Articles (I6) and Spaces recap threads (I5) inside x_engine. If demand patterns shift:

    - **Fork x_spaces sibling lane if Spaces hosting demand crosses 3+ clients with weekly cadence.** Trigger: ≥3 clients in the gofreddy book host weekly Spaces. The x_spaces lane scopes Spaces as primary surface — title hook + description + co-host pairing + per-session brief + recap-thread bundle. Different rubric: title hook is shorter (Spaces titles ≤200 chars); voice register is conversational-spoken not punchy-written; recap-thread shape might extend to 8-15 units.
    - **Fork x_articles sibling lane if Articles long-form demand crosses 3+ clients with weekly Premium+ cadence.** Trigger: ≥3 clients in the gofreddy book publish weekly Articles. The x_articles lane scopes long-form X-Articles separately — Article shape up to 25k chars; headline anatomy + section structure + paragraph rhythm differs from threads; Google-discoverability/SEO weight as additional outcome axis; same 5 core criteria (X-1..X-5) but Article-shape-adjusted thresholds.
    - **Promote bundle-coherence judge BC-1..BC-5 if first-engagement bundle coherence becomes load-bearing failure.** Trigger: ≥3 fixtures show clear cross-component drift (voice mismatch between strategy doc and sample posts; reply-target list ignoring strategy-doc-named pillars; measurement plan not actually closing the feedback loop). Promote BC-1..BC-5 as a separate workflow-layer judge per §13 above.

    Sibling-fork is the lane-split discipline; bundle-coherence-judge promotion is the criteria-expansion discipline. Both deferred to v3 unless measured. v2 ships with the current scope (x_engine produces Component A + Components B-L bundle; artifact judge X-1..X-5 stays atomic).

15. **Quote-tweet-of-self vs quote-tweet-of-other (NEW in v2 per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §1.5 + §1.5.2 / I4).** I4 covers both. The QT-of-self is amplification-shape (continuation, "X weeks later," update); the QT-of-other is conversation-shape (counter-take, extension, specific-knowledge reframe). These are different artifact shapes with different X-1 / X-2 / X-3 anchors. Recommendation: `structural_gate` distinguishes via parent-context check (does the QT make sense without the parent? if yes → single post; if no → parent context dependency is intentional and artifact correctly shaped); same 5-criterion judge applies; sub-anchors in CoT private reasoning toolkit, not in criterion prose. **Defer:** if QT-of-self vs QT-of-other shows variance divergence on judge scoring after 3 generations, promote as a `structural_gate` sub-flag for telemetry.

16. **Reply substance threshold DH3-DH5 (NEW in v2 per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §1.18 / I3).** I3 commits to DH3-DH5 substantive replies; DH0-DH2 (name-calling, ad hominem, responding-to-tone) NEVER ship. The boundary between DH2 (responding-to-tone) and DH3 (contradiction-with-reasoning) is judgment-laden. Recommendation: artifact judge X-3 already catches DH0-DH2 (they're stylistic disagreement, not substantive); explicit DH3-DH5 anchor lives in private reasoning toolkit, not in criterion prose. `structural_gate` adds: reply-shape deterministic check (reply must reference at least one specific claim in the parent; reply must not be pure tone-response).

17. **Engagement-velocity-first design vs founder-time constraint (NEW in v2 per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §A21).** Component J 30/60/90 roadmap explicitly negotiates founder time-commitment for first 5-10 replies within 30 min of posting. The lane can produce *suggested response drafts* for the first replies, but the founder still has to be online. Operational concern, not lane-design concern; ensure Component J shape check enforces presence of the founder-time block.

18. **Build-in-public confidentiality boundary (NEW in v2 per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §1.14 + Q9).** Some clients can't share MRR / users / churn publicly (B2B enterprise SaaS with NDA constraints; regulated finance; legal / medical). The strategy doc (Component C) should explicitly negotiate the confidentiality boundary per client. Bundle-coherence judge BC-3 (if promoted, vertical-appropriateness) would flag if the strategy doc proposes build-in-public-shape for a vertical where it's regulatorily blocked. v2 places this in `structural_gate` Component C check.

19. **AI-slop signature drift — quarterly refresh (NEW in v2 per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §Q15).** §3c list of 20 cuts (em-dash density, signature-phrase blocklist, tricolon density, "Stop X. Start Y." rhythm, listicle uniformity, hashtag count, link suppression, engagement-bait CTAs, confessional bait shape) is based on 2025-2026 AI-slop signatures. These will drift as LLMs train on the named tells. Recommendation: refresh AI-slop signature list quarterly; bundle-coherence judge (if promoted) gets a "post-2026 slop signature" sub-check on artifacts produced after the signature-list freshness threshold.

20. **Vertical breadth vs depth for v2 ship (NEW in v2 per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §Q5).** §4 of the comprehensive scope research lists 7 verticals (SaaS founder / AI lab researcher / agency principal / service firm partner / finance operator / e-commerce operator / indie hacker). Recommendation: ship v2 calibration for 3 verticals deeply (SaaS founder + AI lab researcher + agency principal) — the other 4 follow in v2.1 / v3. Component D (reply-target list), Component G (Communities map), Component F (Spaces brief), Component E (DM templates) are vertical-specific; calibrate for 3 verticals first; expand. The 5-criterion judge stays universal across verticals (mechanism-universal); the bundle's variable components are where vertical adjustment lives.

21. **I3 substantive replies — judge-coverage deferral to v3.1 / sibling lane (NEW in v3 per spot-check audit Finding 5).** I3 substantive replies (10-20/week steady-state) are NOT judged at criterion layer; structural_gate validates shape only. Combined with I4 (1-3 QTs/week, also structural-only), this means >50% of the lane's steady-state output volume is un-judged at criterion layer. Path forward: defer judge-layer I3 scoring to v3.1 (a reply-adapted 5-criterion judge per `docs/research/2026-05-19-x-engine-comprehensive-scope.md` §1.6, with X-1/X-2/X-3 anchors adapted for reply shape — Axis B operates on "first-fixation-survivable token referencing parent claim"; Axis C operates on "reply-body delivers the specific disagreement / extension the opening promised") OR fork a sibling-lane `x_replies` if reply-discovery becomes load-bearing (≥3 clients in the gofreddy book run 70/30 reply-to-original ratios per A4 modern-lever). **For v3, accept that >50% lane output is un-judged at criterion layer** and observe whether this matters in production via variance instrumentation — specifically: if the lane's steady-state engagement metrics diverge from per-fixture X-1..X-5 judge means (high-judge-score sessions producing low real-world engagement, or low-judge-score sessions producing high real-world engagement), the reply substrate is likely dominating and the v3.1 / sibling-lane decision becomes urgent. Until measured, v3 ships with I3 at structural_gate-only with the DH-zone deterministic check per §8 Q16.
