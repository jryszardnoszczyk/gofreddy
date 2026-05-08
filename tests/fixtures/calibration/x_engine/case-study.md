---
draft_id: cal-x-case-study
angle_id: 0
platform: x
length_bracket: case_study
char_count: 1347
voice_pillar: harness-engineering
---

[BODY]
Last month the gofreddy harness ran a multi-cycle audit on its own marketing-audit pipeline. It surfaced 33 actionable findings. After 5 cycles the verifier had confirmed 20 of them.

Cycle 1 was the loudest. The verifier flagged 8 silent-failure paths that would have shipped to production. Two of them caused a webhook collision that swallowed the non-zero exit code from a child process. The fix was 4 lines of Python.

Cycle 3 surfaced something I did not expect. A stale-clear cache in the F4 short-circuit. The harness had been running on yesterday's intent classification for 9 hours without anyone noticing. Cost: nothing. Risk: every run silently invalid. The kind of bug a human review would never spot because the surface output looked right.

Cycle 5 cleaned up the long tail. Most cycle-5 fixes were about the audit's authoring style. Case-mangled labels. An anemic Brand and Narrative section. A phantom Monitoring score that displayed when the section had been pruned. Boring fixes, but also the difference between a finding the user trusts and one they ignore.

The story is not "AI fixes its own bugs." The real story is more useful. A verifier that runs cheaply enough to fire 5 times against the same pipeline finds bugs no one would have hand-debugged. 47 hours of agent time led to one config change that cleaned all of it up.
[/BODY]

[META]
hook: Last month the gofreddy harness ran a multi-cycle audit on its own marketing-audit pipeline.
authority_anchor: "It surfaced 33 actionable findings. After 5 cycles the verifier had confirmed 20 of them."
specific_number: "33 actionable findings, 20 verified, 47 hours of agent time"
attribution: "gofreddy harness PR #45 squash 0543d7b"
[/META]
