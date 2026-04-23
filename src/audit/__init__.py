"""Marketing audit pipeline — v1 dogfood.

Implementation of the locked-lens-scope audit pipeline per:
- docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md (1534-line plan)
- docs/plans/2026-04-23-002-marketing-audit-lhr-design.md (v1 autonomy + phasing)

v1 scope (4-6 weeks to ship first 5 paid audits):

    stage1a (preflight)  — deterministic Python checks, no LLM
    stage1b              — brief generation (existing agent)
    stage2               — 4 Stage-2 agents (Findability, Narrative, Acquisition, Experience)
    stage3               — SubSignal → ParentFinding synthesis, 9 report sections
    stage4               — proposal generation + pricing
    stage5               — deliverable rendering (PDF + HTML)

Current implementation state:

    preflight/  — architectural scaffold (no network I/O yet)

Everything else in this plan is future work; nothing audit-orchestration ships yet.
"""
from __future__ import annotations
