---
draft_id: cal-li-case-study
angle_id: 0
platform: linkedin
length_bracket: case_study
char_count: 2634
voice_pillar: marketing
---

[BODY]
Six weeks ago I started running gofreddy on its own marketing surfaces.

Day 1. I ran 149 always-on lenses against the gofreddy About page, the homepage, and the four landing pages we link to from LinkedIn. The audit returned 36 measured findings across 11 marketing areas. Half of them surprised me; half of them did not.

The half that did not surprise me: discoverability findings about thin technical SEO, content findings about not enough technical depth on the agency-pricing page, sales findings about a lukewarm CTA on the About page. Boring, expected, easy to fix.

The half that did surprise me: the brand and narrative pass scored my own About page lower than I would have. The lens flagged that I described gofreddy as an AI-native marketing agency in three substantively different ways across three pages. Not three angles of the same definition. Three substantively different definitions. A reader hitting the homepage would not match what they read on the About page.

Day 12. I ran the autoresearch harness on the audit pipeline itself. The harness surfaced 33 findings; the verifier confirmed 20 of them within 5 cycles. Of those 20, eight were silent-failure paths that would have shipped a broken audit to a client. Two of those broke a webhook integration in a way that swallowed the non-zero exit code from a child process. The fix was 4 lines of Python.

Day 30. I closed the loop. I rewrote the gofreddy positioning to reflect a single coherent definition. I reran the audit. The 9-axis Brand and Narrative axis went from 4.2 to 7.8. Not because the writing was better. Because the writing was now consistent with itself.

Two takeaways for the operators reading this.

First, your marketing audit is only as honest as the auditor of the auditor. We treat the harness as the QA layer for everything we ship to clients, including our own positioning. If you cannot run your audit against your own work and survive it, you cannot run it against a client's work and earn the fee.

Second, the boring findings are the most valuable. The brand-narrative coherence finding cost about ten cents of compute to surface. The cost to fix was 90 minutes of writing. The yield was that every subsequent reader gets a coherent story about what gofreddy actually does. Coherence is the marketing equivalent of a clean test suite: invisible when it works, expensive when it does not. The cycle is repeating now on the agency-pricing page and the fintech vertical landing page; I will run the lens catalog on each surface, watch the score move, and rewrite the surfaces that score below 6.5 against the brand and narrative axis.
[/BODY]

[META]
hook: Six weeks ago I started running gofreddy on its own marketing surfaces.
authority_anchor: "I ran 149 always-on lenses against the gofreddy About page, the homepage, and the four landing pages we link to from LinkedIn"
specific_number: "9-axis Brand and Narrative score went from 4.2 to 7.8"
attribution: "gofreddy harness PR #45 squash 0543d7b"
hashtags: "MarketingOps, B2BMarketing, AIagents, MarketingAudit, AgencyOps"
[/META]
