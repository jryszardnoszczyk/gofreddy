# Rotation-policy agent task

**Invocation:**
```bash
claude --print --input-file docs/agent-tasks/rotation-policy.md \
  --var pool=holdout-v1 \
  --var manifest_path=~/.config/gofreddy/holdouts/holdout-v1.json
```

**Cadence:** monthly. Skip for the first 90 days after MVP — the initial Phase 1 taxonomy partition is authoritative until ≥3 months of `kind="saturation_cycle"` events have accumulated.

**Goal:** produce an updated `anchors / rotating` partition for a holdout pool, based on observed saturation and discriminability history. Operator reviews the proposed diff + commits.

## Inputs (via `--var`)

| Variable | Example | Purpose |
|---|---|---|
| `pool` | `holdout-v1` | Which pool's partition to reconsider |
| `manifest_path` | `~/.config/gofreddy/holdouts/holdout-v1.json` | Current manifest; carries the current `rotation` block |

## Steps

The agent must reason over recovery; do not hard-branch in this spec.

1. **Read saturation history.** Filter `~/.local/share/gofreddy/events.jsonl` for `kind="saturation_cycle"` and group per fixture. Need ≥3 months of data for each fixture to reason about stability; fixtures with less history cannot be promoted to anchor or rotated out.

2. **Read discriminability verdict history** per holdout fixture from prior `freddy fixture discriminate` runs (JSONL output under `~/.local/share/gofreddy/fixture-cache/<pool>/<fixture_id>/discriminability/`). Missing-file tolerance: a fixture never run through discriminate cannot be moved; note it and proceed.

3. **Read current partition** from `$manifest_path`'s `rotation` block (`anchors_per_domain`, `random_per_domain`). Combined with the domain fixture lists this gives the current anchor/rotating split.

4. **POST to the unified system-health agent:**
   ```
   POST ${EVOLUTION_JUDGE_URL}/invoke/system_health/saturation
   Authorization: Bearer ${EVOLUTION_INVOKE_TOKEN}
   Body:
     {
       "role": "saturation",
       "mode": "rotation_proposal",
       "pool": "<pool>",
       "cycle_events": <per-fixture aggregated saturation history>,
       "discriminability_history": <per-fixture verdict lists>,
       "current_partition": <the anchor/rotating split read from manifest>
     }
   ```
   The judge-service's `system_health_agent` handles `mode="rotation_proposal"`; no new autoresearch Python is required.

5. **Print the agent's proposed partition + reasoning.** Write to stdout a diff in the format:
   ```
   Domain: geo
     anchors:   v1.0  →  v1.1
       [remove] geo-bmw-ev-de  (saturated 4/5 of last 6 cycles; discriminability=not_separable last 3 runs)
       [add]    geo-stripe-docs-gated (high discriminability 5/6 cycles; entering stable regime)
     rotating:  v1.0  →  v1.1
       (complement)
   ```

6. **If the operator approves**, rewrite the manifest's `rotation` block and commit the diff to `docs/plans/rotation-policy-log.md` (in-repo; the manifest itself lives out-of-repo and is not committed). The log entry carries:
   - Timestamp of the run
   - Agent's raw reasoning (verbatim)
   - The diff (before → after anchor/rotating sets per domain)
   - Operator approval note (who approved, what they checked)

## Output contract

- **Exit 0** with a stdout diff + reasoning when a proposal is ready for review.
- **Exit 1** when insufficient data (fewer than 3 months of saturation events per fixture) — print which fixtures need more data.
- **Exit 2** on configuration error (manifest missing, judge unreachable).

## Why this is an agent task, not a CLI

Partition changes are low-frequency, high-reasoning: they depend on trend observation across months of data, detection of correlated saturation, and judgment about which fixtures stabilize into "anchor" stability vs. continue rotating. A Python CLI would have to encode rules for each of those judgments; the agent can reason about them with full reasoning traces that the operator can audit.

## Agent-side behavior guidance

- Be conservative: do not propose changes unless ≥2 consecutive cycles agree that a fixture's role should change.
- Prefer staying pat: if the agent's confidence is <0.8, return "no change proposed" with reasoning about what data would be needed.
- Do not propose changes that would result in `< anchors_per_domain` fixtures in any domain — the manifest expects a minimum count.
- When in doubt, reason about it in the output rather than silently hide uncertainty.
