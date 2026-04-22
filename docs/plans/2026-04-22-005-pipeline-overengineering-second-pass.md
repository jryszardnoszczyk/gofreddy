---
title: "Pipeline over-engineering — second-pass deep research"
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-004-pipeline-overengineering-deep-research.md
---

# Pipeline over-engineering — second-pass deep research

After the first pass produced 26 confident recommendations, JR asked: "are there other places in the auto-research code where we should be making these changes — i.e., reducing programmatic bloat with adaptable agentic behavior?"

This is the second-pass result. Three parallel research agents audited surfaces NOT covered in the first pass.

## Scope of second pass

- **Cluster 7 (autoresearch extras):** `select_parent.py`, `frontier.py`, `compute_metrics.py`, `archive_index.py`, `evolve_ops.py`, `lane_runtime.py`, `lane_paths.py`, `geo_verify.py`, `archive_cli.py`
- **Cluster 8 (evaluation + competitive):** all of `src/evaluation/`, `src/competitive/service.py`, `src/competitive/markdown.py`, sample monitoring adapter `src/monitoring/adapters/news.py`
- **Cluster 9 (providers + CLI):** `src/seo/providers/dataforseo.py`, `src/geo/providers/cloro.py`, `src/fetcher/instagram.py`, `cli/freddy/commands/{monitor,evaluate,iteration,auto_draft}.py`

## Headline result

**23 new findings: 12 HIGH, 8 MEDIUM, 3 LOW.**

The biggest concentration is in **`src/evaluation/`** — 8 findings, 5 HIGH. The "fixed outer-loop evaluator" has accumulated content-judgment-in-Python that survived three rounds of prior audit. This is structurally similar to the autoresearch program prescription drift (F5.1) but living in a different file: every time a judge hallucinated, we calcified a guard in code; the guards have grown into a content-judgment layer.

## Top 12 HIGH-priority new findings

| # | ID | Surface | What it is | Why agent wins |
|---|---|---|---|---|
| 29 | F-A.1 | autoresearch parent selection | sigmoid × novelty formula picks next parent variant | Agent reads trajectory + failure modes; rationale lands in lineage |
| 30 | F-A.2 | autoresearch alerts | hardcoded thresholds (`drift>0.35`, `fixture_sd>0.30`) | Agent distinguishes real drift from gen-to-gen noise |
| 31 | F-A.3 | autoresearch geo_verify | raw JSON dump + boilerplate "compare manually" footer | Agent produces actual PASS/PARTIAL/FAIL verdict |
| 32 | F-E.1 | evaluation judges | `fuzzy_match` token-overlap (0.5 threshold) for evidence verification | Semantic paraphrase is what LLMs do; threshold-dance (0.8→0.5) is the tell |
| 33 | F-E.2 | evaluation judges | gradient evidence-gate caps score at 3 if <2 quotes | Calibration judge generalizes across criteria with different evidence shapes |
| 34 | F-E.4 | evaluation service | per-domain word-range length factor (e.g. competitive 2000-5000) | Agent picks range from input data richness, not 2025 guess |
| 35 | F-E.5 | evaluation structural | 500-char + 3-header gate on competitive briefs | Rubrics already judge substance; gate preempts with worse heuristic |
| 36 | F-E.6 | evaluation structural | "no_excessive_rework" >3 attempts cap + 50% synth ratio | Process-efficiency gates kill good output that took rework |
| 37 | F-E.7 | evaluation structural | digest-hallucination regex (`"Digest persisted" in session.md`) | Claim-grounding agent catches paraphrases the regex misses |
| 38 | F-E.10 | competitive service | `_ad_domain_matches` exact-host filter silently drops legit ads | Agent recovers tracked-URL redirects + multi-domain brands |
| 39 | F-P.2 | monitor CLI | `_build_summary` (top-20-by-engagement + word-length themes + 3-per-source recency) | Word-length themes produce junk; engagement is platform-naive |
| 40 | F-P.3 | evaluate CLI | `_DOMAIN_FILE_PATTERNS` hardcoded dispatch (with comments admitting past bugs) | Producer-owned YAML or classifier agent ends silent-ignore bugs |

## Pattern observations

**The src/evaluation/ pattern.** Every file in the supposed-fixed outer-loop evaluator has accumulated content-judgment in Python. The trail: a judge hallucinated → we added a Python guard → the guard calcified → it's now content-judgment-in-code. F-E.5/6/7 are all variations: `structural.py` has become a second judge written in Python, but worse than the LLM judges because it can't reason. Per the cluster 8 agent: *"gated the judge on a heuristic because the judge used to hallucinate; heuristic calcified into content-judgment-in-code."*

