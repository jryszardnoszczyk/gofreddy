# MA-5 — Severity Calibration

**Status:** DRAFT (master plan §6.4; JR review-iterate before manifest freeze)

## What this rubric scores

Severity (0-3) on every SubSignal + ParentFinding is anchored to lens-specific severity_anchors from the rubric YAML. No severity inflation. ParentFinding severity = max of children (rollup rule). Severity distributions across the audit are credible — not a sea of "3"s.

## What "good" looks like

- SubSignal severities map to the lens YAML's severity_anchors text
- ParentFinding severity = max(children.severity) — verified deterministic
- Audit-wide severity distribution: roughly 30-50% sev 1, 30-40% sev 2, 10-20% sev 3, ~10% sev 0
- Severity-3 findings have evidence to match (multiple sources, broad impact, clear cost)
- Critical claims aren't downgraded to sev-2 to soften the audit

## What "bad" looks like

- Half or more of all findings tagged severity 3 (inflation)
- Severity choices don't match lens YAML anchors
- ParentFinding severity ≠ max of children (rollup error)
- A severity-3 finding with one piece of weak evidence (false alarm)
- A severity-1 finding that's actually a structural problem (false negative)

## Score scale (0-10)

- **0-2** Severity is undifferentiated; everything is sev-2 or sev-3; no anchoring
- **3-4** Severity choices exist but anchors not respected; rollup errors present
- **5-6** Most severities anchored; rollup mostly correct; distribution skewed but defensible
- **7-8** Severities anchored + rollup correct + distribution credible
- **9-10** Above + severity choices internally consistent across cross-section findings

## Anchors for severity-of-MA-5-failure

- ParentFinding severity ≠ max(children.severity): severity-of-failure 3 (deterministic check)
- A severity-3 finding with single weak evidence: severity-of-failure 2
- A severity-3 finding that the lens YAML wouldn't anchor to "critical": severity-of-failure 2
- Audit with >60% severity-3 findings: severity-of-failure 3 (systemic inflation)

## Notes for JR review

- Severity calibration is the audit's currency. Inflation collapses credibility — once a Head of Marketing realizes "3" doesn't mean what they thought, every other "3" reads as noise.
- Consider: should the rollup check be enforced by Pydantic validator instead of judged here? (It already is — see `agent_models.ParentFinding._recompute_rollup`. But the JUDGE should still verify the agent didn't try to override.)
- Sync with `judges/MA-5-judge.md`.
