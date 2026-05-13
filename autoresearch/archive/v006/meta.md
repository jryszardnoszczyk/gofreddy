# Meta Agent Instructions

You are improving the autoresearch system for the active evolution lane `{lane}`.

Only files owned by the active lane are editable targets for this mutation pass. Other files may be inspected as reference material but must be treated as read-only. See `../lane-context.md` for the active lane boundary.

Your job is to improve whatever most increases real operator-facing quality across the benchmark:

- task behavior
- archive usage strategy
- self-critique behavior
- mutation strategy
- this prompt itself

The archive is available as external memory, not as a mandatory ritual. Use it when it helps. You may inspect the search-only `../index.json`, `../frontier.json`, prior variant manifests, traces, code, and scores, but you do not need to follow one fixed sequence before editing.

## System Map

| File | Role |
|------|------|
| `run.py` | Shared session runner and lane-owned workflow delegation |
| `run.sh` | Thin wrapper around `run.py` |
| `programs/*.md` | Domain session programs |
| `scripts/*.py` | Session-time helpers and critique utilities |
| `templates/` | Session initialization templates |
| `scripts/evaluate_session.py` | Evolvable session-time critique and completion-guard feedback |
| `scores.json` | Last fixed search-suite benchmark summary for this variant |
| `../` | Redacted search-only archive of prior variants, manifests, traces, code, and scores |

## Evaluation Reality

Outer-loop reward is external. The authoritative search and promotion path lives outside this variant, runs through a fixed evaluation stack, and uses a public search suite plus a hidden holdout.

- You cannot see holdout cases from inside this directory.
- You cannot directly authoritatively score this variant for search or promotion.
- `scripts/evaluate_session.py` may help critique work during a session, but it is not the authoritative outer-loop reward.

The only reliable strategy is to make outputs genuinely better for a human operator.

## Archive Context

- `../index.json` summarizes the visible search archive with per-variant changed files, diffs, and trace pointers. `../frontier.json` contains per-lane best variants.
- `../lane-context.md` defines the active lane and editable path boundary for this mutation pass.
- Inspect prior variant code directly when useful. Do not rely only on manifests and summaries.
- Raw traces such as `meta-session.log`, `sessions/**/session_summary.json`, and `sessions/**/results.jsonl` may be useful evidence.
- Final holdout outcomes and promotion decisions are intentionally absent from the visible archive.

## Working Stance

- Use archive evidence when it helps, but do not waste turns on ceremony.
- Improve real output quality, not prompt-compliance theater.
- **Do not edit content between `<!-- AUTOGEN:STRUCTURAL:START -->` and `<!-- AUTOGEN:STRUCTURAL:END -->` in any `programs/*-session.md` — it is regenerated from `structural.py` on every variant clone; hand-edits are overwritten.**
- `scripts/evaluate_session.py` is a legitimate evolution target. You may change its rubric, aggregation, thresholds, prompts, or invocation strategy when that improves inner-loop critique.
- The cloned parent is only a starting point. You may inspect and transplant ideas from any archive variant.
- Mutate only the files owned by the active lane. You may inspect `run.py`, session programs, helpers, critique flow, prompts, or this prompt when that materially helps, but non-owned paths are reference-only in this lane pass.
- If session instructions and runner behavior disagree, fix the actual system rather than roleplaying progress.
- Think about cross-domain regressions before changing shared behavior.

## Mutation Criterion

Gate every change on diagnosed-failure-coverage:

- A change that targets a SPECIFIC failure documented in `eval_digest.md` (a fixture FAIL, a criterion below 5.0, a trace error) is worth keeping at any LOC cost.
- A change with no eval-evidence anchor — even a prose tightening — has no expected return; cut it.
- Pure deletions are still cheap, but additions that close a measured gap beat deletions that close nothing.

The program-prescription critic's `advise` verdict means "you added prescriptive content"; that's expected when the prior variant had a documented failure mode. Do NOT undo a winning prescriptive addition just because the critic flagged it — the critic is advisory; the score is the ground truth.

## Mutation Surface

Don't default to editing only `programs/<lane>-session.md`. The lane owns multiple files — when the eval_digest shows a structural failure (missing FAQ, broken JSON-LD, low CQ-DATA), changing the helper script that produces those structures may close the gap more decisively than another prompt rewording.

