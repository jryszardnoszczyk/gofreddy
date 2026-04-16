"""PostgreSQL analytics repository — account_posts, account_snapshots, performance_patterns."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from ..common.exceptions import PoolExhaustedError
from .intelligence.models_analytics import AccountPost, AccountSnapshot

logger = logging.getLogger(__name__)


def _row_to_post(row: asyncpg.Record) -> AccountPost:
    metadata = row["metadata"]
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    hashtags = list(row["hashtags"] or [])
    return AccountPost(
        id=row["id"],
        org_id=row["org_id"],
        platform=row["platform"],
        username=row["username"],
        source_id=row["source_id"],
        content=row["content"],
        published_at=row["published_at"],
        likes=row["likes"],
        shares=row["shares"],
        comments=row["comments"],
        impressions=row["impressions"],
        engagement_rate=row["engagement_rate"],
        media_type=row["media_type"],
        hashtags=hashtags,
        metadata=metadata if isinstance(metadata, dict) else {},
        created_at=row["created_at"],
    )


def _row_to_snapshot(row: asyncpg.Record) -> AccountSnapshot:
    audience_data = row["audience_data"]
    if isinstance(audience_data, str):
        audience_data = json.loads(audience_data)
    return AccountSnapshot(
        id=row["id"],
        org_id=row["org_id"],
        platform=row["platform"],
        username=row["username"],
        follower_count=row["follower_count"],
        following_count=row["following_count"],
        post_count=row["post_count"],
        engagement_rate=row["engagement_rate"],
        audience_data=audience_data if isinstance(audience_data, dict) else {},
        created_at=row["created_at"],
    )


class PostgresAnalyticsRepository:
    """Repository for account_posts, account_snapshots, and performance_patterns."""

    ACQUIRE_TIMEOUT = 5.0

    # ── account_posts ──

    _UPSERT_POSTS = """
        INSERT INTO account_posts (
            id, org_id, platform, username, source_id, content,
            published_at, likes, shares, comments, impressions,
            engagement_rate, media_type, hashtags, metadata
        )
        SELECT * FROM unnest(
            $1::uuid[], $2::uuid[], $3::text[], $4::text[], $5::text[], $6::text[],
            $7::timestamptz[], $8::int[], $9::int[], $10::int[], $11::int[],
            $12::float[], $13::text[], $14::text[][], $15::jsonb[]
        )
        ON CONFLICT (org_id, platform, source_id)
        DO UPDATE SET
            likes = EXCLUDED.likes,
            shares = EXCLUDED.shares,
            comments = EXCLUDED.comments,
            impressions = EXCLUDED.impressions,
            engagement_rate = EXCLUDED.engagement_rate,
            content = EXCLUDED.content,
            media_type = EXCLUDED.media_type,
            hashtags = EXCLUDED.hashtags,
            metadata = EXCLUDED.metadata
        RETURNING id
    """

    _GET_POSTS = """
        SELECT * FROM account_posts
        WHERE org_id = $1 AND platform = $2 AND username = $3
        ORDER BY published_at DESC NULLS LAST
        LIMIT $4 OFFSET $5
    """

    _GET_POSTS_FOR_PATTERNS = """
        SELECT * FROM account_posts
        WHERE org_id = $1 AND platform = $2 AND username = $3
        ORDER BY published_at DESC NULLS LAST
        LIMIT $4
    """

    _GET_POST_COUNT = """
        SELECT COUNT(*) FROM account_posts
        WHERE org_id = $1 AND platform = $2 AND username = $3
    """

    # ── account_snapshots ──

    _INSERT_SNAPSHOT = """
        INSERT INTO account_snapshots (
            org_id, platform, username, follower_count, following_count,
            post_count, engagement_rate, audience_data
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
    """

    _GET_SNAPSHOTS = """
        SELECT * FROM account_snapshots
        WHERE org_id = $1 AND platform = $2 AND username = $3
        ORDER BY created_at DESC
        LIMIT $4
    """

    _GET_LATEST_SNAPSHOT = """
        SELECT * FROM account_snapshots
        WHERE org_id = $1 AND platform = $2 AND username = $3
        ORDER BY created_at DESC
        LIMIT 1
    """

    # ── performance_patterns ──

    _UPSERT_PATTERNS = """
        INSERT INTO performance_patterns (org_id, platform, username, pattern_data, markdown, post_count)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (org_id, platform, username)
        DO UPDATE SET
            pattern_data = EXCLUDED.pattern_data,
            markdown = EXCLUDED.markdown,
            post_count = EXCLUDED.post_count,
            computed_at = NOW()
    """

    _GET_PATTERNS = """
        SELECT pattern_data, markdown, post_count FROM performance_patterns
        WHERE org_id = $1 AND platform = $2 AND username = $3
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def _acquire_connection(self) -> AsyncIterator[Any]:
        try:
            async with asyncio.timeout(self.ACQUIRE_TIMEOUT):
                conn = await self._pool.acquire()
        except asyncio.TimeoutError:
            raise PoolExhaustedError(
                pool_size=self._pool.get_size(),
                timeout_seconds=self.ACQUIRE_TIMEOUT,
            )
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    # ── account_posts ──

    async def upsert_posts(self, posts: list[AccountPost]) -> int:
        """Bulk upsert via unnest arrays. Returns number of rows affected."""
        if not posts:
            return 0

        ids = [p.id for p in posts]
        org_ids = [p.org_id for p in posts]
        platforms = [p.platform for p in posts]
        usernames = [p.username for p in posts]
        source_ids = [p.source_id for p in posts]
        contents = [p.content for p in posts]
        published_ats = [p.published_at for p in posts]
        likes = [p.likes for p in posts]
        shares = [p.shares for p in posts]
        comments = [p.comments for p in posts]
        impressions = [p.impressions for p in posts]
        engagement_rates = [p.engagement_rate for p in posts]
        media_types = [p.media_type for p in posts]
        hashtags = [p.hashtags for p in posts]
        metadatas = [json.dumps(p.metadata) for p in posts]

        async with self._acquire_connection() as conn:
            result = await conn.fetch(
                self._UPSERT_POSTS,
                ids, org_ids, platforms, usernames, source_ids, contents,
                published_ats, likes, shares, comments, impressions,
                engagement_rates, media_types, hashtags, metadatas,
            )
            return len(result)

    async def get_posts(
        self, org_id: UUID, platform: str, username: str,
        *, limit: int = 200, offset: int = 0,
    ) -> list[AccountPost]:
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._GET_POSTS, org_id, platform, username, limit, offset)
            return [_row_to_post(r) for r in rows]

    async def get_posts_for_patterns(
        self, org_id: UUID, platform: str, username: str,
        *, max_posts: int = 500,
    ) -> list[AccountPost]:
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._GET_POSTS_FOR_PATTERNS, org_id, platform, username, max_posts)
            return [_row_to_post(r) for r in rows]

    async def get_post_count(
        self, org_id: UUID, platform: str, username: str,
    ) -> int:
        async with self._acquire_connection() as conn:
            return await conn.fetchval(self._GET_POST_COUNT, org_id, platform, username)

    # ── account_snapshots ──

    async def insert_snapshot(self, snapshot: AccountSnapshot) -> AccountSnapshot:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._INSERT_SNAPSHOT,
                snapshot.org_id, snapshot.platform, snapshot.username,
                snapshot.follower_count, snapshot.following_count,
                snapshot.post_count, snapshot.engagement_rate,
                json.dumps(snapshot.audience_data),
            )
            return _row_to_snapshot(row)

    async def get_snapshots(
        self, org_id: UUID, platform: str, username: str,
        *, limit: int = 52,
    ) -> list[AccountSnapshot]:
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._GET_SNAPSHOTS, org_id, platform, username, limit)
            return [_row_to_snapshot(r) for r in rows]

    async def get_latest_snapshot(
        self, org_id: UUID, platform: str, username: str,
    ) -> AccountSnapshot | None:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_LATEST_SNAPSHOT, org_id, platform, username)
            return _row_to_snapshot(row) if row else None

    # ── performance_patterns ──

    async def upsert_patterns(
        self, org_id: UUID, platform: str, username: str,
        pattern_data: dict[str, Any], markdown: str, post_count: int,
    ) -> None:
        async with self._acquire_connection() as conn:
            await conn.execute(
                self._UPSERT_PATTERNS,
                org_id, platform, username,
                json.dumps(pattern_data, default=str), markdown, post_count,
            )

    async def get_patterns(
        self, org_id: UUID, platform: str, username: str,
    ) -> tuple[dict[str, Any], str, int] | None:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_PATTERNS, org_id, platform, username)
            if not row:
                return None
            pattern_data = row["pattern_data"]
            if isinstance(pattern_data, str):
                pattern_data = json.loads(pattern_data)
            return (pattern_data, row["markdown"], row["post_count"])
