# Stage 4 — Proposal (Opus, 1 call)

You are running Stage 4 for **{prospect_domain}**. Stage 3 has delivered the audit findings. Your job: turn the highest-leverage findings into a 3-tier proposal that pitches the agency engagement.

## What you receive

### `report.json` (machine-readable findings)

```json
{report_json}
```

### `data/capability_registry.yaml`

```yaml
{capability_registry}
```

The capability registry catalogs ~48 distinct service offerings the agency delivers, each tagged with one of three engagement tiers (`fix_it`, `build_it`, `run_it`). Read it. Each capability lists the typical scope, ballpark investment, deliverables, and prerequisite ParentFinding shape it answers.

## What you produce

Write two files via the `Write` tool. Use cwd = `clients/<slug>/audit/proposal/`.

### 1. `proposal.md`

Three H2 sections in **fixed order** (structural validator enforces):

```
# Proposal — <prospect_domain>

## fix_it

(Discrete one-off fixes the prospect can fund standalone. Typical $5K-$15K. Maps to the 3-7 highest-severity findings that have a clear scoped fix. Each fix entry follows the card shape below.)

## build_it

(Productized engagement: a defined scope with a tangible deliverable shipped on a fixed timeline. Typical $15K-$60K. Maps to the 1-3 highest-leverage findings whose recommendation requires a substantial workstream. Each build entry follows the card shape below.)

## run_it

(Ongoing retainer: the agency runs a function or workstream as a service. Typical $5K-$25K/month. Maps to the 1-2 areas where ongoing operation is the right unit. Each run entry follows the card shape below.)
```

### Tier card shape (per entry within each tier)

```markdown
### <Engagement Name>

- **Engagement:** <one-line description>
- **Investment:** <$X-$Y range>
- **Best for:** <prospect-state-this-fits — phrased so the prospect recognizes themselves>
- **What this tier delivers:**
  - <deliverable 1>
  - <deliverable 2>
  - <deliverable 3>
- **What we won't do at this tier:** <explicit boundary — important for tier-laddering credibility>
- **Addresses findings:** <ParentFinding IDs from report.json — must reference ≥1>
- **Capability registry entry:** <capability_id from yaml>
```

### Per-tier rules

- Every tier MUST have ≥1 entry. If the audit didn't surface clear `fix_it` work, write 1-2 entries of "table-stakes hygiene fixes" — they always exist and they justify the tier's existence.
- Every entry references ≥1 `addresses_findings` from report.json. If a finding has `proposal_tier_mapping` set, prefer that placement; if not set, infer from severity + recommendation language (one-off → fix_it; productized scope → build_it; ongoing → run_it).
- Investment ranges should align with capability_registry's typical investment fields. Don't invent prices outside the registry's bands.

### 2. `proposal.json` (machine-readable)

```json
{{
  "audit_id": "<from report.json>",
  "prospect_domain": "{prospect_domain}",
  "tiers": {{
    "fix_it": {{
      "engagements": [
        {{
          "name": "...",
          "investment_usd_range": [5000, 15000],
          "best_for": "...",
          "deliverables": ["...", "..."],
          "wont_do": "...",
          "addresses_finding_ids": ["fa-pf-001", "ex-pf-003"],
          "capability_registry_id": "fix-it-tech-seo-fixes"
        }}
      ]
    }},
    "build_it": {{ "engagements": [...] }},
    "run_it": {{ "engagements": [...] }}
  }},
  "generated_at": "<ISO-8601>",
  "narrative_anchor": "<1-sentence why this proposal shape fits this prospect>"
}}
```

## Synthesis principles

1. **Tier laddering, not tier choice.** The proposal should lay out how a prospect could engage at any tier — not pick one for them. Each tier stands alone but also tees up the next.
2. **The `What we won't do at this tier` line is load-bearing.** It's the credibility-creator. Without it, every tier reads like upsell pressure.
3. **Don't propose engagements the audit didn't justify.** If the audit didn't surface a need for, say, a brand-rebuild engagement, don't list one. Engagement-fit (MA-8) judges this directly.
4. **Cost-of-delay framing where it fits.** Each `build_it` entry can carry a "what closes if this isn't started by X" beat — pulls from the finding's recommendation if present.
5. **Reference the registry.** Don't invent capabilities. Pull from the YAML.

## Voice + AI-tell hygiene

Same rules as Stage 3 narrative writer. No `utilize` / `leverage` / `seamless`. Em-dash ≤ 1 per paragraph. Specific, blunt, evidence-anchored.

## Hard rules

1. **3 H2 sections in fixed order**: `fix_it`, `build_it`, `run_it`.
2. **Every entry references ≥1 finding ID** from report.json.
3. **Investment within registry bands** (don't invent $200K engagements if registry caps build_it at $60K).
4. **Don't fabricate capabilities** — registry is authoritative.
5. **`What we won't do` line per entry** — non-negotiable.

When done, return both file paths + a 1-sentence summary of the proposal's strategic shape.
