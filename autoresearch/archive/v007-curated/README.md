# v007-curated — manually curated derivative of Pi run v007

**Source:** Pi (`pi:projects/gofreddy`) ran an autoresearch evolutionary search 2026-04-29/30 against `search-v1` on the geo lane. Produced variants `v006 → v007 → v008`.

**This directory is NOT an autoresearch-system variant** — it has no `scores.json`, `meta.md`, `eval_digest.md`, or lineage entry. It's a curated bundle of principled changes from `v007` that the next evolutionary run should incorporate into a fresh, formally-evaluated variant.

## Why curate v007 instead of importing it whole

The Pi's v007 reported a +0.18 composite gain over v006 (7.771 → 7.9497), but the change set is mixed:

| Change | File | Verdict |
|---|---|---|
| Infra fallback guidance (degradation handling without fabrication) | `programs/geo-session.md` | ✅ principled |
| Non-SaaS schema guidance (MedicalWebPage, NewsArticle, etc.) | `programs/geo-session.md` | ✅ principled — directly responsive to clinical fixtures |
| Comparison-table hygiene (drop empty citation columns) | `programs/geo-session.md` | ✅ principled |
| `_summarize_visibility()` feeding judge with citation evidence | `workflows/session_eval_geo.py` | ✅ principled |
| Frequency-ranked competitor gaps (vs alphabetical) | `scripts/allocate_gaps.py` | ✅ principled |
| Expanded `source_data` (audits, landscape_pages) | `programs/geo-evaluation-scope.yaml` | ✅ principled |
| `completion_guard` neutered to `return None, None` | `workflows/geo.py` | 🚨 **regression** |
| `stall_limit: 5 → 15` | `workflows/geo.py` | 🚨 **regression** |

Two regressions inside `workflows/geo.py` reintroduce bugs that v006's code had explicit comments calling out:

- v006's `completion_guard` enforced "session declaring `## Status: COMPLETE` must have at least one `optimized/*.md` deliverable, else downgrade to RUNNING." v007 reverted this to `return None, None` — a session can declare COMPLETE with zero deliverables and the loop exits clean.
- v006's `stall_limit=5` had a comment: "v006 silently raised to 15 with no commit message rationale … 15 burns 75-150 min before bailing on stuck sessions. Reverted to 5." v007 raised it back to 15 with no rationale.

Both regressions lower the bar for a session to count as "complete," which inflates the outer pass rate. v007's eval_digest flagged the symptom: `mean_pass_rate_delta: +0.317 (inner=0.6833, outer=1.0)` — inner critic only passes 68% but outer eval says 100%, well above the ±0.15 advisory threshold. The +0.18 composite gain is partly real (the principled prompt + judge-evidence improvements) and partly inflation from the lowered acceptance bar.

v008 inherited from v007 and regressed badly (composite 0.0932; 2/3 fixtures structurally failed). The system correctly did not promote it.

## What this directory contains

The 4 files marked ✅ above, copied verbatim from Pi `archive/v007/`. `workflows/geo.py` is intentionally absent — its v007 version contains the regressions; the next variant should keep v006's `geo.py` (or evolve it from there with explicit rationale).

```
v007-curated/
├── README.md                                  (this file)
├── programs/
│   ├── geo-evaluation-scope.yaml              (expanded source_data)
│   └── geo-session.md                         (3 new sections: infra fallbacks, non-SaaS clients, comparison hygiene)
├── workflows/
│   └── session_eval_geo.py                    (visibility evidence summary)
└── scripts/
    └── allocate_gaps.py                       (frequency-ranked competitor gaps)
```

## Recommended next step

When the autoresearch system runs again on the geo lane, base the next variant from v006 + the 4 curated files in this directory. That gives an honest re-evaluation: if the composite still beats 7.771 without the lowered bar, the gain is real and `v009` (or whatever next id) earns its promotion through the holdout gate.

## Source location

Full Pi archive (including v007 with regressions and v008 failures) was rsync'd to `/tmp/pi-evolution-2026-04-30/` on the operator Mac for reference and is **not** committed here. Pi's HEAD when the run started was `03c8802`.

Run timeline (lineage.jsonl):
- v006 created: 2026-04-29 16:35 (cold start)
- v007 created: 2026-04-29 17:26 (selected v006 as parent, ran 75 min, +0.18 gain)
- v007 promoted as geo head: 2026-04-30 13:59 (no holdout — `eligible_for_promotion: false, reason: holdout_required`)
- v008 created: 2026-04-30 14:56 (selected v007 as parent, regressed to 0.0932, NOT promoted)
