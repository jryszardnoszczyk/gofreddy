# Voice corpus consent — operator template

**Purpose:** generic consent-capture template that operators copy into
`clients/<slug>/voice/CONSENT.md` when ingesting a new client's voice
corpus. The destination file is gitignored (per
`clients/*/**` rule in `.gitignore`); only this template lives in repo.

**When to use:** before importing any private/proprietary voice corpus
(books, prior articles, private correspondence, internal documentation)
that's used as authority signal for the gofreddy voice persona compiler.

**When NOT to use:** for personas whose corpus is public domain
(gofreddy's own published content, the `jr` persona's public substrate)
or fully synthetic. Those persona slugs set
`voice_corpus_consent_required: false` in their client.yaml.

---

## Template body (copy into `clients/<slug>/voice/CONSENT.md`)

```markdown
# Voice corpus consent — <client display name>

**Client slug:** <client-slug>
**Voice persona:** <persona-slug>
**Date of consent:** <YYYY-MM-DD>
**Consent owner:** <full legal name + role>

## Scope of use

The works listed under "Corpus inventory" below are licensed to
gofreddy for the following purpose only:

1. Loading into the gofreddy autoresearch substrate as input to the
   voice persona compiler (`src/voice/persona.py:compile_substrate`).
2. Producing derived authority signal (tone, rhythm, register,
   vocabulary, sentence-shape preferences) that downstream content
   lanes (article_engine, linkedin_engine, x_engine, ad_engine,
   site_engine) consume when generating new content on behalf of
   the client.
3. Storage at rest under `clients/<client-slug>/voice/corpus/` on
   gofreddy infrastructure for the duration of the client engagement
   plus 90 days post-termination.

The works are **NOT** licensed for:

- Inclusion verbatim in any content published to the client's channels
  or third parties.
- Use as training data for any model trained on multiple clients'
  data jointly.
- Distribution or sharing outside the gofreddy autoresearch substrate.

## Corpus inventory

| File | Source | Year | Author/owner | License/relationship |
|---|---|---|---|---|
| (e.g. `book-ch01.txt`) | (e.g. Wydawnictwo PWN, 2018) | 2018 | (e.g. Dr. X) | (e.g. author retains copyright; this consent covers internal use only) |

## GDPR Art. 7 — withdrawal procedure

The consent owner may withdraw consent at any time by emailing
`legal@gofreddy.ai` with subject line "Voice corpus withdrawal —
<client-slug>". Within 5 business days of receipt, gofreddy will:

1. Delete the corpus files under
   `clients/<client-slug>/voice/corpus/`.
2. Mark the persona's `voice_corpus_consent_required` field as
   `true` and the corpus directory as withdrawn in the operator
   runbook.
3. Quarantine any in-flight evolution variants that consumed the
   corpus from publication.

Existing published content derived from the corpus prior to
withdrawal is NOT retroactively recalled unless the withdrawal
specifically requests recall under the engagement letter's recall
SLA clause.

## Bar-secrecy interactions (legal clients only)

For corpora consisting of legal partner prior articles, public
case-commentary, or expert opinions, the consent owner confirms:

1. The works do NOT contain client-confidential information protected
   under KERP Art. 27 / Zbiór §10 / attorney-client privilege.
2. Where the works reference past matters, those matters were either
   (a) public-record at time of writing or (b) anonymized prior to
   publication.
3. The author's bar-secrecy duties have NOT been waived by ingestion;
   the corpus is processed for stylistic signal only, not as substantive
   matter content.

## Medical-secrecy interactions (medical clients only)

For corpora consisting of physician prior writing, the consent owner
confirms:

1. The works do NOT identify individual patients or use information
   protected under physician-patient confidentiality (Ustawa o zawodach
   lekarza i lekarza dentysty Art. 40).
2. Patient testimonials or case studies in the corpus carry their own
   separate written GDPR Art. 9 consent (if applicable); the corpus
   consent does NOT extend to those underlying patient records.

## Signature

The consent owner confirms that they have authority to license the
works under the terms above, that the works are accurately inventoried,
and that any third-party rights (co-authors, publishers, contributing
researchers) have been resolved separately.

- Consent owner signature: ___________________________
- Date: ___________________________
- Witness (gofreddy side, required for regulated archetypes):
  ___________________________
```

---

## Operator runbook hooks

- **Before ingest:** operator MUST capture this consent. Without a
  signed `CONSENT.md` alongside the corpus, the per-client launch
  runbook MUST NOT proceed past corpus-ingestion step. Pre-publish
  reviewer (U7) will flag any artifact whose persona references a
  corpus without `CONSENT.md` on disk.
- **Retention:** keep signed PDF / scanned copy of the executed consent
  in operator legal storage (not in git). The on-disk Markdown record
  is operationally adequate but the signed instrument is the legal
  record.
- **Quarterly review:** during quarterly operator review, verify each
  active client's `CONSENT.md` is current (no withdrawal received,
  scope hasn't drifted, no new corpus files added without
  inventory-row updates).
- **Termination:** at engagement-letter termination, run the deletion
  procedure described in the GDPR Art. 7 section above as standard
  exit step regardless of withdrawal request.
