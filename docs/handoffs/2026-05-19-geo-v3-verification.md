---
date: 2026-05-19
type: adversarial verification review
target: docs/handoffs/2026-05-18-judge-design-step1-geo.md (v3 — Option D surgical edits)
reviewer-role: GEO v3 verification reviewer (epistemological / surgical-edit fidelity / preservation audit)
v2_spot_check: docs/handoffs/2026-05-19-geo-v2-spot-check.md
guide: docs/rubrics/judge-design-guide.md
status: complete
---

# GEO v3 verification

## Verdict at the top

**APPROVE WITH ONE RESIDUAL — ship v3.** Six of eight v2 findings are cleanly addressed by the
surgical edits. One (§8 first-cohort overfitting at section level) is acknowledged in passing but
not operationalized — acceptable as documented open question. One (§1 healthcare substitute reader
out-of-family) is not addressed because the v3 brief did not scope it for surgical edit — flagged
here as a v4 candidate, NOT a v3 blocker. Architecture preservation is clean: 6 criteria preserved,
GEO-1 / GEO-3 / GEO-5 prose untouched, GEO-2 / GEO-4 score-1 prose preserved with 4th examples
purely additive, 12-section bundle preserved, AND-conjunction preserved, all 8 v1 surgical
restoration folds preserved.

## Per-finding verification

### GEO-6 imagine-confusable CoT → PASS

v2 flagged: "Step 1 ('Identify the entity's most-confusable similar-name target from page
context') cannot be reliably executed from a reference-free brief." The double-imagination
pathology — judge must imagine a confusable, then check the page against it — would produce
unfalsifiable scoring and high variance.

v3 state: **fully addressed at lines 1316-1330.** The CoT Step 1 is rewritten to score "ONLY
against what the page explicitly disambiguates against." The instruction is explicit: "If the
page does not explicitly disambiguate, the disambiguation sub-requirement does not apply and
the judge emits 0.5 + 'unknown' + 'page does not name what it's disambiguating against' for
that sub-requirement." The fix is stronger than the v2 ask — it adds the literal "Do NOT imagine
confusables the page could have addressed but didn't" guard and names the parallel CI-4 / CI-6
v3.6 precedent. The score-1 anchor language at sub-requirement (a) is preserved verbatim (the
"explicit disambiguation block early when the entity has a most-confusable similar-name target"
phrasing remains) but the CoT now enforces brief-stated-only scoring. Score-0 anchor likewise
preserved. This is the correct surgical pattern — anchor prose untouched, CoT enforcement
tightened.

### GEO-2 competitor-winning 4th example → PASS

v2 flagged: the competitor-acknowledgment sub-clause was theoretical without a concrete worked
example; the rejection-of-self-preference path could let the workflow score 1 without doing
positive analytical work.

v3 state: **addressed at lines 959-976.** Example D adds a competitor-winning acknowledgment
worked example — Linear-GitHub-integration loss + counter-claim on issue-tracking
customizability + dated sources on both sides + absolute-date framing throughout. The example
satisfies the AND-conjunction explicitly: extractable form (named competitor + named feature +
dated source + dated counter-claim) AND human-trust-survivable substance (loss is named with
specific feature attribution, not "competitor is better in some ways"; counter-claim is named
with specific count attribution). The example is hedged with "do not optimize toward this; the
test is the acknowledgment-of-genuine-loss discipline, not the specific competitor named" — per
design-guide §7 reference-free discipline. The closing paragraph at lines 1006-1011 retains the
"Required for full score-1" competitor-acknowledgment requirement. Net: the theoretical
sub-clause is now a worked example with discriminating substance. Clean surgical edit.

### GEO-4 citability-moat 4th example → PASS

v2 flagged: "citability moat" sub-clause was theoretical; could let a vendor-vacuum page score 1
by claiming "we have a proprietary methodology no one else can validate."

v3 state: **addressed at lines 1117-1141.** Example D adds the gofreddy 149-lens audit
methodology worked example. The example earns the moat without vendor-vacuum collapse via four
explicit anti-patterns the example breaks: (a) methodology named with provenance (CXL ResearchXL
+ Phase-0 9-meta-frames), not "our proprietary system"; (b) specific scope named (149 lenses,
9 dimensions, 200-400 rows per audit), not "comprehensive analysis"; (c) output reproducible
with a published client artifact link; (d) framework itself open-sourced (MIT licensed) — the
moat is depth-of-application, not access-control. The example concludes with an explicit
score-0 contrast ("We deliver world-class audits using our proprietary methodology" scores 0).
This is the strongest of the three 4th-example additions because it discriminates against the
exact failure mode v2 named. Hedged per reference-free discipline. Score-1 anchor prose
otherwise preserved.

