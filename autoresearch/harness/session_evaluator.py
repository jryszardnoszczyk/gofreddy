"""Frozen evaluator templates and decision rules for session critique.

Extracted from archive/v001/scripts/evaluate_session.py (Unit 13, R21).
These constants and functions are infrastructure that the *evaluator* uses
to build critique prompts and compute KEEP/REWORK decisions.  They are
intentionally separated from the evolvable domain logic so that the
evolution proposer's workspace never contains them.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
AUTORESEARCH_DIR = HARNESS_DIR.parent
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))


DEFAULT_PASS_THRESHOLD = 0.5
HARD_FAIL_THRESHOLD = 0.5


def compute_weighted_failure_count(failed: list) -> int:
    """Double-weight failures with score <= HARD_FAIL_THRESHOLD."""
    return sum(2 if float(r.get("score", 0) or 0) <= HARD_FAIL_THRESHOLD - 1e-9 else 1 for r in failed)


GRADIENT_CRITIQUE_TEMPLATE = """\
You are an external session critique judge for a {domain_name} artifact.

Evaluate ONLY this criterion:

## Criterion: {criterion_id}
{criterion_definition}

{cross_item_context}

Score the artifact on a 1-5 scale:
- 1 = clear failure
- 2 = mostly fails
- 3 = mixed or borderline
- 4 = solid pass
- 5 = exceptional pass

Use the source data and content supplied separately. Keep the reasoning concise and quote short evidence from the artifact when possible.
"""


def build_critique_prompt(
    domain_name: str,
    criterion_id: str,
    criterion_definition: str,
    cross_item_context: str | None,
) -> str:
    """Format the gradient critique template for a single criterion.

    Parameters
    ----------
    domain_name:
        Human-readable domain name (e.g. "geo", "competitive").
    criterion_id:
        Unique criterion identifier.
    criterion_definition:
        Full text of the criterion rubric.
    cross_item_context:
        Prior-item comparison block, or *None* if not applicable.

    Returns
    -------
    str
        The fully formatted prompt string.
    """
    context_block = (
        cross_item_context
        or "No prior-item comparison context is available for this criterion."
    )
    return GRADIENT_CRITIQUE_TEMPLATE.format(
        domain_name=domain_name,
        criterion_id=criterion_id,
        criterion_definition=criterion_definition,
        cross_item_context=context_block,
    )


def compute_decision_threshold(evaluated_count: int) -> int:
    """Return the minimum number of failures that triggers a REWORK decision.

    The rule is: ``threshold = math.ceil(evaluated_count / 4)``.
    If ``failed_count >= threshold``, the decision is REWORK; otherwise KEEP.

    Coupled to the outer loop's geometric-mean aggregation (evaluate_variant
    :py:func:`_geometric_mean`): because a single weak rubric drags the
    fixture score down, the inner threshold is tight enough that weak
    dimensions trigger REWORK before they reach the outer judge.
    """
    return math.ceil(evaluated_count / 4)
