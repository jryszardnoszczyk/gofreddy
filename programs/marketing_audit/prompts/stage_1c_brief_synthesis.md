# Stage 1c — Brief Synthesis (Opus, 1 call)

You are running Stage 1c for **{prospect_domain}** (slug: `{client_slug}`). Stage 1b's discovery has populated `prediscovery/signals.md`, `gaps.jsonl`, and `bundles_active.json`. You synthesize that into a structured brief that the four Stage-2 agents will read as their primary context.

This is **one call**, no multi-turn. Read the inputs, write the four output files, return.

## Inputs

### Intake form

```json
{intake_data}
```

### `signals.md`

```markdown
{signals}
```

### `gaps.jsonl`

```
{gaps_jsonl}
```

### `bundles_active.json`

```json
{bundles_active}
```

## Outputs (write to `prediscovery/`)

### 1. `brief.md`

Prose for Stage-2 agent consumption. Structure:

```
# Marketing Audit Brief — {prospect_domain}

## ICP Refinement
(Who buys this, who decides, what triggers urgency. Refined from intake + observed signals.)

## Competitor Slate
(3-7 named competitors with quick rationale per pick. Mark each as direct / secondary / indirect.)

## Top Pain Points
(3-5 prospect-side problems the audit will likely surface. Specific, evidence-anchored.)

## Strategic Hypotheses
(2-4 bets about what's broken in the prospect's GTM motion that the audit should test.)

## Phase-0 Snapshot
(Reference to phase0_meta.json — list which of the 9 frames have data, which are gap-flagged.)

## Bundle Activations
(Per master plan §2.4 + bundles_active.json — vertical/geo/segment activations with one-sentence why.)

## Gap-Driven Caveats
(Top 3 gaps from gaps.jsonl that materially shape what Stage 2 can and cannot conclude.)
```

Aim for ~1500-2500 words. Stage-2 agents will read this verbatim; quality of synthesis matters more than coverage breadth.

### 2. `brief.json`

Structured form of the same content for downstream consumption:

```json
{{
  "audit_id": "<from intake>",
  "prospect_domain": "{prospect_domain}",
  "icp": {{
    "primary_buyer": "<role>",
    "primary_decision_maker": "<role>",
    "urgency_triggers": ["..."]
  }},
  "competitors": [
    {{ "name": "...", "domain": "...", "type": "direct|secondary|indirect", "rationale": "..." }}
  ],
  "top_pain_points": ["..."],
  "strategic_hypotheses": ["..."],
  "active_bundles": {{
    "vertical": [...],
    "geo": [...],
    "segment": [...]
  }},
  "blocking_gaps": [
    {{ "section": "...", "question": "...", "downstream_impact": "..." }}
  ]
}}
```

### 3. `phase0_meta.json`

The 9 Phase-0 meta-frames per master plan §2.4. For each frame, populate what you can measure from Stage 1b's signals; leave fields null where the data isn't available (Stage 3 will surface those nulls as a "Phase-0 gap" finding):

```json
{{
  "frame_1_traffic_mix": {{
    "organic_share_pct": null,
    "paid_share_pct": null,
    "direct_share_pct": null,
    "referral_share_pct": null,
    "social_share_pct": null,
    "ai_referrer_share_pct": null,
    "evidence_urls": [],
    "confidence": "L|M|H"
  }},
  "frame_2_trajectory": {{
    "12mo_visit_change_pct": null,
    "channel_movement": "describe what moved",
    "evidence_urls": [],
    "confidence": "L|M|H"
  }},
  "frame_3_geo_mix": {{
    "top_geographies": [],
    "geo_concentration_index": null,
    "evidence_urls": [],
    "confidence": "L|M|H"
  }},
  "frame_4_share_of_voice": {{
    "category_sov_pct": null,
    "named_competitors": [],
    "evidence_urls": [],
    "confidence": "L|M|H"
  }},
  "frame_5_engagement_proxies": {{
    "bounce_rate": null,
    "session_duration_sec": null,
    "pages_per_session": null,
    "evidence_urls": [],
    "confidence": "L|M|H"
  }},
  "frame_6_channel_model_fit": {{
    "icp_to_channel_alignment_score": null,
    "weakest_channel": "...",
    "strongest_channel": "...",
    "evidence_urls": [],
    "confidence": "L|M|H"
  }},
  "frame_7_growth_loops_inventory": {{
    "loops_observed": [],
    "loops_missing_for_segment": [],
    "evidence_urls": [],
    "confidence": "L|M|H"
  }},
  "frame_8_maturity_tier": {{
    "tier": "early|growth|scale|mature",
    "rationale": "...",
    "evidence_urls": [],
    "confidence": "L|M|H"
  }},
  "frame_9_north_star_tell": {{
    "implied_north_star_metric": "...",
    "supporting_signals": [],
    "evidence_urls": [],
    "confidence": "L|M|H"
  }}
}}
```

### 4. `agent_reading_guides.json`

A ~150-token per-agent guidance object that pulls the Phase-0 frames most relevant to each agent's lens portfolio:

```json
{{
  "findability": "Frame 1 traffic mix (organic share is your anchor). Frame 2 trajectory. Frame 3 geo mix. ICP context: [...]. Top hypothesis to test: [...]. Top gap to work around: [...].",
  "narrative": "Frame 4 share of voice. Frame 8 maturity tier. Frame 9 north-star tell. ICP context: [...]. Top hypothesis to test: [...]. Top gap to work around: [...].",
  "acquisition": "Frame 6 channel-model fit. Frame 7 growth-loops inventory. ICP context: [...]. Top hypothesis to test: [...]. Top gap to work around: [...].",
  "experience": "Frame 5 engagement proxies. Frame 9 north-star tell. ICP context: [...]. Top hypothesis to test: [...]. Top gap to work around: [...]."
}}
```

Each guide ≤ 150 tokens. The Stage-2 agents read this BEFORE they look at the lens YAML; it's their orientation, not their checklist.

## Synthesis principles

1. **Refine, don't rehearse.** The intake already says what JR thinks — your job is to update it with the empirical signal Stage 1b uncovered.
2. **Phase-0 nulls are findings.** A frame you can't populate is a gap; don't fabricate. Stage 3 will lift Phase-0 gaps into a dedicated "State of the Business" finding.
3. **Strategic hypotheses must be testable.** "Their GTM is weak" is not a hypothesis. "Their pricing page lacks anchor-tier psychology" is.
4. **Reading guides shape investigation.** Each guide should change what its target agent looks at first, not what it concludes.

When done, return the four file paths you wrote in your final reply.
