# Self-improving reports — gap audit (2026-05-08)

Audit of `feat(autoresearch): self-improving HTML+PDF report rendering` (commit `bfd66b6`, local main, not pushed).

This document is brutally honest about what's wired, what's stubbed, what's duplicate, and what's dead. It exists because earlier work overclaimed completeness and the user asked for a real audit.

---

## TL;DR

The render pipeline runs end-to-end for **4 of 5 lanes** (geo / competitive / monitoring / storyboard) and produces a real 42 KB HTML + 580 KB PDF + 206 KB screenshot per fixture from a real session dir. **Marketing_audit is unwired**, and even if it were wired, it would conflict with the existing production report system. **Several "supporting" pieces are dead code** (judge, render_rubric_ids, Stage-2 synthesis is generic). **Most of the session data — the 80–92% that lives in `logs/iteration_*.log.err` — is ignored.**

---

## P0 — Critical gaps (block the "everything works and is proper" claim)

### G1. Marketing_audit lane has zero report.html wiring AND would conflict with the existing one

- `autoresearch/archive/v006/workflows/marketing_audit.py` does **not** set `render_report=`.
- `render_report.COMPOSERS` has no `"marketing_audit"` key — even if the lane opted in, `render()` would log "no composer registered" and return `{}`.
- **Conflict**: marketing_audit already has a full Stage-5 deliverable pipeline at `src/audit/stages.py:stage_5_deliverable` (Jinja2 + WeasyPrint, `templates/audit_report.html.j2`, 193 lines, ULID-slugged, idempotent on resume). This is the production system shipped in PR #45 (commit `0543d7b`, 2026-05-08).
- Naively wiring render_report.py for marketing_audit would either (a) duplicate the deliverable, or (b) overwrite `report.html` and break the slug→portal flow.

**Fix**: leave marketing_audit on Stage-5, but standardise the `report.html` location across all lanes so the portal route can serve all 5 lanes from one path. Add `compose_marketing_audit` only if we want to UNIFY visual style across lanes (currently the audit_report.html.j2 has its own design language).

### G2. ~80–92% of session bytes are ignored

Real session sizes (representative sample per lane):

| Lane | Total | File count | Logs share |
|---|---|---|---|
| geo (mayoclinic) | 916 KB | 23 | 86% (792 KB in `logs/*.err`) |
| competitive (epic) | 1.3 MB | 33 | 92% (1.2 MB) |
| monitoring (Lululemon) | 2.2 MB | 33 | 91% (2.0 MB) |
| storyboard (Gossip.Goblin) | 9.8 MB | 69 | 80% (8 MB, incl 2.1 MB multiturn) |
| marketing_audit (Anthropic) | 2.1 MB | 27 | 90% (1.9 MB) |

The composers (`compose_geo`, etc.) read 5–10 KB of structured JSON/MD per session and present **counts** of large-file dirs (e.g. "8 mentions/", "5 storyboards/") instead of content.

`extract_session()` does parse the .err transcripts, but only into `iteration_count` + `pivots` + `reasoning_beat` totals. The raw reasoning trace — the actual thing the user wants surfaced — **never makes it into the HTML**.

**Fix**: feed Stage-2 the full extracted reasoning + raw lane-specific dir contents (paginated/sampled), and either (a) let it author HTML directly, or (b) extend the deterministic composer to surface the content of the dirs it currently only counts (storyboards, mentions, anomalies, recommendations, optimized, pages, evals, lens_outputs, etc.).

### G3. Stage-2 "synthesis" is a generic 60-second LLM call producing 2-3 sentences

`maybe_cli_synthesis` does a single codex CLI call with a domain-agnostic prompt:

> "You are writing a 2-3 sentence executive synthesis for a {DOMAIN} autoresearch session report on client '{CLIENT}'. The agent recorded {N} reasoning beats across {M} iterations. Findings header (first 2000 chars):..."

Failure modes:

