# Marketing Audit — Session Program

**Status:** L1 placeholder. Master plan 2026-05-06-001 §7.2 work item 7
requires this file to exist so ``evaluate_variant.layer1_validate``'s
``programs/<domain>-session.md`` per-domain check (line 594) passes
once ``marketing_audit`` is registered as a workflow lane in
``autoresearch/lane_registry.LANES``.

**L3 fills this with the full Stage 2 agent prompts.** Until then,
this file's existence + non-empty content is the only invariant the
substrate enforces.

## Lane head marker

This file marks the lane head's program-doc set. Variants cloned from
the lane head inherit a copy; the meta-agent edits the copy under
``programs/marketing_audit/prompts/...``, leaving this top-level
marker stable as the structural anchor.

## Structural Validator Requirements

<!-- AUTOGEN:STRUCTURAL:START -->
*Do not edit content between `<!-- AUTOGEN:STRUCTURAL:START -->` and
`<!-- AUTOGEN:STRUCTURAL:END -->` — it is regenerated from the lane
registry on every variant clone; hand-edits are overwritten.*

- `findings.md` exists with all 9 deliverable sections — findability,
  narrative, acquisition, experience, competitive, monitoring, geo
  (display: AI Visibility), state_of_business, martech_compliance.
- `proposal.md` (when present) contains the 3 capability-registry tier
  headers in fixed order: fix_it, build_it, run_it.
<!-- AUTOGEN:STRUCTURAL:END -->

## What L3 will add

Per master plan §3.5 + §7.4:

- Stage 1b pre-discovery prompt (Sonnet, multi-turn, ~75 free-API
  URL-pattern blocks)
- Stage 1c brief synthesis prompt (Opus, single call, with
  phase0_meta.json block)
- Stage 2 agent prompts × 4 (Findability, Narrative, Acquisition,
  Experience) with per-agent rubric YAML synthesis instructions
- Stage 3 cross-cutting Phase-0 + narrative writer prompts
- Stage 4 proposal prompt + capability_registry.yaml (~48 entries)
- Stage 5 Jinja2 + WeasyPrint render harness

L1's only job is to stop the substrate L1 gate from rejecting every
new variant with a missing-program-file error.
