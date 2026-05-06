# MA-6 — Polish + Voice Consistency

**Status:** DRAFT (master plan §6.4; JR review-iterate before manifest freeze)

## What this rubric scores

The deliverable's prose has the voice quality of a customer-facing $1K-$15K agency artifact. No AI-tell vocabulary. Voice is consistent across sections (one author, not five). Em-dash density is restrained.

This is the second hardest rubric (paired with MA-1). AI-generated text that hasn't been edited will trip this rubric in seconds.

## Banned vocabulary (auto-fail markers)

- `utilize`, `leverage`, `facilitate`, `robust`, `comprehensive`, `pivotal`, `delve`, `seamless`, `landscape`, `tapestry`, `realm`, `embark`, `harness` (verb), `unlock` (verb), `supercharge`, `empower`, `paradigm`, `holistic`, `synergize`, `transformative`
- `absolutely`, `actually`, `clearly`, `very`, `just`, `simply`, `basically`, `essentially`, `fundamentally`, `ultimately`
- `that being said`, `it's worth noting`, `at its core`, `in today's landscape`, `in the realm of`, `when it comes to`

## What "good" looks like

- Zero banned vocabulary in `findings.md`, `report.md`, `surprises.md`, `proposal.md`
- Em-dash density ≤ 1 per paragraph (use colons, semicolons, or two sentences)
- Voice is conversational-but-authoritative (specific, blunt, evidence-anchored)
- Sentences vary in length (no monoculture of medium-length declaratives)
- Reader could imagine a senior marketing operator wrote it

## What "bad" looks like

- ChatGPT-flavored phrasing throughout
- Em-dash overuse (>2 per paragraph in any section)
- Voice shifts dramatically between sections (different agents' voices not unified)
- Filler words present
- Sentences feel templated

## Score scale (0-10)

- **0-2** Multiple banned-vocab hits per page; sounds like raw LLM output
- **3-4** Some sections clean; others have AI tells; voice inconsistent
- **5-6** Most sections clean; 2-5 banned-vocab hits across full deliverable; voice mostly consistent
- **7-8** Zero banned-vocab; em-dash density restrained; voice consistent
- **9-10** Above + the prose has a recognizable editorial fingerprint (specific, blunt, evidence-anchored)

## Anchors for severity-of-MA-6-failure

- 5+ banned-vocab hits in `report.md`: severity-of-failure 3
- Voice shifts between sections (different agent voices not unified): severity-of-failure 2
- 2-3 banned-vocab hits in `findings.md`: severity-of-failure 1
- Em-dash density >2/paragraph in any section: severity-of-failure 1

## Notes for JR review

- The banned-vocab list is JR's editorial fingerprint. Add/remove items as the v1 audits ship and you discover patterns I missed.
- Consider: a separate auto-fail bar at "5+ banned hits = MA-6 collapses to ≤3 regardless of other quality" — would force editorial passes before ship.
- Sync with `judges/MA-6-judge.md`.
