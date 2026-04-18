## Track a Assignment — CLI Commands

Execute ONLY the capabilities assigned to track `a` in the test-matrix `tracks:` block.

Your flows:
1. **Flow 1** (FIXED — convergence reference): Client new → Client list → Session start → Audit monitor → Sitemap → Detect (A1–A6, sequential)
2. **Flow 2**: SEO audit, Competitive audit (A7–A8, independent)
3. **Flow 3** (Dynamic): Scrape, Search content (A9–A10, independent)

Read `harness/test-matrix.md` for exact commands and pass criteria.

### What to watch for:
- Exit codes: 0 = pass, non-zero = fail (unless expected)
- JSON output: valid structure, required fields non-empty
- Client CRUD: slug uniqueness, list includes created client
- Session lifecycle: session_id returned, visible in API
- Provider-dependent commands (A7, A8, A10): grade BLOCKED if keys missing, not FAIL
