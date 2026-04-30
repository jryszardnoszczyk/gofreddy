# Handoff: lock K-1, K-3, K-11, K-13 → trigger /ce:plan

**Reading-order link:** Open this doc first. Then read the brainstorm
(`docs/brainstorms/2026-04-26-harness-fixer-autoresearch-fusion-requirements.md`)
in this same worktree. The brainstorm's §10 lists 13 K-decisions; you lock four of them.

## What you inherit

- **Worktree:** `.worktrees/harness-fixer-decisions/` (you're already in it).
- **Branch:** `plan/harness-fixer-decisions` — cut from `origin/main@dedb25d`.
  Set up to track `origin/main` (this is fine for now; you'll push to a same-named
  remote branch when done).
- **Brainstorm at HEAD:** the 414-line lane-registry-aware revision is already on this
  branch as commit `fd703b7`. You edit IT — not any other copy.
- **Live `harness/prompts/fixer.md`:** post-K-12 patches (P1+P2+P5) — already shipped
  on origin/main as `58f8044`. Do NOT re-patch.
- **`autoresearch/lane_registry.py`:** the live LaneSpec contract (242 LoC). Read it.

## Your job, exactly

Lock four K-decisions in the brainstorm. Three are pure thinking (K-1, K-11, K-13).
One has a small design surface (K-3 sub-decision (b): `verdicts/manifest.json`
post-run hook schema). NO code changes outside the brainstorm in this work.

After locking, push the branch and call `/ce:plan` to produce the implementation
plan. The brainstorm's "Next Steps" names the four input docs.

## Required reading (in order)

1. **`docs/brainstorms/2026-04-26-harness-fixer-autoresearch-fusion-requirements.md`**
   in this worktree — the 414-line brainstorm. §10 lists the 13 K-decisions; locking
   K-1/K-3/K-11/K-13 is your job. Note that §10 also flags K-7 + K-8 as RESOLVED by
   the lane_registry refactor (don't relitigate) and K-12 as SHIPPED on main as
   commit `58f8044` (don't re-patch).
2. **`autoresearch/lane_registry.py`** in this worktree (242 LoC) — the live LaneSpec
   contract. Note `file_hash` / `compute_manifest` / `verify_manifest` at lines
   223-243. K-1's freezing-mechanism portion is already resolved by these utilities.
3. **`docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md`** —
   §"Known Divergence Points" lists 7 deferred axes. The brainstorm already locked
   DPs #1, #2, #4 in its §7 "Divergence Locks". DON'T re-litigate those.
4. **`docs/architecture/lane-registry.md`** — LaneSpec field reference + worked
   example for adding a research-shaped lane.
5. **`harness/prompts/fixer.md`** in this worktree — the v0 fixer prior the lane will
   freeze (post-K-12 patches).
6. **`harness/prompts/verifier.md`** — the frozen judge that the fixer must satisfy.
7. **`harness/engine.py`** lines 92-153 (`Verdict` schema) and lines 17-26 in
   `harness/findings.py` (defect taxonomy + `Finding` schema). These are candidates
   for the K-1 frozen-content list.
8. **`harness/safety.py`** — the leak-detection regex JR raised as a possible K-1
   addition.
9. **`harness/runs/`** — sample 2-3 recent run directories. Look at `harness.log`,
   `verdicts/<track>/<id>.yaml`, and `findings.md`. K-3 sub-decision (b) needs a
   schema for `verdicts/manifest.json`; you can only design it after seeing what
   data is actually emitted.

## Authoritative branch state at handoff (2026-04-29)

| Branch | HEAD | Contents |
|---|---|---|
| `origin/main` | `dedb25d` | K-12 patches at `58f8044`; brainstorm 414-line version present via `8952747` rescue commit |
| `origin/plan/harness-fixer-autoresearch-fusion-requirements` | `7883266` | Original brainstorm + revision history. **Reference only.** Don't push to it. |
| `origin/plan/audit-engine-fusion-v1` | `3f1698d` | Marketing_audit fusion plan (1,951 lines). Reference only. |
| **`plan/harness-fixer-decisions` (this branch)** | `fd703b7` | brainstorm imported from `7883266`. **You commit your locks here.** |

## The four blockers — what to deliver for each

### K-1 — Frozen content list

The brainstorm §10 K-1 names six frozen items: `verifier.md`, Finding schema, Verdict
schema, defect taxonomy, `_VERIFIED_TOKENS` / `_FAILED_TOKENS` token sets. One open
candidate: should `harness/safety.py`'s leak-detection regex (`_FIXER_REACHABLE` in
`harness/config.py`) also be SHA256-frozen?

**Your output:** ~100-150 words in the brainstorm under §10 K-1. Recommend YES or NO
on `harness/safety.py` inclusion with reasoning. Identify any *other* frozen-content
candidates you discover during analysis — but be conservative.

**Trade-off:**
- **Frozen too narrowly:** meta-agent could mutate behavior in unexpected places.
- **Frozen too broadly:** every legitimate harness improvement requires a v0 re-freeze
  cycle. Operator burden compounds.

Adding a 7th frozen item requires real evidence the meta-agent could exploit it.

### K-3 — Fixture canonicalization

Two sub-decisions per the brainstorm:

**(a) `golden_outcome` source.** Each fixture is `(Finding YAML, base_sha, golden_outcome)`.
Where does `golden_outcome` come from?
- Option A: read `harness/runs/run-*/verdicts/<id>.yaml` verbatim. Free, but inherits
  historical verifier flakes (Bugs #11/#17/#18 from `engine.py`).
- Option B: JR re-judges ~30 historical verdicts. ~2.5 hrs of JR's time. Scrubs flakes.
- Option C: hybrid — start with verbatim, audit-flag the K=5 highest-disagreement
  fixtures for re-judge.

**Your output:** recommend one option with reasoning. Show the trade-off. Don't decide
which fixtures to re-judge — JR makes that call after picking an option.

**(b) `verdicts/manifest.json` post-run hook.** The brainstorm says: emit a post-run
hook in `harness/run.py` that captures `(finding_id → base_sha, commit_sha,
verdict_status)` from `harness.log`. ~2-3 hours of new code (NOT in this work — just
design it).

**Your output:** propose the JSON schema concretely. Pseudocode the parsing logic
(grep `harness.log` for `verify phase: <id> (commit <sha[:8]>)` lines + correlate with
`verdicts/<track>/<id>.yaml` files). Identify edge cases:

- Findings that were `--fixers-only`-resumed across multiple runs (does `harness.log`
  get appended or rewritten?)
- Findings that hit the silent-hang rate-limit (no commit_sha at all)
- Findings where the fixer wrote `harness/blocked-<id>.md` but no commit
- The legacy `run-20260422-224908` (Bug #17 contamination — should the manifest tool
  refuse to emit for this run, or emit with a `tainted: true` flag?)

This is the more substantial K-3 deliverable. ~250-350 words in the brainstorm.

### K-11 — Order of operations vs marketing_audit fusion

Brainstorm's current recommendation: **harness_fixer ships first** (smaller scope,
internal-only, validates LaneSpec substrate before customer-facing surface). The
marketing_audit fusion plan is 1,951 lines / 7-9 weeks; harness_fixer is ~3 weeks.

**Your output:** ~150-200 words. Test "harness_fixer first" against three concrete
scenarios:

1. What if marketing_audit's plan exposes a LaneSpec gap (a 6th callable, a 10th data
   field) that harness_fixer's plan would have caught earlier? Is harness_fixer
   genuinely a strict subset of marketing_audit's complexity, or could it be missing
   something only marketing_audit reveals?
2. What if both ship in parallel? The brainstorm claims the registry is additive.
   Verify by reading `lane_registry.py:LANES` — is adding two new dict entries
   genuinely independent?
3. What does "harness_fixer first" actually need on the marketing_audit side? E.g.,
   is the `_INNER_PHASE_TAGS` allowlist extension (lane-registry-plan DP #6)
   load-bearing for harness_fixer too?

End with: serial-harness-first / serial-marketing-first / parallel.

### K-13 — verifier_report.json schema

Brainstorm proposes:
```json
{
  "finding_id": "str",
  "verdict": "verified|failed|blocked",
  "probes_passed": "list[int]",
  "reason": "str",
  "wall_clock_s": "float",
  "tokens_in": "int",
  "tokens_out": "int"
}
```

**Your output:** ~150-200 words. Confirm or revise. Specifically address:

- Should `probes_passed` be `list[int]` (which probes by number) or
  `dict[str, bool]` (which probes by name → pass/fail)? The latter is friendlier to
  dropping/adding probes later. The former is smaller.
- Where does the post-verify hook in `harness/engine.py:verify` get the token counts
  from? Read `harness/engine.py` — is there a `ResultMessage` JSON parsing step that
  exposes `tokens_in`/`tokens_out`, or is this new instrumentation?
- What field captures the `commit_sha` being verified? The brainstorm doesn't list
  it; HM-3 needs it to compute the `changes.txt` artifact.
- Is there a flake/error case (silent rate-limit hang, malformed verdict YAML) where
  the report should be emittable but with `verdict: error` or similar? Currently the
  enum is `verified|failed|blocked`.

End with the final schema you'd commit to the brainstorm.

## Working procedure

1. Read the required materials above in the listed order.
2. Verify you're on the right branch:
   ```
   git branch --show-current   # should print: plan/harness-fixer-decisions
   git log --oneline -3        # top should be fd703b7 (brainstorm import)
   ```
3. Edit ONLY `docs/brainstorms/2026-04-26-harness-fixer-autoresearch-fusion-requirements.md`.
   Update the §10 entries for K-1, K-3, K-11, K-13 with locked recommendations. Update
   the brainstorm's "Outstanding Questions / Resolve Before Planning" section to
   reflect what's now resolved.
4. Commit:
   ```
   git add docs/brainstorms/2026-04-26-harness-fixer-autoresearch-fusion-requirements.md
   git commit -m "$(cat <<'EOF'
   plan(harness-fixer): lock K-1, K-3, K-11, K-13 — brainstorm ready for /ce:plan

   K-1: <one-line summary of the lock>
   K-3: <one-line summary>
   K-11: <one-line summary>
   K-13: <one-line summary>

   Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
   EOF
   )"
   ```
5. Push:
   ```
   git push -u origin plan/harness-fixer-decisions
   ```
6. Then trigger `/ce:plan` against the brainstorm. Its "Next Steps" names the four
   input docs.

## Hard rules (per JR — non-negotiable)

- **NO destructive git operations.** Specifically: NO `git reset --hard`, NO
  `git push --force`, NO `git branch -D`, NO `git clean -fd` outside scratch dirs,
  NO rewriting published commits. If a state looks weird, report it to JR — DO NOT
  "fix" it by force.
- **NO "while I'm here" scope expansion.** This handoff is K-1 + K-3 + K-11 + K-13
  ONLY. If you discover K-4 (HM-1..HM-8 weights) needs revision, surface it as a
  follow-up — don't rewrite the brainstorm beyond the four targets.
- **NO new LaneSpec fields.** The lane-registry plan explicitly forbids 6th-callable /
  10th-data-field expansion; the brainstorm's three Divergence Locks (#1, #2, #4)
  honor this. K-1/K-3/K-11/K-13 should not require any new LaneSpec surface. If you
  find one is unavoidable, STOP and surface it as a hard-stop to JR.
- **Don't re-patch K-12.** `harness/prompts/fixer.md` is locked at origin/main's
  current state. Brainstorm K-12 says SHIPPED — leave it.
- **Don't litigate K-7 or K-8.** The lane-registry refactor resolved them.
- **Don't touch other branches.** This branch is `plan/harness-fixer-decisions`. Do
  not push to `plan/harness-fixer-autoresearch-fusion-requirements`, `main`, or any
  other branch. Do not merge this branch yourself — JR opens the PR.

## Hard-stop conditions — escalate to JR before continuing

- If reading `lane_registry.py` reveals a missing field or callable that K-1/K-3/K-11/K-13
  would force you to add, STOP and surface it.
- If reading `harness/runs/run-*/` reveals the fixture corpus is unworkable for K-3
  (e.g., `harness.log` is missing on >50% of runs), STOP and surface it.
- If `git push origin plan/harness-fixer-decisions` is rejected, STOP and surface it
  — DO NOT force-push.
- If the brainstorm at `fd703b7` has been edited by someone else between when you
  read it and when you go to commit (i.e., `git fetch origin` shows
  `plan/harness-fixer-decisions` ahead of you), STOP and surface it. DO NOT rebase
  or merge automatically.

## Report back to JR at the end

5-bullet summary:
1. K-1 lock — what was added/excluded from the frozen list
2. K-3 lock — golden_outcome strategy + manifest schema headline
3. K-11 lock — order chosen + key reasoning
4. K-13 lock — final JSON schema
5. Commit SHA + push status; whether `/ce:plan` was triggered or is still pending

If anything is unresolved, list as "Open for JR".

## A note on the workflow you're inheriting

JR has been deliberate about not letting agents take destructive shortcuts. Two
prior incidents in this fusion work shaped that:
- A lane-registry refactor handoff prompt got executed via a forked agent before
  proper review; the substrate-plugin variant over-engineered the problem (5028351 →
  reverted to bare-bones LaneSpec). Lesson: don't propose substrate when callable
  hooks suffice.
- An agent attempted to "clean up" a stale local commit via `git reset --hard`; JR
  rejected this with explicit caps-lock prohibition. Lesson: surface state oddities,
  don't normalize them.

Stay tight to the four K-decisions, lock them with reasoning, push, hand back. That
is the work.
