"""Tests for PostgresAnalysisRepository — real PostgreSQL.

Test isolation: each test runs inside a transaction that rolls back on teardown.
Uses the `analysis_repo` and `db_conn` fixtures from conftest.py.
"""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import asyncpg
import pytest

from src.analysis.exceptions import IntegrityError, PoolExhaustedError
from src.analysis.models import VideoAnalysisRecord
from src.analysis.repository import PostgresAnalysisRepository


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_record(**overrides) -> VideoAnalysisRecord:
    """Create a VideoAnalysisRecord with sensible defaults."""
    defaults = {
        "id": uuid4(),
        "video_id": uuid4(),
        "cache_key": f"test:{uuid4().hex[:8]}:v1",
        "overall_safe": True,
        "overall_confidence": 0.95,
        "risks_detected": [],
        "summary": "Test summary",
        "content_categories": [],
        "moderation_flags": [],
        "sponsored_content": None,
        "processing_time_seconds": 5.5,
        "token_count": 1000,
        "error": None,
        "model_version": "1",
        "analyzed_at": datetime.now(timezone.utc),
        "analysis_cost_usd": 0.01,
    }
    defaults.update(overrides)
    return VideoAnalysisRecord(**defaults)


# ── Cache Lookup Tests ───────────────────────────────────────────────────────


@pytest.mark.db
class TestGetByCacheKey:
    @pytest.mark.asyncio
    async def test_cache_hit(self, analysis_repo, db_conn):
        """Insert a record, then fetch by cache_key — should return it."""
        record = _make_record(cache_key="tiktok:realtest:v1")
        await analysis_repo.save(record)

        result = await analysis_repo.get_by_cache_key("tiktok:realtest:v1")

        assert result is not None
        assert result.id == record.id
        assert result.cache_key == "tiktok:realtest:v1"
        assert result.overall_safe is True
        assert result.overall_confidence == 0.95

    @pytest.mark.asyncio
    async def test_cache_miss(self, analysis_repo):
        """Fetch non-existent cache_key — should return None."""
        result = await analysis_repo.get_by_cache_key("tiktok:nonexistent:v1")
        assert result is None


@pytest.mark.db
class TestGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, analysis_repo):
        """Insert a record, then fetch by ID — should return it."""
        record = _make_record()
        await analysis_repo.save(record)

        result = await analysis_repo.get_by_id(record.id)

        assert result is not None
        assert result.id == record.id
        assert result.summary == "Test summary"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, analysis_repo):
        """Fetch non-existent ID — should return None."""
        result = await analysis_repo.get_by_id(uuid4())
        assert result is None


# ── Save / UPSERT Tests ─────────────────────────────────────────────────────


@pytest.mark.db
class TestSave:
    @pytest.mark.asyncio
    async def test_save_success(self, analysis_repo, db_conn):
        """Save a new record — should be persisted in the DB."""
        record = _make_record(cache_key="save:success:v1")
        result = await analysis_repo.save(record)

        assert result.id == record.id

        # Verify directly in DB
        row = await db_conn.fetchrow(
            "SELECT * FROM video_analysis WHERE id = $1", record.id
        )
        assert row is not None
        assert row["cache_key"] == "save:success:v1"
        assert row["overall_safe"] is True

    @pytest.mark.asyncio
    async def test_upsert_updates_on_conflict(self, analysis_repo, db_conn):
        """Save same cache_key twice — second save should UPDATE, not duplicate."""
        cache_key = f"upsert:test:{uuid4().hex[:8]}"
        record1 = _make_record(cache_key=cache_key, summary="First save")
        await analysis_repo.save(record1)

        # Save again with same cache_key but different data
        record2 = _make_record(cache_key=cache_key, summary="Updated save", overall_safe=False)
        saved2 = await analysis_repo.save(record2)

        # Should have exactly one row with this cache_key
        count = await db_conn.fetchval(
            "SELECT count(*) FROM video_analysis WHERE cache_key = $1", cache_key
        )
        assert count == 1
        # Repository must return the persisted row ID (existing row on conflict).
        assert saved2.id == record1.id

        # The updated values should be persisted
        result = await analysis_repo.get_by_cache_key(cache_key)
        assert result is not None
        assert result.overall_safe is False

    @pytest.mark.asyncio
    async def test_save_with_risks_and_categories(self, analysis_repo, db_conn):
        """Save a record with JSONB data — verify round-trip."""
        record = _make_record(
            risks_detected=[{"category": "violence", "severity": "medium"}],
            content_categories=[{"vertical": "entertainment", "sub_category": "comedy"}],
            moderation_flags=["violence_mild"],
        )
        await analysis_repo.save(record)

        result = await analysis_repo.get_by_cache_key(record.cache_key)
        assert result is not None
        assert len(result.risks_detected) == 1
        assert result.risks_detected[0]["category"] == "violence"
        assert len(result.content_categories) == 1
        assert result.moderation_flags == ["violence_mild"]


