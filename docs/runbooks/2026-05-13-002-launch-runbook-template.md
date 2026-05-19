# Per-client launch runbook — operator template

**Purpose:** generic step-by-step that operators follow to onboard a
new content-engine client and reach first-publication-window. Copy
to `docs/runbooks/<YYYY-MM-DD>-002-<client-slug>-launch-runbook.md`
and fill in per-client specifics; the per-client copy is the
production artifact, this template is the regression checkpoint.

**When to use:** before the first publication run for any new client.

**Audience:** gofreddy operator (or operator + client point-of-contact
in joint kickoff).

---

## Preconditions

The substrate is ready if:

- `clients/<slug>/client.yaml` exists, loads via
  `src.clients.loader.load_client_config(slug)`, and pydantic
  validation passes (`pytest tests/clients/test_config.py`).
- The client's archetype is in the `Archetype` literal
  (`src/clients/config.py`). v1 supports `b2b_saas`,
  `b2c_aesthetics`, `b2b_regulated`, `b2b_tech`. New archetypes are
  a 1-line literal edit per the D11 invariant.
- The client's reviewer-assist checklist
  (`reviewer_assist_checklists[0]`) exists at
  `reviewer_assist/checklists/<name>.yaml` and loads via
  `src.compliance.loader.load_rule_set(name)`. v1 ships
  `medical_pl`, `legal_pl`, `gdpr_eu`.

## Steps

### Step 1 — voice persona setup

1. Pick the persona slug for the client. If sharing an existing
   persona (e.g. `dr_maria` reused across articles + LinkedIn + X +
   ads + site), set `voice_persona_ref: <slug>` in client.yaml. If
   bespoke, create `voice_personas/<slug>.yaml` per U3 schema.
2. Decide consent posture:
   - **Public-corpus persona** (e.g. `jr`): `voice_corpus_consent_required: false`.
   - **Private-corpus persona** (regulated clients, named individuals):
     `voice_corpus_consent_required: true`. Capture written consent
     via [the voice consent template](2026-05-13-002-voice-consent-template.md)
     BEFORE Step 2.
3. Ingest the corpus to `voice_personas/corpora/<slug>/` (gitignored
   except for `jr`). Markdown preferred; PDF via `pdfplumber` /
   `pymupdf`. Keep filenames stable (the compiler reads files in
   filesystem order; renames change the substrate hash).

### Step 2 — brand assets collection

1. Create `clients/<slug>/brand/` (gitignored). Operator-side only.
2. Collect from the client:
   - `style-guide.md` — written brand voice + tone notes.
   - `logo.svg` — vector logo (PNG fallback only when
     `brand_strictness: permissive`).
   - `palette.json` — color tokens (hex codes).
   - `tokens.json` — site_engine brand tokens (typefaces, spacing,
     motion) when `site_engine` is in `enabled_channels`.
   - Reference imagery (optional but recommended for image_engine
     calibration).
3. Verify each path referenced in client.yaml's `brand_assets` +
   `site_engine.brand_tokens` resolves.

### Step 3 — pre-publish reviewer onboarding

1. Confirm the named primary reviewer
   (`pre_publish_reviewer.email`) is correct and has been briefed:
   - Reviewer responsibility: every artifact gets a digest email
     (HMAC-signed link) with the proposed content + reviewer-assist
     flags. Reviewer clicks Approve/Reject/Rework within the
     `pre_publish_reviewer.sla` budget.
   - **§Compliance Posture briefing:** the reviewer-assist checklist
     flags are scaffolding, NOT legal-grade compliance gates.
     Reviewer carries the actual ship/no-ship decision.
   - Email setup: reviewer's mailbox can receive
     `noreply@gofreddy.ai` HMAC-signed digests; mail filters do not
     route them to spam.
2. Per TD-17 (placeholder rule-set regime): for `medical_pl` or
   `legal_pl` clients, also confirm `pre_publish_reviewer_secondary`
   is nominated and onboarded the same way. Two-reviewer signoff is
   required for every artifact until outside-counsel review of the
   reviewer-assist YAML lands (v1.5 promotion gate).
3. Test the email flow with a synthetic artifact. Verify the
   reviewer receives the digest, the Approve/Reject/Rework links
   work, and the audit event lands in
   `clients/<slug>/audit/events.jsonl`.

### Step 4 — first dry-run

