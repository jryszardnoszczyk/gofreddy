---
date: 2026-05-18
type: research deliverable
status: complete
topic: Monitoring digest vertical-specific conventions
parent: docs/handoffs/2026-05-18-judge-design-step1-monitoring.md
sibling: docs/research/2026-05-15-judges-domain-monitoring.md
companion: docs/research/2026-05-18-ci-vertical-conventions.md (parallel pattern for CI lane)
---

# Vertical-Specific Conventions in Executive Monitoring Digests
## Financial services / healthcare / B2B SaaS / legal / professional services / founder-led startups / regulated industries — what changes per vertical, what the MON judge must accommodate

**Companion to:** `docs/research/2026-05-15-judges-domain-monitoring.md` (generalist Cision/Coombs/Sandman/AMEC/FAA synthesis). This pass goes vertical-specific so the MON lane's rubric does not silently optimize for a single archetype.

**Why this exists.** The MON v0 spec assumes one reader archetype: senior comms director at a Series-B-or-later company reading Monday 8:55am. The fixture cohort the lane actually grades against — and the substitute readers acknowledged in §1 (founder/CEO of an earlier-stage co, agency lead reading on behalf of multiple clients, in-house counsel monitoring reputational legal exposure) — span at least six structurally distinct verticals. A monitoring digest that earns 5/5 against a B2B SaaS comms director could earn 1/5 against a financial-services CCO who is contractually required to receive a different artifact, or against a Klinika-style practice owner whose "monitoring" is a Saturday glance at Google Maps reviews. If the rubric doesn't see that, a 50-generation evolution loop will overfit to whichever vertical happens to dominate the fixture set — and the resulting judge will systematically misjudge digests written for any other vertical.

---

## 1. TL;DR (300 words)

### Top vertical-specific findings (1–2 per vertical)

**Financial services (regulated, banking/asset-mgmt/insurance):**
- Monitoring is *legally mandated* under SEC Reg S-K, OCC operational-risk guidance, and FINRA Rule 3110 supervisory frameworks. "Reputation risk" is a board-reported KPI; the monitoring artifact must produce an auditable chain into the firm's risk register.
- "Actionable" threshold is set by *materiality* (will it affect a 10-K disclosure or be discussed on the earnings call), not volume or sentiment.

**Healthcare (provider, payer, life-sciences):**
- HIPAA + FDA + state medical-board scope-of-practice create a *narrow definition of what comms can do* on patient-related signals. Monitoring digest that recommends a public response naming a patient is recommending an HHS-investigable disclosure.
- Cadence is *incident-driven*, not weekly — joint-commission events, FDA Class I recalls, and CMS quality-measure publications force same-day cycles, while routine periods run monthly.

**B2B SaaS (Series-B+ tech):**
- "Monitoring" overlaps with customer-success / GTM telemetry — the signal substrate is G2/Capterra/Reddit/HackerNews/Gartner-MQ/LinkedIn — not the trade press. This is the closest fit to the MON v0 archetype.
- Forward projection is *6–8 weeks* (renewal cycle, sales-pipeline window), not 1–2 weeks.

**Legal services (Am Law-style firms):**
- Monitoring is a BD/marketing function and the artifact is the *competitive-lateral newsletter* — the dominant signal is "who's hiring / leaving / promoting" not earned-media sentiment. Most overlap with CI lane.
- Confidentiality rules (SRA/ABA) constrain what can even be summarized; "client" mentions are radioactive.

**Professional services (accounting/consulting/agency):**
- Comms posture is *competence-protective* — partnership reputation is the firm's entire balance sheet. A single Big-4 audit-quality finding moves the needle more than 500 brand mentions.

**Founder-led startups (pre-Series-B):**
- No comms function — the founder IS the monitoring consumer. Cadence is *event-driven and weekly* with a strong Twitter/X / HackerNews / Substack bias.
- "Actionable" means founder-personal response within 24 hours, not "the team should consider."

**Regulated industries (utilities, energy, telecom, defense, pharma):**
- FAA-AD-style mandatory bulletin format is the *literal source convention*; OSHA, NRC, FERC, FDA, and NIST CSF all impose disclosure timelines (some same-day) that determine cadence.
- "Silence" is regulatorily-required behavior in many phases (pre-IPO quiet period, FDA pre-approval, NRC events) — a digest that flags expected silence as anomalous is wrong.

### Strongest single recommendation for the MON spec

