# MA-7 — Gap Honesty

**Status:** DRAFT (master plan §6.4; JR review-iterate before manifest freeze)

## What this rubric scores

`gap_flagged` rubrics from per-agent `rubric_coverage` maps surface in `gap_report.md`. Missing-data findings are surfaced in `findings.md`, not papered over with speculation. Phase-0 nulls are findings. Provider-blocked lenses are honest gaps, not invented signals.

## What "good" looks like

- `gap_report.md` exists and is non-empty (most audits will have ≥5 gap_flagged lenses across agents)
- Every `gap_flagged` lens has a `reason` field (provider-down, no-public-data, paywalled, etc.)
- Phase-0 frame nulls surface as `state_of_business` findings ("we couldn't measure X because Y")
- Findings prefixed with "(N=1, low confidence)" where evidence is genuinely thin
- Recommendations adjust for gap-impact ("conditional on validating with the prospect's GA4 data")

## What "bad" looks like

- `gap_report.md` is empty when agents have provider-blocked lenses
- Findings hide gaps under speculation ("their conversion rate is likely 30-50%")
- Phase-0 nulls silently omitted
- N=1 evidence presented as broad pattern
- Recommendations confidently prescribe action where evidence is thin

## Score scale (0-10)

- **0-2** Gaps suppressed; speculation papers over missing data
- **3-4** Some gaps surfaced; speculation in 2-3 places
- **5-6** Most gaps surfaced; sparse N=1 caveats; Phase-0 nulls partially handled
- **7-8** All gap_flagged lenses in gap_report; Phase-0 nulls surface as findings; N=1 caveats present
- **9-10** Above + recommendations explicitly condition on gap-impact (the audit treats gaps as part of the strategic story, not as failures)

## Anchors for severity-of-MA-7-failure

- A finding with N=1 evidence presented as broad pattern: severity-of-failure 3
- A `gap_flagged` lens not surfaced in gap_report.md: severity-of-failure 2
- A Phase-0 null silently omitted from State-of-the-Business: severity-of-failure 2
- A recommendation that prescribes confidently where evidence is thin: severity-of-failure 2

## Notes for JR review

- Gap honesty is the competitive differentiator vs cheap-AI-generated audits. Other tools fabricate; we surface gaps as findings.
- Consider: should the rubric explicitly check for "every Phase-0 null = ≥1 finding" as a hard rule?
- Sync with `judges/MA-7-judge.md`.
