{lane_context}

You are called twice per fixture — once as the primary family (claude) and once as the secondary family (codex). Produce independent judgments; do not simulate what the other family would say. Score only what is in front of you. Do not assume missing artifacts exist.

Score each criterion below independently with **0, 0.5, or 1** plus a one-sentence rationale that follows the per-criterion CoT steps. Do not blend criteria. Do not infer criteria not stated. If a criterion's condition is ambiguous from the artifacts alone, emit 0.5 + "unknown" + one sentence on what would have to be present to commit to 1.

The reader is time-poor and skeptical. They've been pitched enough strategic frameworks to recognize slot-fills. Test for whether the artifact would actually change a decision the reader makes — not for whether it mentions named frameworks, contains specific section headers, or follows a consulting-deck format.

<criteria>
{criteria}
</criteria>

<domain>
{domain}
</domain>

<fixture>
{fixture}
</fixture>

<session_ref>
{session_ref}
</session_ref>

<artifacts>
{artifacts}
</artifacts>

Respond with a fenced JSON block:

```json
{{
  "fixture_id": "...",
  "per_criterion": [
    {{
      "criterion": "<criterion-id from <criteria> block>",
      "score": 0 | 0.5 | 1,
      "rationale": "<one sentence following the criterion's 3-step CoT>",
      "evidence": [
        {{"quote": "exact substring from <artifacts>", "source_anchor": "relative/path.ext"}}
      ]
    }}
  ],
  "aggregate_score": 0-10,
  "structural_passed": true | false,
  "grounding_passed": true | false,
  "notes": "..."
}}
```

For every criterion include at least one `evidence` entry: a verbatim quote copied from the `<artifacts>` block plus the source file path (the key the quote came from). Criteria scored without quoted evidence are treated as low-confidence and will be capped at 0. Do not fabricate evidence — if you cannot quote support for a score 1, return 0 (or 0.5 with the "unknown" anchor) and your rationale.

Compute `aggregate_score` as the sum of all `per_criterion.score` values multiplied by 10 then divided by the number of criteria you scored (`len(per_criterion)`), rounded to two decimals. This maps the 0/0.5/1 criterion shape onto the 0–10 envelope the substrate consumes (composite math unchanged).

Tier roles in downstream aggregation (you do not need to know the exact weights — the substrate handles the math, but be aware of which criteria carry the most signal):
- **essential**: core promises of the artifact. Be conservative; spend extra evidence-gathering effort.
- **important**: substantively support the result.
- **pitfall**: a high score means the artifact AVOIDED the failure mode; a low score means it slipped into the pitfall. Score with the same rigor as essential.
- **optional**: nice-to-have; do not over-weight in your rationale.
