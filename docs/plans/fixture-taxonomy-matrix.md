# Fixture Taxonomy Matrix (Plan B Phase 1)

**Status:** authored 2026-04-23. Living artifact — update when adding/removing fixtures. Last refreshed 2026-05-08 (added marketing_audit + x_engine + linkedin_engine domain rows; fixed search-v1 placeholder angle IDs).
**Scope:** `search-v1` (in-repo, 41 fixtures as of v1.2: 12 geo + 7 competitive + 6 monitoring + 6 storyboard + 4 marketing_audit + 4 x_engine + 4 linkedin_engine) + `holdout-v1` composition (28 fixtures as of 2026-05-08 evening: 4 per lane × 7 lanes). Two pools deliberately disjoint (no client/angle overlap) so cross-pool divergence measures generalization to fresh data.

## The 6 axes

Every fixture lives in exactly one cell of this grid. Every pool maps a cell to exactly one fixture.

| Axis | Values |
|---|---|
| **1. domain** | `geo` · `competitive` · `monitoring` · `storyboard` · `marketing_audit` · `x_engine` · `linkedin_engine` |
| **2. language** | `en` · `de` · `pt-BR` · `ja` · `es` · `fr` · `zh` · `multi` |
| **3. geography** | `US` · `EU` · `LATAM` · `APAC` · `global` |
| **4. vertical** | `saas` · `ecomm` · `health` · `fintech` · `media-creator` · `enterprise` · `agriculture` · `auto` · `hosting` · `gaming` · `creator-economy` · `legal-services` · `consumer-DTC` · `marketplace` |
| **5. adversarial-axis** | `none` · `paywall-gated` · `SPA` · `rate-limited` · `captcha` · `blog-vs-docs` · `stale-content` · `noisy-content` |
| **6. stressed-rubric-criteria** | `factuality` · `grounding` · `recency` · `instruction-following` · `format-adherence` · `multi-lingual` · `cross-platform` · `voice-consistency` · `slop-freeness` · `cohort-diversity` · `9-axis-completeness` |

**Why 6 axes not more:** any axis that never varies across fixtures adds no discriminability. If every fixture had the same platform (say, web), adding "platform" would produce a 1-value axis that can't fail a variant for the wrong reason. These 6 are the ones where variants actually differ in behavior today.

---

## Placement: all 41 existing search-v1 fixtures (v1.2)

Each row names the fixture and its cell value on each axis.

### geo domain (6)

| fixture_id | language | geography | vertical | adversarial | stressed-rubric |
|---|---|---|---|---|---|
| `geo-semrush-pricing` | en | US | saas | none | factuality + format-adherence |
| `geo-ahrefs-pricing` | en | US | saas | none | factuality + format-adherence |
| `geo-moz-homepage` | en | US | saas | none | factuality |
| `geo-bluehost-shared-hosting` | en | US | hosting | none | factuality + grounding |
| `geo-mayoclinic-atrial-fibrillation` | en | US | health | none | factuality + grounding |
| `geo-patagonia-nano-puff-pdp` | en | US | ecomm | none | factuality + format-adherence |

**Read:** six **English / US / mostly-SaaS / non-adversarial** fixtures. No language variation, no geography variation, no adversarial stress. This is the widest coverage gap in the suite.

### competitive domain (6)

| fixture_id | language | geography | vertical | adversarial | stressed-rubric |
|---|---|---|---|---|---|
| `competitive-figma` | en | global | saas | none | grounding |
| `competitive-canva` | en | global | saas | none | grounding |
| `competitive-miro` | en | global | saas | none | grounding |
| `competitive-epic-ehr` | en | US | health + enterprise | none | factuality + grounding |
| `competitive-johndeere-precisionag` | en | US | agriculture + enterprise | none | factuality + grounding |
| `competitive-patreon` | en | global | media-creator | none | grounding |

**Read:** competitive has slightly better vertical coverage (4 distinct verticals) but same English-only / non-adversarial limitation as geo.

### monitoring domain (6)

| fixture_id | language | geography | vertical | adversarial | stressed-rubric |
|---|---|---|---|---|---|
| `monitoring-shopify-2026w12` | en | global | ecomm + saas | recency (weekly window) | recency |
| `monitoring-lululemon-2026w12` | en | global | ecomm | recency | recency |
| `monitoring-notion-2026w12` | en | global | saas | recency | recency |
| `monitoring-rippling-firstweek` | en | global | saas + enterprise | recency + first-week edge case | recency |
| `monitoring-ramp-arc-t0` | en | global | fintech + enterprise | recency (t0-vs-t1 pair) | recency + cross-platform |
| `monitoring-ramp-arc-t1` | en | global | fintech + enterprise | recency (t0-vs-t1 pair) | recency + cross-platform |