- The prompt sends only the first 2000 chars of `findings.md` and the beat counts. It does **not** send transcripts, page scrapes, deliverables, or per-fixture artifacts.
- Output is a string, dropped into a fixed `.rprt-meta-pattern` block in section 1. The CLI does **not** author HTML, pick layouts, or adapt to the data.
- The prompt is **identical for all 5 lanes**.
- 60-second timeout × 5 lanes × N fixtures = real evolve-loop overhead; it runs every render even when the data is identical to the last run.

**Fix**: pivot to "agent authors the inner HTML." Pass the agent the full extracted data (with size guards) plus a lane-specific brief, and ask it to emit the inner HTML for the report body. Cap one synthesis per session, cache by content-hash.

### G4. No per-lane visual differentiation

All 4 lanes share `.rprt-*` CSS primitives in `src/shared/reporting/report_base.py:BASE_CSS`. The composers vary the *content* (stat-grid columns, section order) but not the *style*. The user explicitly asked: "they should all experiment with different styles."

Concrete examples of what's identical across lanes:
- Color palette (single neutral palette)
- Typography (one type stack)
- Hero block layout
- Stat grid styling
- Findings list styling

**Fix**: add `.rprt-theme-{lane}` CSS overrides. Recommended directions:
- geo → clinical / typographic / data-tables-first
- competitive → editorial / red accents / pull-quote heavy
- monitoring → ops-dashboard / green accents / dense tables
- storyboard → cinematic / dark mode / large media tiles
- marketing_audit → advisory / amber / 9-axis chart-first

---

## P1 — Significant issues (functionality exists but is broken/dead/disconnected)

### G5. `render_judge.py` is dead code

- 130 LOC at `autoresearch/archive/v006/scripts/render_judge.py`.
- `programs/render-rubric.md` defines RND-1..5 rubrics for grading rendered reports.
- **Nothing invokes it**. Not called from `evolve.py`, not wired into the post-session hooks, no test coverage, no CLI surface. The grep hits are all log mentions of the filename in agent reasoning (the agent talked about it during sessions; nothing ran it).
- Without judge integration, the "self-improving" claim has no feedback loop — there's no automated quality signal that drives evolution.

**Fix**: either delete it, or wire it into `evolve.py` as an additional dimension of the variant scorer (alongside search-suite composite + holdout). Without wiring, every report-rendering change ships blind.

### G6. `lane_registry.render_rubric_ids` is a dead field

- Added at `autoresearch/lane_registry.py:68`, defaulting to `()`.
- Zero readers anywhere in the repo.
- Was the planned feedback bridge between LaneSpec and render_judge — never connected.

**Fix**: connect to G5 or remove.

### G7. `detect_meta_patterns.py` is manual-only

- Reachable only via `freddy autoresearch detect-meta-patterns`.
- Not invoked by `evolve.py`, not surfaced in any rendered report, not part of the post-session pipeline.
- The output (cross-lane SequenceMatcher clusters) is the most interesting artifact of the whole exercise but currently has no readers.

