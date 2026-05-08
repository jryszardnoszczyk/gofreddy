# MA-2 — Evidence Traceability

**Status:** DRAFT (master plan §6.4; JR review-iterate before manifest freeze)

## What this rubric scores

Every claim in `findings.md` cites a `lens_id` AND ≥1 `evidence_url`. Numbers are source-attributed (no naked stats). Estimates carry the word "estimated" or "approx" with an explicit confidence range. Generalizations from a small N are flagged.

## What "good" looks like

- Every finding has a `Sources:` line pointing at evidence URLs
- Quantitative claims cite the source ("Foreplay shows 67 active Meta ads, last 90d window")
- Estimates labeled ("estimated 30-50% efficiency loss based on category benchmarks")
- Patterns from N=2-3 evidence points carry a "small-N" caveat
- ParentFinding `addresses_rubrics` arrays match the lens IDs cited in evidence

## What "bad" looks like

- Findings without `Sources:` line
- Numbers floated without attribution ("they're losing ~40% of conversions")
- Estimates presented as facts
- Industry-benchmark claims sourced to "industry data" with no citation
- Patterns claimed from a single observation without "(N=1)" caveat

## Score scale (0-10)

- **0-2** Most findings have no source attribution; reads as opinion
- **3-4** Some findings sourced; numbers float without attribution
- **5-6** Most findings sourced; estimates not labeled as such
- **7-8** Every finding sourced; estimates labeled; small-N caveats present
- **9-10** Above + cross-section evidence-graph is internally consistent (same evidence cited in multiple findings)

## Anchors for severity-of-MA-2-failure

- A finding with a quantitative claim and no source URL: severity-of-failure 3
- An estimate presented as a fact: severity-of-failure 2
- A finding without `Sources:` line but no quantitative claim: severity-of-failure 1

## Notes for JR review

- This is the load-bearing rubric for credibility. Tightening the bar here directly affects whether the audit reads as "research" or as "opinion."
- Consider: should we require ≥2 evidence URLs per finding (vs current ≥1)? Tradeoff = forces deeper investigation but may push gap_flagging up artificially.
- Sync with judge prompt `judges/MA-2-judge.md`.
