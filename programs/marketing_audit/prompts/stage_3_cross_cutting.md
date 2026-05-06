# Stage 3 — Cross-cutting Phase-0 Merge & Dedup (Opus, 1 call)

You are running Stage 3a for **{prospect_domain}**. Four Stage-2 agents (Findability, Narrative, Acquisition, Experience) have each emitted ParentFindings within their own session. Your job: merge across agents.

## What you receive

### `phase0_meta.json`

```json
{phase0_meta}
```

The 9 Phase-0 meta-frames Stage 1c populated. Some fields are populated, some are `null` (gaps). Frames feed every Stage-2 agent's reading guide; they should also surface as findings in the deliverable's "State of the Business" opener.

### All agents' ParentFindings

```json
{parent_findings}
```

Aggregated across the 4 agents. Some report_section overlaps are intentional (the dual-fire lenses #32 and #128). Some are accidental (two agents fired on the same observation from different angles). Your job is to dedupe.

## What you produce

A single text reply (≤4000 words) containing:

### Section 1 — Phase-0 ParentFindings (1-3 of them)

For each Phase-0 frame with notable signal (positive OR negative), draft a dedicated **Phase-0 ParentFinding** that will anchor the deliverable's State-of-the-Business opener. These are tagged `phase0_frame` (1-9) and routed to `report_section: "state_of_business"`. Aim for 1-3 such findings — these are not per-frame; they are the strongest 1-3 stories Phase-0 evidence tells.

Per finding, give:
- `headline` — one strategic sentence
- `frame_anchor` — which Phase-0 frame number (1-9)
- `evidence_summary` — 2-3 sentences naming the measurements + their implications
- `recommendation` — ≥50 words strategic substance, mapped to a proposal tier hint
- `severity` (0-3)
- `confidence` (H/M/L)

**Where Phase-0 frames are gap-filled (`null` in the JSON), surface that honestly as a finding** — "we couldn't measure traffic-mix because the prospect doesn't have GA4 attached + SimilarWeb panel returned no data; this means the audit's channel-fit analysis is based on inference, not measurement." Don't paper over with speculation.

### Section 2 — Cross-agent dedupes (note each merge)

For every ParentFinding cluster where 2+ agents fired on overlapping observations, declare:
- The merge: which finding IDs collapse into which
- The arbitrating angle: which agent's framing wins, OR a synthesis that combines both
- Why: 1-sentence rationale

Most of these will be the dual-fire lenses (#32 Consent Mode v2 → Findability + Experience; #128 Tag-manager hygiene → Findability + Experience). Other duplicates are also possible — flag them.

### Section 3 — Cross-cutting signals (themes the agents missed individually)

Look ACROSS all 4 agents' findings for patterns no single agent could see:
- "Three agents flag positioning drift but each from their own surface" → category-language-fragmentation cross-cutting story
- "Findability + Experience both surface MarTech-stack gaps that block measurement" → measurement-foundations cross-cutting story
- "Acquisition's ad-creative monoculture + Narrative's voice fragmentation + Findability's category-keyword absence" → brand-message-market-fit cross-cutting story

These cross-cuts will become 1-3 additional ParentFindings the deliverable opens with.

## Synthesis principles

1. **Dedupe by SubSignal overlap, not headline overlap.** Two agents may have written different headlines about the same underlying SubSignals — those merge. Two agents writing similar headlines about different SubSignals don't merge.
2. **Phase-0 nulls ARE findings.** Don't apologize for them; surface them.
3. **Cross-cutting requires three pieces of evidence.** A theme isn't cross-cutting unless three+ ParentFindings from different agents support it.
4. **Don't introduce new evidence.** You only synthesize what the agents emitted. If the synthesis exposes a gap, name the gap; don't fill it.
5. **Severity propagates.** A merged ParentFinding takes max(child.severity); a cross-cutting finding takes max of contributing-finding severities.

## Output

Plain markdown reply. Stage 3b's narrative-writer call reads your output verbatim as one of its inputs. Be concise but complete — every Phase-0 ParentFinding + every dedupe + every cross-cutting story shows up.

When done, end your reply with a short bullet list:
- Phase-0 ParentFindings drafted: N
- Cross-agent dedupes performed: N
- Cross-cutting stories identified: N
