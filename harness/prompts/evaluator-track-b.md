## Track B Assignment — API Endpoints

Execute ONLY the capabilities assigned to track `b` in the test-matrix `tracks:` block.

Your flows:
1. **Flow 1** (FIXED — convergence reference, SEQUENTIAL): Create session → List sessions → Complete session → Log action (B1→B2→B3→B4)
2. **Flow 2** (SEQUENTIAL): Create monitor → List monitors (B5→B6)
3. **Flow 3**: Create API key, Evaluation (B7–B8, independent)
4. **Flow 4** (Dynamic): GEO audit, Competitive ads (B9–B10, independent)

Use `curl` with `$HARNESS_TOKEN` for auth. Read `harness/test-matrix.md` for exact endpoints, bodies, and pass criteria.

### What to watch for:
- HTTP status codes: 201 for creation, 200 for queries, not 500
- Response JSON: required fields present, correct types
- Sequential chains: extract `id` from B1 response, use in B2–B4
- Monitor chain: extract `id` from B5, verify in B6 list
- Provider-dependent endpoints (B8, B9, B10): grade BLOCKED if keys missing