1. Pick the lowest-risk lane in `enabled_channels` for the first
   live run. Convention:
   - Regulated archetypes (`b2c_aesthetics`, `b2b_regulated`):
     `linkedin_engine` first — content is professional context,
     reviewer surface is lower than ads.
   - Internet-native archetypes (`b2b_saas`, `b2b_tech`):
     `article_engine` first — long-form gives reviewer most
     pattern-matching surface.
2. Run a single fixture against the picked lane in dry-run mode
   (no publish):
   ```
   freddy autoresearch run --lane <lane> --client <slug> --dry-run
   ```
3. Verify:
   - Voice substrate compiles (`compile_substrate` returns text;
     not empty).
   - Brand assets resolve.
   - At least one variant passes reviewer-assist gate (verdict
     `clean` or `soft_warn`).
   - The pre-publish digest reaches the named reviewer.
4. Iterate on persona / brief / fixture if the dry-run fails.

### Step 5 — site_engine target snapshot (when site_engine is enabled)

1. Capture the client's current live site at a known timestamp;
   commit the snapshot HTML to `clients/<slug>/site_engine/snapshots/`
   (operator-side, gitignored). This is the regression baseline for
   future site_engine variants.
2. Start with a narrow `sections_in_scope` subset (one section, e.g.
   `[hero]`) until a successful Approve/Publish cycle completes.
   Add sections one per week (see `site_engine.weekly_section_target`)
   until the configured full scope is exercised.

### Step 6 — first live publication

1. Run the picked lane against a real brief (not synthetic). Variant
   output goes through reviewer.
2. On Approve: publish to the configured channel via the existing
   channel integration. Record the artifact entry in
   `docs/runbooks/<YYYY-MM-DD>-002-<client-slug>-artifacts.json`.
3. On Reject or Rework: capture the reviewer note + reasoning. If
   the reviewer-assist YAML flagged the artifact and the reviewer
   disagreed (false-positive), file the rule for cross-cycle review.
   If the YAML missed a real issue (false-negative), file the gap
   for cross-cycle review.

### Step 7 — launch window tracking

- Launch window = 30 calendar days from first publication.
- Success bar: ≥5 artifacts approved-and-published within window.
- Tracking: append entries to the per-client artifacts manifest
  (one entry per published artifact with `artifact_id`, `lane`,
  `format`, `channel`, `published_url`, `approver_name`,
  `approval_timestamp`, `published_timestamp`).
- If <5 by day 30, document root cause and one of:
  - D5 regen-with-feedback iteration (improve fixture / persona /
    brief).
  - D14 reviewer-side adjustment (capacity / SLA tuning).
  - Reviewer-assist YAML calibration (flag pattern adjustment).

---

## Per-archetype runbook deltas

This template is archetype-agnostic. Below are the operationally-
meaningful deviations per v1 archetype.

| Archetype | Deltas |
|---|---|
| `b2c_aesthetics` (e.g. Klinika) | medical_pl + gdpr_eu both required; two-reviewer signoff; `content_denylist: [clinical_visuals, before_after_imagery]` enforced; `weekly_publish_target: 5` floor for launch window; Step 3 secondary reviewer is clinic admin/manager |
| `b2b_regulated` (e.g. DWF) | legal_pl + gdpr_eu both required; two-reviewer signoff; `weekly_publish_target: 3` (lower throughput); Step 3 secondary reviewer is second partner or senior associate; Step 4 dry-run lane is `linkedin_engine` (partner-byline format) |
| `b2b_saas` | gdpr_eu only (if EU-targeting); single-reviewer signoff; `article_engine` first; site_engine fully exercised |
| `b2b_tech` | architectural-validation stub only; no publication runs; `archetype_stub_allowed: true` |

New archetypes onboard via 1-line `Archetype` Literal edit + new
checklist YAML + new client.yaml + (optionally) a new entry in
this table.

---

## Smoke checklist for review before first publication

- [ ] `pytest tests/clients/test_config.py` green for the new client.
- [ ] `load_client_config(<slug>)` returns frozen model with no warnings.
- [ ] `load_rule_set(<checklist>)` loads without error.
- [ ] Voice persona corpus exists on disk; `CONSENT.md` filed.
- [ ] Brand assets exist on disk; `brand_strictness` posture verified.
- [ ] Reviewer email tested end-to-end.
- [ ] Secondary reviewer onboarded (for regulated archetypes).
- [ ] At least one dry-run variant achieved verdict `clean` or
      `soft_warn` (not `hard_block`).
- [ ] Engagement letter signed by the client per
      `docs/plans/2026-05-13-002-...` parallel-track risk #12.

When all boxes pass, the client is ready for the first live
publication run.