**Read:** all six stress recency as the rubric criterion (monitoring's raison d'être). Domain coverage within monitoring is decent; the two `ramp-arc-t0/t1` fixtures form a time-pair. English / global only — no regional monitoring fixtures.

### storyboard domain (5)

| fixture_id | language | geography | vertical | adversarial | stressed-rubric |
|---|---|---|---|---|---|
| `storyboard-gossip-goblin` | en | US | media-creator | none | format-adherence |
| `storyboard-techreview` | en | US | media-creator | none | format-adherence + factuality |
| `storyboard-mrbeast` | en | US | media-creator | none | format-adherence |
| `storyboard-khaby-lame-tiktok` | multi | global | media-creator | cross-platform (TikTok-vs-YouTube) | cross-platform + format-adherence |
| `storyboard-porta-dos-fundos` | pt-BR | LATAM | media-creator | multi-lingual | multi-lingual + format-adherence |

**Read:** storyboard is the only domain with non-English coverage (`khaby-lame-tiktok`, `porta-dos-fundos`). It's also the only domain with a platform-variation adversarial (TikTok vs YouTube). Still 5/5 creator-economy vertical — no enterprise/consumer-brand storyboard work.

### marketing_audit domain (4 — added 2026-05-08)

| fixture_id | language | geography | vertical | adversarial | stressed-rubric |
|---|---|---|---|---|---|
| `marketing-audit-anthropic` | en | US | saas (AI) | none | 9-axis-completeness + factuality |
| `marketing-audit-dwf` | en | UK | legal-services | opaque-B2B (institutional) | factuality + grounding |
| `marketing-audit-perplexity` | en | US | saas (AI) | none | 9-axis-completeness + factuality |
| `marketing-audit-substack-creator-economy` | en | global | creator-economy + saas | none | 9-axis-completeness + format-adherence |

**Read:** four English fixtures stressing the 9-axis marketing-audit deliverable (findability, narrative, acquisition, experience, competitive, monitoring, geo, state_of_business, martech_compliance). Pool spans 3 verticals (AI-saas × 2, legal-services × 1, creator-economy × 1). DWF brings the only opaque-B2B adversarial in this lane (institutional pages with little public marketing surface). Holdout-v1 marketing_audit pool — disjoint from this — covers Stripe/Linear/Allbirds/MercadoLibre, adding fintech-infra + dev-tools-saas + DTC-consumer + LATAM-marketplace verticals to the cross-pool measurement surface.

### x_engine domain (4 — added 2026-05-08)

| fixture_id | language | geography | vertical | adversarial | stressed-rubric |
|---|---|---|---|---|---|
| `x_engine-angle-121` | en | US | saas (AI-native marketing) | none | voice-consistency + factuality |
| `x_engine-angle-122` | en | US | saas (AI-native marketing) | none | voice-consistency + slop-freeness |
| `x_engine-angle-123` | en | US | saas (AI-native marketing) | none | voice-consistency + cohort-diversity |
| `x_engine-angle-124` | en | US | saas (AI-native marketing) | none | voice-consistency + slop-freeness |

**Read:** all 4 search-v1 angles share the AI-native-marketing voice_pillar — pool diversity is constrained by Apify's pull breadth, not by design. The X-6 cross-cohort diversity rubric will correctly grade variants that struggle on this homogeneous pool. Holdout-v1 x_engine has full 4-pillar coverage (AI-native marketing + harness eng + Claude Code + Pi/homelab via angles 120/125/126/127) precisely because pool disjointedness here exists to measure pillar generalization.

### linkedin_engine domain (4 — added 2026-05-08)

| fixture_id | language | geography | vertical | adversarial | stressed-rubric |
|---|---|---|---|---|---|
| `linkedin_engine-angle-121` | en | US | saas (AI-native marketing) | none | voice-consistency + format-adherence |
| `linkedin_engine-angle-122` | en | US | saas (AI-native marketing) | none | voice-consistency + format-adherence |
| `linkedin_engine-angle-123` | en | US | saas (AI-native marketing) | none | voice-consistency + cohort-diversity |
| `linkedin_engine-angle-124` | en | US | saas (AI-native marketing) | none | voice-consistency + format-adherence |