# ── Connection Pool Tests ────────────────────────────────────────────────────


@pytest.mark.db
class TestAcquireConnection:
    @pytest.mark.asyncio
    async def test_acquire_timeout(self):
        """Exhaust a tiny pool → PoolExhaustedError with real timeout."""
        # Create a pool with only 1 connection
        import os
        pool = await asyncpg.create_pool(
            dsn=os.environ["DATABASE_URL"],
            min_size=1,
            max_size=1,
        )
        try:
            repo = PostgresAnalysisRepository(pool)
            repo.ACQUIRE_TIMEOUT = 0.1  # 100ms

            # Hold the only connection
            conn = await pool.acquire()
            try:
                with pytest.raises(PoolExhaustedError) as exc_info:
                    await repo.get_by_cache_key("test")

                assert exc_info.value.pool_size == 1
                assert exc_info.value.timeout_seconds == 0.1
            finally:
                await pool.release(conn)
        finally:
            await pool.close()


# ── VideoAnalysisRecord Model Tests (pure logic, no DB needed) ───────────────


class TestVideoAnalysisRecord:
    def test_frozen(self):
        """Test record is immutable."""
        record = _make_record()
        with pytest.raises(AttributeError):
            record.overall_safe = False  # type: ignore

    def test_from_row(self):
        """Test creating record from database row dict."""
        row = {
            "id": uuid4(),
            "video_id": uuid4(),
            "cache_key": "tiktok:abc:v1",
            "overall_safe": False,
            "overall_confidence": 0.5,
            "risks_detected": [{"category": "violence"}],
            "summary": "Violence detected",
            "content_categories": [{"vertical": "entertainment", "sub_category": "comedy"}],
            "moderation_flags": [],
            "sponsored_content": None,
            "processing_time_seconds": 10.0,
            "token_count": 2000,
            "error": None,
            "model_version": "2",
            "analyzed_at": datetime.now(timezone.utc),
            "analysis_cost_usd": 0.02,
        }

        record = VideoAnalysisRecord.from_row(row)

        assert record.cache_key == "tiktok:abc:v1"
        assert record.overall_safe is False
        assert record.risks_detected == [{"category": "violence"}]
        assert record.summary == "Violence detected"
        assert len(record.content_categories) == 1

    def test_to_video_analysis(self):
        """Test converting record to VideoAnalysis schema."""
        from src.schemas import VideoAnalysis

        record = _make_record(
            overall_safe=True,
            overall_confidence=0.9,
            summary="Safe video",
            processing_time_seconds=5.0,
            token_count=500,
        )

        analysis = record.to_video_analysis()

        assert isinstance(analysis, VideoAnalysis)
        assert analysis.overall_safe is True
        assert analysis.overall_confidence == 0.9
        assert analysis.processing_time_seconds == 5.0
        assert analysis.token_count == 500
        assert analysis.summary == "Safe video"
