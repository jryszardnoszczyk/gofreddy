---
date: 2026-05-15
type: Phase 4 synthesis + spec proposal (judge-design)
status: AWAITING JR REVIEW — do not write prose yet
supersedes: none (companion to 2026-05-15-judge-design-reset-and-plan.md)
inputs:
  - docs/research/2026-05-15-judges-domain-geo.md
  - docs/research/2026-05-15-judges-domain-competitive.md
  - docs/research/2026-05-15-judges-domain-monitoring.md
  - docs/research/2026-05-15-judges-methodology.md
---

# Phase 4 synthesis — judge redesign spec (no prose yet)

## TL;DR

Three deliverables converge on a **targeted, not paradigm-rewrite, redesign**:

1. **Keep 0/0.5/1 absolute scoring** as the lineage scorer. Anchors *only* at 0 and 1 (skip 0.5). Behavioral, not topical.
2. **Add pairwise gate on top** at promotion time (variant V vs current C, position-swap, both orderings must agree).
3. **PoLL panel** for absolute: opus + codex + cheap third (Haiku 4.5 or Gemini 2.5 Flash). Cross-family eliminates self-preference inflation.
4. **30–50 label per-lane calibration set**, single-sitting human labels by JR. Drift detection re-runs after every rubric or judge-prompt change.
5. **Re-ground rubric prose per lane** in named domain frameworks (Aggarwal GEO paper, Helmer 7 Powers, Cision React Score, FAA AD format, etc.) — but only AFTER spec approval and ONLY at score-0 and score-1 anchors.

Storyboard: unchanged — current SB-1 through SB-8 are already creator-strategist-grounded.

---

## Per-lane proposed criteria

Lifted from `docs/research/2026-05-15-judges-domain-*.md`. Each grounded in a named source. No prose drafted yet.

### GEO — 7 criteria (was: 8)

| New ID | Name | Grounded in | Replaces |
|---|---|---|---|
| GEO-A | Answer-First Lead (BLUF compliance) | Perplexity 90/100w; Volpini Matryoshka; Profound 44% top-third citation | NEW |
| GEO-B | Evidence Density (stats, quotes, citations) | Aggarwal et al. KDD 2024 top-three methods (+28–40% each); Yext 4.31× first-party-data lift | GEO-2 + GEO-5 |
| GEO-C | Passage Self-Containment | Volpini chunk-completeness; Profound 40–75w passage 3.1× | GEO-1 |
| GEO-D | Entity Consistency / Semantic Triples | Kalicube Entity SEO; Shepard #19 (5.8); Slawski patent analysis | GEO-4 (subsumed) |
| GEO-E | Third-Party Validation / Competitive Acknowledgment | Forrester 2026; Ahrefs brand-mention r=0.664; The Verge AI Mode flagging | GEO-3 |
| GEO-F | Search-Intent and Format Match | Shepard #5/#6 (9.2/9.0); Profound table-vs-prose 4.2× | GEO-7 |
| GEO-G | Freshness and Citable Specifics | Ahrefs 17M-citation freshness; Skywork Perplexity 70% / 12-18mo | NEW |

**Dropped:**
- GEO-6 (cross-page differentiation) — not surfaced in GEO literature as a discrete dimension. Domain agent flagged this as a Freddy-specific concern outside published research. **Decision needed:** keep as a separate non-GEO-literature criterion, or drop?
- GEO-8 (page-specific technical recommendations) — not represented in proposed set. Was this load-bearing or boilerplate?

### Competitive — 7 criteria (was: 8)

| New ID | Name | Grounded in | Replaces |
|---|---|---|---|
| CI-A | Has a Point of View, Not a Catalogue | Octopus Intelligence; Klue executive-briefing template; CI Alliance | CI-1 |
| CI-B | Evidence → Inference → Implication → Recommendation Chain | SCIP methodology; Octopus "so what" discipline; Heuer & Pherson | CI-2 |
| CI-C | Trajectory, Not Just Snapshot | CB Insights teardown structure; Andy Grove 10X forces | CI-3 |
| CI-D | Identifies the Mechanism of Advantage | Helmer 7 Powers Benefit+Barrier; Porter operational-effectiveness vs strategic-positioning; Roger Martin Can't/Won't Test | NEW |
| CI-E | Names Strategic Posture and the Hard Trade-Off | Roger Martin Playing to Win; offensive/defensive/cooperative taxonomy | CI-5 + part of CI-7 |
| CI-F | Surfaces Uncomfortable Truths and Considers Alternative Hypotheses | Heuer & Pherson ACH; CI Alliance "bias is a top-five failure"; "kill your darlings" | CI-6 + part of CI-8 |
| CI-G | Hard Prioritisation: Top 2–3 Actions, Time-Bound | Klue top-3-5 rule; CI Alliance "specific, actionable, tied to business impact"; PMA "no vague verbs" | CI-7 (sharpened) + CI-4 |

