"""Test that no TODO comments remain in production code paths."""

import pathlib

import pytest


class TestNoTodosInProduction:
    """Ensure no TODO comments in billing or webhook production code."""

    def test_no_todo_in_billing(self):
        """No TODOs in src/billing/."""
        src_dir = pathlib.Path(__file__).parent.parent.parent / "src" / "billing"
        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text()
            assert "TODO" not in content, f"TODO found in {py_file.relative_to(src_dir.parent.parent)}"

    def test_no_todo_in_webhooks(self):
        """No TODOs in webhooks router."""
        webhooks_file = pathlib.Path(__file__).parent.parent.parent / "src" / "api" / "routers" / "webhooks.py"
        content = webhooks_file.read_text()
        assert "TODO" not in content, "TODO found in src/api/routers/webhooks.py"
