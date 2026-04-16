"""Tests for PostgresPolicyRepository."""

import json
from uuid import uuid4

import pytest
import pytest_asyncio

from src.policies.repository import PolicyNameExistsError


@pytest.mark.db
class TestPolicyRepository:
    """Database tests for policy CRUD operations."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, db_conn, test_user, policy_repo):
        self.conn = db_conn
        self.user_id = test_user["id"]
        self.repo = policy_repo

    async def test_create_policy(self):
        rules = json.dumps([
            {"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}
        ])
        row = await self.repo.create(self.user_id, "Test Policy", rules)
        assert row["policy_name"] == "Test Policy"
        assert row["user_id"] == self.user_id
        assert row["id"] is not None

    async def test_create_duplicate_name_raises(self):
        rules = json.dumps([
            {"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}
        ])
        await self.repo.create(self.user_id, "Duplicate", rules)
        with pytest.raises(PolicyNameExistsError):
            await self.repo.create(self.user_id, "Duplicate", rules)

    async def test_list_includes_presets(self):
        # Create a user policy
        rules = json.dumps([
            {"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}
        ])
        await self.repo.create(self.user_id, "My Policy", rules)

        rows = await self.repo.list_for_user(self.user_id)
        names = [r["policy_name"] for r in rows]
        # Should include system presets (user_id IS NULL)
        assert "Family Safe" in names
        assert "General Audience" in names
        assert "Mature Content OK" in names
        assert "My Policy" in names
        # Presets should come first (user_id NULLS FIRST)
        preset_indices = [i for i, r in enumerate(rows) if r["user_id"] is None]
        user_indices = [i for i, r in enumerate(rows) if r["user_id"] is not None]
        if preset_indices and user_indices:
            assert max(preset_indices) < min(user_indices)

    async def test_get_by_id(self):
        rules = json.dumps([
            {"moderation_class": "gore", "max_severity": "low", "action": "flag"}
        ])
        created = await self.repo.create(self.user_id, "Get Test", rules)
        row = await self.repo.get_by_id(created["id"])
        assert row is not None
        assert row["policy_name"] == "Get Test"

    async def test_get_by_id_not_found(self):
        row = await self.repo.get_by_id(uuid4())
        assert row is None

    async def test_update_policy(self):
        rules = json.dumps([
            {"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}
        ])
        created = await self.repo.create(self.user_id, "Old Name", rules)
        new_rules = json.dumps([
            {"moderation_class": "gore", "max_severity": "medium", "action": "flag"}
        ])
        updated = await self.repo.update(
            created["id"], self.user_id, "New Name", new_rules,
        )
        assert updated is not None
        assert updated["policy_name"] == "New Name"

    async def test_update_returns_none_for_wrong_user(self):
        rules = json.dumps([
            {"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}
        ])
        created = await self.repo.create(self.user_id, "Owned", rules)
        other_user = uuid4()
        result = await self.repo.update(
            created["id"], other_user, "Stolen", rules,
        )
        assert result is None

    async def test_delete_policy(self):
        rules = json.dumps([
            {"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}
        ])
        created = await self.repo.create(self.user_id, "Delete Me", rules)
        assert await self.repo.delete(created["id"], self.user_id) is True
        assert await self.repo.delete(created["id"], self.user_id) is False

    async def test_delete_returns_false_for_missing(self):
        assert await self.repo.delete(uuid4(), self.user_id) is False

    async def test_two_users_same_name(self):
        """Two different users can create policies with the same name."""
        rules = json.dumps([
            {"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}
        ])
        # Create first user's policy
        await self.repo.create(self.user_id, "Shared Name", rules)
        # Create second user
        other_user_id = uuid4()
        email = f"test-{other_user_id.hex[:8]}@test.com"
        await self.conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)",
            other_user_id, email,
        )
        # Second user can use same name
        row = await self.repo.create(other_user_id, "Shared Name", rules)
        assert row["user_id"] == other_user_id
