# Fixture Taxonomy — Living Index

Short index. Full matrix lives in `docs/plans/fixture-taxonomy-matrix.md`.

## Axes

| Axis | Purpose |
|---|---|
| **domain** | Which domain the fixture exercises (`geo`, `competitive`, `monitoring`, `storyboard`) |
| **language** | `en` · `de` · `pt-BR` · `ja` · `es` · `fr` · `zh` · `multi` |
| **geography** | `US` · `EU` · `LATAM` · `APAC` · `global` |
| **vertical** | `saas` · `ecomm` · `health` · `fintech` · `media-creator` · `enterprise` · `agriculture` · `auto` · `hosting` · `gaming` |
| **adversarial-axis** | `none` · `paywall-gated` · `SPA` · `rate-limited` · `captcha` · `blog-vs-docs` · `stale-content` · `noisy-content` |
| **stressed-rubric-criteria** | `factuality` · `grounding` · `recency` · `instruction-following` · `format-adherence` · `multi-lingual` · `cross-platform` |

## Current search-v1 counts (29 fixtures @ v1.1)

| domain | count | added in v1.1 |
|---|---|---|
| geo | 10 | +4 |
| competitive | 7 | +1 |
| monitoring | 6 | 0 |
| storyboard | 6 | +1 |

## Rubric criteria coverage @ v1.1

| criterion | count | target (≥) | change from v1.0 |
|---|---|---|---|
| factuality | 12 | 2 ✅ | +4 |
| grounding | 10 | 2 ✅ | +3 |
| format-adherence | 8 | 2 ✅ | +1 |
| recency | 6 | 2 ✅ | 0 |
| multi-lingual | 5 | 2 ✅ | +3 |
| cross-platform | 3 | 2 ✅ | 0 |
| **instruction-following** | **2** | 2 ✅ | **+2** |

## Remaining gaps (see full matrix)

1. Gaming vertical: 0 fixtures (stretch pick not shipped).
2. Blog-vs-docs adversarial: 0 fixtures (stretch pick not shipped).
3. Monitoring is English / global only — regional monitoring fixtures are a follow-up.

Phase 3 closed language, geography, SPA, and instruction-following gaps.

## When to update

- **Add/remove a fixture:** update the corresponding domain row in `docs/plans/fixture-taxonomy-matrix.md`, re-run the coverage counts, amend this file's counts.
- **New axis value** (e.g., first `zh` fixture): add the value to the axes table above and to the full matrix doc.
- **Rubric coverage drops below floor:** call it out in the PR description — that's a benchmark-health regression.
