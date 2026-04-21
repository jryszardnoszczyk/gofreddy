### Track B — API + autoresearch

Primary surfaces: `src/` (FastAPI backend, entry `src.api.main:app`), `autoresearch/` (session/variant programs run as Python entry points).

Tools you typically reach for:
- `curl -s http://127.0.0.1:8000/openapi.json | jq '.paths | keys'` to list routes
- `curl -sf -H "Authorization: Bearer $HARNESS_TOKEN" http://127.0.0.1:8000/<route>` to hit authenticated endpoints — the harness injects a JWT via env
- `python -m autoresearch.evolve --help`, `python autoresearch/evaluate_variant.py --help` for autoresearch entry points
- Read `src/api/routes/<name>.py` to understand expected behaviour before declaring a 5xx a defect — some 400/422 responses are correct

Defect patterns common here:
- Route returns 500 on valid-looking input (missing default, unhandled DB error, serialization bug)
- Route returns 200 + `{"status": "error"}` body (wrong HTTP code — counts as self-inconsistency)
- Response shape mismatches OpenAPI schema (self-inconsistency)
- Endpoint referenced in docs or frontend but not registered (dead-reference)
- Autoresearch entry point crashes on minimal args (crash)
