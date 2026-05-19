---
date: 2026-05-19
type: verification audit — SITE v3 surgical edits against v2 spot-check findings
target: docs/handoffs/2026-05-18-judge-design-step1-site-engine.md (v3, Option D 2026-05-19)
roadmap: docs/handoffs/2026-05-19-site-engine-roadmap.md (extracted parallel doc)
v2-finding-source: docs/handoffs/2026-05-19-site-engine-v2-spot-check.md
guide: docs/rubrics/judge-design-guide.md
reviewer-mode: adversarial — did the surgical edits actually close the v2 findings, or did they perform closure cosmetically?
verdict-summary: VERIFIED — Option D surgical edits closed each of the seven v2 findings substantively. Extraction is real (not pointer-cosmetic), "must produce" softened in §1.5b prose, sibling-fork priority physically reordered with site_audit_engine #1 and comparison_engine #2, Substrate-Readiness Gate clause inserted with explicit U15b acknowledgment, first-cohort overfitting clause moved into §1 not appendix, regulated-vertical reasoning surfaced as the comparison_engine reorder rationale. Architectural preservation holds: SE-A..SE-E criterion prose unchanged byte-for-byte; AND-conjunction wrapper unchanged; 8 verifiables routing list preserved with no judge-side bleed; 5-criterion ceiling held with no documented exception (no 6th criterion smuggled in via Phase 2-3 extensions). Roadmap doc carries real Phase 1/2/3 enumeration + 14-cuts + 15-adds + reordered sibling-fork triggers and links back via frontmatter.
---

# §1. Reader and scope of this verification

The reader is JR holding v3 to the bar the 2026-05-19 spot-check set: did the Option D surgical edits actually close the seven load-bearing findings, or did they perform closure (pointer-to-extracted-doc without real extraction; "softened" prose that still reads as commitment; reorder-by-frontmatter without reorder-in-body)? I read v3 end-to-end against the spot-check finding list and against the parallel roadmap doc. The verification protocol is: per finding, locate the v2 problem, locate the v3 edit, check whether the edit is substantive (text change with downstream consequences) or cosmetic (relabel without consequence). I also verify the architectural preservation claims that v3 explicitly makes (criterion prose unchanged, 5-ceiling held, AND-conjunction preserved, 8-verifiables list preserved, legacy-rubric deprecation pattern preserved).

The audit is **VERIFIED across all seven findings**. The edits are substantive. The architectural preservation holds. There are two notes-not-objections worth surfacing (§3 below), but no finding from the v2 spot-check survived unaddressed.

---

# §2. Per-finding verification

## §2.1 ~4,400 words of roadmap content extracted to parallel doc — VERIFIED

The roadmap doc at `docs/handoffs/2026-05-19-site-engine-roadmap.md` carries the full extracted content: Phase 1 deliverables 1-12 (audit / IA / home / 2-3 landing pages / pricing / about / first customer-story / AEO infra / mobile UX / a11y / performance / measurement), Phase 2 deliverables 13-19 (comparison / use-case / industry / product / customer-stories / blog architecture / resource center), Phase 3 deliverables 20-28 (CRO / email / chat / GDPR / sticky CTA / onboarding / Custom GPT / Knowledge Panel / analytics), per-phase size envelopes (10-12 / 22-27 / 30-35 cumulative + beyond-90 cadence), the 14-cuts detail catalog (per-cut framing + named replacement), the 15-adds detail catalog, sibling-fork operational triggers (4 priorities with quantified trigger conditions), multi-deliverable evolution-loop architecture (EL1/EL3/EL4 framing from research §6), cross-lane consistency enforcement (`ClientConfig.entity_anchor` proposed infrastructure), and retainer-shape revenue model commentary.