**Notes:**
- CI-D (Mechanism of Advantage) is **the one genuinely new dimension** — Helmer's two-part test (Benefit AND Barrier) is the most rigorous published frame for separating real moats from claimed ones. Worth its own criterion.
- CI-8 (graceful degradation when data missing) folds into CI-F's assumption-naming + CI-B's so-what chain.
- One additional dimension domain research flagged as missing: **industry-structure context** (BCG Advantage Matrix: Volume/Stalemate/Fragmented/Specialisation). **Decision needed:** add as CI-H, or fold into CI-E as a sub-question?

### Monitoring — 6 criteria + 1 optional (was: 8)

| New ID | Name | Grounded in | Replaces |
|---|---|---|---|
| MON-A | Baseline-relative framing of "what changed" | Brandwatch crisis-alert guide; Sprout SoV practice; ESOV | MON-1 |
| MON-B | Severity tiering with defensible classification | Cision React Score (Harm + Emotionality); FAA AD severity field; SCCT clusters | MON-2 |
| MON-C | Highest-stakes lede in position one | FullIntel executive briefing; SVB + USSS post-mortems; PDB format | MON-3 |
| MON-D | Action items with owner + deadline + consequence (FAA-style) | FAA Airworthiness Directive format (14 CFR Part 39); Tylenol response | MON-4 |
| MON-E | Cross-story compound narrative + forward projection | Harvard Law narrative-contradictions; Ansoff weak signals; Dezenhall iceberg | MON-5 |
| MON-F | "So what" interpretation including absent expected signals | FullIntel; AMEC outcomes-over-outputs; Wells Fargo / BP / Boeing precedent; PDB blank-page convention | MON-6 |
| MON-G (optional) | Temporal arc continuity across digests | Brandwatch continuous-rise indicator; PRWeek Weekender convention | MON-7 |

**Notes:**
- MON-8 (word count proportional to importance) folds into MON-C (position one + structural emphasis).
- MON-G is the lowest-confidence criterion per the domain agent — likely to reward "previously on…" recaps that aren't load-bearing. **Decision needed:** include or skip?

### Storyboard — UNCHANGED (8 criteria, SB-1 through SB-8)

Pre-investigation found SB criteria already grounded in creator-strategist depth:
- Pattern data references (SB-1, SB-7)
- Hook irreplaceability (SB-2)
- Emotional-map-as-claim vs story-beats-as-evidence (SB-3)
- Recontextualization (SB-4)
- Audio as story layer (SB-5)
- AI video model capability awareness (SB-6)
- Creator-specific pacing (SB-7)
- Portfolio diversity (SB-8)

No domain research dispatched. Revisit only if Phase 4 reveals cross-cutting issues.

### X Engine — UNCHANGED (7 criteria, X-1 through X-6 + X-9)

X-9 is the only deterministic-citizenship criterion shipped this cycle. Not touched.

### LinkedIn Engine — UNCHANGED (6 criteria, LI-1 through LI-6)

Not in scope for this cycle.

### Marketing Audit — UNCHANGED (8 criteria, MA-1 through MA-8)

Not in scope for this cycle.

### Site Engine — UNCHANGED

Recently merged (4c240c3); not in scope for this cycle.

---

## Methodology decisions (cross-cutting, from `2026-05-15-judges-methodology.md`)

### Piece 1 — Pairwise gate at promotion time

**Decision:** Add pairwise judge (variant V vs current C) as the *promotion gate*. Keep absolute scoring as the lineage/digest measurement.

**Why:** Liusie 2025 — pairwise flips on 35% of distractor attacks vs 9% for absolute. *But* pairwise is the clean primitive for a single decision (Eugene Yan; AlpacaEval; LMSYS). Use it where it shines (one promotion decision) and avoid it where it doesn't (cross-lineage comparability).

**Cost:** +1 judge call per generation (the second ordering for position-swap). Acceptable.

