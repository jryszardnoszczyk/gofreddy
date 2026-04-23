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

## Current search-v1 counts (23 fixtures @ v1.0)

| domain | count |
|---|---|
| geo | 6 |
| competitive | 6 |
| monitoring | 6 |
| storyboard | 5 |

## Rubric criteria coverage @ v1.0

| criterion | count | target (≥) |
|---|---|---|
| factuality | 8 | 2 ✅ |
| grounding | 7 | 2 ✅ |
| format-adherence | 7 | 2 ✅ |
| recency | 6 | 2 ✅ |
| multi-lingual | 2 | 2 ✅ (at floor) |
| cross-platform | 3 | 2 ✅ |
| **instruction-following** | **0** | 2 ❌ **gap** |

## Known gaps (see full matrix for fills)

1. Language diversity is near-zero outside storyboard (2/23 non-English)
2. Geography is implicitly US/global-only
3. Adversarial axes are almost entirely untested
4. Vertical skew toward SaaS (≈39%)
5. Zero fixtures stress `instruction-following`

Phase 3 (search-v1 → 1.1) addresses gaps 1, 3, 5 with 6–8 additions.

## When to update

- **Add/remove a fixture:** update the corresponding domain row in `docs/plans/fixture-taxonomy-matrix.md`, re-run the coverage counts, amend this file's counts.
- **New axis value** (e.g., first `zh` fixture): add the value to the axes table above and to the full matrix doc.
- **Rubric coverage drops below floor:** call it out in the PR description — that's a benchmark-health regression.