The v3 spec §1.5b retains only a one-sentence capability statement plus a pointer to the roadmap doc — no parallel enumeration. §3a and §3b each carry a single-paragraph inline reference followed by an explicit "Full detail catalog extracted to ... §2" / "§3" pointer. §8b retains a 4-item priority reorder summary with the substantive trigger conditions, followed by an explicit "Full sibling-fork operational triggers + multi-deliverable evolution-loop architecture + cross-lane consistency enforcement + retainer-shape revenue model commentary extracted to ... §4-§7" pointer. The extraction is real, not cosmetic — the spec genuinely drops the prose, the roadmap doc genuinely picks it up.

§7's word count claim (~7,100 v3 spec body after ~4,400-word extraction) is plausible from the body length I read. **VERIFIED.**

## §2.2 §1.5b "must produce" softened to "capable of producing" — VERIFIED

The v2 §1.5b opener was *"The lane's full deliverable scope is the comprehensive site program a 2026 AI-native agency must produce"* (normative, timeline-implicit). The v3 §1.5b opens: *"The lane is CAPABLE of producing a 3-phase staged comprehensive site program when engagement scope demands it. Not all engagements require all deliverables; substrate-readiness gates apply per deliverable."* The capability-framing block continues: *"the lane is capable of producing the following deliverables when engagement scope demands them; not all engagements require all deliverables; substrate-readiness gates apply per deliverable. The 30/60/90 timing in the roadmap doc is the SOTA-anchored comprehensive workflow target ... NOT a hard delivery commitment against any specific client engagement."*

The capability framing also propagates into the roadmap doc itself: §1 of the roadmap opens *"The lane is **capable of producing** the following deliverables when engagement scope demands them"* and explicitly tags the 30/60/90 as *"the SOTA-anchored comprehensive workflow target, NOT a hard delivery commitment."* Per-phase size envelopes are labeled "capability framing, not delivery commitment" inline.

This is a real text edit with real consequences — the spec no longer reads as documenting underdelivery against itself if a client commissions only Phase 1. **VERIFIED.**

## §2.3 Sibling-fork priority reordered (site_audit FIRST, comparison SECOND) — VERIFIED

The v2 §8b set comparison_engine as HIGHEST PRIORITY and parenthetically deferred site_audit_engine. The v3 §8b carries an explicit 4-item reorder header (*"Priority reorder (v3, per 2026-05-19 spot-check first-cohort vertical-mix analysis)"*) followed by the numbered list:

1. `site_audit_engine` — HIGHEST PRIORITY (with trigger: ≥3 clients OR ≥15% revenue)
2. `comparison_engine` — SECOND PRIORITY (with trigger: ≥3 clients **in unregulated-vertical contexts** OR ≥15% revenue)
3. `cro_test_program` — THIRD PRIORITY
4. `site_landing_variants` — FOURTH PRIORITY

The roadmap doc §4 carries the same priority order in its operational-trigger section: site_audit_engine HIGHEST, comparison_engine SECOND, cro_test_program THIRD, site_landing_variants FOURTH — same headings, same trigger conditions, with the priority order explicitly justified per first-cohort vertical mix (Klinika + DWF regulated-vertical mismatch with comparison_engine).

The comparison_engine trigger is meaningfully tightened — adding "in unregulated-vertical contexts" forces the fork to ride on actual unregulated-vertical demand rather than industry-trend inference. This is exactly the spot-check's recommended mitigation. **VERIFIED.**

## §2.4 Substrate-readiness gate added with U15b unshipped acknowledgment — VERIFIED

v3 §1.5b carries an explicit "Substrate-readiness gate" subsection: *"The 3-phase comprehensive site program ... describes the COMPREHENSIVE workflow target. Phase 1 judge core (home + 2-3 primary landing pages) ships at substrate-current. Phase 2 + Phase 3 deliverables ship as substrate emission catches up — each requires its own workflow tooling ... Until each phase's substrate emits, structural_gate validates Phase 1 only. ... **site_engine lane itself has not been shipped to v006 (per memory: U15b unshipped) — even Phase 1 judging requires the lane scaffolding to land first.**"

