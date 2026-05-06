# MA-3 — Phase-0 Framing Applied

**Status:** DRAFT (master plan §6.4; JR review-iterate before manifest freeze)

## What this rubric scores

The State-of-the-Business opener pulls measurements from `phase0_meta.json` (the 9 meta-frames). Per-section findings color by relevant Phase-0 frames where applicable. Phase-0 measurements that came back null are surfaced as findings (gap-honesty), not papered over.

## What "good" looks like

- State-of-the-Business names 3+ Phase-0 frame measurements explicitly
- Measurements quoted with their `confidence` from phase0_meta.json
- Per-section findings reference frames where relevant ("Frame 5 engagement proxies show...")
- Null Phase-0 frames surface as "we couldn't measure X because Y" findings
- The audit's central argument leans on Phase-0 evidence, not just tactical lens findings

## What "bad" looks like

- State-of-the-Business doesn't reference Phase-0 frames at all
- Phase-0 measurements present in JSON but unused in narrative
- Null frames silently omitted instead of surfaced as gaps
- Tactical findings dominate; Phase-0 framing is decorative
- Frame measurements quoted without confidence (presents low-confidence inference as fact)

## Score scale (0-10)

- **0-2** No Phase-0 framing in deliverable; State-of-the-Business is generic
- **3-4** State-of-the-Business mentions Phase-0 once; sections don't connect
- **5-6** State-of-the-Business uses 2-3 frames; some sections reference frames
- **7-8** State-of-the-Business uses 3+ frames with confidence levels; sections reference frames where applicable; null frames surfaced
- **9-10** Above + audit's central argument is Phase-0-anchored; frame measurements drive the strategic story

## Anchors for severity-of-MA-3-failure

- State-of-the-Business with no Phase-0 measurements: severity-of-failure 3
- Phase-0 measurements present but unused in narrative: severity-of-failure 2
- Null frames silently omitted: severity-of-failure 2
- Confidence not quoted on Phase-0 measurements: severity-of-failure 1

## Notes for JR review

- Phase-0 framing is the architectural innovation vs prior audit-pipeline drafts. This rubric makes the framing operationally measurable.
- Consider: should we require a Phase-0 measurement on EVERY ParentFinding's `evidence_summary` where applicable? Currently the bar is per-section reference.
- Sync with judge prompt `judges/MA-3-judge.md`.
