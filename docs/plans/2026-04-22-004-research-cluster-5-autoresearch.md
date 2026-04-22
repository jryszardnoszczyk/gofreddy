---
title: Autoresearch programs + evaluator deep research (F5.1-F5.5)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-004-pipeline-overengineering-deep-research.md
---

# Deep Research — autoresearch over-engineering audit

## Executive summary

Of the 5 autoresearch findings, my read is **1 KEEP / STRENGTHEN, 2 SIMPLIFY, 1 REDESIGN, 1 STRENGTHEN-with-measurement**, and the most consequential are F5.3 and F5.4 (the two-evaluator architecture and its missing telemetry) because every other simplification depends on whether you can detect inner/outer divergence cheaply.

- **F5.1 — Universal prescription pattern**: SIMPLIFY. Real, but the diagnosis is wrong. Rubrics are outcome-shaped, not process-shaped — drift comes from score-5 anchors describing artifact shape that meta-agents transcribe into procedural rules. The rubric authoring style (anchor descriptions) is the structural cause, not the rubric scoring axis.
- **F5.2 — Structural validator content checks**: SIMPLIFY. Worse than the audit said: the *programs* still document `≥100 chars + ≥3 headers` while the actual gate at `src/evaluation/structural.py:101` requires `≥500 chars` and a competitor-data dependency check. The spec in the program is stale relative to the gate. Two ways to remove the over-engineering — either trust judges or update the programs from the gate at build time.
- **F5.3 — Two-evaluator architecture**: STRENGTHEN. Best architectural decision in the system; do not touch the split. But its protection is currently honor-system (meta.md:70 explicitly tells the meta agent not to touch the inner critique prompt because the outer defense has not been verified end-to-end). Strengthen by hardening that interface, not by reworking the layers.
- **F5.4 — Inner/outer correlation telemetry**: STRENGTHEN. Should ship now. ~30 LOC adds the only metric that lets you keep simplifying everything else without flying blind. Already on the team's own list as Gap 7.
- **F5.5 — `report_base.py`**: SIMPLIFY (within autoresearch) but NOT consolidate across pipelines yet. The three "parallel" parsers solve different problems (auto-fix routing vs evolution scoring vs human-readable HTML); shared envelope is fine, shared parser is a forced abstraction.

---

## F5.1 — Universal prescription pattern across the 4 evolved programs

**Today.** Each of `competitive-session.md` / `geo-session.md` / `monitoring-session.md` / `storyboard-session.md` carries 8 numbered criteria (CI/SB/MON/GEO-1..8), a "Hard Rules" section (5 items), a workspace table, format JSON spec, and a "Writing Quality Heuristics" or "Content Quality Standards" block of 4-19 prescriptive bullets. The programs shrunk from 366-511 lines (v001) to 165-197 lines (current_runtime), but the total moved into a `references/` directory of 11 docs totaling 1,775 lines (`autoresearch/archive/current_runtime/programs/references/`) — the surface migrated, the surface area grew.

**Why it exists.** The hypothesis in the audit ("rubric scores PROCESS so meta-agent converges on prescription") is partially right but wrong about the mechanism. I read all 8 GEO and CI rubrics in `src/evaluation/rubrics.py:47-498`. The criteria are outcome-shaped on the scoring axis ("Could an AI engine extract any single content block?", "Can a reader state the brief's central argument in one sentence?"). The drift comes from elsewhere: each rubric's score-5 anchor describes artifact *shape* in detail (e.g., CI-1 score 5: "executive summary states a single strategic position. Every subsequent section provides evidence for, against, or nuance to that position"). The meta agent reads index.json + parent code, not rubrics — but it reads parent programs that absorbed prior attempts to satisfy those score-5 anchors. So shape descriptions become procedural rules transcribed forward through generations.

**What's wrong.** Concrete prescription evidence I found in current programs (load-bearing line numbers):