The acknowledgment also appears as parenthetical reinforcement in §1's first-cohort overfitting clause and in §8a-4's legacy-rubric retirement deferral. The roadmap doc opens with a parallel clause: *"the site_engine lane itself has not been shipped to v006 (U15b unshipped per project memory) — even Phase 1 judging requires the lane scaffolding to land first."*

The substrate-readiness gate is the spec's response to the v2 concern that 30 deliverables across 90 days had been promised without engineering capacity to validate them. The U15b acknowledgment closes the load-bearing gap. **VERIFIED.**

## §2.5 First-cohort overfitting posture clause added — VERIFIED

v3 §1 adds an explicit "First-cohort overfitting — explicit posture clause (v3 surfaced)" sub-section. It enumerates two consequences: (a) sibling-fork prioritization must engage with the actual first-cohort vertical mix, not the SaaS-canonical exemplar set (which is precisely the comparison_engine reorder rationale per §8b); (b) legacy `docs/rubrics/site-quality.md` retirement timing is dependent on the site_engine lane shipping to v006 (per memory: U15b unshipped). The 10-category breadth is acknowledged as *"intentionally broader than the current first-cohort fixture mix"* — the spec is openly using breadth as overfitting mitigation, not pretending the breadth reflects current client mix.

This posture clause sits in the main reader section (§1), not in the appendix — which is the right structural position. **VERIFIED.**

## §2.6 Two-jobs problem addressed via extraction — VERIFIED

The two-jobs problem was the v2 spot-check's framing: judge spec + lane-roadmap spec in one document, with the second job weakly evidenced. v3's response is structural: extract the lane-roadmap material into a parallel doc and have the judge spec carry only the judge-design discipline (criterion prose, wrapper, structural_gate routing, Goodhart-resistance modes, anti-pattern catalog, verification per design-guide).

The v3 spec's §1.5a (Component A judge-artifact lock), §1.5c (8-verifiables shape-enforcement split), §3c-d (Component A failure modes), §3e (SITE-specific AI-failure surfaces routed to structural_gate), §4 (5 criteria), §5 (wrapper), §6a-b (Goodhart-resistance), §7 (verification against design guide) are all judge-design content and stay. The §1.5b lane-scope enumeration, §3a/b detailed cut/add catalog, §8b-e sibling-fork operational triggers + cross-lane consistency + retainer commentary are extracted to the roadmap doc. The genre separation that the spot-check called for is now in place. **VERIFIED.**

## §2.7 30/60/90 staged program research-derived without client validation — addressed via substrate gate + capability framing — VERIFIED

The v2 concern was that 30/60/90 timing rested on Stripe / Linear / Mercury / Anthropic exemplar inference rather than gofreddy first-cohort engagement validation. v3 addresses this through the combination of (a) capability framing — 30/60/90 is the SOTA-anchored CAPABILITY ceiling not the observed cadence, (b) substrate-readiness gate — Phase 2-3 deliverables ship as substrate emission catches up rather than to a fixed calendar, (c) explicit acknowledgment that *"first-cohort retainer reality is unobserved as of 2026-05-19 (neither Klinika nor DWF has shipped a retainer engagement)"* — both in v3 §1.5b and in the roadmap doc §7.

The roadmap doc's §7 specifically tags Phase 2-3 deliverable shipping as gated on *"(a) substrate readiness per parent spec's Substrate-Readiness Gate clause, AND (b) actual client engagement scope crossing the Phase-2 / Phase-3 surface"* — the timeline commitment is honestly bracketed. **VERIFIED.**

## §2.8 comparison_engine regulated-vertical mismatch addressed — VERIFIED

