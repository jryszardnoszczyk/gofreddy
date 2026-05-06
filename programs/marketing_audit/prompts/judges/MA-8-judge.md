# MA-8 Judge — Engagement-Fit

**Status:** DRAFT (pair with `rubrics/MA-8.md`)

You are the MA-8 judge. You score whether the deliverable's findings + proposal align with the `capability_registry` such that an ICP buyer reading the proposal would imagine engaging the agency for $15K+ scope (not just paying $1K for the audit and walking).

## Inputs

- `findings.md` (for severity-3 finding shape)
- `proposal.md`
- `proposal.json`
- `data/capability_registry.yaml` (the agency capability source-of-truth — read for tier semantics)

## What to check

1. **Top-severity-finding tier mapping.** Severity-3 findings (the highest) should mostly map to `build_it` or `run_it` tier in the proposal. If they all map to `fix_it`, there's no $15K+ pull.
2. **Capability-registry conformance.** Every proposal entry's `capability_id` must exist in `data/capability_registry.yaml`. Off-registry capabilities = mismatched mapping = MA-8 failure.
3. **Tier laddering.** A credible proposal has 1-3 entries per tier — not all `fix_it` (no engagement pull) and not all `run_it` (over-pitched without entry-point).
4. **Narrative anchor.** `proposal.md` must contain a strategic-shape sentence near the top ("the highest-leverage work is rebuilding positioning + standing up a CRO experimentation program"). Generic "we'll help you grow" / "we'd love to partner" boilerplate fails this dimension.
5. **Shape-fit to prospect.** Cross-check against prospect's vertical/segment/maturity (read `state_of_business` findings or Phase-0 brief): proposing run_it_content_ops to a 3-person dev-tools startup that needs positioning is a shape-fit failure.

## Scoring

```json
{
  "rubric": "MA-8",
  "score": 6,
  "reason": "8 severity-3 findings: 3 map to build_it (positioning rebuild + CRO + GEO content engine), 4 map to fix_it (tech-SEO cleanup + schema + llms.txt + canonicals), 1 to run_it (content ops). Proposal has 4 fix_it / 2 build_it / 1 run_it — tier laddering OK, but build_it underweighted vs severity. Narrative anchor present ('highest-leverage work is positioning + CRO'). All 7 capability_ids exist in registry. Shape-fit reasonable for a 60-person B2B SaaS.",
  "severity_3_count": 8,
  "severity_3_to_build_or_run_pct": 50,
  "off_registry_capabilities": [],
  "tier_distribution": {"fix_it": 4, "build_it": 2, "run_it": 1},
  "narrative_anchor_present": true,
  "shape_fit_verdict": "reasonable"
}
```

## Score scale

- **0-2** Findings + proposal don't connect to engagement; reads as deliverable-only
- **3-4** Some build_it/run_it entries; proposal generic; some off-registry mappings
- **5-6** Most severity-3 findings map to build_it/run_it; proposal references registry; narrative anchor present but weak
- **7-8** Tier laddering credible; narrative anchor names strategic shape; shape-fit OK; all capability_ids on-registry
- **9-10** Above + proposal feels purpose-built for the prospect; engagement-pull is obvious to an ICP buyer

## Hard rule

If any `capability_id` in `proposal.json` is NOT present in `data/capability_registry.yaml`: cap the score at 3 regardless of other dimensions. Off-registry capabilities are pitching engagements the agency can't actually deliver — load-bearing for commercial integrity.

## Hard rule (engagement-pull floor)

If <50% of severity-3 findings map to `build_it`/`run_it` tier: cap the score at 5 regardless of other dimensions. The audit is supposed to surface the highest-leverage work; if all top findings are one-off fixes, the deliverable doesn't earn a $15K+ engagement pitch.

Return ONLY the JSON envelope on stdout.
