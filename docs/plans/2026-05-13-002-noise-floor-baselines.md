# U11/U12 noise-floor baselines — per-fixture regression bars

**Plan reference:** `docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md`
**Decision lineage:** D10 (revised per TD-7 + TD-19) — direct cutover, no
toggle, per-fixture bar = `max(5%, 2 × std_dev)` calibrated from a
pre-migration noise-floor characterization run.

## Status (2026-05-19)

**Scaffold only. Numbers are TBD.**

The noise-floor characterization spike is an OPERATOR step (live API
runs against the production substrate, ~$30–50 per spike per fixture
set). It is NOT shipped as code in this PR — U11/U12 code lands the
shared-persona migration; the operator records baselines here when the
spike runs.

The migration code lands without baselines because:

1. The default `jr` persona produces a bit-identical compiled substrate
   to the pre-U11 static `voice.md` (single corpus file, empty
   voice_rules, empty style_anchors) — see
   `autoresearch/archive/v007-curated/workflows/linkedin_engine.py`
   `_compile_voice_substrate`. So the JR-baseline case is regression-free
   by construction; the bar is only load-bearing for non-JR personas
   (Klinika dr_maria, DWF partner_jamka, future) and for fixtures that
   actually exercise a different persona.
2. Non-JR personas have empty corpora pre-consent (parallel-track risk
   #1) — the migration cannot regress fixtures for clients whose corpus
   isn't yet ingested.

## Spike procedure (operator-run, per fixture set)

When the operator runs the noise-floor spike, populate the tables below.

### Step 1 — Capture pre-migration baselines

Roll back to pre-U11 (`git stash` or branch hop), then run 5 sequential
holdout passes on each affected fixture in `legacy` mode (the static
`voice.md` source). Record per-fixture composite scores in the
**Pre-migration baseline** table.

### Step 2 — Compute per-fixture std dev

For each fixture, compute the std dev across its 5 holdout passes.
Record in the **σ** column.

### Step 3 — Compute per-fixture bar

`bar = max(0.05 × baseline_mean, 2 × σ)`

Record in the **Bar** column. Threshold for the migrated lane: post-U11
composite must be within `[baseline_mean − bar, baseline_mean + bar]`.

### Step 4 — Run migrated lane against same fixtures

Switch back to post-U11 (this branch + U12 once it lands). Run 1 holdout
pass per fixture. Record post-migration composite in the **Post** column.

### Step 5 — Verdict

For each fixture, mark GREEN (post within bar) or RED (post outside bar).
Any RED blocks merge; remediate by editing the persona or fixture
(adjust angle / voice_rules) before re-attempting.

## linkedin_engine fixtures (U11)

Source: `autoresearch/eval_suites/search-v1.json` linkedin_engine block.

| Fixture                       | Pre baseline mean | σ      | Bar    | Post   | Verdict |
|------------------------------ |------------------ |------  |------  |------  |---------|
| linkedin_engine-angle-121     | TBD               | TBD    | TBD    | TBD    | TBD     |
| linkedin_engine-angle-122     | TBD               | TBD    | TBD    | TBD    | TBD     |
| linkedin_engine-angle-123     | TBD               | TBD    | TBD    | TBD    | TBD     |
| linkedin_engine-angle-124     | TBD               | TBD    | TBD    | TBD    | TBD     |

## x_engine fixtures (U12)

Source: `autoresearch/eval_suites/search-v1.json` x_engine block. To be
populated by the U12 PR's operator spike.

| Fixture                       | Pre baseline mean | σ      | Bar    | Post   | Verdict |
|------------------------------ |------------------ |------  |------  |------  |---------|
| x_engine-angle-121            | TBD               | TBD    | TBD    | TBD    | TBD     |
| x_engine-angle-122            | TBD               | TBD    | TBD    | TBD    | TBD     |
| x_engine-angle-123            | TBD               | TBD    | TBD    | TBD    | TBD     |
| x_engine-angle-124            | TBD               | TBD    | TBD    | TBD    | TBD     |

## Notes

- The JR-default case (all current fixtures) produces bit-identical
  substrate output to pre-U11 — so the bar is unfalsifiable-but-safe
  for those fixtures in this PR. The bar becomes load-bearing the
  moment a non-JR persona is wired into a fixture (Klinika / DWF /
  future).
- The substrate compiler `_compile_voice_substrate` keeps the
  single-file no-rules-no-anchors path bit-identical. Any change to
  that compiler MUST re-baseline this table.
