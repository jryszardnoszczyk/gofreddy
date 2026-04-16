"""Tests for BoundedJsonb validation."""

import pytest
from pydantic import BaseModel, ValidationError

from src.sessions.validation import BoundedJsonb


class _TestModel(BaseModel):
    data: BoundedJsonb


class TestBoundedJsonb:

    def test_valid_dict(self):
        result = _TestModel(data={"key": "value"})
        assert result.data == {"key": "value"}

    def test_valid_list(self):
        result = _TestModel(data=[1, 2, 3])
        assert result.data == [1, 2, 3]

    def test_valid_nested_up_to_3_levels(self):
        data = {"a": {"b": {"c": "value"}}}
        result = _TestModel(data=data)
        assert result.data == data

    def test_rejects_4_levels_nesting(self):
        data = {"a": {"b": {"c": {"d": "too deep"}}}}
        with pytest.raises(ValidationError, match="jsonb_too_deep"):
            _TestModel(data=data)

    def test_rejects_oversized_payload(self):
        # Create a dict > 10KB
        data = {"key": "x" * 11_000}
        with pytest.raises(ValidationError, match="jsonb_too_large"):
            _TestModel(data=data)

    def test_exactly_at_10kb_limit(self):
        # Should pass — exactly at limit
        # 10240 bytes minus overhead for {"k":""} = ~10230 chars
        data = {"k": "x" * 10_220}
        result = _TestModel(data=data)
        assert len(result.data["k"]) == 10_220

    def test_empty_dict(self):
        result = _TestModel(data={})
        assert result.data == {}

    def test_nested_list_depth(self):
        data = {"a": [{"b": "value"}]}  # dict -> list -> dict (3 nesting containers, all < 3)
        result = _TestModel(data=data)
        assert result.data == data

    def test_deeply_nested_list_rejected(self):
        data = {"a": [{"b": [{"c": {"d": "deep"}}]}]}  # 5 levels
        with pytest.raises(ValidationError, match="jsonb_too_deep"):
            _TestModel(data=data)
