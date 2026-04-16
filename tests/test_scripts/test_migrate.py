"""Tests for migration runner — schema verification on bootstrap."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class FakeConnection:
    """Simulates asyncpg.Connection for migration tests."""

    def __init__(
        self,
        *,
        has_tracking_table: bool = True,
        applied_migrations: set[str] | None = None,
        existing_tables: set[str] | None = None,
    ) -> None:
        self.has_tracking_table = has_tracking_table
        self.applied = applied_migrations or set()
        self.existing_tables = existing_tables or set()
        self.executed: list[str] = []
        self._lock_held = False

    async def execute(self, query: str, *args) -> None:
        self.executed.append(query)
        if "pg_advisory_lock" in query:
            self._lock_held = True
        elif "pg_advisory_unlock" in query:
            self._lock_held = False

    async def fetchval(self, query: str, *args):
        if "information_schema.tables" in query and "users" in query:
            return "users" in self.existing_tables
        return None

    async def fetch(self, query: str, *args) -> list[dict]:
        if "schema_migrations" in query:
            return [{"filename": f} for f in self.applied]
        if "information_schema.tables" in query and "table_type" in query:
            return [{"table_name": t} for t in self.existing_tables]
        return []

    async def fetchrow(self, query: str, *args) -> dict | None:
        return None

    async def close(self) -> None:
        pass

    def transaction(self):
        return _FakeTransaction()


class _FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        pass


# All tables created by migrations 001 through 018
COMPLETE_TABLES = {
    "analysis_jobs", "job_videos", "audience_demographics",
    "brand_video_analysis", "users", "api_keys", "subscriptions",
    "usage_periods", "stripe_webhook_events", "trend_snapshots",
    "creators", "deepfake_analysis", "captured_stories",
    "video_analysis_access", "feedback_signals", "improvement_specs",
    "schema_migrations",  # tracking table itself
}


class TestMigrationBootstrap:
    """Tests for schema verification during bootstrap."""

    @pytest.mark.asyncio
    async def test_fresh_db_runs_migrations_normally(self) -> None:
        """Fresh DB with no tables runs all migrations."""
        conn = FakeConnection(existing_tables=set())

        with patch("asyncpg.connect", AsyncMock(return_value=conn)):
            from scripts.migrate import run_migrations

            result = await run_migrations("postgresql://test:test@localhost/test")

        # Should have executed migration SQL (not just bootstrap marks)
        migration_inserts = [
            q for q in conn.executed
            if "INSERT INTO schema_migrations" in q and "ON CONFLICT DO NOTHING" not in q
        ]
        assert len(migration_inserts) > 0 or result > 0

    @pytest.mark.asyncio
    async def test_complete_schema_bootstraps_successfully(self) -> None:
        """Complete existing schema with empty tracking → auto-marks all as applied."""
        conn = FakeConnection(
            applied_migrations=set(),
            existing_tables=COMPLETE_TABLES,
        )

        with patch("asyncpg.connect", AsyncMock(return_value=conn)):
            from scripts.migrate import run_migrations

            result = await run_migrations("postgresql://test:test@localhost/test")

        assert result == 0
        # Should have inserted ON CONFLICT DO NOTHING marks
        bootstrap_marks = [
            q for q in conn.executed if "ON CONFLICT DO NOTHING" in q
        ]
        assert len(bootstrap_marks) > 0

    @pytest.mark.asyncio
    async def test_partial_schema_exits_with_error(self) -> None:
        """Partial schema (missing tables) exits with error."""
        # Only has 'users' but missing many other tables
        partial_tables = {"users", "schema_migrations"}

        conn = FakeConnection(
            applied_migrations=set(),
            existing_tables=partial_tables,
        )

        with patch("asyncpg.connect", AsyncMock(return_value=conn)):
            from scripts.migrate import run_migrations

            with pytest.raises(SystemExit) as exc_info:
                await run_migrations("postgresql://test:test@localhost/test")

            assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_normal_operation_applies_pending(self) -> None:
        """Normal operation with populated tracking applies only pending migrations."""
        conn = FakeConnection(
            applied_migrations={"001_create_analysis_jobs.sql"},
            existing_tables=COMPLETE_TABLES,
        )

        with patch("asyncpg.connect", AsyncMock(return_value=conn)):
            from scripts.migrate import run_migrations

            result = await run_migrations("postgresql://test:test@localhost/test")

        # Should apply pending migrations (all except 001)
        assert result > 0
