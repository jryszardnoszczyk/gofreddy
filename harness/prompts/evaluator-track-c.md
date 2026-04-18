## Track C Assignment — Frontend Pages

Execute ONLY the capabilities assigned to track `c` in the test-matrix `tracks:` block.

Your tests:
1. **C1**: Login page — navigate to `/` or `/login`, verify renders
2. **C2**: Sessions page — navigate to `/sessions?__e2e_auth=1`, verify renders
3. **C3**: Settings page — navigate to `/settings?__e2e_auth=1`, verify renders

Use `playwright-cli` with `-s=track-c` session isolation. Read `harness/test-matrix.md` for exact pass criteria.

### What to watch for:
- Login page: Supabase OAuth button present, no console errors
- Sessions page: page renders with E2E bypass, session list or empty state, filter controls
- Settings page: API keys section visible, no blank sections
- All pages: no uncaught errors in console, no blank/white screens
- Auth bypass: `?__e2e_auth=1` param must work on protected pages
