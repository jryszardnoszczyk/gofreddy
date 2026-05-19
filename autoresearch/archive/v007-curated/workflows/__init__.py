from __future__ import annotations

from .ad_engine import SPEC as AD_ENGINE_SPEC
from .article_engine import SPEC as ARTICLE_ENGINE_SPEC
from .competitive import SPEC as COMPETITIVE_SPEC
from .geo import SPEC as GEO_SPEC
from .image_engine import SPEC as IMAGE_ENGINE_SPEC
from .linkedin_engine import SPEC as LINKEDIN_ENGINE_SPEC
from .monitoring import SPEC as MONITORING_SPEC
from .storyboard import SPEC as STORYBOARD_SPEC
from .x_engine import SPEC as X_ENGINE_SPEC
from .specs import WorkflowSpec


WORKFLOW_SPECS: dict[str, WorkflowSpec] = {
    "geo": GEO_SPEC,
    "competitive": COMPETITIVE_SPEC,
    "monitoring": MONITORING_SPEC,
    "storyboard": STORYBOARD_SPEC,
    "x_engine": X_ENGINE_SPEC,
    "linkedin_engine": LINKEDIN_ENGINE_SPEC,
    "article_engine": ARTICLE_ENGINE_SPEC,
    "image_engine": IMAGE_ENGINE_SPEC,
    "ad_engine": AD_ENGINE_SPEC,
}


def get_workflow_spec(domain: str) -> WorkflowSpec:
    return WORKFLOW_SPECS[domain]
