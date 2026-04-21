# SMOKE — abort gate

These are **deterministic must-work flows**. Any failure = hard abort with `exit_reason="smoke broken"`. The fixer never reads this file.

Smoke runs: (1) once at preflight, (2) at the start of every cycle, (3) once more at tip against the staging branch HEAD (with each landed finding's reproduction appended as extra checks).

Each `---` block below is one check, parsed by `harness/smoke.py`.

---
id: smoke-cli
type: shell
command: .venv/bin/freddy --help
expected_exit: 0
---

The CLI console script exists and imports cleanly. Failure here usually means the editable install is stale (`uv pip install -e .`).

---
id: smoke-api-health
type: http
method: GET
url: http://127.0.0.1:8000/health
expected_status: 200
---

The FastAPI backend is up and responds to `/health`.

---
id: smoke-api-key
type: http
method: POST
url: http://127.0.0.1:8000/v1/api-keys
auth: bearer
body_json: {"name": "smoke-check"}
expected_status: 201
expected_body_contains: key
---

Authenticated API call works end-to-end: JWT is valid, DB row creation works, response shape has a `key` field.

---
id: smoke-frontend
type: playwright
url: http://127.0.0.1:5173/
expect_no_console_error: true
---

Frontend loads root route without an `error`-level console message.

---
id: smoke-cli-client-new
type: shell
command: .venv/bin/freddy client new smoke-check-$(date +%s)
expected_exit: 0
---

A full CLI round-trip that touches filesystem state (creates a client workspace). Catches regressions in config loading, directory creation, JSON emission.