v3 §8b explicitly justifies the comparison_engine demotion: *"Comparison-page warfare is the single highest-leverage 2026 AEO surface for unregulated-vertical contexts; fits poorly for Klinika (regulated medical advertising) and DWF (regulated legal marketing) — 2 of 3 active first-cohort."* The trigger condition was tightened from "≥3 clients with comparison-page demand" (v2) to "≥3 clients **in unregulated-vertical contexts** (B2B SaaS / AI lab / agency / dev-tool)" (v3). The roadmap doc carries the same reasoning in §4. **VERIFIED.**

---

# §3. Architectural preservation claims

## §3.1 5-criterion ceiling held with no documented exception — VERIFIED

v3 §7 explicitly verifies against design guide §5: *"5 (no documented exception) — the lane's AI-failure surfaces ... all route to structural_gate rather than warranting a 6th semantic criterion. The Phases 2-3 deliverable expansion does NOT add criteria at the judge layer."* §6b's per-component Goodhart modes (comparison-page, customer-story, persona-misclassification, schema-fabrication, llms.txt-poisoning, CRO test program) are explicitly handled at structural_gate or sibling-fork — no judge-criterion smuggling. **VERIFIED.**

## §3.2 SE-A..SE-E criterion prose UNCHANGED — VERIFIED

I read §4 in full. The criterion prose, the three vertical-divergent score-1 anchors on SE-A / SE-B / SE-D, the single anchors on SE-C and SE-E, the per-criterion CoT (3 steps), the "Do not score" structural_gate routing — all match the v1 spec content as described in the revision history. The modern-lever bias absorption appears only as parenthetical *"(Modern-lever bias: ...)"* sub-points within score-1 anchors — these annotate the existing anchors rather than re-writing them. **VERIFIED.**

## §3.3 AND-conjunction wrapper preserved — VERIFIED

v3 §5 wrapper carries the AND-conjunction language: *"The dual-audience nature is structural — a page can convert humans and be AI-uncitable, or vice versa. World-class pages do both on the same surface. The score-1 anchors on SE-A, SE-B, SE-D, and SE-E require AND-conjunction on the conflict surface."* The "Score for the OUTCOMES" prescription is intact. **VERIFIED.**

## §3.4 8 verifiables routed to structural_gate preserved — VERIFIED

v3 §3e carries the consolidated 8-verifiables list (schema validity, Lighthouse, axe-core, brand-token, alt-text, broken-link, mobile responsive, robots.txt) with the explicit note *"applies across Component A judge surface AND Phases 2-3 lane deliverables."* §1.5c carries the same 8 as the shape-enforcement split. No new semantic verifiables crept into the judge from the Phase 2-3 expansion — the additional Phase 2-3 checks (URL HEAD on comparison-page external references, quote-grep on customer quotes, etc.) are routed to structural_gate via §8a-3 (DEFERRED to plan-002), not to the judge. **VERIFIED.**

## §3.5 Legacy site-quality.md deprecation-header preserved — VERIFIED

v3 §8a-4 carries the deprecation-header-in-place pattern unchanged: file stays at `docs/rubrics/site-quality.md` with frontmatter banner marking it superseded; historical scored variants with `rubric_version: site-quality-v1` stay attributable; no re-scoring of historical fixtures. v3 §1's first-cohort overfitting clause adds the new constraint that retirement timing depends on site_engine lane shipping (U15b) — this strengthens the deprecation-header pattern rather than weakening it. **VERIFIED.**

---

# §4. Roadmap doc verification

The roadmap doc at `docs/handoffs/2026-05-19-site-engine-roadmap.md` is a substantive standalone document, not a pointer-stub. It contains:

