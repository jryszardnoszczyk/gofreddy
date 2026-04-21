### Track C — Frontend

Primary surface: `frontend/` (Vite + React + TypeScript; entry `npm run dev` → `http://127.0.0.1:5173`).

Tools you typically reach for:
- Playwright via `npx playwright` or a one-line Node subprocess with `require('playwright')`
- Load each route in `frontend/src/lib/routes.ts`; watch browser console and network tab
- `curl -sI http://127.0.0.1:5173/<path>` for quick HEAD checks; always follow up with Playwright for console errors
- Read `frontend/src/routes/<Route>.tsx` to see what the page expects before declaring it broken

Defect patterns common here:
- `console.error` during normal navigation or auth flow (console-error)
- Route referenced in `ROUTES` or `LEGACY_PRODUCT_ROUTES` 404s or crashes (dead-reference)
- Component calls a backend endpoint that returns a different shape than expected (self-inconsistency — confirm by checking the API response directly)
- UI freezes / white screen (crash)
- Unhandled `rejectionhandled` or `unhandledrejection` events in console
