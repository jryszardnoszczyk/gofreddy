# Onboarding Checklist — {{CLIENT_NAME}}

Use this checklist on day 1 with a new client. Target: complete in 2–3 days.

## 1. Access & Credentials

- [ ] Company website admin access (if applicable)
- [ ] Google Analytics read access (account: {{GA_ACCOUNT_ID}})
- [ ] Google Search Console verified domain
- [ ] Ad platform read access (Meta, Google Ads, etc.)
- [ ] Social account API tokens (Twitter/X, Instagram, TikTok, LinkedIn)
- [ ] CMS admin or publishing API token (WordPress, Ghost, etc.)
- [ ] Email platform (for newsletter syncing) — if in scope

All credentials stored in `clients/{{CLIENT_SLUG}}/credentials.env` (git-ignored, 0600 perms).

## 2. Brand Information

- [ ] Brand guidelines PDF / brand book
- [ ] Voice & tone guide
- [ ] Product positioning doc
- [ ] Buyer persona docs
- [ ] Logo assets (SVG + PNG, light + dark)
- [ ] Approved spokespersons list (for video generation)

## 3. Goals & KPIs

| Dimension | Current baseline | 90-day target | 12-month target |
|---|---|---|---|
| Organic traffic | {{TRAFFIC_BASELINE}} | {{TRAFFIC_90D}} | {{TRAFFIC_12M}} |
| Qualified leads | {{LEADS_BASELINE}} | {{LEADS_90D}} | {{LEADS_12M}} |
| Brand mentions | {{MENTIONS_BASELINE}} | {{MENTIONS_90D}} | {{MENTIONS_12M}} |
| Content output | {{CONTENT_BASELINE}} | {{CONTENT_90D}} | {{CONTENT_12M}} |

## 4. Competitors

Primary 5 competitors to monitor:

1. {{COMPETITOR_1}} — {{COMPETITOR_1_URL}}
2. {{COMPETITOR_2}} — {{COMPETITOR_2_URL}}
3. {{COMPETITOR_3}} — {{COMPETITOR_3_URL}}
4. {{COMPETITOR_4}} — {{COMPETITOR_4_URL}}
5. {{COMPETITOR_5}} — {{COMPETITOR_5_URL}}

Keywords to track for share of voice: {{WATCH_KEYWORDS}}

## 5. Setup Steps (for Freddy)

- [ ] `freddy client new {{CLIENT_SLUG}}`
- [ ] Copy `.env.example` → `clients/{{CLIENT_SLUG}}/.env` and populate keys
- [ ] Run baseline audit: `freddy audit seo --client {{CLIENT_SLUG}} {{CLIENT_DOMAIN}}`
- [ ] Run baseline competitive: `freddy audit competitive --client {{CLIENT_SLUG}} {{COMPETITOR_1_DOMAIN}}`
- [ ] Run baseline monitoring: `freddy audit monitor --client {{CLIENT_SLUG}} "{{BRAND_QUERY}}"`
- [ ] Generate baseline portal: `python portal/generate.py --client {{CLIENT_SLUG}}`
- [ ] Send portal URL to client
- [ ] Schedule kickoff call + weekly check-in cadence

## 6. Communication Cadence

- **Weekly:** async status update in shared Slack/email thread (Mondays)
- **Monthly:** live portal updated + monthly report PDF (1st of each month)
- **Quarterly:** 30-min strategy review call

---

Questions: noszczykai@gmail.com · gofreddy.ai