- `competitive-session.md:28-36` — 9 mandatory analytical practices added since v001 (named-angle/mechanism, cadence-before-volume, 15-objection taxonomy, buyer-type tag on every page, pricing-page teardown layer, buyer-stage coverage audit, cost-of-delay framing required, preflight check, prose hygiene pass). Each cites Corey Haines as the source — they're skill-library transcriptions, not evolved heuristics.
- `geo-session.md:24-43` — CQ-1..CQ-19 plus CQ-DATA. `CQ-13` mandates `/pricing.md` + `/llms.txt` checks, `CQ-14` enumerates 7 specific bot user-agents, `CQ-17` lists 9 banned words and an em-dash threshold (`>1 em dash per page = rewrite`).
- `storyboard-session.md:31-37` — "Seven-sweep edit order (sweeps 1-6; skip 7)", banned words list, exact rhythm prescription "one-beat line (≤7 words) → slightly longer line (15-25 words) → one-beat payoff", em-dash heuristic again.
- Prescription token counts (`must|always|never|required` per file): v001 competitive=19 → current=8; v001 geo=19 → current=7; v001 storyboard=21 → current=5; v001 monitoring did not exist in same shape. Counts went DOWN, but the volume of skills-injected mandates (Corey Haines bullets) went UP — they avoid the prescription tokens by phrasing as declarative bullets ("Use the X taxonomy" rather than "You MUST use the X taxonomy"). This is rules-by-another-name, exactly as the audit suspected for the "non-judge-gated heuristics" sections.

The "non-judge-gated heuristics applied during drafting, not scoring criteria" disclaimer (`storyboard-session.md:22`) is the structural admission. If they were genuinely descriptive guidance the agent could ignore, they'd be in `references/`. They're in the program because the meta-agent (or the human) believed they raise scores in the inner critique pass.

**The right model — agentic / hybrid / deterministic.** More agentic. The fundamental fix is to change what the meta-agent is rewarded for, not to rewrite the program every cycle. Two mechanisms:

1. **Evict heuristic bullets to references/, force the program to say only "the rubric is what it is, here are tools, here is the workspace."** Track in telemetry whether scores degrade. If they don't, the prescription was load-bearing only for the meta-agent's confidence, not for output quality.
2. **Outcome-only score-5 anchors.** Rewrite each rubric's score-5 description so it states the *property* the artifact must achieve without describing a structural shape. CI-1 score-5 currently includes "Every subsequent section provides evidence for, against, or nuance to that position" — this is a shape claim; rewriting to "After reading the executive summary, a reader can paraphrase the brief's argument in one sentence and predict what each downstream section will say about it" measures the same outcome without prescribing the section structure.

**Concrete redesign.** (a) Rewrite the 32 rubric score-5 anchors to remove shape language. ~3 hours, all in `src/evaluation/rubrics.py`. (b) Cap session program length at ~80 lines (workspace + tools + format spec + Hard Rules + pointer to rubric + pointer to references). (c) Add a meta-agent constraint: cannot add bullets to programs unless it can also delete an equivalent amount of guidance text — make program-bullet-addition a Pareto-tradeoff move.

**Complexity removed.** Programs shrink from 165-197 lines to ~80. Skills-library mandates (~20-30 per program) move to references where agents can pull them in if useful. Per-cycle program-mutation surface area drops by ~60%.

**New risks.** (1) Inner-critique scores may drop because the inner critique uses the same rubrics — and short programs are weaker at hand-holding the agent toward score-5 shapes. Mitigated by F5.4 telemetry: if outer scores stay flat while inner scores drop, you've discovered the prescription was theater. (2) Meta-agent may rebel: with parent variant program already short, mutation pressure is to add — this is why the bullet-addition Pareto constraint matters.

**Verdict.** SIMPLIFY. The audit was directionally right; the mechanism diagnosis needs revision (anchor-shape, not rubric-axis); the fix is rubric refactor + program cap + meta-agent constraint, not "delete prescription."

---

## F5.2 — Structural validator content checks

**Today.** Programs document a structural validator that checks "file with 'brief' in name + ≥100 chars + ≥3 markdown section headers" (`competitive-session.md:142-144`; storyboard has equivalent). The programs treat this as agent-facing contract.