### Multi-component bundle no client validation → PARTIAL (acceptable)

v2 flagged: "the 12-section §A-§L architecture is research-derived without a single named client
validation point" — workflow burns evolution generations producing §D-§J that no human reads,
sections become Goodhart-attack vectors.

v3 state: **substrate-readiness gate at lines 442-468** is the surgical response. The gate is
real and load-bearing: "§A + §C + §I (judge core) ships at substrate-current. §B + §K ship
near-current... §D-§H + §J + §L ship as substrate emission catches up — each section requires
its own workflow tooling." The gate operationally addresses the spot-check's load-bearing
concern: until substrate tooling lands per section, "structural_gate fails 100% of sessions if
v3 ships against the full bundle." This is stronger than the v2 spot-check recommended posture
(ship §A + §B + §C + §K + thin §I as production-default; §D-§J as on-demand) because the
substrate-readiness gate is enforced by structural_gate, not by JR memory. Important: this
preserves the multi-component architectural target without forcing the workflow to optimize
empty §D-§J sections. The "PARTIAL" classification rests on one residual: there is still no
named client request for the 12-section bundle shape. The substrate-readiness gate decouples
SPEC TARGET from SHIPPING TARGET, which is the right architectural move, but it does not
answer the underlying epistemological question of whether any reader wants the bundle. That
question is now §8 question 1 (preserved from v2 — pairwise redundancy check) and the §10
multi-component fixture validation gate. ACCEPTABLE because the gate ensures no client receives
empty sections; the question can be answered empirically when the substrate emits.

### §8 GEO ↔ site_engine boundary → PASS

v2 flagged: "the GEO ↔ site_engine boundary at §8 question 4 is acknowledged but not explicit
— the spec says 'GEO produces recommendations in §D; site_engine implements pages' but does not
specify the topology-spec contract format."

v3 state: **addressed at lines 1650-1671 (new question 4b).** The new question carries an
explicit work-item routing test: "is this work item changing a SINGLE PAGE for AI-engine
citability + comparison-page warfare + off-page signal engineering (GEO) or changing
SITE-WIDE conversion + IA + multi-page narrative arc (site_engine)?" Tie-break rule named: if
a work item lives in both lanes, route by which judge layer it scores against — citation share
/ retrieval rate → GEO; signup conversion / scroll-depth → site_engine. Per-lane scope explicit
on both sides. The acknowledgment that "site_engine is in mid-build; this boundary draws
against a moving target" is honest and links to the memory entry. Net: the boundary is now
explicit at the work-item level, which is the granularity v2 asked for. Original question 4
(topology recommendation handoff) preserved. Clean additive edit.

### Per-section first-cohort overfitting → PARTIAL (acceptable as open question)

v2 flagged: "First-cohort overfitting at the SECTION level is unaddressed. §E (off-page signal
plan) likely overfits hardest because the optimized §E template against Klinika (Polish Wykop +
RealSelf + Healthgrades + Polish-language Wikipedia) will not transfer to Anthropic (HN +
Lobsters + arxiv + Latent Space + Twitter)."

