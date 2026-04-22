# Churn-Signal Patterns in Mention Data

Source: Corey Haines marketingskills repo, `churn-prevention` skill.
URL: https://github.com/coreyhaines31/marketingskills/tree/main/skills/churn-prevention

Use this when clustering mentions and classifying stories. Turns "a lot of complaints" into named archetypes that feed MON-5 cross-story patterns and MON-2 severity calibration. Complements `watering-hole-source-guide.md` — that file covers where to read, this file covers what the signals mean.

---

## Cancel-reason taxonomy (four archetypes for negative-mention clusters)

When a cluster of negative mentions forms, tag it against this taxonomy before reporting. Each has distinct implications for the digest's action-items section.

| Archetype | Vocabulary markers | Leading indicator | What it means for the client/competitor |
|-----------|--------------------|--------------------|------------------------------------------|
| **Price** | "too expensive," "not worth it," "pricing got insane," "can't justify," "cheaper alternative" | Billing-page complaints, tier-downgrade mentions | Value-perception problem. Addressable with ROI content + comparison pages, not product changes. |
| **Disengagement** | "I stopped using," "just canceled because I wasn't using it," "forgot I was paying," "not active anymore" | Usage-drop mentions, renewal-time cancels | Activation / ongoing-engagement problem. Addressable with onboarding + lifecycle, not pricing or positioning. |
| **Competitive pull** | "switching to X," "moved to Y," "X does it better," "X is just easier" | Competitor mentions inside cancel threads | Positioning or feature-parity problem. Addressable with competitive brief (see competitive session) + targeted feature investment. |
| **Product gap** | "missing feature," "doesn't support," "I wish it could," "had to use another tool for" | 4-star review "only thing I wish…" patterns | Roadmap signal. Addressable with product changes, not marketing. |

**Rule:** tag every negative-mention cluster with exactly one dominant archetype. Mixed-archetype clusters are usually two separate stories — split them before synthesizing.

---

## Leading-indicator timelines (for MON-3 highest-stakes calls)

Mention-side signals have different lead times before a measurable churn spike. Rank severity by lead time:

| Signal | Lead time before cancel | Severity tag |
|--------|-------------------------|--------------|
| Data-export mentions / G2 reviews mentioning "migration" | **Days** to hours from cancel | CRITICAL — the user is leaving this week |
| Billing-page visits spike + support tickets mentioning "charged again" / "can't cancel" | **1-2 weeks** | HIGH — lead time exists, action can save subset |
| Usage complaints ("I stopped using X") cluster in 4-star competitor reviews | **2-4 weeks** | MEDIUM — early signal, product/marketing time to intervene |
| "I wish it did X" on 4-star reviews (missing feature) | **Quarters** | LOW-MEDIUM — roadmap signal, not imminent |
| Generic price grumbling in 3-star reviews | **Ongoing** | LOW (chronic) — context, not crisis |

**MON-3 application:** a story carrying "data-export" or "migration" vocabulary in week-over-week delta should be the lead story regardless of volume. A story of "price grumbling" with 5× the volume but no leading-indicator vocabulary is usually NOT the highest-stakes finding — it's chronic.

---

## 3-star reviews = the most honest signal

Reinforcing the G2 hierarchy already in `watering-hole-source-guide.md` with churn-specific framing:

- **3-star reviews** carry "still using it but…" signal — this is the healthiest warning layer. Mine these first for product-gap and disengagement archetypes.
- **4-star reviews** hide "the only thing I wish…" — mine for product-gap archetype specifically.
- **1-star reviews** are failure modes — mine for price and competitive-pull archetypes, separated from support/onboarding issues.

---

## Complaint-threshold rule for monitoring severity

From Corey's churn-prevention exit-survey framework: a theme mentioned by ≥3 independent sources in the same week window is materially different from the same theme mentioned by ≥3 in a 6-month window. Mention-volume is not enough — time-compression matters.

Severity rules:
- 3+ independent sources within **7 days** on the same archetype → MON-3 candidate.
- 3+ independent sources within **30 days** → MON-5 cross-story pattern candidate.
- 3+ independent sources over **90 days** → chronic/structural tag (anomaly category already defined in monitoring program).

---

## Application template

For each negative-mention cluster, the digest story section should include:

> **Archetype:** {price | disengagement | competitive-pull | product-gap}.
>
> **Lead-time class:** {critical | high | medium | low}.
>
> **Evidence density:** N independent sources over M days. Vocabulary markers observed: "{quote 1}," "{quote 2}," "{quote 3}."
>
> **Escalation path:** this archetype is addressable by {marketing | product | lifecycle | leave-alone}, not {mismatched function}.

This operationalizes MON-2 (severity with limitations), MON-3 (highest-stakes), MON-4 (action items with responsible team), and MON-5 (named cross-story patterns) simultaneously.

---

## Noise filter (negative scoring, from `revops`)

Not every negative mention is signal. Exclude before severity scoring:

- **Bot-generated** (check for account age < 30 days, no profile photo, identical phrasing across accounts, posting cadence >100/day).
- **Competitor employees** (check user's LinkedIn / bio / handle against known competitor domains).
- **Student / personal-use personas** when the product is B2B (target audience mismatch; not signal for B2B motion).
- **Known trolls / abuse accounts** (flagged in prior digests).

These are statistical flags without semantic weight. Filter before tagging archetype; don't let noise dominate severity.
