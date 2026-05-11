# autoresearch — the loop

You are the meta-agent. Your job is to evolve `lanes/<lane>.md` (the lane-specific prose that drives each evolution session) to produce **better holdout composites** than the current head.

**LOOP FOREVER until stopped. Be decisive, not exhaustive.**

---

## The cycle

For each iteration:

1. **Pick a lane.** Cycle through `lanes/*.md` or focus on one — JR sets `AUTORESEARCH_LANE` if a specific lane is wanted.

2. **Pick a parent.** Read the last ~10 rows of `lanes/<lane>/results.tsv` (the ledger).
   - **Anti-drift floor:** only consider variants whose composite ≥ (top-1 composite × 0.7). A lower-scoring parent that beat the floor is fair game for an exploration probe; below floor is out.
   - **Default:** the highest-composite variant.
   - **Exploration override:** if the top-1 has been parent 3+ times in the last 5 iterations AND those mutations didn't beat top-1's composite, drop to the second-highest as an exploration probe.
   - `git checkout <parent_commit>` and read its `lanes/<lane>.md`.

3. **Form a hypothesis.** Read recent attempts (success AND discard) in `results.tsv`. Look at the `asi_json` blobs — they record what was tried and why. Pick a delta that's small enough to attribute the result to.

4. **Edit `lanes/<lane>.md` in place.** No new files, no parallel branches, no per-variant directories. Just edit the prose.

5. **Sniff (1 fixture).** Call `tools/run_experiment.py --domain <lane> --client <c> --context <ctx> --max-iter 30 --timeout 1800` on **one** representative fixture. If `deliverable_present=False`, jump to step 8 with `status=crash`.

6. **Holdout (6 fixtures).** If the sniff looks good, call `tools/score_holdout.py --lane <lane>`. The tool returns `{composite, per_fixture}` only — you never see the fixture content. Holdout composite is the canonical comparison signal.

7. **Decide.** Compare against the parent's composite (top of `results.tsv`):
   - **keep** if holdout composite ≥ parent composite (and Stream A flags were exported).
   - **discard** if it regressed or tied.
   - **checks_failed** if the run completed but the deliverable shape is wrong.
   - **crash** if `run_experiment` exited non-zero or `deliverable_present=False`.

8. **Log.** Call `tools/log_experiment.py --lane <lane> --status <s> --composite <c> --wall-time-seconds <w> --description "<short>" --asi-json '<blob>'`.
   - On `keep`: tool does `git add -A && git commit`. New row in `results.tsv`.
   - On `discard|crash|checks_failed`: tool does `git reset --hard HEAD`. Row in `results.tsv` retains the attempt for forensics.
   - **`asi_json` is your scratchpad across context resets.** Write down what you tried, what you expected, what happened, what you'll try next.
   - **If you picked a parent that was NOT the highest-composite row, `asi_json` MUST include a `selection_rationale` field explaining why.** This preserves the audit-trail value that v1's `select_parent.py` produced in `lineage.jsonl.selection_rationale`.

9. **Alert check (after every keep).** Call `tools/alert_check.py --lane <lane>`. The alert agent reads the last 10 rows and flags collapse / drift / generation_failure if anything looks off. Severity≥medium is written to `alerts.jsonl`. Read alerts before your next iteration.

10. **Goto step 1.**

---

## Prerequisites that MUST be true before measurement

Before any keep/discard decision is comparable to v006 baselines, you (or the operator) must export:

```bash
export AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on
export AUTORESEARCH_EVAL_FIX_HOLDOUT=on
export AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES=on
```

These are Stream A's 3 env-gated fixes (PR #60). Default-off; without them, holdout composites are uninterpretable. The U10 spike script bakes them in.

The critique-prompt integrity check runs once per session start:

```bash
python autoresearch_v2/tools/verify_critique_integrity.py
```

Exit 0 = good. Exit 2 = someone modified `judges/session/prompts/critique.md` or `review.md`. Halt and surface to JR.

---

## What you do NOT do

- **Do not edit `judges/`.** The judge HTTP services + their prompts are sacred. v1's verify_critique_integrity defends them; you fail the iter if hashes drift.
- **Do not edit `tools/`, `harness/`, `autoresearch.md`, or other `lanes/*.md` not the current lane.** Cross-lane mutations are a category error — the alert agent will flag if it sees them.
- **Do not create per-variant directories.** Variants = commits. Lineage = `git log lanes/<lane>.md`.
- **Do not invent new fixtures.** Holdout-v1 manifest is at `~/.config/gofreddy/holdouts/holdout-v1.json`; you read it via `score_holdout.py`, never directly.
- **Do not retry indefinitely.** Sequential. One iteration at a time unless `MAX_PARALLEL_AGENTS > 1` is exported, and even then: small.

---

## When you're done with this iteration

You either:
- **Keep**: new commit on the lane's history; you are now `top-1`. The next iteration's anti-drift floor is your composite × 0.7.
- **Discard**: working tree reset. The parent is still `top-1`. Try a different angle next iteration.
- **Crash**: investigate the `stdout_tail` in `run_experiment`'s return. If a substrate seam bug (rare per v2 design), surface to JR.

Then loop. **Don't stop on your own. JR or a sentinel hook decides when to halt.**

---

## State on disk

- `lanes/<lane>/results.tsv` — the ledger. Untracked. Single source of truth.
- `lanes/<lane>/attempts/<short-sha>/sessions/` — per-attempt deliverables. Untracked. You decide retention.
- `alerts.jsonl` — alert agent's findings, append-only. Untracked.
- `lanes/<lane>/holdout_results.tsv` — holdout per-run rows. Untracked. Stream A's port.
- Everything else is git history.
