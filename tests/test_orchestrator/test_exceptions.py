"""Tests for agent orchestrator exceptions."""

import pytest

from src.orchestrator.exceptions import (
    AgentError,
    BudgetExceededError,
    MaxIterationsError,
)


class TestAgentErrorHierarchy:
    """Test exception inheritance."""

    def test_agent_error_is_exception(self):
        assert issubclass(AgentError, Exception)

    def test_budget_exceeded_is_agent_error(self):
        assert issubclass(BudgetExceededError, AgentError)

    def test_max_iterations_is_agent_error(self):
        assert issubclass(MaxIterationsError, AgentError)

    def test_catch_budget_exceeded_as_agent_error(self):
        """BudgetExceededError is catchable via except AgentError."""
        with pytest.raises(AgentError):
            raise BudgetExceededError(metric="cost_usd", current=1.5, limit=1.0)

    def test_catch_max_iterations_as_agent_error(self):
        """MaxIterationsError is catchable via except AgentError."""
        with pytest.raises(AgentError):
            raise MaxIterationsError(iterations=10, limit=10)


class TestBudgetExceededError:
    """Test BudgetExceededError attributes and message."""

    def test_stores_attributes(self):
        err = BudgetExceededError(metric="cost_usd", current=1.5, limit=1.0)
        assert err.metric == "cost_usd"
        assert err.current == 1.5
        assert err.limit == 1.0

    def test_message_format(self):
        err = BudgetExceededError(metric="cost_usd", current=1.5, limit=1.0)
        assert str(err) == "cost_usd exceeded: 1.5000 >= 1.0000"

    def test_message_format_small_values(self):
        err = BudgetExceededError(metric="cost_usd", current=0.0012, limit=0.001)
        assert str(err) == "cost_usd exceeded: 0.0012 >= 0.0010"


class TestMaxIterationsError:
    """Test MaxIterationsError attributes and message."""

    def test_stores_attributes(self):
        err = MaxIterationsError(iterations=10, limit=10)
        assert err.iterations == 10
        assert err.limit == 10

    def test_message_format(self):
        err = MaxIterationsError(iterations=10, limit=10)
        assert str(err) == "Agent loop did not converge after 10/10 iterations"

    def test_message_format_partial(self):
        err = MaxIterationsError(iterations=7, limit=10)
        assert str(err) == "Agent loop did not converge after 7/10 iterations"
