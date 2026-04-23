# Holdout-v1 16-Row Composition Expansion (Plan B Phase 2 — deferred)

**Status:** stub created 2026-04-23 for MVP carve-out deferral. The MVP shipped with 4 geo fixtures (and empty monitoring/competitive/storyboard slots). This plan rounds it out to the full 16 rows.

## What this plan ships

Fill the 12 empty rows of Plan B's composition table:

- 4 monitoring fixtures (operator-authored using real xpoz monitor UUIDs)
- 4 competitive fixtures (client-slug-based; blocked on refresh CLI fix)
- 4 storyboard fixtures (YouTube + TikTok + Portuguese + TBD; blocked on refresh CLI fix for search-content source)

Requires the refresh CLI-signature fix (`docs/plans/2026-04-23-001-fix-refresh-cli-signature-mismatch.md`) to be live for competitive / storyboard authoring.

## Why deferred (per 2026-04-23 review)

- 3 weeks of operator URL research vs. the Plan B 2-week Phase-2-to-5 timing constraint.
- The 8-fixture MVP alt path satisfies the discriminability + canary requirements with half the upfront time.
- `freddy search-ads` / `freddy visibility` / `freddy search-content` all fail refresh today due to the CLI-signature mismatch bug. Authoring competitive / storyboard fixtures against a broken refresh path is wasted work.

## What's already shipped

- `~/.config/gofreddy/holdouts/holdout-v1.json` with 4 geo fixtures (bmw-i4-de, nubank-br-pix, stripe-docs-atlas, rakuten-travel-jp).
- `docs/plans/fixture-taxonomy-matrix.md` — Phase 1 taxonomy lists ALL 16 proposed cells, so the authoring agent has a starting point.

## Trigger conditions — when to start

Start when BOTH are true:

1. **Refresh CLI fix has landed** (per `docs/plans/2026-04-23-001-fix-refresh-cli-signature-mismatch.md`). Without it, competitive + storyboard refresh fails and the 12-new-row authoring is limited.
2. **MVP's 8-fixture canary has returned `go`** — if the canary returns `fail` or `revise`, the entire holdout design is suspect and no expansion should happen until the holdout is revised.

## Execution sketch

Follow Plan B Phase 2 Step A (dispatch a fixture-authoring agent per fixture). The 4 monitoring fixtures need the operator's xpoz UUIDs; the other 8 can use the composition-table named clients (SAP, Epic, Patreon, etc.).

Expected budget: ~2–3 weeks of operator URL/client research (semantic work, not code).

## Acceptance

- `~/.config/gofreddy/holdouts/holdout-v1.json` has 16 fixtures (4 per domain).
- `freddy fixture validate` passes.
- `freddy fixture dry-run <id>` returns `verdict=healthy` for all 16.
- `freddy fixture discriminate` returns `separable` across the 16-row suite.
