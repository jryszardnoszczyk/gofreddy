"""Tests for PolicyService business logic."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.tiers import Tier
from src.policies.models import BrandPolicyCreate, PolicyRule
from src.policies.service import (
    PolicyNotFoundError,
    PolicyService,
    PresetModificationError,
    SEVERITY_ORDER,
    TierRestrictedClassError,
)
from src.schemas import ModerationClass, Severity


def _make_mock_repo():
    return AsyncMock()


def _make_row(*, user_id=None, policy_name="Test", rules=None, policy_id=None):
    """Create a mock DB row dict."""
    row = {
        "id": policy_id or uuid4(),
        "user_id": user_id,
        "policy_name": policy_name,
        "rules": rules or [{"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}],
        "created_at": MagicMock(),
        "updated_at": MagicMock(),
    }
    return row


class TestSeverityOrder:
    def test_severity_order_exists(self):
        assert SEVERITY_ORDER["none"] == 0
        assert SEVERITY_ORDER["low"] == 1
        assert SEVERITY_ORDER["medium"] == 2
        assert SEVERITY_ORDER["high"] == 3
        assert SEVERITY_ORDER["critical"] == 4


class TestCreatePolicy:
    @pytest.mark.asyncio
    async def test_create_validates_tier_classes_free(self):
        """FREE user with PRO-only class raises TierRestrictedClassError."""
        repo = _make_mock_repo()
        service = PolicyService(repository=repo)
        body = BrandPolicyCreate(
            policy_name="Bad Policy",
            rules=[PolicyRule(
                moderation_class=ModerationClass.NAZI_SYMBOLS,  # PRO-only
                max_severity=Severity.NONE,
                action="block",
            )],
        )
        with pytest.raises(TierRestrictedClassError):
            await service.create_policy(uuid4(), Tier.FREE, body)

    @pytest.mark.asyncio
    async def test_create_pro_user_all_classes(self):
        """PRO user can use any moderation class."""
        repo = _make_mock_repo()
        user_id = uuid4()
        repo.create.return_value = _make_row(user_id=user_id, policy_name="Pro Policy")
        service = PolicyService(repository=repo)
        body = BrandPolicyCreate(
            policy_name="Pro Policy",
            rules=[PolicyRule(
                moderation_class=ModerationClass.NAZI_SYMBOLS,
                max_severity=Severity.NONE,
                action="block",
            )],
        )
        result = await service.create_policy(user_id, Tier.PRO, body)
        assert result.policy_name == "Pro Policy"
        repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_free_user_core_class_ok(self):
        """FREE user can use core moderation classes."""
        repo = _make_mock_repo()
        user_id = uuid4()
        repo.create.return_value = _make_row(user_id=user_id, policy_name="Free OK")
        service = PolicyService(repository=repo)
        body = BrandPolicyCreate(
            policy_name="Free OK",
            rules=[PolicyRule(
                moderation_class=ModerationClass.HATE_SPEECH,  # core class
                max_severity=Severity.NONE,
                action="block",
            )],
        )
        result = await service.create_policy(user_id, Tier.FREE, body)
        assert result.policy_name == "Free OK"


class TestUpdatePolicy:
    @pytest.mark.asyncio
    async def test_update_rejects_preset(self):
        """Preset policy (user_id=None) cannot be updated."""
        repo = _make_mock_repo()
        repo.update.return_value = None
        repo.get_user_id_by_id.return_value = "preset"
        service = PolicyService(repository=repo)
        body = BrandPolicyCreate(
            policy_name="Modified",
            rules=[PolicyRule(
                moderation_class=ModerationClass.HATE_SPEECH,
                max_severity=Severity.NONE,
                action="block",
            )],
        )
        with pytest.raises(PresetModificationError):
            await service.update_policy(uuid4(), Tier.PRO, uuid4(), body)

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        """Non-existent policy returns PolicyNotFoundError."""
        repo = _make_mock_repo()
        repo.update.return_value = None
        repo.get_user_id_by_id.return_value = None
        service = PolicyService(repository=repo)
        body = BrandPolicyCreate(
            policy_name="Ghost",
            rules=[PolicyRule(
                moderation_class=ModerationClass.HATE_SPEECH,
                max_severity=Severity.NONE,
                action="block",
            )],
        )
        with pytest.raises(PolicyNotFoundError):
            await service.update_policy(uuid4(), Tier.PRO, uuid4(), body)


class TestDeletePolicy:
    @pytest.mark.asyncio
    async def test_delete_rejects_preset(self):
        """Preset policy cannot be deleted."""
        repo = _make_mock_repo()
        repo.delete.return_value = False
        repo.get_user_id_by_id.return_value = "preset"
        service = PolicyService(repository=repo)
        with pytest.raises(PresetModificationError):
            await service.delete_policy(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """Non-existent policy returns PolicyNotFoundError."""
        repo = _make_mock_repo()
        repo.delete.return_value = False
        repo.get_user_id_by_id.return_value = None
        service = PolicyService(repository=repo)
        with pytest.raises(PolicyNotFoundError):
            await service.delete_policy(uuid4(), uuid4())


class TestGetPolicy:
    @pytest.mark.asyncio
    async def test_get_returns_404_for_other_users_policy(self):
        """Other user's custom policy returns PolicyNotFoundError (not 403)."""
        repo = _make_mock_repo()
        other_user = uuid4()
        repo.get_by_id.return_value = _make_row(user_id=other_user, policy_name="Private")
        service = PolicyService(repository=repo)
        with pytest.raises(PolicyNotFoundError):
            await service.get_policy(uuid4(), uuid4())  # different user

    @pytest.mark.asyncio
    async def test_get_preset_visible_to_all(self):
        """Presets (user_id=None) are visible to any user."""
        repo = _make_mock_repo()
        repo.get_by_id.return_value = _make_row(user_id=None, policy_name="Preset")
        service = PolicyService(repository=repo)
        result = await service.get_policy(uuid4(), uuid4())
        assert result.is_preset is True


class TestListPolicies:
    @pytest.mark.asyncio
    async def test_list_returns_presets_first(self):
        """Presets appear before user policies in the list."""
        repo = _make_mock_repo()
        user_id = uuid4()
        repo.list_for_user.return_value = [
            _make_row(user_id=None, policy_name="Preset A"),
            _make_row(user_id=user_id, policy_name="User B"),
        ]
        service = PolicyService(repository=repo)
        result = await service.list_policies(user_id)
        assert result[0].is_preset is True
        assert result[1].is_preset is False


class TestDuplicateModerationClass:
    def test_duplicate_moderation_class_rejected(self):
        """Duplicate moderation_class in rules raises validation error."""
        with pytest.raises(ValueError, match="Duplicate moderation_class"):
            BrandPolicyCreate(
                policy_name="Bad",
                rules=[
                    PolicyRule(
                        moderation_class=ModerationClass.HATE_SPEECH,
                        max_severity=Severity.NONE,
                        action="block",
                    ),
                    PolicyRule(
                        moderation_class=ModerationClass.HATE_SPEECH,
                        max_severity=Severity.LOW,
                        action="flag",
                    ),
                ],
            )