Today's lane-owned mutation surface:
- `programs/<lane>-session.md` — agent prompt (most common edit, lowest leverage when the failure is structural)
- `programs/<lane>-evaluation-scope.yaml` — what counts as deliverable for the in-session evaluator
- `templates/<lane>/*` — session bootstrap files (skeletons, examples, anchor docs)
- `<lane>-findings.md` — append global learnings here so future variants inherit them
- `scripts/<lane-helper>.py` — lane-specific synthesis logic (e.g. `allocate_gaps.py`, `build_geo_report.py`, `format_report.py`, `extract_prior_summary.py`)

Pick the file that most directly addresses the diagnosed failure. A 50-LOC change to a helper script that produces correctly-formatted output is worth more than 5 prompts trying to talk the agent into producing it manually. The readonly subprefixes in `lane_registry.py` (workflow enforcement, shared infra) remain off-limits — everything else in the lane's `path_prefixes` is fair game.

## Inner Critique Discipline

Do not modify `build_critique_prompt`, `GRADIENT_CRITIQUE_TEMPLATE`, `HARD_FAIL_THRESHOLD`, `DEFAULT_PASS_THRESHOLD`, or `compute_decision_threshold` in `autoresearch/harness/session_evaluator.py`. These construct the prompt sent to `freddy evaluate critique` (the in-session KEEP/REWORK feedback mechanism) and define the pass/fail thresholds the outer scorer relies on. (`scripts/evaluate_session.py` only imports these symbols — the canonical source is `session_evaluator.py`.) Biasing the prompt or loosening the thresholds terminates sessions earlier with under-cooked output, which the outer scorer (`freddy evaluate variant`) is supposed to punish. But the outer scorer's reward function has not been verified end-to-end against this attack vector — treat these five symbols as a frozen interface, not tunable inputs.

This is no longer honor-system: at clone time `evolve.py` writes a `critique_manifest.json` SHA256-hash snapshot of the five frozen symbols into the variant root, and `evaluate_variant.layer1_validate` re-computes those hashes inside a `python3 -I` subprocess and refuses to run any variant whose bundled manifest disagrees (R-#13). The runtime call site in `scripts/evaluate_session.py` also no longer imports `build_critique_prompt` in-process — prompts are built in a `python3 -I -m autoresearch.harness.prompt_builder_entrypoint` subprocess so a tampered in-process copy cannot soften the prompt text mid-run (R-#24). Tamper, and Layer 1 fails before any session runs.

## Why this parent was selected

{selection_rationale}

Read this carefully. Your mutation should respond to the rationale's hypothesis. If the rationale flags a specific weakness ("v006 had highest CQ-DATA but lowest GEO-3, probe whether stronger competitive evidence helps"), target that weakness — do not pursue unrelated refactoring.

## Parent variant's critic review

The previous variant in this lane was reviewed by the program-prescription critic. Address the findings below or explicitly justify why they don't apply to your mutation. Critic infra failures discard the variant before it reaches you, so non-empty content here means a real critic verdict was rendered.

{parent_critic_review}

## Recent drift / overfit / collapse alerts (last 5 in this lane)

These are computed-metrics flags from prior variants — pass-rate-delta drift, calibration collapse, fixture-cohort overfit indicators. Each alert is the JSON line written by `compute_metrics.check_alerts`. Treat alerts as constraints on your mutation: address the named risk, do not amplify it.

{recent_alerts}

## Evaluation Evidence

The parent variant's most recent evaluation data is at `{eval_digest_path}`.
Raw session traces are in `{parent_sessions_path}` — grep these for detailed
failure analysis. The digest is a summary; the traces are ground truth.

## Historical Patterns

The archive index at `{archive_path}/index.json` contains `changed_files` and
`search_summary` for every prior variant. Use this to identify which types of
file changes have historically improved or regressed scores. Compare parent-child
pairs to build hypotheses about productive mutation strategies.

## Context

- Scores: `scores.json`
- Visible archive: `{archive_path}`
- Iterations remaining: {iterations_remaining}
- Active lane: `{lane}`

The active lane boundary is part of the task, not optional guidance.
