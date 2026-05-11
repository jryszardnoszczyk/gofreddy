"""Autonomous canary go / fail / revise decision agent."""
from __future__ import annotations

import json

from ._common import make_decide


decide = make_decide(
    agent_name="canary_agent",
    prompt_filename="canary.md",
    allowed={"go", "fail", "revise"},
    format_kwargs=lambda payload: {
        "canary_checkpoints": json.dumps(
            payload.get("canary_checkpoints", {}), sort_keys=True,
        ),
        "variant_id": payload.get("variant_id", ""),
    },
)
