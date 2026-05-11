"""Autonomous rollback / hold decision agent."""
from __future__ import annotations

import json

from ._common import make_decide


decide = make_decide(
    agent_name="rollback_agent",
    prompt_filename="rollback.md",
    allowed={"rollback", "hold"},
    format_kwargs=lambda payload: {
        "head_trajectory": json.dumps(
            payload.get("head_trajectory", {}), sort_keys=True,
        ),
        "previous_head": json.dumps(
            payload.get("previous_head", {}), sort_keys=True,
        ),
        "lane": payload.get("lane", ""),
    },
)
