"""Autonomous promote / reject decision agent."""
from __future__ import annotations

import json

from ._common import make_decide


decide = make_decide(
    agent_name="promotion_agent",
    prompt_filename="promotion.md",
    allowed={"promote", "reject"},
    format_kwargs=lambda payload: {
        "candidate_scores": json.dumps(
            payload.get("candidate_scores", {}), sort_keys=True,
        ),
        "head_scores": json.dumps(
            payload.get("head_scores", {}), sort_keys=True,
        ),
        "lane": payload.get("lane", ""),
    },
)
