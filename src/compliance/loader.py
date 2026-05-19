"""Reviewer-assist checklist loader."""

from __future__ import annotations

from pathlib import Path

import yaml

from src.compliance.schema import ComplianceRuleSet


_REPO_ROOT = Path(__file__).resolve().parents[2]


class ChecklistNotFoundError(FileNotFoundError):
    """Raised when reviewer_assist/checklists/<name>.yaml does not exist."""


def _checklist_yaml_path(name: str) -> Path:
    """Resolve a checklist name to its YAML path.

    Both real checklists (`<name>.yaml`) and placeholder checklists
    (`_placeholder_<name>.yaml`) live in the same directory; the loader
    prefers the real file when both exist (after U16/U17 authoring),
    falls back to the placeholder otherwise.
    """
    base = _REPO_ROOT / "reviewer_assist" / "checklists"
    real = base / f"{name}.yaml"
    if real.is_file():
        return real
    placeholder = base / f"_placeholder_{name}.yaml"
    if placeholder.is_file():
        return placeholder
    return real  # Will fail the existence check at the caller; lets the
                 # error message reference the canonical (non-placeholder)
                 # path the operator should create.


def load_rule_set(name: str) -> ComplianceRuleSet:
    """Load + validate ``reviewer_assist/checklists/<name>.yaml`` (or its
    ``_placeholder_<name>.yaml`` sibling) into a frozen ``ComplianceRuleSet``.

    Raises:
        ChecklistNotFoundError: when neither the real nor placeholder file
            exists.
        pydantic.ValidationError: when the YAML fails schema validation.
        yaml.YAMLError: when the YAML is malformed.
    """
    yaml_path = _checklist_yaml_path(name)
    if not yaml_path.is_file():
        raise ChecklistNotFoundError(
            f"reviewer_assist/checklists/{name}.yaml (or "
            f"_placeholder_{name}.yaml) not found. Author the YAML or "
            f"verify the checklist name spelling."
        )

    raw = yaml.safe_load(yaml_path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(
            f"reviewer_assist/checklists/{yaml_path.name} must contain a "
            f"mapping at the top level (got {type(raw).__name__})."
        )

    return ComplianceRuleSet.model_validate(raw)


__all__ = [
    "ChecklistNotFoundError",
    "load_rule_set",
]
