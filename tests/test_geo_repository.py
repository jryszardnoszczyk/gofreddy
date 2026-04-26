"""Tests for GEO repository — requires real PostgreSQL."""

import pytest
from uuid import uuid4

from src.geo.repository import PostgresGeoRepository


@pytest.mark.db
class TestPostgresGeoRepository:
    """Repository CRUD tests with real database."""

    @pytest.fixture
    async def repository(self, pool):
        """Create repository with test pool."""
        return PostgresGeoRepository(pool)

    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.mark.asyncio
    async def test_create_and_get(self, repository, user_id):
        """Create an audit and retrieve it."""
        audit_id = uuid4()
        await repository.create(
            audit_id=audit_id,
            user_id=user_id,
            url="https://example.com/test",
            keywords=["cloud", "computing"],
        )

        result = await repository.get_by_id(audit_id)
        assert result is not None
        assert result["url"] == "https://example.com/test"
        assert result["status"] == "pending"
        assert result["keywords"] == ["cloud", "computing"]

    @pytest.mark.asyncio
    async def test_get_by_id_and_user(self, repository, user_id):
        """Ownership check returns result for correct user."""
        audit_id = uuid4()
        await repository.create(audit_id=audit_id, user_id=user_id, url="https://example.com")

        # Correct user
        result = await repository.get_by_id_and_user(audit_id, user_id)
        assert result is not None

        # Wrong user
        other_user = uuid4()
        result = await repository.get_by_id_and_user(audit_id, other_user)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_status(self, repository, user_id):
        """Update status transitions."""
        audit_id = uuid4()
        await repository.create(audit_id=audit_id, user_id=user_id, url="https://example.com")

        await repository.update_status(audit_id, "processing")
        result = await repository.get_by_id(audit_id)
        assert result["status"] == "processing"

        await repository.update_status(audit_id, "error", error="Timeout")
        result = await repository.get_by_id(audit_id)
        assert result["status"] == "error"
        assert result["error"] == "Timeout"

    @pytest.mark.asyncio
    async def test_update_completed(self, repository, user_id):
        """Update with completed results."""
        audit_id = uuid4()
        await repository.create(audit_id=audit_id, user_id=user_id, url="https://example.com")

        await repository.update_completed(
            audit_id=audit_id,
            overall_score=0.85,
            report_md="# GEO Audit Report\n\nScore: 85%",
            findings={"critical": 1, "important": 2},
            cost_usd=0.05,
        )

        result = await repository.get_by_id(audit_id)
        assert result["status"] == "complete"
        assert float(result["overall_score"]) == 0.85
        assert result["report_md"].startswith("# GEO Audit Report")
        assert result["findings"]["critical"] == 1

    @pytest.mark.asyncio
    async def test_list_by_user(self, repository, user_id):
        """List audits for a user."""
        for i in range(3):
            await repository.create(
                audit_id=uuid4(),
                user_id=user_id,
                url=f"https://example.com/page{i}",
            )

        results = await repository.list_by_user(user_id, limit=10)
        assert len(results) == 3

        # Newest first
        assert results[0]["url"] == "https://example.com/page2"

    @pytest.mark.asyncio
    async def test_list_pagination(self, repository, user_id):
        """List with limit and offset."""
        for i in range(5):
            await repository.create(
                audit_id=uuid4(),
                user_id=user_id,
                url=f"https://example.com/page{i}",
            )

        page1 = await repository.list_by_user(user_id, limit=2, offset=0)
        page2 = await repository.list_by_user(user_id, limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0]["url"] != page2[0]["url"]

    @pytest.mark.asyncio
    async def test_nonexistent_audit(self, repository):
        """Get nonexistent audit returns None."""
        result = await repository.get_by_id(uuid4())
        assert result is None
