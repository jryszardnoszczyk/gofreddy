---
track: b
cycle: 1
timestamp: 2026-04-18T10:00:05+02:00
pass: 0
partial: 0
fail: 1
blocked: 0
findings:
  - id: B-3
    capability: PATCH /v1/sessions/{id}
    grade: FAIL
    summary: Session completion returned 500 instead of 200.
---

## Detailed Findings

### B-3: PATCH /v1/sessions/{id} — FAIL

**Prompt sent**: "curl -X PATCH localhost:8080/v1/sessions/{id}"
