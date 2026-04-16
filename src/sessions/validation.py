"""Validation types for session tracking."""

import json
from typing import Annotated, Any

from pydantic import AfterValidator
from pydantic_core import PydanticCustomError

_MAX_JSONB_BYTES = 10_240  # 10KB
_MAX_DEPTH = 3


def _check_depth(value: Any, current: int, max_depth: int) -> None:
    """Check nesting depth. current=0 for the root container."""
    if isinstance(value, dict):
        if current >= max_depth:
            raise PydanticCustomError(
                "jsonb_too_deep", f"JSONB field exceeds {max_depth} levels of nesting"
            )
        for v in value.values():
            _check_depth(v, current + 1, max_depth)
    elif isinstance(value, list):
        if current >= max_depth:
            raise PydanticCustomError(
                "jsonb_too_deep", f"JSONB field exceeds {max_depth} levels of nesting"
            )
        for v in value:
            _check_depth(v, current + 1, max_depth)


def _validate_bounded_jsonb(value: dict[str, Any] | list[Any]) -> dict[str, Any] | list[Any]:
    serialized = json.dumps(value, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > _MAX_JSONB_BYTES:
        raise PydanticCustomError("jsonb_too_large", "JSONB field exceeds 10KB")
    _check_depth(value, current=0, max_depth=_MAX_DEPTH)
    return value


BoundedJsonb = Annotated[
    dict[str, Any] | list[Any], AfterValidator(_validate_bounded_jsonb)
]
