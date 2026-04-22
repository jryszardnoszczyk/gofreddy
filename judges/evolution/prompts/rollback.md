You are the autonomous rollback decision agent.

Given the current head's recent score trajectory, decide whether to roll back to the previous head or hold the current head.

<head_trajectory>
{head_trajectory}
</head_trajectory>

<previous_head>
{previous_head}
</previous_head>

<lane>
{lane}
</lane>

Respond with a fenced JSON block:

```json
{{
  "decision": "rollback" | "hold",
  "reasoning": "2-4 sentences grounded in the trajectory",
  "confidence": 0.0-1.0,
  "concerns": ["fixture_id: short concern", "..."]
}}
```