v3 state: **partially addressed at §8 question 9 (lines 1707-1718).** Question 9 is broadened in
v3: "When DTC / fintech / hospitality / B2C app / agency / service-business fixtures land — or
any fixture from a vertical not in {legal-services, AI-lab, healthcare, B2B-SaaS, fintech, DTC}
— trigger re-validation pass on the affected criteria. Specifically: form-factor distribution
may shift; per-vertical evidence convention may need parameter additions; the §A-§L
deliverable architecture's per-section emphasis may need adjustment (e.g., DTC fixtures need
much heavier §G agentic-commerce content + §E Reddit-engagement content than B2B SaaS does;
regulated-finance fixtures need heavier §I compliance-officer-bio content + §J defense
content)." This NAMES the per-section overfit risk for §E and §G + §I + §J. It does NOT
operationalize how the lane picks which substrate map to instantiate per fixture or how the
structural_gate validates the per-vertical community-substrate fit. ACCEPTABLE because the v2
spot-check flagged this as a watchlist item, not a ship-blocker; the substrate-readiness gate
(which defers §E to "when the Reddit/Wikipedia/Wikidata signal-engineering plan generator
lands") naturally pushes the per-vertical community-substrate map into the §E substrate tool
spec, where it belongs. Won't ship empty §E sections; per-vertical fit can be operationalized
when the §E generator lands.

### Polish first-cohort handling in modular layer → PASS

v2 flagged: "§1 broadened US-primary, and §E names 'Polish Wikipedia + Wikidata for PL clients'
+ 'Wykop for general; per-vertical communities in PL' without specifying which non-Polish
components flex." Needed explicit operationalization — `geo_locale` enum, per-section locale-flex
parameter.

v3 state: **explicitly addressed at lines 234-243 (new "First-cohort posture (v3 explicit)"
paragraph) + preserved §8 question 17.** The v3 paragraph is direct: "Klinika Melitus and DWF
Poland are the only two onboarded clients (both Polish-language, both regulated-vertical —
aesthetic dermatology and law). The US-primary substitute readers enumerated above are the
**architectural target** as the client base expands Q3-2026+; they are NOT first-cohort
fixtures." Per-locale fixture passes required. The straddle is explicit: "concrete Polish-
language fixtures exercising the rubric today, US-primary substitute-readers shaping the
rubric for tomorrow — is **intentional during cohort expansion** and is not a contradiction."
This is the cohort-expansion-discipline pattern v2 asked for. The §8 question 17 ("Polish-
language coverage as first-class or as overlay") is preserved as a follow-up: per-language
fixtures only when a client has substantial Polish-language work product; don't bifurcate
the spec. The locale-flex mechanism is not yet a `geo_locale` enum — it's section-emphasis-
per-client-need — but that's acceptable as v1 posture; the mechanism question is deferred to
when a non-Polish locale fixture lands. Clean explicit-posture addition.

### §1 healthcare substitute reader out-of-family → NOT ADDRESSED (acceptable, v4 candidate)

v2 flagged: "the service-business / local owner-operator persona is the same out-of-family
inclusion CI v3.5 carried." Founder at AI lab and owner-operator at a Warsaw clinic commission
GEO for fundamentally different reasons, at radically different scales, against radically
different evidence substrates.

v3 state: **NOT addressed by surgical edit.** The §1 substitute-readers list at lines 147-173
is unchanged in v3. The CI peer review flagged this; GEO inherits it. The v3 revision history
at lines 65-80 does not name this as in-scope for the v3 surgical edits — the spot-check audit
explicitly bounded the v3 work to (a) GEO-6 CoT Step 1, (b) GEO-2 4th example, (c) GEO-4 4th
example, (d) substrate-readiness gate, (e) first-cohort posture, (f) GEO ↔ site_engine
boundary. The healthcare-substitute-reader concern was a SHIPPED residual in the v2 spot-check,
not a load-bearing edit ask.

**Verdict on this finding:** acceptable as v4 candidate. The first-cohort posture paragraph at
lines 234-243 mitigates the concern partially — "Klinika Melitus and DWF Poland are the only
two onboarded clients" makes the healthcare/service-business substrate explicit as first-cohort
context, not architectural target. The architectural-target reader is US-primary tech-savvy
founder/early-co. The substitute-readers list at §1 is now the "long-term architectural target
range" — owner-operator at a service business stays in the list because it IS a real
architectural target for an AI-native agency. But the v2 epistemological critique stands: the
list straddles two very different commissioning patterns (local-pack capture for SMB vs
AI-citation share for global SaaS) and the §C / §E / §G section emphasis required for Klinika
is nearly disjoint from Anthropic's. If empirical multi-vertical fixture validation (§8
question 10) shows the criteria produce systematically different rationale shapes across these
readers, this folds into v4. NOT a v3 ship-blocker.

## Architecture preservation audit

- **6 criteria preserved:** GEO-1 / GEO-2 / GEO-3 / GEO-4 / GEO-5 / GEO-6. ✓ No criteria
  added; no criteria removed. The ≤5-ceiling exception (GEO-6) preserved per §7 documented-
  exception discipline.
- **GEO-1 / GEO-3 / GEO-5 prose unchanged:** confirmed line-by-line. GEO-1 anchors (lines
  847-909) untouched. GEO-3 anchors (lines 1015-1068) untouched. GEO-5 anchors (lines
  1174-1249) untouched. ✓
- **GEO-2 / GEO-4 score-1 / score-0 prose unchanged outside 4th-example additions:**
  confirmed. GEO-2 score-1 (lines 922-958) preserved; Example D (959-976) is additive only.
  GEO-2 score-0 (lines 978-985) preserved. GEO-4 score-1 (lines 1082-1116) preserved; Example
  D (1117-1141) is additive only. GEO-4 score-0 (lines 1142-1147) preserved. ✓
- **12-section §A-§L bundle preserved:** the substrate-readiness gate decouples ship-time
  from spec-target without removing any section. All 12 sections (§A through §L) preserved
  at lines 264-332. ✓
- **AND-conjunction preserved:** explicit at every criterion outcome question + score-1 anchor
  + wrapper §5 (line 1398: "each criterion uses AND-conjunction language in its score-1
  anchor"). ✓
- **All 8 v2 surgical restorations preserved:** §9 prose-fold record at lines 1827-1864
  itemizes all 8 v1 folds explicitly. Verified each one against v3 prose location. ✓
- **Reference-free discipline preserved:** all 4 new examples (GEO-2 Example D, GEO-4
  Example D) hedged with "do not optimize toward this" + specific test discipline named. ✓
- **Goodhart-resistance preserved:** §6 (lines 1441-1521) unchanged; per-criterion + 7
  per-vertical + 3 v2-additional envelope-collapse-mode defenses intact. ✓

## Residual risks if v3 ships as-is

1. **§E per-vertical community-substrate map operationalization.** The substrate-readiness gate
   defers §E shipping until the §E generator lands; the generator spec must include per-
   vertical community-substrate map (Polish-Wykop vs HN/Lobsters/arxiv) as a first-class
   parameter, not an afterthought. Flag for the §E generator design pass. LOW risk for v3
   because §E does not ship structurally-required until the generator does.

2. **GEO-6 ↔ GEO-2 redundancy absorption pre-fold.** v3 preserves the prediction that GEO-6
   will likely absorb into GEO-2 in the redundancy check. The v3 spot-check raised this risk
   in concern 3; v3 does not pre-fold the disambiguation + KG-anchor + absolute-date sub-
   requirements into GEO-2 in case the absorption fires before the fold. ACCEPTABLE because
   the redundancy check is the next gate and the result is observable; if absorption fires,
   the sub-requirements get folded explicitly into GEO-2 BEFORE the absorption commits.

3. **GEO-5 ↔ GEO-2 specificity-discipline correlation.** v2 spot-check flagged the "concrete
   counts vs vague boilerplate" sub-clause in GEO-5 score-0 as risking GEO-5↔GEO-2 redundancy.
   v3 does not tighten this clause. ACCEPTABLE because the pairwise redundancy check (§8
   question 1) is the empirical gate — if the correlation lands >0.7, GEO-5 absorbs into the
   surviving criterion at the next iteration.

## Overall

The v3 surgical edits are clean. The GEO-6 CoT rewrite is the strongest edit — it inherits the
CI-4 / CI-6 v3.6 pattern explicitly and bounds the judge's scoring surface to brief-stated
disambiguation only, preserving the anchor prose while tightening the CoT enforcement. The two
4th-example additions (GEO-2 Example D, GEO-4 Example D) earn their place because they
discriminate against the exact failure modes v2 named (competitor-acknowledgment-as-omission;
vendor-vacuum citability-moat claims). The substrate-readiness gate is the right structural
response to the multi-component-bundle epistemological concern — it preserves the architectural
target while preventing the workflow from optimizing empty sections. The first-cohort posture
paragraph and the GEO ↔ site_engine boundary 4b are clean additive edits that address what v2
asked for without disturbing the rubric architecture.

The one finding NOT addressed (§1 substitute-readers-list out-of-family straddle) was
intentionally out of scope for v3 per the revision history; the partial first-cohort-posture
mitigation is sufficient for v3 ship. v4 candidates: (a) operationalize per-vertical community-
substrate map in the §E generator spec; (b) revisit substitute-readers list when empirical
fixture validation produces evidence of cross-reader rationale-shape divergence.

Ship v3.
