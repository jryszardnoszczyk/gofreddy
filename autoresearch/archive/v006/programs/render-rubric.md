# Rendering quality rubrics — RND-1 to RND-5

Spec section A6 (`docs/plans/2026-05-07-003-self-improving-report-rendering.md`).
These five gradient-anchored prompts grade the rendered HTML report (after
screenshot capture) on five dimensions. Cross-lane: same prompts apply to
geo / competitive / monitoring / storyboard reports because all four use
the shared `.rprt-*` section-element library from `BASE_CSS`.

Calibration source: `autoresearch/archive/v009/sessions/geo/nubank/report.png`
captured 2026-05-08 from `render_report.py` first-runnable smoke test.

---

## RND-1: Typography & visual hierarchy

Evaluate the rendered report screenshot for ONE quality:
Is the visual hierarchy immediately readable from the typography alone?
Can a viewer identify the title, section heads, body, and metadata
without relying on color or layout cues?

Score 1: Type sizes are flat or inconsistent. Section heads and body copy
look the same weight. Hierarchy is invisible — viewer cannot scan.

Score 3: Type hierarchy exists but is muddled. Some sections stand out
through size, others rely on color or background. Inconsistent line-height
or weight choices reduce scanability.

Score 5: Type alone communicates structure. Display serif at the hero
contrasts cleanly with sans-serif body. Section heads are obviously
section heads. Mono-font is reserved for code and metadata. Scanning
works without color.

Cite specific evidence from the screenshot (element coordinates,
size differences). Provide your reasoning, then give your score.

---

## RND-2: Information density & breathing room

Evaluate the rendered report for ONE quality:
Is information density appropriate to the content type, with enough
breathing room that no section feels rushed AND no section feels padded?

Score 1: Either dense text walls with no whitespace OR sparse layouts
with floating fragments. Reader fatigue or boredom either way.

Score 3: Density is uneven. Some sections (findings, tables) are dense;
hero or stat-tile sections feel cramped or overpadded. Inconsistent
section margins.

Score 5: Density tracks content type. Stat-tiles and hero have generous
whitespace because they're meant to scan. Findings and tables are denser
because they reward reading. Section margins are consistent across the
report. The reader always knows where the eye should go next.

Cite specific evidence. Provide reasoning, then score.

---

## RND-3: Print/PDF readiness

Evaluate the rendered report's PDF output for ONE quality:
Does the report survive paged-media rendering without orphans, widows,
broken tables, or stat-tiles split across pages?

Score 1: Tables span page breaks awkwardly. Headings are orphaned at
the bottom of pages. Stat-tile rows split. Section margins disappear
in print mode.

Score 3: Most content reflows correctly but at least one major element
(comparison table, findings list) breaks across a page in a way that
hurts comprehension.

Score 5: Every section respects page-break-inside: avoid where it
matters. Tables either fit a page or repeat headers. Stat-tiles never
split. Hero, callouts, finding cards stay intact. Print CSS produces
a publishable PDF.

Cite the page-break behavior you observed. Provide reasoning, then score.

---

## RND-4: Design-token consistency

Evaluate the rendered report for ONE quality:
Does every visual element draw from the same design system — same color
palette, same typographic scale, same spacing tokens — without any
off-brand drift?

Score 1: Multiple type families appear (Times, Arial, Comic) without
purpose. Colors are picked ad-hoc (saturated greens next to muted blues).
Spacing varies wildly between sections.

Score 3: Most elements share tokens but at least one section uses a
different scale, color, or font that breaks the system. Probably the
result of a copy-paste from a different template.

Score 5: Every section pulls from BASE_CSS + .rprt-* primitives only.
Colors map to a 6-8 swatch palette consistently. Typography is two-three
fonts max (display serif, body sans, mono code). Spacing follows a
single scale. The whole report could be a Figma frame from one design
system.

Cite specific consistencies or breakages. Provide reasoning, then score.

---

## RND-5: Interactivity & evidence linkability

Evaluate the rendered report for ONE quality:
Can a reviewer drill from any claim to the underlying evidence —
clickable URLs to live pages, internal anchors to artifact files,
sortable tables, expandable detail panels?

Score 1: Static page with no hyperlinks. Claims float without trace.
"32 measured citations" is a number, not a link to the citation list.
Reader has no way to verify.

Score 3: Some links exist (URLs in body copy) but tables, comparison
matrices, and finding cards are static. Reader can verify some claims,
not most.

Score 5: Every URL is clickable. Comparison tables are sortable. Finding
cards expand to show full evidence. The optimized markdown is shown in
full or accessible via expandable sections. Claims are auditable in one
click. Static-only reports score below 4.

Note: This rubric only applies to HTML rendering, not PDF. PDF reports
should score N/A on RND-5.

Cite specific interactive (or non-interactive) elements. Provide
reasoning, then score.

---

Aggregate scoring: arithmetic mean of RND-1..5 (skip RND-5 for PDF-only
review). Threshold for promotion: ≥3.5 mean. Below 3.5 = render-quality
regression vs the parent variant.