**Read:** mirrors x_engine's 4 angles per master plan v13 D13 (X + LinkedIn share the same `angles` table; per-platform divergence lives in the rubrics + prompts, not the fixture set). Stressed-rubric criteria differ from x_engine because LI rubrics weight format-adherence higher (LI-5 hashtag count + length-bracket fidelity) while X rubrics weight cohort diversity higher (X-6 archetype variance across drafts).

---

## Coverage gaps (identified 2026-04-23, refreshed 2026-05-08)

Reading across the 6 axes, the gaps are striking:

### Gap 1 — Language diversity is near-zero outside storyboard

- Only **2/23** fixtures are non-English (`storyboard-khaby-lame-tiktok`, `storyboard-porta-dos-fundos`)
- `geo`, `competitive`, `monitoring` are **100% English**
- Variants that behave differently in multi-lingual corpora (tokenization, reasoning-chain fidelity, multilingual-specific failure modes) are **untested** outside storyboard

### Gap 2 — Geography is implicitly US/global only

- Explicit regional fixtures: 0
- Variants that regress on non-US SEO/search patterns (`.de` Amazon, `.jp` Rakuten, Mercado Libre) would not surface here

### Gap 3 — Adversarial axes are almost entirely untested

| adversarial-axis | coverage |
|---|---|
| `paywall-gated` | 0/23 |
| `SPA` (client-side render) | 0/23 |
| `blog-vs-docs` (same-intent different-surface) | 0/23 |
| `rate-limited` | 0/23 |
| `captcha` | 0/23 |
| `stale-content` | 0/23 (monitoring's recency stress is orthogonal) |
| `noisy-content` | 0/23 |

The suite measures **happy-path fluency**. It cannot discriminate variants that degrade when scraped content is behind auth, rendered in JS, or contains substantial noise.

### Gap 4 — Vertical skew

| vertical | count |
|---|---|
| saas | 9 (≈39%) |
| media-creator | 5 (≈22%) |
| ecomm | 3 |
| health | 2 |
| enterprise | 4 (mostly overlapping with other verticals) |
| fintech | 2 (Ramp pair) |
| hosting | 1 |
| agriculture | 1 |
| auto | 0 |
| gaming | 0 |

SaaS dominates. Vertical-specific failure modes (legal/regulated content, long-tail gaming reviews, automotive spec pages) have zero representation.

### Gap 5 — Stressed-rubric distribution

| criterion | fixture count |
|---|---|
| factuality | 8 |
| grounding | 7 |
| format-adherence | 7 |
| recency | 6 (all monitoring) |
| multi-lingual | 2 |
| cross-platform | 3 |
| instruction-following | 0 |

**Zero fixtures stress instruction-following specifically.** If a variant starts ignoring operator instructions, no current fixture would catch it; it would slip through until deployment.

---

## Phase 3 fills (search-v1 → 1.1 — SHIPPED 2026-04-23)

Six additions closing the three most important gaps (language, adversarial, instruction-following). Picks had to use DIFFERENT URLs from the holdout-v1 entries to keep the pools disjoint — the BMW case is explicit: holdout uses `/bmw-i4.html`, search-v1 uses `/bmw-ix.html`. Both stress the same `de/EU/auto/multi-lingual` cell so divergence between pools measures generalization to the same intent on a fresh URL.

| # | fixture_id | domain | language | geography | vertical | adversarial | stressed-rubric | URL / context |
|---|---|---|---|---|---|---|---|---|
| 1 | `geo-bmw-ix-de` | geo | de | EU | auto | none | factuality + multi-lingual | `https://www.bmw.de/de/topics/faszination-bmw/elektro/bmw-ix.html` |
| 2 | `geo-rakuten-books-jp-spa` | geo | ja | APAC | ecomm | SPA | factuality + multi-lingual + SPA | `https://books.rakuten.co.jp/` |
| 3 | `geo-stripe-docs-payments` | geo | en | US | saas | none | grounding + instruction-following | `https://docs.stripe.com/payments` |
| 4 | `geo-nubank-br-conta` | geo | pt-BR | LATAM | fintech | none | factuality + multi-lingual | `https://nubank.com.br/conta-digital/` |
| 5 | `competitive-sap-s4hana-de` | competitive | de | EU | enterprise | none | grounding + multi-lingual | context slug `sap-s4hana-enterprise` |
| 6 | `storyboard-techlinked-howto-en` | storyboard | en | US | media-creator | instruction-following (explicit format env) | instruction-following + format-adherence | `youtube` + env `AUTORESEARCH_STORYBOARD_FORMAT=explainer-90s` |

**How the 6 picks close the gaps:**
- #1 (bmw-iX DE) + #4 (nubank-BR) add German + Portuguese + explicit non-US regions to `geo`. Parallel holdout entries (`geo-bmw-ev-de` i4 page, `geo-nubank-br-pix`) stress the same cell on fresh URLs.
- #2 (rakuten-books-JP-SPA) adds Japanese + APAC + the missing SPA adversarial.
- #3 (stripe-docs-payments) adds instruction-following (operator-style reference doc).
- #5 (sap-s4hana-DE) adds German to competitive + enterprise-B2B intent.
- #6 (techlinked-howto) adds explicit instruction-following to storyboard via the format env var.

Net effect on the matrix:
- Language coverage: 2 → 6 non-English fixtures.
- Geography coverage: 0 → 4 regional fixtures.
- Instruction-following coverage: 0 → 2 fixtures.
- Adversarial-axis coverage: 0 SPA → 1 SPA.

**Stretch picks now shipped (search-v1 v1.1 after full-Plan-B implementation 2026-04-23):**
- `geo-gamefaqs-ff7-rebirth` (gaming, noisy-content adversarial) — URL `https://gamefaqs.gamespot.com/ps5/700267-final-fantasy-vii-rebirth`
- `geo-kubernetes-blog-vs-docs` (saas, blog-vs-docs adversarial) — URL `https://kubernetes.io/docs/concepts/workloads/`

search-v1 total now 31 fixtures @ v1.1.

---

## Rubric-coverage matrix (Step 5)

| rubric criterion | search-v1 @ 1.0 count | search-v1 @ 1.1 count (after Phase 3) | holdout-v1 MVP (8-fixture subset) count |
|---|---|---|---|
| factuality | 8 | 12 | 4 (all 4 geo rows) |
| grounding | 7 | 10 | 2 (geo-stripe-docs-gated, geo-rakuten-travel-spa) |
| format-adherence | 7 | 8 | 0 |
| recency | 6 | 6 | 4 (all 4 monitoring rows) |
| multi-lingual | 2 | 5 | 2 (geo-nubank-br-pix, geo-rakuten-travel-spa) |
| cross-platform | 3 | 3 | 0 |
| instruction-following | 0 | 2 | 0 |

Acceptance after Phase 3: every rubric criterion has ≥2 fixtures stressing it across search-v1 + holdout-v1. `instruction-following` goes from 0 to 2 — the sharpest single-criterion lift.

---

## Pool assignment

Every fixture in the matrix lives in **exactly one pool**. Pool membership is set by where the fixture is authored, not by a tag:

- `search-v1` pool → `autoresearch/eval_suites/search-v1.json` (in-repo, proposer-visible).
- `holdout-v1` pool → `~/.config/gofreddy/holdouts/holdout-v1.json` (out-of-repo, proposer-invisible).

The discriminability check (Plan A Phase 10) exists to prevent the same fixture ending up in both pools by accident; its guard is that `(fixture_id, pool)` is a composite key.

**Holdout-v1 full 16-row composition (SHIPPED 2026-04-23):**
- geo (4): `geo-bmw-ev-de` (anchor), `geo-rakuten-travel-spa` (anchor), `geo-nubank-br-pix` (rotating), `geo-stripe-docs-gated` (rotating)
- competitive (4): `competitive-opaque-private-b2b` (anchor), `competitive-axios-vs-semafor` (anchor), `competitive-toyota-vs-byd-ev` (rotating), `competitive-nubank-vs-latam-banks` (rotating)
- monitoring (4): `monitoring-twitch-low-volume` (anchor), `monitoring-tsmc-apac` (anchor), `monitoring-unilever-cpg` (rotating), `monitoring-deutsche-bank` (rotating) — context fields are `${AUTORESEARCH_HOLDOUT_MONITORING_*_CONTEXT}` placeholders; operator must export real xpoz monitor UUIDs before refresh succeeds
- storyboard (4): `storyboard-tokyo-creative-ja` (anchor), `storyboard-beautiful-chorus-nonverbal` (anchor), `storyboard-amixem-fr` (rotating), `storyboard-mkbhd-pivoting` (rotating)

---

## How to update this artifact

When adding or removing a fixture:

1. Add/remove the row in the appropriate domain table above.
2. Re-run the Rubric-coverage matrix counts.
3. If a gap row shifts below its threshold (e.g., `instruction-following` count drops below 2), flag it in the commit message — that's a regression of benchmark health.
4. Re-check discriminability via `freddy fixture discriminate` (Plan A Phase 10).

`autoresearch/eval_suites/TAXONOMY.md` carries a one-page living index pointing here.