**Implementation:**
- New judge prompt that takes (V, C, criteria) and returns "V better / C better / tie + reasoning"
- Run both orderings; promote only if both agree V > C
- Live alongside existing absolute scorer; no archive invalidation

**Decision needed:** approve / defer / reject this addition.

### Piece 2 — Panel of cheap diverse judges (PoLL) for absolute scoring

**Decision:** Add a cheap third judge (Anthropic Haiku 4.5 OR Google Gemini 2.5 Flash) to the existing opus + codex absolute scorer. Mean over the three.

**Why:** Verga et al. 2024 — three-model panel jumped Cohen κ from 0.627 → 0.763, σ from 6.1 → 2.2, **7–8× cheaper**. Cross-family eliminates the Li et al. 2025 self-preference inflation (6–22% own-family scoring bias).

**Cost:** *Lower* than current opus-only, not higher. Third judge is cheap.

**Implementation:**
- One new model in `src/evaluation/judges/`
- Aggregator at `_invoke_external_critique`
- Geo's gpt-5.5 cybersecurity filter (per `project-geo-regression-root-cause-2026-05-12`) means geo runs with 2-judge fallback, not 3 — that's fine

**Decision needed:** approve / defer / reject; if approve, which third judge (Haiku 4.5 or Gemini 2.5 Flash or both behind config)?

### Piece 3 — Calibration set (30–50 labels per lane)

**Decision:** Build 30 human-labeled artifacts per lane, labeled 0/0.5/1 by JR in a single sitting per lane. Track Cohen κ vs JR labels per judge version. Re-score on every rubric edit OR meta-agent mutation; any single-label flip pauses promotion until explained.

**Why:** Hopkins 2026 — bounds degrade rapidly below n=25; 50 stabilizes. Anthropic's "Demystifying Evals" pattern: per-dimension calibration as a living artifact. Without this, the other two pieces are unverified.

**Cost:** Labor-intensive — ~2-3 hours per lane for JR. 3 lanes (GEO + CI + monitoring) = ~9 hours total.

**Implementation:**
- Pick 30 fixtures per lane from archive (mix of promoted + rejected variants)
- JR labels each one 0/0.5/1 per criterion in single sitting
- Stored as `autoresearch/calibration/<lane>-2026-05-15.jsonl`
- Validate-script runs current judges against the set, reports Cohen κ + per-label disagreements
- Drift gate: if κ drops vs previous version, block promotion

**Decision needed:** approve / defer; timeline for labeling.

---

## What we are NOT doing (DO-NOTs grounded in literature)

Per `2026-05-15-judges-methodology.md` §9:

- **No σ-widening** as design target. The Krippendorff α<0.8 + our own `2ce99bb` noise floor stand.
- **No broader scale (1–5 or 1–10)**. Central tendency bias literature warns against this at small N. 0/0.5/1 with behavioral anchors is the right structure.
- **No 3+ exemplar artifacts** per criterion in the prompt. Extreme-only anchors (0 + 1, skip 0.5) match full Likert anchors per Empirical Design Choices 2025. And dumping prior promoted variants as exemplars is the most direct preference-leakage path.
- **No static rubric** across many evolution generations. Pan et al. 2024 ICRH — feedback loops invalidate static evals. Re-validate calibration at version boundaries.
- **No trusting any single absolute score** for promotion. Piece 1 (pairwise gate) is the actual decision; absolute is the archived lineage measurement.
- **No anti-gaming clauses** in rubric prose. No production paper validates their effect-size. Theatrical.
- **No σ-targeting calibration scripts**. We already have the answer: noise floor is inherent.

---

## Mapping current → proposed (so JR can see the shifts)

### GEO

```
GEO-1 (block self-contained)          → GEO-C (passage self-containment, sharper)
GEO-2 (specific verifiable claims)    → GEO-B (evidence density, +stats/quotes/citations)
GEO-3 (competitor acknowledgment)     → GEO-E (third-party validation, broader)
GEO-4 (voice/tone consistency)        → GEO-D (entity consistency, KG-grounded)
GEO-5 (first-party attribution)       → folded into GEO-B
GEO-6 (cross-page differentiation)    → DROPPED unless JR keeps
GEO-7 (search-intent matching)        → GEO-F (intent + format match, +tables)
GEO-8 (page-specific tech recs)       → DROPPED unless JR keeps
+ GEO-A (answer-first lead)          NEW
+ GEO-G (freshness)                  NEW
```

