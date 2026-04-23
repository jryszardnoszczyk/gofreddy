### Track C — Frontend

Primary surface: `frontend/` (Vite + React + TypeScript; entry `npm run dev` → `http://127.0.0.1:5173`).

## Required tools for this track

For every frontend route or interaction you investigate you MUST:

1. Load the page via Playwright (headless Chromium is fine). Do not rely on `curl -sI` alone — curl cannot observe React runtime errors, hydration mismatches, or `console.error` output.
2. Read the browser console after each navigation. Record every `console.error` or unhandled rejection observed. Include the full message in the finding's evidence block.
3. Exercise at least one interaction on the page (click a link, submit a form, open a modal). Static loads miss interaction bugs.

If Playwright is unavailable in your environment, emit `done reason=blocked-no-playwright` and stop. Findings filed without Playwright evidence for frontend pages are demoted to low-confidence and will not reach the fixer.

Still useful alongside Playwright:
- `curl -sI http://127.0.0.1:5173/<path>` for quick route-existence checks
- Reading `frontend/src/routes/<Route>.tsx` or `frontend/src/lib/routes.ts` AFTER loading the page — never before. Always verify you observed the problem first; source inspection is for narrowing the defect, not inferring it.

Defect patterns common here:
- `console.error` during normal navigation or auth flow (console-error)
- Route referenced in `ROUTES` or `LEGACY_PRODUCT_ROUTES` 404s or crashes (dead-reference)
- Component calls a backend endpoint that returns a different shape than expected (self-inconsistency — confirm by checking the API response directly with `curl`, then replay in Playwright to watch the component's reaction)
- UI freezes / white screen (crash)
- Unhandled `rejectionhandled` or `unhandledrejection` events in console
