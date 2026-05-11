# Lane: marketing_audit — full-stack marketing audit

**What this lane does:** evolves the prose at `lanes/marketing_audit.md` so each session produces a 9-section `findings.md` + a multi-format report covering findability, narrative, acquisition, experience, competitive intelligence, monitoring, AI visibility (GEO), state of business, and martech compliance.

**Baseline you're trying to beat:**
- Anthropic v1: 0.5/8 KEEP — the lane's acceptance run
- DWF: 1.0/8 KEEP
- Perplexity: 1.0/8 KEEP

These are partial-session baselines from when the lane shipped (2026-05-08, PR #45). New baselines must be established post-marketing-audit driver loop wiring (`bash autoresearch/archive/v006/scripts/run_marketing_audit_to_complete.sh`).

---

## Deliverable contract

The session writes a stack of artifacts under `sessions/marketing_audit/<client>/`. Each session MUST satisfy:

1. **`findings.md` with all 9 deliverable sections** — `findability`, `narrative`, `acquisition`, `experience`, `competitive`, `monitoring`, `geo` (display label: "AI Visibility"), `state_of_business`, `martech_compliance`.
2. **`proposal.md`** (when present) **contains the 3 capability-registry tier headers in fixed order**: `fix_it`, `build_it`, `run_it`.

Plus the other listed deliverables: `report.md`, `report.json`, `report.html`, `report.pdf`.

Any structural failure → `checks_failed`.

---

## Fresh-strategy driver loop (CRITICAL)

This lane uses **fresh-strategy single-phase-per-subprocess** mode — `default_timeout=2400, multiturn_timeout=10800, stall_limit=7` in v006/workflows/marketing_audit.py. The 8-stage pipeline requires `run.py` to be re-invoked phase-by-phase by the driver script at `autoresearch/archive/v006/scripts/run_marketing_audit_to_complete.sh`.

`tools/run_experiment.py` honours this lane-specific default — when `--domain marketing_audit` is passed, `strategy` defaults to `fresh`. If you forget to invoke the driver loop externally, the session reaches `IN_PROGRESS` and never `COMPLETE` (this was the bug behind the 3 stuck Stripe/DWF/Perplexity audits pre-fix).

For v2 mini-spikes: invoke the driver script from your test harness; do NOT call `run_experiment` directly per fixture.

---

## The 8 MA judges (your fitness function)

Composite = geometric mean across MA-1 .. MA-8. The lane was extensively pressure-tested in PR #45's §7.7 acceptance test against anthropic-test1 (all 6 stages, halted at ship-gate, 117KB report.html with 36 findings).

Key levers from PR #45 dry-run + deep-review:
- **9-axis labels** must NOT be case-mangled — `state_of_business` not `State of Business` in the structural gate; display labels are separate.
- **Brand & Narrative section** anemic-output was a known regression class — guard against thin narrative analysis.
- **Sources hrefs** must be valid (broken Sources hrefs caused a PR #45 fix).
- **Phantom Monitoring score** — don't fabricate a monitoring composite if no monitoring substage ran.

---

## 2 of 5 callables wired (v1 lane registry)

`custom_score` + `custom_validate` are wired. `custom_promote` stays None until post-audit-3 holdout fixtures land. `custom_mutate` uses the default meta-agent. v2 preserves all of this through the v006 workflow subprocess.

---

## What you CANNOT edit

- `autoresearch/archive/v006/workflows/marketing_audit.py`
- `autoresearch/archive/v006/workflows/session_eval_marketing_audit.py`

Plus the universal don't-edit rules.

---

## Mutation surfaces that worked (per PR #45)

- The 11 production bug fixes shipped during dry-run + deep-review (silent rc=1 retry collision, max_turns budgets, schema strictness, F4 short-circuit + stale-clear, _safe_format, RUBRICS registration, deploy scaffolds, broken Sources hrefs, phantom Monitoring score, case-mangled 9-axis labels, anemic Brand & Narrative). These are PROSE-side mutations baked into v006/programs/marketing_audit-session.md — v2 inherits them via the subprocess.

## Mutation surfaces that regressed

- Multiturn-strategy default — collapses the 8-phase pipeline into one agent context; either hits context limits or produces shallow phase work. Always use fresh-strategy via the driver script.

---

## Fixture coverage

- Search-v1: `marketing_audit-*` fixture_ids in `eval_suites/search-v1.json`.
- Holdout-v1: per-lane fixtures in `~/.config/gofreddy/holdouts/holdout-v1.json`.

---

## Recent history pointers

- `git log --oneline lanes/marketing_audit.md`
- Last ~10 rows of `lanes/marketing_audit/results.tsv`
- `alerts.jsonl` filtered by `lane=marketing_audit`