**Why it exists.** Cheap pre-judge gate — fail-fast before paying for 8 LLM judge calls. `src/evaluation/service.py:188-202` shows the gate is hard: structural fail → judges don't run → score=0 → variant scored as catastrophic failure.

**What's wrong.** Three specific issues, in order of severity:

1. **The program spec is stale relative to the gate.** `src/evaluation/structural.py:101` requires `len(brief_content.strip()) < 500` to fail (not 100). The structural.py docstring at line 86-89 even says: "Placeholder briefs with no underlying data previously passed structural with 100 chars + 3 headers (dead-weight report pattern). Bumping to 500 chars and requiring parseable competitor data blocks ... without encoding content judgments in frozen code." So the team already discovered the audit's exact concern, fixed the gate, but **forgot to update the four program files**. The agent spec and the runtime check disagree by 5x. An agent reading the program will optimize for a 100-char brief and score 0 catastrophically.
2. **Geometric-mean-with-floor compounds the cliff.** `evaluate_variant.py:59` floors at 0.01, but a structural fail returns `score: 0.0` (`evaluate_variant.py:577`) which is then passed to `_geometric_mean` and floored to 0.01 only when included in a multi-fixture geomean. A single structural fail still drags the domain mean to ~0.04 across 3 fixtures (cube root of 0.01·1·1). One agent that misunderstands the spec wipes the variant's domain score for that lane.
3. **Monitoring carries 14 assertions in `_validate_monitoring`** (`structural.py:140-289`), of which several encode content judgments dressed as structural: "no synthesize attempts > 3" (`structural.py:217-231`, behavioral cap), "digest_meta_grounded" (`structural.py:271-281`, hallucination guard reading session.md narrative). These are content-rule gates, not shape gates.

**The right model — agentic / hybrid / deterministic.** Hybrid, but biased much further toward deterministic-as-cheap-pre-filter only. Three rules:

- **Structural gates check existence and parseability only.** File-exists, JSON-parses, valid-markdown. Nothing else.
- **Length, header count, and behavioral caps belong in judge rubrics.** A judge can read a 99-char brief and decide "too short to evaluate" with a low score; that's a calibrated outcome, not a binary cliff.
- **Hallucination guards belong in evaluator-side checks** (the inner critique), not in the structural gate which the program file documents.

**Concrete redesign.**

1. Auto-generate the "Structural Validator Requirements" section of each program from the gate code at build time (script reads `structural.py`, emits markdown). Eliminates drift permanently. ~50 LOC.
2. Strip content-shape rules from `structural.py`: drop the 500-char threshold, the ≥3-headers check, the no-excessive-rework cap, the digest-hallucination guard. Keep file-exists + JSON-parses + competitor-data-parses (genuine structural).
3. Replace the geomean-with-0.01-floor for structural failures with explicit "score=null, excluded from domain geomean, but counted as fail in promotion summary." This stops one agent's misread from wiping the lane.

