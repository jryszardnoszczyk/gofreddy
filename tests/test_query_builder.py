"""Tests for the shared query builder (PR-078, Task 1)."""

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

import pytest

from src.monitoring.query_builder import build_monitor_query


@dataclass(frozen=True, slots=True)
class FakeMonitor:
    """Minimal monitor-like object for testing."""
    boolean_query: str | None = None
    keywords: list[str] | None = None


class TestBuildMonitorQuery:
    def test_boolean_query_priority(self):
        """Boolean query takes precedence over keywords."""
        m = FakeMonitor(boolean_query="Nike AND shoes", keywords=["Nike", "Just Do It"])
        assert build_monitor_query(m) == "Nike AND shoes"

    def test_multi_keyword_or_join(self):
        """Multiple keywords are joined with OR."""
        m = FakeMonitor(keywords=["Nike", "Just Do It", "nike.com"])
        assert build_monitor_query(m) == "Nike OR Just Do It OR nike.com"

    def test_single_keyword_passthrough(self):
        """Single keyword is returned as-is."""
        m = FakeMonitor(keywords=["Nike"])
        assert build_monitor_query(m) == "Nike"

    def test_empty_keywords_returns_empty(self):
        """Empty keywords list returns empty string."""
        m = FakeMonitor(keywords=[])
        assert build_monitor_query(m) == ""

    def test_no_keywords_or_boolean_returns_empty(self):
        """Neither boolean_query nor keywords returns empty string."""
        m = FakeMonitor()
        assert build_monitor_query(m) == ""

    def test_special_chars_preserved(self):
        """Special characters in keywords are preserved for sanitizer to handle."""
        m = FakeMonitor(keywords=["C++", "C#", "@mentions"])
        result = build_monitor_query(m)
        assert "C++" in result
        assert "C#" in result

    def test_boolean_query_empty_string_treated_as_falsy(self):
        """Empty boolean_query falls through to keywords."""
        m = FakeMonitor(boolean_query="", keywords=["Nike"])
        assert build_monitor_query(m) == "Nike"
