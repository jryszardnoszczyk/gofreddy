from __future__ import annotations

from .competitive import SPEC as COMPETITIVE_SPEC
from .geo import SPEC as GEO_SPEC
from .monitoring import SPEC as MONITORING_SPEC
from .storyboard import SPEC as STORYBOARD_SPEC
from .specs import WorkflowSpec


WORKFLOW_SPECS: dict[str, WorkflowSpec] = {
    "geo": GEO_SPEC,
    "competitive": COMPETITIVE_SPEC,
    "monitoring": MONITORING_SPEC,
    "storyboard": STORYBOARD_SPEC,
}


def get_workflow_spec(domain: str) -> WorkflowSpec:
    return WORKFLOW_SPECS[domain]