**Fix**: invoke after every full evolve cycle (or on-demand from the report's own UI), and surface the top-N patterns in each report's appendix and/or in a new "Cross-Lane Patterns" page in the portal.

### G8. Geo lane has TWO report generators running side-by-side

Real session dir for geo/mayoclinic now has:
```
report.md      ← from build_geo_report.py (existing, called from pre_summary_hooks)
report.json    ← from build_geo_report.py
report.html    ← from render_report.py (new, called from post_session render_report hook)
report.pdf     ← from render_report.py
report-screenshot.png ← from render_report.py
```

`build_geo_report.py` (373 lines) and `compose_geo` (in render_report.py) are independent — they read overlapping JSON/MD inputs but emit different outputs. Neither references the other.

**Fix**: decide if `build_geo_report.py` gets retired in favor of `compose_geo`, or if `compose_geo` should consume `report.md`/`report.json` produced by build_geo_report (DRY). My read: collapse to one pipeline; build_geo_report's MD/JSON output is structurally useful and should be the input to render.

### G9. No test coverage for render or CLI

- `cli/tests/test_commands.py` does **not** test `freddy autoresearch render|publish|detect-meta-patterns`.
- No tests for `compose_geo`, `compose_competitive`, `compose_monitoring`, `compose_storyboard`, or `render()`.
- No tests for `portal_report_view`.
- The only test passing is `test_extract_reasoning.py` (10/10 — covers extract_reasoning.py only).
- "Smoke test" so far has been: I ran it once by hand on one fixture.

**Fix**: pytest fixtures of frozen session dirs per lane → assert (a) HTML produced ≥ N KB, (b) PDF non-empty, (c) all expected sections present, (d) meta-pattern script runs without errors.

### G10. `extract_reasoning.py` heuristics are calibrated against a single fixture

The 10/10 calibration tests run against a single mayoclinic transcript. The classifier (`classify_beat`) uses regex heuristics that may not generalize across:
- Different inner-agent backends (claude vs codex vs opencode produce different transcript shapes)
- Different lane vocabularies (geo's "I'll fetch the page" vs storyboard's "I'll generate the storyboard")
- Multiturn sessions (storyboard's `multiturn_session.log.err` is 2.1 MB and structurally different from regular iteration_*.err)

**Fix**: extend tests to cover one transcript per lane × per backend = ~12 fixtures.

---

## P2 — Reuse opportunities not taken

### G11. `src/shared/reporting/report_base.py` already has the primitives we partially reimplemented

Already exists (798 LOC):
| Function | What it does | render_report.py reimplemented as |
|---|---|---|
| `load_json` | safe JSON read | `safe_json` (dup) |
| `load_markdown` | safe MD read with truncation | `safe_read` (dup) |
| `parse_findings` | parse findings.md → structured dict | `parse_findings_md` (dup) |
| `render_findings` | findings dict → HTML | `build_findings` (dup) |
| `render_session_log` | session_log.md → HTML table | NOT used |
| `render_logs_appendix` | iteration logs → collapsed HTML | NOT used (would surface the 80% of bytes we're ignoring!) |
| `render_session_summary` | session_summary.json → HTML | NOT used |
| `md_to_html` | minimal MD-inline → HTML | `md_inline` (dup) |
| `build_html_document` | sections → full doc | USED ✓ |
| `html_to_pdf` / `html_to_screenshot` | Chrome subprocess | USED ✓ |

**Fix**: replace duplicates with imports from `report_base`; in particular wire up `render_logs_appendix` — that single change would surface the iteration .err transcripts in every report.

### G12. `src/shared/reporting/scrub.py` for PII redaction is not used

40-LOC scrubber for emails / phone / API keys. Reports contain agent transcripts that may include scraped page content with PII. Currently not run.

**Fix**: pipe transcript content through `scrub()` before embedding.

### G13. Marketing_audit's `audit_report.html.j2` has design ideas worth porting

The Jinja2 template covers: 9-axis health chart, state-of-business panel, gap report, proposal section, sources. None of these patterns are in the new `.rprt-*` library. If we want a unified visual chassis, the audit template is ahead.

**Fix**: extract the 9-axis chart + sources block + proposal panel into `.rprt-*` primitives (`.rprt-9axis`, `.rprt-sources`, `.rprt-proposal`) so all lanes can use them.

### G14. No connection to lineage / frontier / evaluation feedback

- `archive/index.json` records per-variant metrics but has no `report_html_path` field.
- `archive/lineage.jsonl` has no rendering signal.
- `archive/frontier.json` ditto.
- `evolve.py`'s variant_scorer doesn't know reports exist.

**Fix**: add `artifacts.report_html`, `artifacts.report_pdf` to the variant record after each render, so the portal can surface "compare v007 vs v008 reports for geo/mayoclinic" without filesystem walks.

---

## P3 — Process / honesty issues

### G15. Commit message overclaimed

The commit `bfd66b6` says "self-improving HTML+PDF report rendering across all lanes". Truthful version: "report rendering wired for 4 of 5 lanes, no per-lane styling, no judge feedback loop, generic 2-3-sentence Stage-2 synthesis, ignores 80%+ of session bytes."

### G16. The "self-improving" claim has no feedback loop

For something to self-improve we need:
1. A judged quality signal per render (G5: judge is dead)
2. That signal recorded in lineage/frontier (G14: not recorded)
3. Variant scoring that includes render quality (not implemented)
4. Mutate-and-test loop that proposes report-template variants (not implemented)

Currently we have: rendering. That's it. "Self-improving" is aspirational.

**Fix**: scope down or scope up. Either rename the spec to "Per-lane HTML+PDF reporting" and ship that cleanly, or commit to wiring G5 + G14 + scorer integration to make the self-improvement claim real.

---

## Data the render currently surfaces vs ignores (per lane)

### geo
- ✅ session_summary.json, gap_allocation.json, competitors/visibility.json, findings.md, results.jsonl
- ⚠️ pages/ (counts only, content ignored)
- ⚠️ optimized/ (counts only)
- ❌ logs/iteration_*.err (parsed for beats only — raw content dropped)
- ❌ evals/

### competitive
- ✅ session_summary.json, findings.md, brief.md, results.jsonl
- ⚠️ competitors/, analyses/ (counts only)
- ❌ pages/, logs/ (raw content)

### monitoring
- ✅ session_summary.json, findings.md, digest.md, results.jsonl
- ⚠️ mentions/, anomalies/ (counts only)
- ❌ synthesized/, recommendations/, stories/, evals/, logs/

### storyboard
- ✅ session_summary.json, findings.md, results.jsonl
- ❌ selection/videos.json (the composer reads this path but it doesn't exist in real sessions — silent miss)
- ❌ storyboards/*.json (5 × 20 KB of ACTUAL DELIVERABLES — completely ignored)
- ❌ stories/, patterns/, clips/, frames/, api_errors/, evals/, logs/

### marketing_audit
- N/A (lane unwired)

---

## Recommended fix order

If we want to land "everything works and is proper":

**Phase A — close the obvious holes (~1 day)**
1. G8: collapse build_geo_report + compose_geo into one pipeline; render_report consumes report.md/json
2. G11: replace duplicates with `src/shared/reporting/report_base` imports; wire `render_logs_appendix` so transcripts show
3. G1: decide marketing_audit policy. Recommended: **point post-session render_report at Stage-5's existing report.html** for marketing_audit (no compose_marketing_audit, just adopt the existing deliverable as the canonical lane report). Update portal _LANES allowlist accordingly.
4. Storyboard composer reads the real `storyboards/*.json` (G2 fix for storyboard specifically — this is the lane with the most ignored content)

**Phase B — give it a soul (~2 days)**
5. G4: per-lane `.rprt-theme-*` CSS palettes
6. G3: rewrite Stage-2 to accept full extracted data + lane brief, output inner HTML, cache by content hash
7. G2: extend composers to surface the dirs they currently only count (mentions/, anomalies/, recommendations/, etc.)
8. G9: pytest coverage per lane × backend with frozen session fixtures

**Phase C — make "self-improving" real (~3-4 days)**
9. G5 + G6: wire render_judge into the post-session hook, write scores to `archive/v006/metrics/render.jsonl`
10. G14: add `artifacts.report_*` fields to lineage/index/frontier
11. G7: invoke detect_meta_patterns post-evolve, surface in cross-lane appendix + a dedicated portal page
12. Variant scorer: include render-quality signal as a tertiary dimension behind search-composite and holdout

**Phase D — drop the load-bearing fictions**
13. If we don't do Phase C, rename the spec from "self-improving" to "lane reporting" and update commit message language going forward
14. Remove dead code (render_judge.py + render_rubric_ids field + render-rubric.md) if not adopted in Phase C

---

## Numbers

- Lanes claimed wired: 5 (per commit message)
- Lanes actually wired: **4**
- Code added in the commit: **+2,948 LOC**
- Code that's dead or unused: **~280 LOC** (render_judge.py 130 + render_rubric_ids field + render-rubric.md 138 + ~30 LOC of duplicate helpers)
- Code that duplicates `src/shared/reporting/report_base.py`: **~80 LOC**
- Real net useful code: **~2,500 LOC** (composers + extract_reasoning + Typer CLI + portal route + CSS primitives + spec doc)

End of audit.
