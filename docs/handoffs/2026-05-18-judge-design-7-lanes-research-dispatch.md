---
date: 2026-05-18
type: research dispatch plan (judge-design — 7 lanes Path 2)
status: dispatched in parallel
parent_session: post-compact resumption from `2026-05-18-judge-design-next-session-brief.md`
companion: Path 1 (CI v3.3 validation) running in parallel agent — prompt on JR's clipboard
---

# 7-Lane Research Dispatch — Judge Design Path 2

## Decision

Path 2 commenced. Path 1 (CI v3.3 validation) offloaded to a parallel Claude Code agent in this same repo (prompt on JR's clipboard at session resume).

## Total dispatch: 29 agents, parallel, background mode

Estimated total cost ~$435 ($15/agent × 29). Estimated wall ~30–60 min per agent (all parallel).

Each agent's deliverable lands at `docs/research/2026-05-18-{lane}-{axis}.md`.

## Per-lane axis allocation (lane-customized per brief §"Path 2" table — NOT mechanical 4-question repeat)

### GEO (4 agents)
AEO content; AI engines are the reader; dual-audience tension central.

| Axis | File | Key question |
|---|---|---|
| 1 | `2026-05-18-geo-vertical-conventions.md` | How does optimal AEO content shape vary across legal / healthcare / B2B-SaaS / fintech / DTC e-commerce? |
| 2 | `2026-05-18-geo-artifact-taxonomy.md` | Page-type form factors: FAQ vs how-to vs comparison vs listicle vs glossary vs hub — when is each optimal? |
| 3 | `2026-05-18-geo-ai-failure-modes.md` | **CRITICAL** — entity confab, source confab, citation drift, recency distortion when AI engines (Perplexity / ChatGPT / Claude / Gemini) are the reader |
| 4 | `2026-05-18-geo-dual-audience-tension.md` | How to score content that must serve both human reader and AI citation engine; Aggarwal-method-by-domain variance |

### MON (4 agents)
Executive monitoring digests; absence-as-signal; compound narratives.

| Axis | File | Key question |
|---|---|---|
| 1 | `2026-05-18-monitoring-vertical-conventions.md` | Executive briefing variance by industry — financial services vs healthcare vs B2B SaaS vs legal vs founder-led |
| 2 | `2026-05-18-monitoring-artifact-taxonomy.md` | Weekly digest vs daily alert vs deep-dive vs scorecard — when is each correct and what's the form factor for each? |
| 3 | `2026-05-18-monitoring-ai-failure-modes.md` | Confab on monitoring claims (event citations, competitor moves), recency distortion (stale signal as fresh), false-urgency framing |
| 4 | `2026-05-18-monitoring-compound-narrative-absence.md` | Compound-narrative detection (multi-week thread emerging) + absence-as-signal (what's NOT mentioned that should be) |

### SB (4 agents)
Storyboard / video scripts; creator-voice fidelity; AI-video-model capability awareness.

| Axis | File | Key question |
|---|---|---|
| 1 | `2026-05-18-storyboard-creator-voice-fidelity.md` | MrBeast vs Casey Neistat vs Johnny Harris voice signatures — what's measurable about voice match? |
| 2 | `2026-05-18-storyboard-ai-failure-modes.md` | Storyboard-specific confab (fake stats, fake quotes), narrative-arc gaming, hook-formula overuse |
| 3 | `2026-05-18-storyboard-pattern-data-cold-start.md` | When the client has 0–1 published videos, how does the judge score voice-match without overfitting? |
| 4 | `2026-05-18-storyboard-ai-video-model-capability.md` | Sora 3 / Veo 4 / Runway Gen-5 / Kling 3 capability boundaries — what shots the storyboard must NOT specify in 2026 |

### MA (5 agents)
Marketing audit; audit-shape by maturity stage; upstream diagnostic.

| Axis | File | Key question |
|---|---|---|
| 1 | `2026-05-18-marketing-audit-vertical-conventions.md` | Audit variance by industry × stage: Seed/A/B/C/IPO; SMB vs MM vs enterprise; B2B vs B2C |
| 2 | `2026-05-18-marketing-audit-artifact-taxonomy.md` | Audit-shape by maturity: 5-page report vs 30-page teardown vs slide deck vs scorecard — when is each correct? |
| 3 | `2026-05-18-marketing-audit-ai-failure-modes.md` | Confab on financial metrics, channel performance claims, competitor data; misdiagnosis (treating symptom as root cause) |
| 4 | `2026-05-18-marketing-audit-decision-format-mapping.md` | 30/60/90 day fractional-CMO action plan vs strategic memo vs scorecard — which decision class maps to which artifact? |
| 5 | `2026-05-18-marketing-audit-upstream-diagnostic.md` | Distinguishing marketing-symptom from product/positioning/pricing root cause — how does the judge reward correct attribution? |

### X (4 agents)
X (Twitter) content; algorithm signals; hook discipline; voice screenshot test.

| Axis | File | Key question |
|---|---|---|
| 1 | `2026-05-18-x-engine-algorithm-jan-2026.md` | X open-source algorithm Jan-2026: reply weighting, profile-click weighting, dwell signals, screenshot anti-virality |
| 2 | `2026-05-18-x-engine-hook-discipline.md` | Cole / Dickie / Hormozi opening-line taxonomy; first-7-words and first-tweet-of-thread research |
| 3 | `2026-05-18-x-engine-voice-screenshot-test.md` | Account-voice fidelity — can a reader screenshot this and credibly believe it's from the founder? How to score? |
| 4 | `2026-05-18-x-engine-ai-slop-detection.md` | **CRITICAL** — X-specific AI-slop tells: em-dash patterns, "Stop X. Start Y." constructions, listicle bloat, ghost-engineer voice |

### LI (4 agents)
LinkedIn content; Van Der Blom Depth Score; author-context coherence.

| Axis | File | Key question |
|---|---|---|
| 1 | `2026-05-18-linkedin-engine-van-der-blom-depth.md` | LinkedIn Algorithm Insights Jan-2026 Depth Score factors — dwell, comment quality, share weight, post-format weights |
| 2 | `2026-05-18-linkedin-engine-comment-seed-quality.md` | Comment-bait vs comment-magnet distinction; how to reward genuine discourse-seeding without penalizing CTAs |
| 3 | `2026-05-18-linkedin-engine-ai-slop-li-specific.md` | **CRITICAL** — LinkedIn-specific AI-slop: broetry line breaks, "I X for Y years. Here's what I learned:", em-dash, false-vulnerability hooks |
| 4 | `2026-05-18-linkedin-engine-author-context-coherence.md` | Does the post match the author's stated expertise/role/recent activity? How to score author-context drift? |

### SITE (4 agents)
Site / landing pages; dual-audience tension; CXL hero audit; site-quality.md retirement.

| Axis | File | Key question |
|---|---|---|
| 1 | `2026-05-18-site-engine-dual-audience-tension.md` | Human conversion + AEO citation — when do these conflict and how does the judge weigh? |
| 2 | `2026-05-18-site-engine-cxl-hero-audit.md` | CXL / Marketing Examples / Dunford hero-section heuristics — value prop, proof, friction reduction |
| 3 | `2026-05-18-site-engine-site-quality-md-retirement.md` | Current `docs/rubrics/site-quality.md` SE-1..SE-8 — what to keep / cut / merge for v3.3-pattern conformance |
| 4 | `2026-05-18-site-engine-vertical-conventions.md` | B2B SaaS vs e-commerce vs services vs marketplace vs API/dev-tool — landing page conventions by category |

## Hard constraints (applied to ALL 29 dispatches, verbatim from JR)

- No σ-widening, anti-gaming clauses, framework-name embedding in rubric prose
- No feature-checking — route verifiables to structural_gate
- No "smoke testing the prose"
- Outcome questions with behavioral binary anchors required
- Cross-family three-model panel (Opus 4.7 + GPT-5.5 + Gemini 3 Flash)
- Pointwise digest + pairwise promotion gate with position swap
- Reference-free (no model-authored exemplars)
- First-cohort overfitting watch — don't anchor on DWF/Klinika/Anthropic alone

## What this dispatch does NOT do

- Does NOT update lane spec drafts (those happen in Path-A iteration AFTER research returns)
- Does NOT touch live code rubrics (parallel Path-1 agent handles CI; other 7 lanes wait)
- Does NOT dispatch synthesis/integration research (that's a downstream step after lane-level research returns)
- Does NOT validate research findings empirically (deferred to post-Path-A code implementation)

## Synthesis plan (post-research)

After all 29 dispatches return, per-lane synthesis:
1. Read lane's 4–5 research deliverables
2. Apply three load-bearing lessons (outcome-questions / not over-engineered / no first-cohort overfit)
3. Path-A iterate the v0 spec with JR section by section (Reader / Success / Failure / Criteria)
4. Document any justified-exception breaches (CI-6-equivalent criteria) per lane
5. Produce v1 spec per lane

## Status log (updated as dispatches complete)

| # | Lane | Axis | Status |
|---|---|---|---|
| 1 | GEO | vertical-conventions | DISPATCHED |
| 2 | GEO | artifact-taxonomy | DISPATCHED |
| 3 | GEO | ai-failure-modes | DISPATCHED |
| 4 | GEO | dual-audience-tension | DISPATCHED |
| 5 | MON | vertical-conventions | DISPATCHED |
| 6 | MON | artifact-taxonomy | DISPATCHED |
| 7 | MON | ai-failure-modes | DISPATCHED |
| 8 | MON | compound-narrative-absence | DISPATCHED |
| 9 | SB | creator-voice-fidelity | DISPATCHED |
| 10 | SB | ai-failure-modes | DISPATCHED |
| 11 | SB | pattern-data-cold-start | DISPATCHED |
| 12 | SB | ai-video-model-capability | DISPATCHED |
| 13 | MA | vertical-conventions | DISPATCHED |
| 14 | MA | artifact-taxonomy | DISPATCHED |
| 15 | MA | ai-failure-modes | DISPATCHED |
| 16 | MA | decision-format-mapping | DISPATCHED |
| 17 | MA | upstream-diagnostic | DISPATCHED |
| 18 | X | algorithm-jan-2026 | DISPATCHED |
| 19 | X | hook-discipline | DISPATCHED |
| 20 | X | voice-screenshot-test | DISPATCHED |
| 21 | X | ai-slop-detection | DISPATCHED |
| 22 | LI | van-der-blom-depth | DISPATCHED |
| 23 | LI | comment-seed-quality | DISPATCHED |
| 24 | LI | ai-slop-li-specific | DISPATCHED |
| 25 | LI | author-context-coherence | DISPATCHED |
| 26 | SITE | dual-audience-tension | DISPATCHED |
| 27 | SITE | cxl-hero-audit | DISPATCHED |
| 28 | SITE | site-quality-md-retirement | DISPATCHED |
| 29 | SITE | vertical-conventions | DISPATCHED |
