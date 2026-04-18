---
track: a
cycle: 1
timestamp: 2026-04-18T10:00:00+02:00
pass: 0
partial: 0
fail: 1
blocked: 0
findings:
  - id: A-3
    capability: freddy audit monitor
    grade: FAIL
    summary: Monitor audit command exited with non-zero status and no JSON output.
---

## Detailed Findings

### A-3: freddy audit monitor — FAIL

**Prompt sent**: "freddy audit monitor --client demo-clinic"
