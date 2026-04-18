from __future__ import annotations

from .session_eval_common import SessionEvalSpec
from .session_eval_competitive import SPEC as COMPETITIVE_SPEC
from .session_eval_geo import SPEC as GEO_SPEC
from .session_eval_monitoring import SPEC as MONITORING_SPEC
from .session_eval_storyboard import SPEC as STORYBOARD_SPEC


SESSION_EVAL_SPECS: dict[str, SessionEvalSpec] = {
    "geo": GEO_SPEC,
    "competitive": COMPETITIVE_SPEC,
    "monitoring": MONITORING_SPEC,
    "storyboard": STORYBOARD_SPEC,
}


def get_session_eval_spec(domain: str) -> SessionEvalSpec:
    return SESSION_EVAL_SPECS[domain]
