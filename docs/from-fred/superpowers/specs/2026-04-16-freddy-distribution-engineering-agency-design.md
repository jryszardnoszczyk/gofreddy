# Freddy — Distribution Engineering Agency

**Date:** 2026-04-16
**Status:** Approved design, pending implementation plan
**Author:** JR Noszczyk

## Overview

Freddy pivots from a SaaS marketing intelligence platform to a one-person distribution engineering agency. The agency builds AI-powered distribution systems for clients — not campaigns, but infrastructure that compounds over time. The existing Freddy codebase provides the foundation: autoresearch (self-evolving workflows), data provider integrations (15+ APIs), evaluation framework (LLM judges), audit trail/tracking system, and CLI tooling.

## Positioning

**What Freddy is:** A distribution engineering agency that builds AI agent systems to replace traditional marketing departments.

**What Freddy is not:** A traditional creative agency, a consultancy that delivers decks, or a SaaS product.

**Core thesis:** Marketing is now a systems engineering problem. One engineer with an AI agent swarm outperforms a team of ten operating manually. The agency sells systems and outcomes, not hours and headcount.

**Differentiators:**
- Radical transparency — every action logged, every agent transcript visible, every dollar of AI spend tracked via client portal
- Systems that compound — autoresearch evolves client workflows over time, so performance improves and agency cost-per-client decreases
- Engineer-built — custom agent architectures per client, not generic playbooks

**Brand:** gofreddy.ai. Personal brand under JR Noszczyk on X and LinkedIn.

## Target Market

**Phase 1 (now):** Local businesses in Poland. Two clients lined up — a medical dermatology clinic and a legal office. Lower ticket ($1-4K/mo) but immediate revenue and case study material.

**Phase 2 (3-6 months):** Solo founders and early-stage startups. Higher ticket ($5-10K/mo). Attracted through content/personal brand built during Phase 1.

**Phase 3 (6-12 months):** Growth-stage companies in US and Europe. Premium tier ($8-15K/mo). Multi-channel distribution systems.

## Service Offering

Every client engagement follows three phases:

### Phase 1: Distribution Audit
- **Duration:** 1-2 weeks
- **Pricing:** $1-3K (local businesses), $3-5K (tech)
- **Deliverable:** Written audit report + prioritized roadmap
- **Scope:** Current distribution landscape analysis — SEO visibility, competitor positioning, social presence gaps, untapped channels, ad landscape
- **Tools:** Agency CLI + existing data provider integrations (DataForSEO, Foreplay, Adyntel, Xpoz, etc.)
- **Purpose:** Diagnostic that also serves as the sales document for Phase 2. Paid to filter tire-kickers.

### Phase 2: System Build
- **Duration:** 3-6 weeks
- **Pricing:** $5-10K (local), $15-25K (tech)
- **Deliverable:** Working distribution systems — agents running, content flowing, dashboards live
- **Scope:** Build the infrastructure the audit identified. Could include: SEO content pipeline, ad creation + testing system, social monitoring setup, local search optimization, video content pipeline.
- **Tools:** Claude Code + Agency CLI + Autoresearch

### Phase 3: Operate & Evolve
- **Duration:** Ongoing, 3-month minimum commitment
- **Pricing:** $2-4K/mo (local), $5-10K/mo (tech)
- **Deliverable:** Monthly performance reports + full audit trail access
- **Scope:** Run systems, monitor performance, evolve agents, expand to new channels. Autoresearch runs continuously, improving workflows.
- **Key principle:** Agency margin increases over time as agents improve. If month 6 costs the same effort as month 1, something is wrong.

### Initial Client Plans

**Dermatology clinic:** Audit local SEO landscape, competitor ad spend, social presence gaps. Build likely centers on local SEO + content system, possibly Google Ads automation, review management.

**Legal office (Poland):** Audit local search, competitor positioning, referral channels. Build likely SEO-heavy (legal is dominated by search), possibly LinkedIn presence for the lawyers.

## Technical Architecture

Three pillars, tied together through Claude Code skills.

### Pillar 1: Agency CLI (`freddy`)

Personal workbench — a tool for the operator, not a product for clients.

- **Client workspace management** — `freddy client new <name>`, isolated directory per client with config, credentials, audit logs
- **Data provider wrappers** — extracted from existing Freddy integrations into clean commands: `freddy seo audit <domain>`, `freddy ads research <competitor>`, `freddy monitor <brand>`
- **Audit logging** — every command automatically logs: what was run, duration, AI cost, full transcript. Feeds the client portal.
- **Session management** — `freddy session start <client> <domain>` kicks off research sessions, tracks artifacts

Extracted from existing Freddy CLI (`cli/freddy/commands/`), which already has 50+ commands across hand-written and auto-generated categories.

### Pillar 2: Autoresearch (extracted & generalized)

Self-evolving workflow engine. Carried forward from Freddy largely intact.

- Core loop: run -> evaluate -> select -> evolve -> promote
- Adapted to work per-client: each client's workflows evolve independently
- The 4 domain lanes (GEO, competitive, monitoring, storyboard) remain as starting templates; new lanes can be created per client need
- Evaluation framework preserved: 8-criterion LLM judges, geometric mean scoring, content-hash caching
- 12 benchmark fixtures carried forward as baseline; client-specific fixtures added per engagement

### Pillar 3: Client Portal