**Complexity removed.** ~100 LOC from `structural.py` (monitoring's 14 assertions trimmed to 4). Per-program structural section auto-derived (~12 lines × 4 programs = 48 lines of program text now machine-generated). Stale-doc class of bugs eliminated.

**New risks.** Without the 500-char floor + competitor-data check, the "dead-weight report" failure mode the team explicitly fixed comes back. Mitigation: dead-weight reports score 1/5 across CI-2 and CI-8 (evidence-traced + data-gaps-as-findings), which already drags the geomean to ~0.18 (1·1·5·5·5·5·5·5)^(1/8). The cliff is replaced by a slope, which is what you want for agent feedback.

**Verdict.** SIMPLIFY. Cheap, high-confidence; addresses both the over-engineering and a live drift bug between docs and code.

---

## F5.3 — Two-evaluator architecture (session-time evolvable + outer-loop fixed)

**Today.** `scripts/evaluate_session.py` lives inside the variant and is fully editable by the meta agent (the program prompts even tell it to). `src/evaluation/` is server-side, fixed, runs `freddy evaluate variant` from outside the variant. `evaluate_variant.py:564-684` orchestrates the outer evaluation. README.md:108-123 documents this as a deliberate split: "session critique is evolvable, outer-loop reward is fixed."

**Why it exists.** Hyperagents (Section 7) explicitly keeps the outer loop unchangeable while letting the inner mutate. Meta-Harness (Section 5) keeps the proposer fixed. Autoresearch follows the standard playbook. The ASYMMETRY is the entire defense against reward hacking.

**What's wrong.** The architecture is correct. The implementation has one hidden honor-system gap that makes it brittle. From `meta.md:70`:

> "Do not modify `_build_critique_prompt` or `GRADIENT_CRITIQUE_TEMPLATE` in `scripts/evaluate_session.py`. ... Biasing this prompt toward leniency terminates sessions earlier with under-cooked output, which the outer scorer (`freddy evaluate variant`) is supposed to punish. **But the outer scorer's reward function has not been verified end-to-end against this attack vector — treat the inner critique prompt as a frozen interface, not a tunable input. The lane infrastructure does not enforce this; the discipline is yours.**"

This is the team telling the meta agent in plain text: "the architecture has a hole, please don't exploit it." That's an honor-system policy in a system whose entire purpose is to evolve programs that maximize score. It's exactly the kind of seam an evolution loop is designed to find. Combined with the fact that `evaluate_session.py` is 367 lines and meta.md says it's "a legitimate evolution target" (line 52) where rubric, aggregation, thresholds, prompts, and invocation strategy are all fair game, the gap between "you may evolve A, B, C, D" and "but please don't touch this one specific function" is wide.

The other failure mode the audit raises — "inner evaluator drift visible only at promotion failure" — is real (Gap 7 in GAPS.md, scored 6/10, on the team's roadmap). Without F5.4 telemetry, you find drift only when a variant scores well on inner critique, beats the search suite, then fails the hidden holdout — a 30+ minute round trip per detection.

**The right model — agentic / hybrid / deterministic.** STRENGTHEN, not redesign. Keep the layered-evaluator architecture intact. Harden the seam.

**Concrete redesign.** (Three layers, in priority order.)

1. **Mechanical gate, not honor system.** Add to layer-1 validation (`evaluate_variant.py:384-411`): `_build_critique_prompt` and `GRADIENT_CRITIQUE_TEMPLATE` get a structural hash check. Compute SHA256 at variant clone time, store in `manifest.json`, fail L1 if changed. Variant authors who legitimately need to evolve the inner critique would have to mutate a clearly-marked "experimental" critique builder (e.g., `_build_experimental_critique_prompt`) which is allowed but invocations from within the standard pipeline are forbidden. This converts honor-system into capability restriction, the pattern the audit memory calls out as the strongest in any pipeline (audit plan R4).
2. **Per-criterion outer-evaluator gating during promotion.** Currently `_search_promotion_summary` checks `require_holdout` only (`evaluate_variant.py`). Add: any variant whose inner-critique pass rate diverges from outer-critique pass rate by more than `max_drift_threshold` (recommend 0.15) on the search suite is blocked from holdout regardless of composite score. This is concrete; it requires F5.4 telemetry to compute.
3. **Sealed inner-critique invocation.** The inner critique runs under the variant's own Python; nothing prevents it from importing a helper that intercepts and rewrites criterion-aggregation logic without touching the listed protected functions. Move inner critique to a subprocess with `python -I` (isolated mode) and an allow-list of importable modules.

**Complexity removed.** Net adds rather than removes — but eliminates the honor-system class of risk (currently load-bearing for safety with zero enforcement). Replaces ~10 lines of meta.md hand-waving with ~50 lines of L1 verification.

**New risks.** (1) Hash check makes legitimate critique-prompt experimentation harder. Mitigation: experimental field is allowed; invocation pattern is what's blocked. (2) Subprocess isolation slows inner critique by ~200ms per call. Mitigation: this runs N times per session, ~30N ms total — invisible against a 300s fixture.

**Verdict.** STRENGTHEN. Highest-leverage intervention in the system because it lets you trust every other simplification (you know drift will be caught). Do this before F5.1 / F5.2 simplifications land.

---

## F5.4 — Inner-vs-outer evaluator correlation telemetry

**Today.** The metric does not exist. `evaluate_variant.py` records `dimension_scores`, `structural_passed`, `dqs_score` per fixture but never compares them against the inner critique's per-criterion pass rate from the session's `results.jsonl`. Drift is invisible until promotion fails on holdout.

**Why it exists/doesn't.** The inner-evaluator data is in the right place — `sessions/<domain>/<client>/results.jsonl` records inner critique pass/fail per artifact (the `KEEP/REWORK/DISCARD` decisions). The outer evaluator data is in scored fixture results. Nothing joins them. The team's own GAPS.md scores this Gap 7 (6/10, "ADDRESSING") with the exact diagnosis: "Lenient evaluator → less rework → lower cost → Pareto frontier REWARDS this." They know.

**What's wrong.** Two consequences flow from absence:

1. **Promotion regressions look like model noise rather than systematic drift.** A variant that quietly biased its inner critique toward leniency may pass search, fail holdout, and look like an "unlucky variance" event because there's no signal that distinguishes "inner judged this 0.85 and outer agreed at 0.83" from "inner judged this 0.95 and outer scored 0.62." The team would correctly conclude that single-fixture variance is high (Gap 18, 7/10) and add re-runs, masking the actual drift signal.
2. **F5.3 hardening can't be evaluated without it.** You can ship the L1 hash check in F5.3 but you can't measure whether it's working — drift could route around hash protection through subtler aggregation tweaks. Telemetry is the audit layer.

**The right model — agentic / hybrid / deterministic.** Pure deterministic. This is exactly the kind of measurement that should never be agentic — telemetry whose entire value is being a fixed reference point.

**Concrete redesign.** ~30 LOC, single PR:

1. In `_score_session` (`evaluate_variant.py:564-684`), after outer scoring, parse the session's `results.jsonl` for the inner-critique pass rate (count of `decision=KEEP` / total evaluations, weighted by criterion).
2. Add to the scored fixture record: `inner_pass_rate`, `outer_pass_rate` (= mean of `dimension_scores` ≥ pass_threshold), `pass_rate_delta`.
3. Aggregate per-variant in `_aggregate_suite_results` — add `mean_pass_rate_delta` and `max_pass_rate_delta_across_fixtures` to `domain_metrics`.
4. Surface in `index.json` per-variant. Plot trend in evolve.sh `score-current` summary output.
5. Add a soft alert: if `mean_pass_rate_delta > 0.1` for any variant, log a `WARN: possible inner-evaluator drift` line during finalization. Do not block promotion — the holdout is the hard gate. This is purely diagnostic.

**Complexity removed.** None — additive. But this is what enables removing other complexity (F5.1, F5.2) safely.

**New risks.** Telemetry can be gamed if the meta-agent reads it and biases mutations to keep delta low while drifting in another way. Low risk because: (a) the meta-agent doesn't currently see scores.json (it's in IGNORED_FILES per archive_index.py:19-25) — extending that ignore-list to include the new fields keeps the metric meta-blind; (b) the holdout remains the hard gate.

**Verdict.** STRENGTHEN. Ship before F5.1 simplifications. This is the cheapest, highest-leverage instrumentation in the system. Already on team roadmap as Gap 7 — this finding upgrades its priority.

---

## F5.5 — `report_base.py` (577 LOC) — parallel findings/report infrastructure

**Today.** `autoresearch/report_base.py` (577 LOC, just verified — file ends at line 577) provides: (a) custom regex-based markdown parser for `findings.md` (`parse_findings`, lines 82-149), (b) hardcoded `BADGE_COLORS` dict for 6 categories CONTENT/SCHEMA/INFRA/PROCESS/API/QUALITY (lines 72-79), (c) bespoke `[CATEGORY] Title` regex (line 119), (d) mistune for markdown→HTML rendering, (e) HTML scaffold + base CSS + Chrome-headless PDF generator. Used by `archive/{v001,v006,current_runtime}/scripts/build_geo_report.py` and similar generators per domain.

The audit claims this is parallel to:
- harness's YAML-front-matter findings.md parser (`harness/findings.py`, 106 LOC) — verified, parses YAML front-matter blocks via regex+yaml, produces `Finding` dataclass (lines 31-65). Used by `harness/review.py` for PR body generation.
- audit pipeline's planned Pydantic Finding envelope — verified from the audit plan (planned, not built).

**Why it exists.** Three independently grown systems, three different output expectations:
- harness Finding → routed to actionable/review (`harness/findings.py:93-106`), no rendering needed beyond markdown PR body.
- audit-pipeline Finding → customer-facing PDF with health score rollup, severity weighting, etc.
- autoresearch findings.md → operator-facing HTML/PDF in dev runs, inspected occasionally.

**What's wrong.** The "three implementations of the same job" framing is half-right and half-wrong:

- **Half right (over-engineered):** `report_base.py:82-149`'s `parse_findings` is a custom-regex markdown parser that handles two title formats (`### [TAG] Title` and `### Title`) and three section headers (Confirmed/Disproved/Observations). It's brittle (silently flushes on section change), HTML-coupled (the parser's output structure mirrors the renderer's needs — note how `tag` is captured and immediately consumed by `BADGE_COLORS` lookup in `render_findings:243-249`). This was almost certainly a 2-hour Python script that grew into a 577-line module because every domain wanted a slightly different report shape.
- **Half wrong (forced abstraction):** The audit suggests "consolidating the 3 parsers into one library." This is the more dangerous move. The three jobs are different:
  - harness must distinguish `category in DEFECT_CATEGORIES AND confidence == "high"` for autonomous routing — needs strict envelope.
  - audit-pipeline must severity-weight for customer-readable health score — needs typed envelope with severity/confidence as Pydantic enums.
  - autoresearch needs none of this; findings.md is operator post-hoc reading material.

A single shared `Finding` envelope across all three pipelines would force harness to drag in customer-facing severity ranks it doesn't use, and force autoresearch's developer-tooling renderer to parse a strict Pydantic envelope when its current `findings.md` is hand-written by agents who don't always follow schema.

**The right model — agentic / hybrid / deterministic.** Deterministic, but with a different consolidation axis than the audit proposes. Don't unify the parser; unify the *envelope spec* and let each pipeline ship its own thin parser.

**Concrete redesign.** Three steps:

1. **Replace `report_base.parse_findings` (lines 82-149) with `mistune`-AST traversal.** mistune is already imported (line 28). Walk the AST for h2/h3 nodes; categorize by h2 text; collect h3 children. Drops ~70 LOC, makes the parser robust to the markdown variations that currently fail silently. ~40 LOC.
2. **Auto-generate per-domain report builders from a domain spec.** The four `build_*_report.py` files in `archive/<v>/scripts/` are 80% identical scaffolding around a `domain → outputs → sections` mapping. Replace with a single `build_report.py` that reads a domain config dict (`{"sections": ["session_summary", "findings", "iteration_log", "report_md", "logs_appendix"], "extra_columns": [...]}`). Removes ~3 × 100 LOC of near-duplicate code.
3. **Publish `Finding` envelope spec (markdown) shared by all three pipelines, not the parser.** A single `docs/finding-envelope-v1.md` defining the YAML front-matter keys + which keys are required for which use case. Each pipeline implements its own parser that conforms; harness keeps its strict YAML parser, autoresearch keeps its loose section-header parser, audit pipeline gets Pydantic. Cross-pipeline communication uses the envelope as protocol, not a shared module.

**Complexity removed.** ~70 LOC from `report_base.parse_findings`. ~200 LOC across the three `build_*_report.py` scripts. Zero change to harness/findings.py or to the not-yet-built audit pipeline. Total ~270 LOC.

**New risks.** (1) mistune AST traversal is dependent on mistune internal API stability — pin the version. (2) Auto-generated report builders force a shared section vocabulary; domain-specific custom rendering loses some flexibility. Mitigation: domain config can include a `custom_sections: [(title, callable)]` escape hatch for one-offs.

**Verdict.** SIMPLIFY (within autoresearch). Don't consolidate across pipelines yet — that's a 2027 problem after the audit pipeline ships and you can see which envelope shape actually wins. The audit's "three implementations" framing is real as observation but premature as prescription.
