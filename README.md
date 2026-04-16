# gofreddy

Distribution engineering agency CLI. Powers the work at [gofreddy.ai](https://gofreddy.ai).

One engineer + autonomous agents replacing marketing departments. Forked from the Freddy SaaS codebase — every provider integration is identical; the SaaS layer (FastAPI, Supabase, Stripe, Postgres) is stripped out in favor of direct provider calls and per-client file workspaces.

## Install

Requires Python 3.13 (not 3.14).

```bash
git clone <this repo>
cd gofreddy
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env    # fill in provider credentials
```

## Usage

```bash
# Verify credentials
freddy setup

# Create a client workspace
freddy client new acme-corp

# Run audits (each writes to clients/acme-corp/cost_log.jsonl)
freddy audit seo --client acme-corp acme.com
freddy audit competitive --client acme-corp competitor.com
freddy audit monitor --client acme-corp "acme corp"

# Reports + audit trail
freddy client log acme-corp
freddy client report acme-corp
python portal/generate.py --client acme-corp
# → open portal/output/acme-corp/index.html
```

## Structure

```
cli/freddy/           # CLI surface — commands + shared helpers
  commands/           # client, audit, setup, save, sitemap, auto-draft,
                      # iteration, transcript
src/                  # Provider integrations, file-based sessions
  common/             # Cost recorder (JSONL), Gemini models
  seo/                # DataForSEO
  competitive/        # Foreplay, Adyntel
  monitoring/         # Xpoz, NewsData
  generation/         # Video generation (Fal, Grok, TTS)
  sessions/           # File-based repository
  ... (16 modules total)
landing/              # gofreddy.ai landing page
docs/templates/       # Proposal, service agreement, audit report, etc.
portal/               # Client portal static generator
clients/              # Per-client workspaces (git-ignored except .gitkeep)
```

## Principles

- Every provider comes from the Freddy SaaS codebase verbatim — no reimplementation
- Sessions and cost logs live under `clients/<name>/` as JSON/JSONL
- Commit directly to main. No branches for single-engineer workflow.

## Contact

noszczykai@gmail.com
