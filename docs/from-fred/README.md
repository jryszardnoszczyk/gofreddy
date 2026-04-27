# Frozen reference material from `freddy`

Source: `freddy` repo @ commit `50602a2` (2026-04-18).

These 10 markdown files are a **frozen snapshot** of high-value research, plans, and design notes that the GoFreddy fork has institutional reasons to preserve. They are **not actively maintained**, are **not authoritative for current work**, and may reference modules / paths / assumptions that no longer apply to GoFreddy.

Read for context only — do not port code from these.

## Most directly applicable

`research/2026-04-17-workflow-failure-root-causes.md` — 31 documented autoresearch failure root causes with line numbers and fixes. Directly applicable when debugging autoresearch issues.

## Contents

```
from-fred/
├── research/
│   ├── 2026-04-11-autoresearch-evaluation-infrastructure-audit.md  — evaluator harness deep-dive
│   ├── 2026-04-11-autoresearch-prompt-audit.md                     — prompt token inventory + 2 HIGH findings
│   ├── 2026-04-13-autoresearch-session-loop-audit.md               — session-loop stability audit
│   ├── 2026-04-14-autoresearch-run2-audit.md                       — run-2 agent behaviour patterns
│   ├── 2026-04-16-storyboard-mock-removal-and-evolution-readiness.md — pre-evolution assessment
│   └── 2026-04-17-workflow-failure-root-causes.md                  — 31 failures with fixes (most useful)
├── plans/
│   ├── 2026-04-08-001-fix-harness-round1-findings-plan.md          — harness bug-fix backlog
│   ├── 2026-04-14-004-refactor-harness-unconstrained-loop-plan.md  — harness redesign rationale
│   └── 2026-04-18-001-migrate-autoresearch-to-gofreddy-plan.md     — original Freddy → GoFreddy migration plan
└── superpowers/specs/
    └── 2026-04-16-freddy-distribution-engineering-agency-design.md — distribution-engineering-agency design
```

## What this is not

- **Not a port.** No code from these documents has been ported to GoFreddy by virtue of being in this directory. Code ports are tracked separately in `docs/plans/2026-04-27-001-fred-port-gaps-checklist.md` and its successors.
- **Not authoritative.** Where these documents conflict with current GoFreddy plans / decisions, the GoFreddy plans win.
- **Not a spec.** Internal links inside these files point to freddy's repo structure and may be broken in this view; that's expected.