**The CLI summarization pattern.** When a CLI command has to collapse a large result set (monitor mentions, evaluate file lists), the collapsing logic is hand-written: word-frequency themes, length-gates, top-N thresholds. F-P.2 and F-P.3 are the two clearest cases. These are exactly where qualitative work is happening with no LLM in the loop.

**The provider discipline is right.** DataForSEO, Cloro, Instagram providers all stop cleanly at API-shape normalization. They DON'T try to classify toxic backlinks, judge citation prominence, or filter mentions. The qualitative creep happens downstream in CLI commands and the evaluator. Provider layer is a positive exemplar — apply same discipline elsewhere.

**Two findings overlap with prior audit:** F-E.5 deepens F5.2 (the structural-validator drift bug); F-A.2 is structurally similar to F3.1 (deterministic scoring vs. agent synthesis). These confirm the prior pattern at new code sites.

## Recommendations from this pass

### Do these now (cheap, high-value)

- **#29 (F-A.1) parent selection** — affects every variant evolution; rationale-in-lineage makes the loop debuggable. Expensive failure mode (bad parent picks waste a generation = ~30 min).
- **#31 (F-A.3) geo_verify verdict** — currently rubber-stamps verification by punting comparison to human. One LLM call converts theater into real verification.
- **#35 (F-E.5) drop 500-char gate** — depends on the F5.2 doc-regen also landing. Rubrics already judge substance. Net: one fewer cliff-failure source.
- **#37 (F-E.7) claim-grounding agent** — the regex guard at `structural.py:276-281` only catches ONE hallucination phrasing. Agent catches paraphrases. Cheap.
- **#39 (F-P.2) monitor.py summary** — "themes via word-length>4" is almost certainly producing junk nobody has audited. Replace with summarizer agent.
- **#40 (F-P.3) evaluate.py file patterns** — hardcoded dispatch with comments admitting past bugs. Producer-owned YAML is the cheap fix; classifier agent is the agentic fix.

### Tactically important (do soon)

- **#30 (F-A.2) alert thresholds** — three magic constants currently produce alarm fatigue or silent drift; agent lets them be context-aware.
- **#32 (F-E.1) fuzzy_match → paraphrase agent** — the threshold-dance history (0.8→0.5) is the strongest signal that this code is fighting the wrong battle.
- **#33 (F-E.2) gradient evidence-gate** — the 5→3 cliff is mathematically ugly; calibration judge fixes it.
- **#36 (F-E.6) no_excessive_rework + synth ratio** — kills good output that took thoughtful rework. Move signals to rubrics.
- **#38 (F-E.10) ad-domain filter** — silently drops legit ads. Agent fallback for near-matches.

### Structural / architectural

- **#34 (F-E.4) length-factor formula** — domain-blind word ranges; agent picks per audit.
- Other MEDIUM/LOW findings are real but lower-leverage; see cluster docs for details.

## Updated total count

After this pass, the full set of confident recommendations:

- **Pass 1 (recorded):** 26 confident recommendations + 4 honest withdrawals + 2 not-yet-decided
- **Pass 2 (this doc):** 23 new findings (12 HIGH worth treating as recommendations; the other 11 worth recording but lower priority)

**If we promote the 12 HIGH from pass 2 to confident recommendations, total = 38.**

The 8 MEDIUM and 3 LOW from pass 2 should be triaged but aren't urgent.

## Pointers to deep analyses

- [Cluster 7: Autoresearch extras (F-A.1..5)](2026-04-22-005-research-cluster-7-autoresearch-extras.md)
- [Cluster 8: Evaluation + competitive (F-E.1..12)](2026-04-22-005-research-cluster-8-evaluation-competitive.md)
- [Cluster 9: Providers + CLI (F-P.1..6)](2026-04-22-005-research-cluster-9-providers-cli.md)

## Open question for JR

We've now identified ~38 confident recommendations across two passes. Is there a third pass worth doing — e.g., the frontend, the supabase migrations, the api routers, the autoresearch programs themselves (`programs/*.md` content audit)? My honest read: probably not — the high-leverage agentification candidates concentrate in (a) evaluation/scoring, (b) CLI summarization, (c) autoresearch selection/alerts, all of which we've now covered. Frontend rendering is correctly deterministic; supabase migrations have no agent role; API routers are mostly thin handlers. **Recommend stopping the discovery phase and starting on the implementation triage.**
