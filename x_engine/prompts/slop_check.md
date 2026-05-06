# Slop Check (final gate, deterministic)

Note: most slop detection is done in `pipeline/slop_gate.py` via regex (faster, deterministic). This prompt is only used when the deterministic gate flags ambiguous cases that need an LLM judgment call.

**Inputs:**
- `text`: the candidate tweet/thread
- `flags`: list of regex flags raised (e.g. `["em_dash", "phrase:Most people don't realize"]`)

**Your job:** decide whether the flag is a true positive (slop) or a false positive (the phrase is legitimate in this context).

**Output JSON:**
```json
{
  "verdict": "block | allow",
  "reason": "one sentence"
}
```

**Default to BLOCK.** False positives are cheap; shipping slop is expensive. Only allow when the phrase is unambiguously the right word in the sentence (rare).

Return only the JSON.