Transparency layer — web-accessible dashboard per client.

- Shows: every action taken, agent transcripts, AI spend, time tracking, deliverables, performance metrics
- Updated automatically from CLI audit logs
- Hosted on gofreddy.ai — each client gets a private URL or login
- Can start as a simple static site generated from audit logs, evolve into a proper dashboard
- Extracted from Freddy's existing tracking/auditing system

### Claude Code Skills (the multiplier)

Daily workflow is Claude Code. Skills encode distribution workflows:

- `/audit <client>` — runs the full distribution audit flow
- `/build-seo-pipeline <client>` — scaffolds an SEO content system
- `/evolve <client> <domain>` — kicks off autoresearch evolution cycle
- `/report <client>` — generates monthly performance report
- `/publish <client>` — distributes content across configured channels

Every skill calls the CLI. Every CLI command logs to the audit trail. The portal reflects everything automatically.

### Architecture flow:

```
Operator (Claude Code + Skills)
    |
Agency CLI (freddy)
    |-- Data Providers (SEO, Ads, Social, etc.)
    |-- Autoresearch (per-client workflow evolution)
    |-- Audit Logger (every action tracked)
    |-- Publishing (multi-channel distribution)
    |
Client Portal (gofreddy.ai/client/<name>)
    |-- Dashboards, transcripts, spend, results
```

## Content Pipeline & Personal Brand

### Landing Page (gofreddy.ai)

Agency landing page, not a SaaS marketing page. Single page to start.

- **Hero:** One sentence — "I build AI-powered distribution systems that replace marketing departments"
- **How it works:** Three phases (Audit -> Build -> Operate)
- **Proof:** Case studies as they come, own metrics in the meantime
- **Differentiator:** Client portal / full audit trail transparency
- **About:** Engineer background, "distribution engineer" positioning
- **CTA:** Book an audit / contact form

Design: clean, technical, no agency fluff. Engineering portfolio aesthetic.

### Personal Brand

**X (primary):**
- Building in public — what systems you're creating, what agents you're running, what results you're getting
- "Distribution engineer" thesis — riff on the concept with your own experience and results
- Frequency: daily or near-daily

**LinkedIn (secondary):**
- Polished versions of X content, targeting founders and decision-makers
- Case study breakdowns
- Frequency: 2-3x per week

**AI-generated video (automated):**
- Storyboard pipeline from autoresearch generates short-form video content
- Distributed to TikTok, Instagram Reels, YouTube Shorts
- Topics: distribution engineering concepts, behind-the-scenes, results breakdowns
- Runs largely on autopilot — autoresearch evolves video quality over time

### Content flywheel:

```
Client work -> results -> content (X, LinkedIn) -> new clients -> more results
                                                        |
Storyboard pipeline -> AI video -> TikTok/IG/YT Shorts -> wider reach
```

## Agency Documentation

The agency needs operational documents beyond code:

- **Client proposal template** — customizable per audit findings, covers scope/pricing/timeline
- **Service agreement / contract template** — engagement terms, 3-month minimum, scope definitions, change order process
- **Audit report template** — standardized format for distribution audit deliverables
- **Monthly report template** — performance metrics, actions taken, recommendations
- **Onboarding checklist** — what you need from a new client (access, credentials, goals, brand guidelines)

## What Gets Extracted From Freddy

**Carry forward:**
- Autoresearch module (core loop, evaluation, frontier, archive)
- CLI commands (data provider wrappers, session management)
- Audit trail / tracking system
- Data provider integrations (DataForSEO, Foreplay, Adyntel, Xpoz, ScrapeCreators, etc.)
- Evaluation framework (LLM judges, scoring, caching)
- Storyboard pipeline (for own content generation)
- Publishing adapters (YouTube, TikTok, WordPress, LinkedIn, Bluesky)

**Leave behind:**
- SaaS shell (auth, billing, multi-tenant workspace, API routers)
- React frontend
- FastAPI backend structure (routers, dependencies, middleware)
- Supabase multi-user schema
- Cloud Run / Cloud Build deployment

**Build new:**
- Agency CLI (new scaffold wrapping extracted capabilities)
- Client portal (web dashboard generated from audit logs)
- Landing page (gofreddy.ai)
- Claude Code skills for distribution workflows
- Agency document templates

## Launch Roadmap

### Week 1: Foundation + Audit Kickoff
- Landing page live on gofreddy.ai
- New repo scaffolded — CLI core, autoresearch, audit logging extracted
- First X posts — announce positioning, start "distribution engineer" narrative
- Client audits started for dermatology clinic and legal office
- LinkedIn profile updated

### Week 2: Audits Delivered + Build Begins
- Audit reports delivered to both clients
- Build phase contracts signed — scope defined by audit findings
- CLI wired up — client workspaces, audit logging flowing
- Content rhythm established — daily X, 2-3x LinkedIn
- Storyboard pipeline pointed at own brand — first AI videos queued

### Week 3-4: Build Phase + Systems Live
- Client systems being built per audit findings
- Client portal accessible — clients can see audit trail
- Autoresearch running on at least one client workflow
- First AI-generated videos published
- First case study draft from audit results

### Week 4 Success Criteria
- Two paying clients in operate phase (or transitioning build -> operate)
- Working agency CLI with audit logging
- Live landing page on gofreddy.ai
- Active content presence on X + LinkedIn
- At least one automated content pipeline running
