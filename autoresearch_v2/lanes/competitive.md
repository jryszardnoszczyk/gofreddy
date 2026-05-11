# Lane: competitive — competitive intelligence briefs

**What this lane does:** evolves the prose at `lanes/competitive.md` so each session produces a `brief.md` synthesizing competitive intelligence about a target market or company — and per-competitor JSON files capturing structured evidence.

**Baseline you're trying to beat:**
- v006 search-v1 composite (last measured): **7.4** for the competitive domain. v009 holdout baseline pending — first holdout run post-promotion sets it.

---

## Deliverable contract

The session writes a `brief.md` under `sessions/competitive/<client>/`. Each session MUST satisfy:

1. **A file with `brief` in its name** ending in `.md` exists (`brief.md` is canonical; `competitive-brief.md` etc. are accepted by the structural gate).
2. **At least one `competitors/<name>.json`** (excluding `_`-prefixed helpers) is present and parses as valid JSON. Shape only at the structural level; the 8 CI judges evaluate sufficiency.

If either fails, the iter is `checks_failed`.

---

## The 8 CI judges (your fitness function)

Composite = geometric mean across CI-1 .. CI-8. Specific judge prompts live at `judges/evolution/prompts/scorer.md` (read-only — defended by `verify_critique_integrity.py`).

The competitive lane historically rewards:
- **Honest positioning** — same axis as GEO-3. Acknowledge where the client loses.
- **Specific named comparators** — per-competitor JSON with actual product names, pricing tiers, feature matrices.
- **Quote attribution** — quotes from review sites, customer threads, analyst reports — with source URL and access date.
- **Schema consistency across competitors** — every `competitors/<name>.json` uses the same key set so the brief can compose them.

---

## What you CANNOT edit

- `autoresearch/archive/v006/workflows/competitive.py`
- `autoresearch/archive/v006/workflows/session_eval_competitive.py`

These define the structural gate. Editing them is a scope violation; the alert agent will flag the cross-lane mutation. You also can't edit any other `lanes/*.md`, `tools/`, `harness/`, `judges/`, or `autoresearch.md`.

---

## Recent mutation surfaces that worked

- Adding "find at least one quote with verifiable attribution" rule per competitor.
- Forcing the brief.md to end with a 5-row comparison table.
- Requiring at least one `competitors/<name>.json` per direct competitor named in the brief (forces evidence-before-claims).

## Mutation surfaces that have regressed

- Demanding all competitors covered to the same depth — overfits prompt to fixtures where the client has 8+ competitors; light-coverage fixtures crash.
- Stripping the "where competitors win" requirement — same axis as GEO-3 collapse pattern.

---

## Fixture coverage (no content revealed)

- Search-v1 (visible): see `autoresearch/eval_suites/search-v1.json` for `competitive-*` fixture_ids only. **Never read the fixture content yourself.**
- Holdout-v1 (hidden): per-lane fixtures in `~/.config/gofreddy/holdouts/holdout-v1.json`. `tools/score_holdout.py` returns only composite + per-fixture metadata.

---

## Recent history pointers

- `git log --oneline lanes/competitive.md` — evolution history
- Last ~10 rows of `lanes/competitive/results.tsv` — recent attempts
- `lanes/competitive/holdout_results.tsv` — holdout trajectory
- `alerts.jsonl` filtered by `lane=competitive`