### Competitive

```
CI-1 (thesis)                          → CI-A (point of view, sharper)
CI-2 (reasoning chain)                 → CI-B (evidence → inference → implication chain)
CI-3 (trajectory)                      → CI-C (trajectory with CB Insights structure)
CI-4 (recommendations actionable)      → folded into CI-G (hard prioritisation)
CI-5 (asymmetric opportunities)        → CI-E (strategic posture + trade-off)
CI-6 (uncomfortable truths)            → CI-F (uncomfortable truths + ACH)
CI-7 (hard prioritisation)             → CI-G (sharpened)
CI-8 (graceful degradation)            → folded into CI-F's assumption-naming
+ CI-D (mechanism of advantage)       NEW (Helmer Benefit+Barrier)
? CI-H (industry-structure context)   DECISION NEEDED (BCG matrix)
```

### Monitoring

```
MON-1 (what changed)                   → MON-A (baseline-relative, sharper)
MON-2 (severity classification)        → MON-B (with Cision React Score structure)
MON-3 (highest-stakes lede)            → MON-C (with PDB/FullIntel structure)
MON-4 (action items)                   → MON-D (FAA AD format)
MON-5 (compound narratives)            → MON-E (Harvard Law narrative-contradictions)
MON-6 (so what + absences)             → MON-F (FullIntel + AMEC + PDB blank-page convention)
MON-7 (temporal arc)                   → MON-G OPTIONAL — decision needed
MON-8 (word count proportional)        → folded into MON-C structural emphasis
```

---

## Decisions JR needs to make before I write prose

1. **GEO-6 (cross-page differentiation):** keep as Freddy-specific non-GEO-literature criterion? Drop?
2. **GEO-8 (page-specific tech recommendations):** keep? Drop?
3. **CI-H (industry-structure context, BCG matrix):** add as separate criterion, fold into CI-E, or skip?
4. **MON-G (temporal arc continuity):** include or skip? (Domain agent flagged as lowest-confidence.)
5. **Pairwise promotion gate (Piece 1):** approve / defer / reject?
6. **PoLL panel third judge (Piece 2):** approve; which third (Haiku 4.5 / Gemini 2.5 Flash / config-driven)?
7. **Calibration set (Piece 3):** approve; when can JR label? 30 fixtures × 3 lanes = ~9 labor-hours.
8. **Storyboard:** confirm hands-off, or want a similar research pass anyway?
9. **Marketing Audit / X / LinkedIn / Site Engine:** confirm out of scope for this cycle?

---

## What happens after JR review

Once JR signs off on criteria-set + methodology pieces:

**Phase 4 Step 4 — Prose writing.** For each criterion in approved set:
- Score-0 behavioral anchor (what a failing artifact looks like, with concrete pattern)
- Score-1 behavioral anchor (what an excellent artifact looks like, with concrete pattern)
- Reference to the named source ("per Cision React Score severity model", "per FAA AD action-item format")
- Sub-questions if criterion is checklist-style; gradient prose if continuous
- NO 0.5 anchor (per Empirical Design Choices 2025)
- NO exemplar artifacts inserted into prompt (preference-leakage)
- NO anti-gaming clauses or substitution tests

**Phase 4 Step 5 — Calibration set construction.** JR labels 30 per lane per the protocol above.

**Phase 4 Step 6 — Pairwise gate + PoLL panel implementation.** Code changes to `src/evaluation/judges/` and `score_variant.py`.

**Phase 4 Step 7 — Empirical iteration.** First evolution run with new rubrics. Watch for mode collapse (population score variance → noise floor for 2+ generations = mode collapse, not convergence).

---

## Files

- This synthesis: `docs/handoffs/2026-05-15-judge-design-phase4-synthesis.md`
- Reset plan (parent): `docs/handoffs/2026-05-15-judge-design-reset-and-plan.md`
- Domain research GEO: `docs/research/2026-05-15-judges-domain-geo.md`
- Domain research competitive: `docs/research/2026-05-15-judges-domain-competitive.md`
- Domain research monitoring: `docs/research/2026-05-15-judges-domain-monitoring.md`
- Methodology research: `docs/research/2026-05-15-judges-methodology.md`
- Phase 1 commit: `f1d2599 revert(rubrics): restore original substantive prose for 13 criteria; keep X-9 + substrate work`