**Replace the single Monday-8:55am cadence assumption with a `decision_shape`-aware reader spec** (parallel to the CI lane's v3.3 move). Add three vertical-specific score-1 anchor examples to MON-1, MON-2, MON-3, MON-4, MON-5 — one from a regulated/financial vertical, one from B2B SaaS, one from a small-practice/founder context. Without naming the vertical in the rubric prose. The current single-archetype framing will train the workflow to produce Cision-React-Score-shaped outputs across all verticals; three anchors at the same rigor disrupt the slot-fill.

---

## 2. Vertical A — Financial services (banking, asset management, insurance)

### 2.1 Who reads the monitoring digest in financial services

Three placement patterns dominate:

1. **Chief Reputation Officer / Chief Communications Officer.** At Citi, JPMorgan, Goldman, Morgan Stanley, BlackRock, Vanguard, Allianz, AIG, Prudential — there is a dedicated CCO/CRO function reporting to the CEO or to a board-level Risk Committee. Their monitoring is integrated with the firm's enterprise-risk-management framework (per OCC Heightened Standards for large national banks, FRB SR 11-7 model risk management, and the Basel III operational-risk capital framework).
2. **General Counsel / Compliance.** In smaller institutions or for litigation/regulatory-adjacent signals, monitoring routes to the GC's office. Reputational risk is treated as a sub-class of operational risk per FRB SR 13-19 "Reputational Risk" guidance.
3. **Investor Relations / CFO.** For publicly-traded firms, IR monitors analyst notes, short-seller reports, and Reg-FD-relevant signals. The artifact connects to earnings-call prep and 10-K disclosure decisions.

The reader is *not* a Series-B comms director — these are senior executives with fiduciary exposure. A misclassified "crisis" signal that prompts a 10-K disclosure or a Reg-FD-violating selective leak is a career-ending mistake.

### 2.2 What counts as "actionable" vs "noise" in financial services

The threshold is **materiality**, defined by securities law (SEC Staff Accounting Bulletin 99 — "would a reasonable investor consider this information important in making an investment decision") and by the firm's internal materiality matrix. A monitoring digest that flags 230 Twitter mentions about a customer-service complaint is generating noise. A digest that flags a single short-seller report from a known activist short (Muddy Waters, Hindenburg, Citron, Spruce Point) is generating action.

Other actionable-tier signals: a SEC enforcement action announcement; a Treasury OFAC sanctions designation affecting a counterparty; a Moody's/S&P/Fitch credit-watch placement; a CFPB consent order; a Wells notice; an FCA Final Notice or Decision Notice; a DOL ERISA enforcement action; a NAIC examination finding; a class action filing crossing $100M aggregate damages threshold; a 13D filing by an activist investor crossing 5%; a CFO/CRO/Chief Audit departure.

Noise-tier signals: routine Glassdoor reviews; competitor product launches without market-share implications; trade-press think-pieces without named-analyst attribution; customer-service complaints below the firm's standard volume baseline.

### 2.3 Cadence convention in financial services

Cadence is **legally and regulatorily structured**, not vendor-default:

- **Real-time / same-day pager.** SEC 8-K disclosure events (4 business days), FRB enforcement actions, Treasury sanctions designations, FINRA Disciplinary Notices, market-stress events (a 1% intraday SPX move triggers reputation-monitoring escalation at most large banks).
- **Daily pre-market digest.** Investor Relations briefings before market open; analyst-note review; overnight Asia/Europe regulatory headlines.
- **Weekly executive review.** Reputation-risk dashboard to CCO + GC; surfaces non-urgent but trending signals.
- **Monthly board-package input.** Reputation KPI dashboard feeds the Board Risk Committee or Audit Committee report.
- **Quarterly 10-Q narrative input.** Material reputation events fold into the Risk Factors and MD&A sections.

The MON v0 single-cadence weekly Monday-8:55am framing is wrong for financial services. A digest that buries a Wells notice published Thursday until Monday morning has caused a 4-day regulatory exposure window.

### 2.4 Regulatory and legally-required monitoring patterns

**Legally required:**

- **SEC Reg S-K Item 105 (Risk Factors)** + **Item 303 (MD&A)** — material reputation events must be disclosed in 10-K/10-Q; monitoring is the upstream feed.
- **FRB SR 11-7** — model risk management; reputation-risk model validation. For systemically important banks: SR 12-17, SR 16-11, SR 20-13.
- **OCC Heightened Standards (12 CFR Part 30 Appendix D)** — covered banks ($50B+ assets) must have a Reputation Risk Management Program; "the bank should have a process to identify and assess reputation risk arising from the activities, products, services, and operations."
- **FINRA Rule 3110 (Supervision)** + **Rule 4530 (Reportable Events)** — broker-dealers must monitor and report certain disciplinary and reputational events within 30 days.
- **CFPB rules + state attorneys-general** — consumer-financial-product complaint volume tracking is contractually structured into UDAAP compliance frameworks.
- **EU MiCA + DORA + GDPR Art. 33–34** — financial firms operating in EU have 72-hour cybersecurity-incident reporting under DORA and similar timelines for data-breach reputation events under GDPR.
- **Solvency II / IDD for insurers** — reputation risk is a Pillar 2 ORSA input.

**Operationally required (industry standard but not strictly legal):**

- **NIST Cybersecurity Framework + SOC 2** mention monitoring of brand-impersonation, phishing-domain registration, dark-web credential exposure.
- **AICPA Trust Services Criteria** — Common Criterion 7.4: "the entity monitors information from internal and external sources about changes in laws, regulations, customer needs, and other matters that affect risks to the entity."
- **NAIC ORSA** for insurers.

This regulatory density means the monitoring artifact is not just an editorial document — it is an *evidentiary artifact* that has to survive examiner review. A digest that buries a material event, or that mis-classifies a sub-material event as "crisis" causing premature public disclosure, creates legal exposure on both sides.

### 2.5 Format conventions

The dominant formats:

1. **Pre-market Investor Relations brief.** 1–2 pages, sent to CFO + CEO + Board Chair before market open. Bloomberg-Intelligence-grade rigor; named-source citations mandatory; tone is dry-and-precise.
2. **Reputation Risk Dashboard.** Quarterly Board Risk Committee artifact. KPI-driven (Net Promoter Score, Edelman Trust delta, Glassdoor weighted rating, complaint volume vs peer baseline, regulatory-action count, plaintiff-firm-attention index).
3. **Weekly enterprise-risk integrated brief.** Combines reputation, operational, compliance, and credit signals in a single executive briefing. Banks (e.g. Citi's Enterprise Risk function) often produce this through their Operational Risk team rather than Comms.
4. **Real-time pager (push notification on the Risk Committee Chair's phone).** For material-event escalation only.

Length convention: short. The "two-paragraph executive summary plus exhibits" format is dominant. A 7-section weekly digest is wrong shape.

### 2.6 Failure modes specific to financial-services monitoring

- **Materiality miscalibration.** Flagging routine consumer complaints at the same tier as a Wells notice trains the executive to ignore the digest. Worse — under-flagging an event that *was* material creates Reg-FD or 10-K disclosure exposure.
- **Selective-disclosure / Reg-FD bypass.** A monitoring digest distributed unevenly across executives — where one exec acts on it before public disclosure — is a Reg-FD violation. Monitoring distribution lists are themselves a compliance artifact.
- **Sentiment-as-trust-proxy.** Twitter sentiment is uncorrelated with depositor behavior; the SVB-failure post-mortem showed sentiment metrics were lagging by 48 hours when wire-transfer outflows were the leading indicator. A digest that leans on Twitter-sentiment for a bank or asset manager has missed the actual signal substrate.
- **Plaintiff-firm-attention-index ignorance.** Plaintiff-firm IR-monitoring (the moment a 10b-5 firm files an investigation announcement) is a leading indicator of securities litigation. A digest that omits plaintiff-firm tracking is missing a comp-grade litigation signal.
- **Short-seller-asymmetry.** A single Hindenburg-grade short report can move a stock 20%; routine analyst notes don't. The digest must weight by author-impact, not by mention count.

---

## 3. Vertical B — Healthcare (provider systems, payers, life sciences)

### 3.1 Who reads the monitoring digest in healthcare

Three patterns:

1. **Hospital-system Chief Communications Officer / Chief Patient Experience Officer.** Large IDNs (HCA, Ascension, Providence, Kaiser, NYU Langone) run dedicated reputation-monitoring teams. Reader is C-suite, often reporting to Chief Strategy Officer.
2. **Payer Communications + Government Affairs.** UnitedHealth, Anthem, Aetna, Cigna run integrated CCO + GA functions because payer reputation is inseparable from CMS Star Ratings, Medicare Advantage marketing rules, and state-DOI relationship management.
3. **Life-sciences (pharma, device) Corporate Communications.** Pfizer, Lilly, Novartis, Medtronic — monitoring is integrated with pharmacovigilance and FDA regulatory affairs. Reader is corporate-comms head AND chief medical officer AND regulatory affairs.

For a small/mid practice (Klinika Melitus archetype): there is no monitoring function. The practice owner reads Google reviews and RealSelf on Saturday. Monitoring digest is a different artifact at this scale.

### 3.2 What counts as "actionable" vs "noise" in healthcare

Actionable signals:

- **FDA actions:** Class I recalls (same-day), Warning Letters (48–72h), 483 observations becoming public, FAERS adverse-event signal cluster, MDR-reportable device incidents.
- **CMS / HHS:** OIG inspection findings, CMS Star Ratings publication, quality-measure publication (HEDIS, HCAHPS scores), No Surprises Act enforcement.
- **Joint Commission / accreditor events.** Sentinel events are confidential but become public via state-board reporting; loss of accreditation is existential.
- **State medical-board complaints + disciplinary actions.** Public disclosure is mandatory in all states; aggregator sites (Healthgrades, RateMDs) amplify.
- **Patient-safety viral incidents.** A single TikTok with 5M views about a misdiagnosis can trigger immediate response cycles.
- **Class action / mass-tort filings.** Especially product-liability (J&J talc, Bayer Roundup) and data-breach (Change Healthcare 2024).
- **Cyber incidents.** HHS HIPAA Wall of Shame disclosure (500+ patient breach within 60 days, plus state-AG notifications).

Noise: routine 4-star Google reviews; competitor menu-pricing changes (relevant to small practices, not health systems); industry-conference think-pieces.

### 3.3 Cadence convention in healthcare

Cadence is **incident-driven**, with regulatory clocks setting the timeline:

- **Same-day pager:** FDA Class I recall, Joint Commission sentinel event, HHS breach >500 patients, state-AG referral, viral patient-safety social-media event.
- **48–72 hour brief:** FDA Warning Letter, CMS quality-measure publication day, OIG inspection-finding day.
- **Weekly digest:** Routine periods — competitor service-line launches, journal publications, AMA/AHA/AHIP policy positions.
- **Monthly deep-dive:** CMS rule cycles (annual MPFS / OPPS / IPPS), state-DOI rate filings.
- **Annual:** AHRQ Patient Safety Indicators, Leapfrog Grades, CMS Star Ratings calibration.

The Monday-8:55am cadence is wrong for healthcare. A health system that received an FDA Warning Letter Friday at 4pm needs the digest Saturday morning, not Monday. A Joint Commission sentinel-event determination at 11am Tuesday needs same-day routing.

### 3.4 Regulatory and legally-required monitoring patterns

**Legally required:**

- **HIPAA Breach Notification Rule (45 CFR §164.400–414).** Breaches affecting 500+ patients must be reported to HHS within 60 days and posted publicly on the HHS "Wall of Shame." Monitoring patient-data-breach signals is a compliance prerequisite, not a comms preference.
- **FDA pharmacovigilance (21 CFR Parts 314, 600, 803).** Adverse-event monitoring + MDR reporting for devices. Comms signals from social-media adverse-event reports feed into mandatory FAERS/MAUDE submission.
- **OSHA + Joint Commission.** Workplace-violence and patient-safety event reporting + accreditor disclosure.
- **CMS Conditions of Participation.** Hospitals must monitor quality metrics; underperformance triggers public scoring.
- **State medical boards.** Disciplinary action disclosure varies by state but is universally public.
- **Sunshine Act (Open Payments).** Manufacturer-to-provider payment disclosure; reputation-monitoring tracks media coverage of payment data.

**FDA-specific patterns relevant to MON judge:**

- **FDA Warning Letters** are *published* on FDA.gov; monitoring includes regex on the FDA inspection database. The FAA Airworthiness Directive format precedent (cited in the parent monitoring research) maps directly onto FDA Warning Letters in structure (unsafe condition, applicability, required corrective action, deadline).
- **MedWatch + FAERS** — voluntary and mandatory adverse-event reporting.
- **REMS programs** (Risk Evaluation and Mitigation Strategies) require monitoring of dispensing patterns and safety signals.

### 3.5 Format conventions

The dominant formats:

1. **Patient-safety event brief.** Strict legal-defensibility format; tone is clinical and present-tense; goes into the system's risk-management record. NOT a marketing artifact.
2. **CMS Stars dashboard.** Quarterly internal artifact; KPI-driven.
3. **Crisis-mode same-day situation report.** Following the Joint Commission "after-action review" format; named owners and corrective actions.
4. **Conference / journal-coverage weekly.** The "what's the field saying about us and our competitors" newsletter — closer to the MON v0 archetype but with much heavier reliance on PubMed, MMWR, NEJM, JAMA citations than on Twitter or trade press.

Length convention: bifurcated. Same-day patient-safety briefs are 300–500 words, rigidly structured. Weekly comms digests for executive consumption are 1–2 pages.

### 3.6 Failure modes specific to healthcare monitoring

- **HIPAA-violating "actionable" recommendation.** Recommending public response that names a patient or implies patient identity is *causing* the digest's reader to commit a HIPAA breach. The most dangerous failure mode in this vertical.
- **FDA-pre-approval-disclosure leakage.** Recommending public response on a not-yet-approved product is a federal regulatory violation. A digest that says "engage the negative coverage of your investigational drug" is mis-prescribing.
- **AMA/ACGME advertising-rule violation.** Many specialties have restrictions on claims ("board-certified" usage, comparative-efficacy claims). A digest recommending "respond by claiming superior outcomes" can prescribe a rule-violation.
- **Sentinel-event hush-mode misread.** Joint Commission sentinel events are subject to confidential investigation; a monitoring digest that recommends "respond publicly" during the confidential phase is wrong.
- **Local-vs-system framing.** A patient complaint at one Kaiser facility is local; the same complaint at a smaller IDN may be system-level. Misreading the level is a recurring failure mode.
- **Vendor-rep echo (mirror of CI healthcare).** Pharma rep / device-rep informal CI feeds into comms; absorbing rep framing without disclosure imports bias.

---

## 4. Vertical C — B2B SaaS (Series-B+ tech), founder-led startups (pre-Series-B), legal services, professional services, regulated industries

### 4.1 B2B SaaS (closest match to MON v0 archetype)

**Reader:** Head of Marketing / VP Comms / CMO at a Series-B-or-later SaaS company. Reports to CEO or CRO.

**Cadence:** Weekly is correct; the Monday-8:55am framing fits. Plus a daily-pager for security incidents (SOC2/ISO27001/customer-data exposure).

**Actionable signals:**
- G2/Capterra review-velocity changes (especially anomalous negative-review clusters)
- Reddit subreddit threads in technical communities (r/devops, r/dataengineering, r/selfhosted, r/sysadmin)
- HackerNews front-page mentions (positive or negative)
- Gartner Magic Quadrant placement movements
- Forrester Wave placement movements
- Customer churn at a flagship-account level (often surfaced via LinkedIn departure tracking)
- Competitor pricing-page changes (monitored via Page-monitoring tools like Wachete or Visualping)
- Customer-status-page incidents at competitors (signals product-quality differential)
- LinkedIn personnel-movement signals (hires/exits at named competitors)
- Earnings-call mentions (for public competitors)

**Forward projection window:** 6–8 weeks aligns with sales-pipeline window and renewal cycle. The MON v0 "1–2 weeks" framing is too short.

**Noise:** brand-mention volume from generic tech-blog content farms; competitor announcements that don't change positioning; routine industry-event tweet density.

**Format conventions:**
- Slack-channel running thread + weekly digest synthesis
- Linear/Notion competitive intelligence page with comment threads
- Quarterly Board-deck slide on "competitive landscape"
- Customer-success / GTM joint review

This is the vertical for which the MON v0 spec is best calibrated. Most fixture work to date appears to be from this vertical (Anthropic, Perplexity — Series-A+ AI-labs sharing the B2B SaaS reader-pattern).

**Failure modes:**
- Vanity-metric over-weighting (Twitter mentions, share-of-voice without ESOV)
- Missing the LinkedIn-departure signal (the highest-fidelity leading indicator of competitor instability)
- HackerNews-bias (over-weights HN coverage in markets where HN doesn't represent the buyer)
- Failing to integrate customer-success signals (NPS deltas, support-ticket-pattern shifts)

### 4.2 Founder-led startups (pre-Series-B)

**Reader:** The founder/CEO. No CMO, no comms function. Reader IS the actor and the audience.

**Cadence:** Event-driven and weekly. Founders self-monitor in real time on Twitter/X, Discord, Slack communities, Substack. A weekly digest synthesizes what they couldn't catch personally.

**Actionable signals:**
- Investor tweets / Substack posts about the company or category
- Customer founder tweets (especially churn signals)
- HackerNews / r/programming / r/startups / r/SaaS top posts
- Direct-mention search across Twitter/X, Reddit, Discord
- Substack and podcast-mentions in the category's analyst tier (Stratechery, Latent Space, Lenny's Newsletter, Software is Awesome, First Round Review, The Generalist, Not Boring, Every)
- Competitor founder tweets (very high-signal)
- YC Demo Day batch announcements (each batch surfaces 5–15 immediate competitors)

**Forward projection window:** 1–4 weeks; founder time-horizon is short.

**Noise:** Most enterprise-trade-press coverage; analyst reports (Gartner/Forrester rarely cover pre-Series-B); industry-conference content.

**Format conventions:**
- Single-channel Slack message or Notion doc; rarely formal
- 5–10 bullet points with direct links
- Founder may forward 1–2 to their leadership team

**Failure modes:**
- Over-formalizing the digest (founder doesn't want a 7-section weekly)
- Missing the "Founder Twitter" tier of signal (a competitor founder admitting struggle on Twitter is a 10× signal vs press coverage)
- Recommending action that requires a function the company doesn't have ("the comms team should respond" — there is no comms team)
- Missing the YC Demo Day batch effect (5–15 immediate same-category competitors enter the market in one day each batch)

### 4.3 Legal services (Am Law-style firms)

**Reader:** Managing partner, BD director, or practice-group head. Most monitoring overlaps with the CI lane.

**Cadence:** Weekly is conventional; daily for high-stakes lateral moves and directory-publication days (Chambers, Legal 500, IFLR1000 publication dates).

**Actionable signals (per CI vertical-conventions doc §2.4):**
- Lateral-partner moves (Leopard / Firmscape / Above the Law tracking)
- Directory tier-shifts (Chambers tier-changes, Legal 500 movements)
- Major matter-wins and losses (court-filing analytics)
- Citi Hildebrandt Client Advisory annual publication day
- Partner-promotion announcements (signals practice-area investment)
- Client RFP wins/losses
- Law-firm M&A signals
- Solicitors' Regulation Authority / state bar disciplinary actions

**Noise:** Trade-press think-pieces, generic legal-marketing content, junior-associate Glassdoor reviews.

**Format conventions:** Conservative; 1–2 page BD memo; rigid citation density. Chambers and Legal 500 directory citations are treated with quasi-judicial weight.

**Confidentiality constraints:** Solicitors' Regulation Authority (UK) and state bar rules constrain what can be referenced. "Client" mentions are radioactive — a monitoring digest that recommends naming a client in a public response is recommending a rule violation.

**Failure modes (specific to monitoring layer, distinct from CI):**
- Directory-publication-day burying — Chambers publishes annually; a digest that doesn't lead with tier-shifts on publication week has buried the lede.
- Lateral-rumor-vs-confirmed-move confusion — Above the Law publicizes rumored moves before firms confirm. Treating rumor as confirmed creates false-positive actionability.
- Client-name leak — recommending a response that names a client is a regulatory violation in all UK + US jurisdictions.

### 4.4 Professional services (Big-4 accounting, MBB consulting, agency)

**Reader:** Chief Brand / Chief Communications Officer reporting to the Managing Partner or CEO of a partnership.

**Cadence:** Weekly is conventional; same-day for audit-quality findings (PCAOB inspection results, SEC enforcement against an audit client).

**Actionable signals:**
- PCAOB inspection report findings (annual, but adverse findings move the needle structurally)
- SEC enforcement against audit clients
- Bain/McKinsey/BCG annual ranking publications (Vault, Glassdoor, Universum employer-brand)
- Partner promotions / departures at competitors
- Client wins/losses (especially MBB)
- Tier-1 trade press critical coverage (Financial Times, Wall Street Journal, The Economist)
- Whistleblower / regulatory investigations of the firm
- Industry-wide events (Big-4 audit-quality crisis, MBB exit-rumor cycles)

**Reputation as balance sheet:** Partnership reputation is the firm's entire financial value. A single PCAOB Part I.A finding can trigger a $100M+ client-loss cascade. The digest must treat single high-severity competence events as comparable in stake to multi-month brand campaigns.

**Format conventions:** Conservative; resembles legal more than tech. Page-counts low; citation density high. Internal-only distribution; the firm doesn't want its monitoring artifact leaking.

**Failure modes:**
- Treating volume of brand mentions as the primary signal when single high-severity competence events dominate.
- Missing PCAOB or oversight-body publication days.
- Over-publicizing the firm's monitoring artifact — partnership culture treats public discussion of competitive monitoring as undignified.

### 4.5 Regulated industries (utilities, energy, telecom, defense, pharma, transportation)

**Reader:** Chief Communications Officer + Chief Compliance Officer + General Counsel (often jointly). Sector-specific regulators (NRC, FERC, FCC, FAA, EPA, FDA, DoD) impose monitoring requirements.

**Cadence:** Sector-driven and incident-driven:

- **Utilities (NERC, FERC):** NERC CIP cybersecurity-incident reporting requires same-day brief on certain events.
- **Nuclear (NRC):** Event reporting under 10 CFR 50.72 — telephone notifications within 1–8 hours of certain events; immediate same-day briefing requirement.
- **Telecom (FCC):** Network Outage Reporting System (NORS) — 120-minute initial notification of certain outages.
- **Defense (DoD CMMC, DFARS):** 72-hour cyber-incident reporting; DoD cleared-personnel-event reporting.
- **Pharma (FDA):** As covered in §3.
- **Aviation (FAA):** Airworthiness Directive cycle; SAFO/InFO notice cycle.

The MON judge's FAA-AD-format inspiration (per the parent research §1.4) is *literally the source convention* in aviation. A digest in this vertical that doesn't match FAA-AD structure misreads the operational expectation.

**Actionable signals:**
- Regulator-published enforcement notices
- Industry-association safety bulletins
- Peer-company incident disclosures
- Whistleblower / inspector-general reports
- Class-action filings with regulatory-spillover potential
- Capitol Hill hearing announcements
- State PUC / state attorney-general actions

**"Silence as signal" inversion:** In many regulated phases, silence is *required* — FDA pre-approval, NRC events in classified-investigation phase, SEC quiet period pre-IPO, DoD classified information. A monitoring digest that flags expected silence as anomalous in these phases is wrong. The digest must distinguish "anomalous silence" (Wells Fargo whistleblower silence) from "required silence" (FDA pre-approval).

**Format conventions:** Bulletin-driven; FAA-AD-style fields literally enforced in some sectors. The "compliance time" field is operationalized to the hour.

**Failure modes:**
- Misreading required-silence as anomalous-silence (very dangerous in pharma + defense).
- Bulletin-format-drift — these sectors expect rigid format; a discursive digest doesn't get used.
- Missing the regulator-publication-day cycle (NERC, FERC, NRC publish on fixed cycles; a digest that doesn't synchronize is publishing stale).

---

## 5. Cross-vertical synthesis (500 words)

### What's universal across all seven verticals

Three patterns hold:

1. **Baseline-relative framing of what changed.** Whether the baseline is 4-week trailing mention volume (B2B SaaS), peer Chambers tier (legal), CMS Stars score (healthcare), or volume-vs-Bloomberg-Intelligence index (financial services) — every vertical demands deltas, not absolute numbers. The MON-1 criterion as written holds across verticals; only the *unit* of the baseline varies.

2. **Highest-stakes lede in position one.** Across every vertical the most-consequential development opens the artifact. The unit of "consequence" varies (a SEC Wells notice in financial services, an FDA Warning Letter in healthcare, a 6-partner Pinsent pull in legal, a flagship-customer churn in SaaS) but the principle is invariant. MON-3 as written holds.

3. **Action items with owner / deadline / consequence.** The FAA-AD-derived structure is the literal source format in regulated industries and the operational standard everywhere else. MON-4 as written holds.

### What's vertical-specific and load-bearing

Six dimensions vary structurally enough that the v0 spec is at risk of vertical-overfit:

1. **Reader-decision shape.** B2B-SaaS comms director = weekly synthesis. Founder = real-time + weekly digest. Financial-services CCO = daily pre-market + weekly board input + 8-K-trigger pager. Healthcare CCO = incident-driven with monthly baseline. The single Monday-8:55am framing maps cleanly onto B2B SaaS, partially onto legal, poorly onto financial services and healthcare and regulated industries.

2. **Cadence.** Weekly is the wrong default. Cadence is *event-class-driven* — material event → same-day; routine cycle → weekly; deep-dive → monthly; calibration → quarterly. The judge must not penalize a same-day brief for "missing the Monday-8:55am framing."

3. **"Actionable" threshold.** Financial-services = materiality (SEC SAB 99). Healthcare = regulatory + patient-safety + accreditor. B2B SaaS = revenue-impact + customer-success signal. Founder = founder-personal-response-within-24h. Legal = partnership-vote-relevant. Professional services = reputation-as-balance-sheet (single competence event > 500 brand mentions). Regulated industries = regulator-clock-driven. A single severity scheme doesn't fit all seven.

4. **Required-silence vs anomalous-silence.** MON-5's "silence as signal" framing must distinguish phases where silence is regulatorily required (FDA pre-approval, SEC quiet period, NRC classified investigation, DoD classified information, Joint Commission sentinel-event investigation) from phases where silence is an anomalous signal (Wells Fargo whistleblower silence pattern, BP Deepwater Horizon non-escalation pattern). Penalizing required silence as "missed signal" trains the workflow toward regulatorily-noncompliant recommendations.

5. **Confidentiality constraints.** Legal (SRA/ABA), healthcare (HIPAA), financial services (Reg-FD, MNPI), and defense (CMMC/DFARS) impose distinct constraints on what monitoring artifacts can even reference. A digest that recommends naming a patient (healthcare), a client (legal), or material-nonpublic info (financial services) is recommending a rule violation.

6. **Format expectation.** FAA-AD-style bulletin in regulated industries. Bloomberg-Intelligence-style pre-market in financial services. Slack-thread in founder. 1–2 page BD memo in legal. Annual KPI dashboard in healthcare-Stars. Series-B SaaS comms director is the only reader who expects the FullIntel-style 200–400 word weekly executive brief.

### Single most important takeaway

The MON v0 spec's substitute-readers gesture ("founder/CEO of an earlier-stage company with no in-house comms; agency lead reading on behalf of multiple clients; in-house counsel monitoring reputational legal exposure") is correct in direction but underdeveloped in calibration. The score-1 anchors in MON-1 through MON-5 currently use a single archetype example each — all from a Series-B-SaaS-flavored frame ("Pinsent partner-pull aftermath," "competitor analyst-day silence"). A 50-generation evolution loop against these anchors will learn to produce Series-B-SaaS-shaped outputs across all fixtures. The fix is three-anchor expansion per criterion (one regulated/financial, one B2B SaaS, one small-practice/founder), with NO vertical-name in the rubric prose.

---

## 6. Implications for MON v1 spec (400 words)

### Concrete recommendations

**1. Add per-vertical score-1 anchor examples to MON-1, MON-2, MON-3, MON-4, MON-5.** Three anchors per criterion at the same rigor level, drawn from divergent verticals. Worked example for MON-4 (action items with owner, deadline, consequence):

> Example A (do not optimize toward this): "Head of Comms calls the Bloomberg reporter who broke the Pinsent-pull story by Wednesday 3pm to offer named-partner context. Otherwise, the legacy-firm-loyalty narrative hardens for the Q3 trade-press cycle." [legal/professional services]
>
> Example B (do not optimize toward this): "CFO + IR Head review the Hindenburg short report this morning; commit to a Reg-FD-compliant response posture (engage / decline / delay) by 2pm market close. Otherwise, the silence increases the probability of an analyst-downgrade in the Friday note cycle." [financial services]
>
> Example C (do not optimize toward this): "Founder DMs the @swyx Latent Space podcast host within 24 hours to engage on the developer-tools comparison; otherwise, the framing locks in for the next pod episode that's the highest-distribution channel in our category right now." [founder-led startup]

**2. Replace the single Monday-8:55am cadence framing with a `decision_shape`-aware Reader spec** parallel to CI v3.3 §1. Acknowledge three decision-shapes:
- **Routine-cycle-weekly** (B2B SaaS, legal, professional services) — Monday-morning archetype holds.
- **Event-driven-with-baseline** (healthcare, regulated industries) — incident → same-day; routine → monthly.
- **Founder-personal-real-time** (pre-Series-B) — continuous + weekly synthesis.

The judge still tests "would the reader walk into their decision-shape-appropriate context knowing the most-consequential development" — but the context window is decision-shape-relative, not Monday-8:55am-fixed.

**3. Add a "required silence vs anomalous silence" distinction to MON-5's CoT.** Step 2 of the MON-5 CoT should explicitly require: "For each flagged absence, determine whether silence is regulatorily-required (FDA pre-approval, SEC quiet period, classified investigation, sentinel-event confidential phase) or anomalous (no-required-silence + expected-signal-missing). Required silence is not a missed signal; recommending response during required-silence is a rule-violation."

**4. Add three vertical-specific Goodhart-collapse modes to §3 Failure.** Currently anchored on "every item gets HIGH/MEDIUM/LOW tag" and "Cross-Story Patterns section populated with weak connections." Add:
- **Materiality miscalibration** (financial services) — treating routine volume spikes at the same tier as material events; misclassifying material events as routine.
- **HIPAA-violating recommendation** (healthcare) — recommending a response that names a patient or implies patient identity.
- **Required-silence misread** (regulated industries) — recommending response during regulatorily-required silence phases.

**5. Generalize MON-4's "owner is concrete (CEO, Head of Comms, Head of Legal)" anchor.** Add: "or the founder themselves; or a fractional/agency contact; or a board-committee chair; or a regulator-relations lead." Single-spec "Head of Comms" anchor over-fits to B2B SaaS.

**6. Defer the "vertical sub-persona" bifurcation to fixture validation.** Don't bifurcate the MON spec into N vertical-specific specs yet. Run the existing monitoring fixtures + 2–3 new fixtures from divergent verticals (a healthcare digest, a financial-services pre-market brief, a founder-led-startup weekly) through MON v1 with three vertical anchors per criterion. If the judge produces vertical-discriminating rationales, single-spec + diverse-anchors suffices. If not, escalate.

---

## 7. Open questions

1. **Cadence-class field in workflow input.** Does the MON workflow already receive a `cadence_class` input (routine-weekly / event-driven / pager-tier)? If not, propagate the field so structural_gate can enforce decision-shape-appropriate timing. Without it, the judge cannot fairly grade a same-day FDA-Warning-Letter brief against a routine Monday digest.

2. **Regulatory-required-silence reference list.** The MON judge's CoT for MON-5 needs a list of regulator-required-silence phases (FDA pre-approval, SEC quiet period, NRC classified investigation, Joint Commission sentinel-event confidential phase, DoD classified). Should this live in the rubric prose (risks framework-name-embedding) or in structural_gate (risks the judge missing it semantically)? Recommend: include in the shared judge-prompt wrapper as a CoT instruction without naming specific frameworks.

3. **Plaintiff-firm-attention-index and short-seller-asymmetry signals.** These are load-bearing in financial services but absent from the v0 spec's evidence-substrate framing. Should they enter as named exemplars in the MON-2 (severity classification) anchor, or via the parent research's "Sandman Risk = Hazard + Outrage" reasoning toolkit? Defer to fixture-validation evidence.

4. **MON-G (temporal arc continuity) — re-introduce per vertical?** The v0 spec dropped MON-G as lowest-confidence. Multi-week continuity is *especially* load-bearing in legal services (lateral-rumor → confirmed-move arcs run 4–8 weeks) and financial services (Wells notice → settlement arcs run quarters). A vertical-specific re-introduction may be warranted. Defer to fixture-validation.

5. **First-cohort overfitting watch.** Per the CI v3.3 §8.7 pattern: if MON fixtures stay concentrated in Series-B-SaaS-flavored archetypes (Anthropic / Perplexity-style), the judge will overfit to that vertical regardless of the three-anchor expansion. Trigger: any monitoring fixture from healthcare / financial services / founder / regulated industries should prompt a re-validation pass on the affected criteria.

6. **Health-system / payer / pharma sub-vertical decomposition.** Healthcare is treated as one vertical in this research; in practice provider systems, payers, and life sciences have meaningfully different decision-shapes. If fixture-validation surfaces that healthcare-as-one-vertical is too coarse, sub-decompose.

7. **Comms-vs-CI lane boundary in legal services.** The MON lane and CI lane have overlapping coverage of lateral-move signals in legal services. Operationally: who owns "directory tier-shift" coverage — MON (treating it as reputation signal) or CI (treating it as competitive-position signal)? Risk: both lanes optimize for the same signal in evolution, with neither producing the differentiating insight. Recommend explicit lane-boundary in the workflow's prompt spec.

---

## 8. Citations

### Financial services
- [SEC Reg S-K Item 105 (Risk Factors)](https://www.sec.gov/divisions/corpfin/cf-noaction.shtml)
- [SEC Staff Accounting Bulletin 99 — Materiality](https://www.sec.gov/interps/account/sab99.htm)
- [FRB SR 11-7 — Model Risk Management Guidance](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm)
- [FRB SR 13-19 — Reputational Risk](https://www.federalreserve.gov/supervisionreg/srletters/sr1319.htm)
- [OCC Heightened Standards (12 CFR Part 30 Appendix D)](https://www.occ.gov/news-issuances/federal-register/2014/79fr54518.pdf)
- [FINRA Rule 3110 (Supervision)](https://www.finra.org/rules-guidance/rulebooks/finra-rules/3110)
- [FINRA Rule 4530 (Reportable Events)](https://www.finra.org/rules-guidance/rulebooks/finra-rules/4530)
- [EU DORA (Digital Operational Resilience Act)](https://eur-lex.europa.eu/eli/reg/2022/2554/oj)
- [GDPR Articles 33-34 (Breach Notification)](https://gdpr-info.eu/art-33-gdpr/)
- [NAIC ORSA (Own Risk and Solvency Assessment)](https://content.naic.org/cipr-topics/own-risk-and-solvency-assessment-orsa)
- [Hindenburg Research](https://hindenburgresearch.com/)
- [Muddy Waters Research](https://www.muddywatersresearch.com/)
- [Citron Research](https://www.citronresearch.com/)
- [SVB Failure FDIC Report](https://www.fdic.gov/news/press-releases/2023/pr23033.html)

### Healthcare
- [HIPAA Breach Notification Rule (45 CFR §164.400–414)](https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html)
- [HHS "Wall of Shame" — Breach Portal](https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf)
- [FDA Warning Letters](https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/compliance-actions-and-activities/warning-letters)
- [FDA MedWatch Adverse Event Reporting](https://www.fda.gov/safety/medwatch-fda-safety-information-and-adverse-event-reporting-program)
- [FAERS — FDA Adverse Event Reporting System](https://www.fda.gov/drugs/questions-and-answers-fdas-adverse-event-reporting-system-faers)
- [CMS Conditions of Participation](https://www.cms.gov/Medicare/Provider-Enrollment-and-Certification/CertificationandComplianc/Hospitals)
- [Joint Commission Sentinel Event Policy](https://www.jointcommission.org/sentinel_event.aspx)
- [Sunshine Act / Open Payments](https://openpaymentsdata.cms.gov/)
- [21 CFR Parts 314, 600, 803 — Pharmacovigilance](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-D/part-314)

### B2B SaaS / founder-led
- [G2 review platform](https://www.g2.com/)
- [Capterra review platform](https://www.capterra.com/)
- [Stratechery — Ben Thompson](https://stratechery.com/)
- [Latent Space — Shawn Wang / Alessio Fanelli](https://www.latent.space/)
- [Interconnects — Nathan Lambert](https://www.interconnects.ai/)
- [Lenny's Newsletter](https://www.lennysnewsletter.com/)
- [First Round Review](https://review.firstround.com/)
- [Software is Awesome / Software Engineering Daily](https://softwareengineeringdaily.com/)
- [Y Combinator Demo Day](https://www.ycombinator.com/demoday)

### Legal services
- [Solicitors' Regulation Authority Code of Conduct](https://www.sra.org.uk/solicitors/standards-regulations/code-conduct-solicitors/)
- [Chambers and Partners Rankings](https://chambers.com/)
- [The Legal 500](https://www.legal500.com/)
- [Above the Law](https://abovethelaw.com/)
- [Leopard Solutions Firmscape](https://www.leopardsolutions.com/firmscape/)
- [Citi Hildebrandt 2025 Client Advisory](https://www.citiglobalwealth.com/content/dam/cpb/internet/www-citiglobalwealth-com/wealth-at-work/docs/2025-Citi-Hildebrandt-Client-Advisory.pdf.coredownload.pdf)

### Professional services
- [PCAOB Inspection Reports](https://pcaobus.org/oversight/inspections/inspection-reports)
- [Vault Consulting Rankings](https://www.vault.com/best-companies-to-work-for/consulting)
- [Universum Employer Brand](https://universumglobal.com/)

### Regulated industries
- [FAA Airworthiness Directives — 14 CFR Part 39](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-39)
- [FAA AD Content & Format](https://www.faa.gov/aircraft/air_cert/continued_operation/ad/ad_content)
- [NRC 10 CFR 50.72 Event Reporting](https://www.nrc.gov/reading-rm/doc-collections/cfr/part050/part050-0072.html)
- [NERC CIP Standards](https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx)
- [FCC Network Outage Reporting System (NORS)](https://www.fcc.gov/network-outage-reporting-system-nors)
- [CMMC DoD Cybersecurity Maturity Model Certification](https://www.acq.osd.mil/cmmc/)
- [DFARS Cyber Incident Reporting](https://www.acq.osd.mil/dpap/dars/dfars/html/current/204_73.htm)
- [OSHA Recordkeeping & Reporting](https://www.osha.gov/recordkeeping)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [SOC 2 / AICPA Trust Services Criteria](https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2)

### Crisis-comms theory & cross-vertical (from parent monitoring research)
- [Cision React Score](https://www.brandwatch.com/blog/introducing-react-score/)
- [Coombs SCCT (2007)](https://link.springer.com/article/10.1057/palgrave.crr.1550049)
- [Peter Sandman Outrage Management](https://www.psandman.com/index-OM.htm)
- [AMEC Integrated Evaluation Framework](https://amecorg.com/amecframework/)
- [Barcelona Principles V4.0](https://amecorg.com/wp-content/uploads/2025/06/Barcelona-Principles-V4.0-%E2%80%93-FINAL30.6-compressed.pdf)
- [Edelman 2026 Trust Barometer](https://www.edelman.com/sites/g/files/aatuss191/files/2026-01/2026%20Edelman%20Trust%20Barometer%20Global%20Report_Final.pdf)
- [FullIntel Executive Briefing template](https://fullintel.com/blog/executive-briefing-that-leadership-actually-reads/)
- [President's Daily Brief format](https://en.wikipedia.org/wiki/President%27s_Daily_Brief)
- [Eric Dezenhall, *Glass Jaw*](https://dezbooks.net/books/glass-jaw/)
- [Brandwatch Alerts Guide](https://www.brandwatch.com/blog/use-alerts-crisis-management/)
- [Strategic Early Warning Systems / Ansoff weak signals](https://en.wikipedia.org/wiki/Strategic_early_warning_system)
- [PRSA Boeing 737 MAX Crisis Comms Lessons](https://www.prsa.org/article/crisis-communication-lessons-from-boeing-s-737-max-tragedies)
- [Harvard Law School: Narrative Contradictions](https://corpgov.law.harvard.edu/2025/09/13/narrative-contradictions-the-invisible-governance-risk/)