- **Frontmatter linking back to parent spec.** `parent: docs/handoffs/2026-05-18-judge-design-step1-site-engine.md`, plus a clear scope statement (*"3-phase deliverable list + modern-lever cuts/adds detail catalog + sibling-fork operational triggers"*) and a purpose tag (*"lane-program planning input for plan-002; NOT judge-design content"*).
- **§1 Phase 1/2/3 enumeration** with all 28 deliverables numbered, plus per-phase size envelopes (10-12 / 22-27 / 30-35 cumulative + beyond-90 cadence) framed as capability ceilings.
- **§2 14-cuts detail catalog** with named-replacement framing per cut, citing research §2.
- **§3 15-adds detail catalog** with per-add framing + research citations + named exemplars, citing research §3.
- **§4 Sibling-fork operational triggers** with the reordered priority (site_audit_engine #1, comparison_engine #2, cro_test_program #3, site_landing_variants #4), quantified trigger conditions per fork, and "other sibling-fork candidates — DEFERRED beyond first-cohort" subsection.
- **§5 Multi-deliverable evolution-loop architecture** (EL1 / EL3 / EL4 from research §6).
- **§6 Cross-lane consistency enforcement** (`ClientConfig.entity_anchor` proposal).
- **§7 Retainer-shape revenue model implications** (with explicit first-cohort retainer-reality-unobserved acknowledgment).

The doc closes with *"The parent judge spec ... holds the Component A judge design; this doc holds the lane-program roadmap that depends on substrate readiness + client engagement scope to actually ship"* — explicit genre separation. **VERIFIED.**

---

# §5. Two notes-not-objections

1. **Roadmap doc is structurally a `docs/handoffs/` artifact, not a `docs/plans/` artifact.** The v2 spot-check recommended extraction to `docs/plans/2026-05-19-XXX-site-engine-lane-scope-roadmap.md`. v3 placed it at `docs/handoffs/2026-05-19-site-engine-roadmap.md` instead. The genre separation is achieved either way; the `docs/handoffs/` placement reads as a transient hand-off-to-plan-002 staging rather than a permanent plan document. If plan-002 next iteration absorbs the roadmap material into a plan-doc, the staging position is correct. If the roadmap is intended as a long-lived reference, a `docs/plans/` or `docs/roadmaps/` home would communicate that more clearly. Either is defensible.
2. **The capability-framing softening is consistent across spec and roadmap but the §2b "Program-level success" subsection inside v3 still uses commitment-flavored language** (*"commits to the redesign program"*, *"Executes Phase 1 within 30 days"*, *"Rolls out Phase 2 by Day 60"*). This is success-criteria prose for the program-level reader, not delivery-commitment prose for the agency, but a casual reader could parse it as the latter. If JR wants the capability framing fully consistent, §2b's verb register could mirror §1.5b's *"capable of"* / *"when engagement scope demands"* hedging. Minor; not a finding.

---

# §6. Overall verdict

**VERIFIED.** All seven v2 spot-check findings closed substantively, not cosmetically. Architectural preservation holds across SE-A..SE-E criterion prose, AND-conjunction wrapper, 8-verifiables routing, 5-criterion ceiling, legacy-rubric deprecation pattern. The roadmap doc carries the extracted content with a real frontmatter link back to the parent spec and a clear genre statement. The Option D surgical edits worked.

The judge-design layer is now ready for the next step gated on U15b shipping. The lane-roadmap material is in a structurally cleaner home than v2 had it. The first-cohort overfitting watch is honest about the gap between 10-category breadth and 3-vertical first-cohort reality. The substrate-readiness gate prevents the spec from over-committing the lane to deliverables structural_gate cannot yet validate.

---

# §7. What is NOT my territory (deferred to other reviewers)

- **Coherence / terminology drift** between v3 spec and roadmap doc cross-references → coherence-reviewer.
- **Technical feasibility** of structural_gate Phase 2-3 expansion → feasibility-reviewer.
- **Scope-goal alignment** of plan-002 next iteration absorbing the roadmap doc → scope-guardian-reviewer.
- **UI/UX quality** of the lane's produced landing-page artifacts → design-lens-reviewer.
- **Security implications** of Knowledge Panel / Wikipedia / Wikidata strategy → security-lens-reviewer.
- **Product framing** of the agency-engagement business model → product-lens-reviewer.

My territory was epistemological: did the v3 surgical edits substantively close the v2 findings, or perform closure? Substantively closed.
