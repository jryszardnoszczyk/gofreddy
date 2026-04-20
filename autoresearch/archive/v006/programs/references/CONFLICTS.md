# Conflicts surfaced during external-knowledge injection

Record here any place a Corey Haines skill contradicts an evolved CQ rule or established program guidance. Surface; do not resolve. The meta-agent resolves.

---

## 2026-04-18 — initial injection pass (ai-seo / seo-audit / schema-markup / competitor-alternatives / ad-creative / marketing-psychology / customer-research / community-marketing / copywriting / social-content)

No systemic conflicts surfaced.

### Minor tensions (non-blocking)

- **FAQ count.** Corey's content-patterns reference suggests "enough FAQs to be useful" without a fixed count. CQ-2 specifies 5-7 self-contained answers (minimum 3 for thin pages via CQ-11). The existing evolved rule is more specific — keep CQ-2.
- **Answer length.** Corey specifies 40-60 words for snippet extraction. CQ-1 already specifies 40-60 words for the answer-first intro. Aligned — citation upgraded, not conflict.
- **Schema on homepage.** CQ-10 restricts Organization schema with sameAs to homepage/about only. Corey's ai-seo recommends Organization schema on all pages. CQ-10 is more conservative and targets duplicate-schema pollution. Keep CQ-10.

## 2026-04-20 — pass-2 comprehensive injection

### New minor tensions

- **Schema single-block rule vs `@graph`.** CQ-10 says "exactly one schema block per page." Corey's `schema-markup` reference recommends using a `@graph` array inside that one block to carry multiple typed entities (Organization + WebSite + BreadcrumbList). Technically compatible — `@graph` is inside a single `<script>` tag, so CQ-10 is preserved — but the "exactly one @type per block" implicit reading tightens when multiple types are grouped. CQ-16 added to codify the `@graph` pattern. Surface to meta-agent.
- **Sweep 7 "Zero Risk" excluded from prose-hygiene.** Corey's `copy-editing` seven-sweep order ends with a conversion-CTA-focused Sweep 7 (risk-reversal, guarantees, fear-reduction). This contradicts GEO CQ-3 (honest competitive positioning) and SB-4 (earned emotional transitions). Explicitly excluded in `prose-hygiene.md`; sweeps 1-6 apply.
- **"Authoritative tone" vs AI-tell vocabulary.** Princeton GEO study says authoritative tone = +25% citation boost. Corey's `ai-writing-detection` blocklist strips words like "robust/comprehensive/cutting-edge" that also read as "authoritative" to a naive writer. Resolution in `prose-hygiene.md`: authoritative = evidence density (numbers, named sources), NOT adjective stacking. CQ-17 codifies.

### Rejected skills (and why, for meta-agent transparency)

Round 1 rejects (from original pass): competitor-alternatives reconsidered and injected in this pass.

Round 2 rejects:
- **All 7 CRO skills** (ab-test-setup, page-cro, form-cro, onboarding-cro, popup-cro, signup-flow-cro, paywall-upgrade-cro) — optimize live-funnel human behavior; GoFreddy produces LLM-judged research artifacts. No fitness-function overlap.
- **Lifecycle/growth:** email-sequence, cold-email, lead-magnets, referral-program, free-tool-strategy — authoring playbooks, not analytical frames.
- **community-marketing** — about building the client's own community; monitoring reads existing community mentions. Platform-engagement signals in monitoring-session already carry what was useful.
- **marketing-ideas** — 139-idea ideation catalog; no decision surface inside a session program.
- **analytics-tracking** — GA4/GTM/UTM implementation; sessions consume already-measured data.
- **aso-audit** — no app-store domain in GoFreddy.
- **ad-creative/references/generative-tools.md** — tool-picking infra content for building ad pipelines; not a session-prompt concern.
- **social-content/references/post-templates.md** — authoring templates for writing LinkedIn/Twitter posts; duplicates hook-patterns.md for the one useful piece.
