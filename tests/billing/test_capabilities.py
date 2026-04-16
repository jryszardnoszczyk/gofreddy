"""Tests for CAPABILITY_COSTS dict and billing helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.capabilities import CAPABILITY_COSTS, CapabilityCost, get_capability_cost
from src.billing.credits.exceptions import TierRestricted
from src.billing.credits.helpers import with_credit_billing
from src.billing.tiers import Tier


class TestCapabilityCosts:
    def test_all_entries_are_capability_cost(self):
        for name, cost in CAPABILITY_COSTS.items():
            assert isinstance(cost, CapabilityCost), f"{name} is not CapabilityCost"

    def test_all_credits_non_negative(self):
        for name, cost in CAPABILITY_COSTS.items():
            assert cost.credits >= 0, f"{name} has negative credits"

    def test_all_tiers_valid(self):
        for name, cost in CAPABILITY_COSTS.items():
            assert cost.min_tier in (Tier.FREE, Tier.PRO), f"{name} has invalid tier"

    def test_phase0_tools_present(self):
        phase0_tools = ["analyze_video", "get_analysis", "search", "check_usage"]
        for tool in phase0_tools:
            assert tool in CAPABILITY_COSTS, f"Missing Phase 0 tool: {tool}"

    def test_free_tools_are_zero_cost(self):
        for name in ("search", "discover_creators", "get_analysis", "check_usage"):
            assert CAPABILITY_COSTS[name].credits == 0, f"{name} should be free"

    def test_get_capability_cost_existing(self):
        cost = get_capability_cost("analyze_video")
        assert cost.credits == 5

    def test_get_capability_cost_missing(self):
        with pytest.raises(KeyError):
            get_capability_cost("nonexistent_tool")


class TestWithCreditBilling:
    @pytest.mark.asyncio
    async def test_zero_cost_skips_billing(self):
        compute_fn = AsyncMock(return_value={"results": []})
        result = await with_credit_billing(
            credit_service=None,
            billing_flags=None,
            user_id=uuid4(),
            capability_name="search",
            source_id="test",
            compute_fn=compute_fn,
        )
        assert result == {"results": []}
        compute_fn.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_billing_disabled_skips_billing(self):
        billing_flags = MagicMock()
        billing_flags.hybrid_write_enabled = False
        billing_flags.hybrid_read_enabled = False
        compute_fn = AsyncMock(return_value="ok")
        result = await with_credit_billing(
            credit_service=MagicMock(),
            billing_flags=billing_flags,
            user_id=uuid4(),
            capability_name="analyze_video",
            source_id="test",
            compute_fn=compute_fn,
        )
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_tier_enforcement_rejects_free_user(self):
        with pytest.raises(TierRestricted) as exc_info:
            await with_credit_billing(
                credit_service=None,
                billing_flags=None,
                user_id=uuid4(),
                capability_name="manage_monitor",
                source_id="test",
                compute_fn=AsyncMock(),
                user_tier=Tier.FREE,
            )
        assert exc_info.value.required_tier == Tier.PRO

    @pytest.mark.asyncio
    async def test_tier_enforcement_allows_pro_user(self):
        compute_fn = AsyncMock(return_value="ok")
        billing_flags = MagicMock()
        billing_flags.hybrid_write_enabled = False
        billing_flags.hybrid_read_enabled = False
        result = await with_credit_billing(
            credit_service=MagicMock(),
            billing_flags=billing_flags,
            user_id=uuid4(),
            capability_name="manage_monitor",
            source_id="test",
            compute_fn=compute_fn,
            user_tier=Tier.PRO,
        )
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_reserve_capture_flow(self):
        reservation = MagicMock()
        reservation.id = uuid4()
        credit_service = AsyncMock()
        credit_service.authorize_usage.return_value = reservation
        credit_service.capture_usage.return_value = MagicMock()

        billing_flags = MagicMock()
        billing_flags.hybrid_write_enabled = True
        billing_flags.hybrid_read_enabled = False

        compute_fn = AsyncMock(return_value=MagicMock(cached=False))

        await with_credit_billing(
            credit_service=credit_service,
            billing_flags=billing_flags,
            user_id=uuid4(),
            capability_name="analyze_video",
            source_id="test",
            compute_fn=compute_fn,
        )

        credit_service.authorize_usage.assert_awaited_once()
        credit_service.capture_usage.assert_awaited_once_with(
            reservation.id, units_captured=5
        )

    @pytest.mark.asyncio
    async def test_cached_result_voids_reservation(self):
        reservation = MagicMock()
        reservation.id = uuid4()
        credit_service = AsyncMock()
        credit_service.authorize_usage.return_value = reservation

        billing_flags = MagicMock()
        billing_flags.hybrid_write_enabled = True
        billing_flags.hybrid_read_enabled = False

        cached_result = MagicMock(cached=True)
        compute_fn = AsyncMock(return_value=cached_result)

        await with_credit_billing(
            credit_service=credit_service,
            billing_flags=billing_flags,
            user_id=uuid4(),
            capability_name="analyze_video",
            source_id="test",
            compute_fn=compute_fn,
        )

        credit_service.void_usage.assert_awaited_once_with(reservation.id)
        credit_service.capture_usage.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_exception_voids_reservation(self):
        reservation = MagicMock()
        reservation.id = uuid4()
        credit_service = AsyncMock()
        credit_service.authorize_usage.return_value = reservation

        billing_flags = MagicMock()
        billing_flags.hybrid_write_enabled = True
        billing_flags.hybrid_read_enabled = False

        compute_fn = AsyncMock(side_effect=RuntimeError("boom"))

        with pytest.raises(RuntimeError):
            await with_credit_billing(
                credit_service=credit_service,
                billing_flags=billing_flags,
                user_id=uuid4(),
                capability_name="analyze_video",
                source_id="test",
                compute_fn=compute_fn,
            )

        credit_service.void_usage.assert_awaited_once_with(reservation.id)

    @pytest.mark.asyncio
    async def test_void_failure_does_not_swallow_original_exception(self):
        reservation = MagicMock()
        reservation.id = uuid4()
        credit_service = AsyncMock()
        credit_service.authorize_usage.return_value = reservation
        credit_service.void_usage.side_effect = RuntimeError("void failed")

        billing_flags = MagicMock()
        billing_flags.hybrid_write_enabled = True
        billing_flags.hybrid_read_enabled = False

        compute_fn = AsyncMock(side_effect=ValueError("original error"))

        with pytest.raises(ValueError, match="original error"):
            await with_credit_billing(
                credit_service=credit_service,
                billing_flags=billing_flags,
                user_id=uuid4(),
                capability_name="analyze_video",
                source_id="test",
                compute_fn=compute_fn,
            )
