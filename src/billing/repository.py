"""Database operations for billing entities."""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from asyncpg import Pool

from .models import APIKey, Subscription, UsagePeriod, User
from .tiers import Tier, get_tier_config

logger = logging.getLogger(__name__)


class BillingRepository:
    """Repository for billing database operations."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    # ─── User Operations ───────────────────────────────────────────────────

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, stripe_customer_id, supabase_user_id, created_at FROM users WHERE id = $1",
                user_id,
            )
            return self._row_to_user(row) if row else None

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email (case-insensitive)."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, stripe_customer_id, supabase_user_id, created_at "
                "FROM users WHERE LOWER(email) = LOWER($1)",
                email,
            )
            return self._row_to_user(row) if row else None

    async def get_user_by_stripe_customer(self, stripe_customer_id: str) -> User | None:
        """Get user by Stripe customer ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, stripe_customer_id, supabase_user_id, created_at FROM users WHERE stripe_customer_id = $1",
                stripe_customer_id,
            )
            return self._row_to_user(row) if row else None

    async def create_user(
        self,
        email: str,
        stripe_customer_id: str | None = None,
        supabase_user_id: str | None = None,
    ) -> User:
        """Create a new user (idempotent on supabase_user_id).

        Uses ON CONFLICT to handle race conditions when two concurrent
        requests from the same OAuth user both try to auto-create.
        Email is normalized to lowercase before storage.
        """
        normalized_email = email.lower()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, stripe_customer_id, supabase_user_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (supabase_user_id) DO NOTHING
                RETURNING id, email, stripe_customer_id, supabase_user_id, created_at
                """,
                normalized_email,
                stripe_customer_id,
                supabase_user_id,
            )
            # ON CONFLICT DO NOTHING means existing user was found — fetch it
            if row is None and supabase_user_id is not None:
                row = await conn.fetchrow(
                    "SELECT id, email, stripe_customer_id, supabase_user_id, created_at "
                    "FROM users WHERE supabase_user_id = $1",
                    supabase_user_id,
                )
            return self._row_to_user(row)

    async def get_user_by_supabase_id(self, supabase_user_id: str) -> User | None:
        """Get user by Supabase user ID (OAuth login lookup)."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, stripe_customer_id, supabase_user_id, created_at "
                "FROM users WHERE supabase_user_id = $1",
                supabase_user_id,
            )
            return self._row_to_user(row) if row else None

    async def link_supabase_user(self, user_id: UUID, supabase_user_id: str) -> bool:
        """Link an existing user to a Supabase auth identity.

        Only links if the user doesn't already have a Supabase identity.
        Returns True if the link was created, False if already linked.
        """
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE users SET supabase_user_id = $2 "
                "WHERE id = $1 AND supabase_user_id IS NULL",
                user_id,
                supabase_user_id,
            )
            return result == "UPDATE 1"

    async def update_user_stripe_customer(self, user_id: UUID, stripe_customer_id: str) -> None:
        """Update user's Stripe customer ID."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET stripe_customer_id = $2 WHERE id = $1",
                user_id,
                stripe_customer_id,
            )

    async def set_stripe_customer_if_null(self, user_id: UUID, stripe_customer_id: str) -> bool:
        """Compare-and-swap: set stripe_customer_id only if currently NULL.

        Returns True if this call set the value, False if another request won the race.
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "UPDATE users SET stripe_customer_id = $2 "
                "WHERE id = $1 AND stripe_customer_id IS NULL "
                "RETURNING id",
                user_id,
                stripe_customer_id,
            )
            return row is not None

    # ─── User Preferences ─────────────────────────────────────────────────

    async def get_preferences(self, user_id: UUID) -> dict:
        """Get user preferences from JSONB column."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT preferences FROM users WHERE id = $1",
                user_id,
            )
            if row is None or row["preferences"] is None:
                return {}
            prefs = row["preferences"]
            if isinstance(prefs, str):
                prefs = json.loads(prefs)
            return dict(prefs) if prefs else {}

    async def update_preferences(self, user_id: UUID, preferences: dict) -> dict:
        """Merge preferences into users.preferences JSONB column.

        Uses jsonb_concat (||) to merge — new keys override existing, other keys preserved.
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "UPDATE users SET preferences = COALESCE(preferences, '{}'::jsonb) || $2::jsonb "
                "WHERE id = $1 "
                "RETURNING preferences",
                user_id,
                json.dumps(preferences),
            )
            if row is None:
                return {}
            prefs = row["preferences"]
            if isinstance(prefs, str):
                prefs = json.loads(prefs)
            return dict(prefs) if prefs else {}

    # ─── API Key Operations ────────────────────────────────────────────────

    async def get_user_by_api_key(self, api_key: str) -> User | None:
        """Get user by API key (timing-safe hash comparison)."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_prefix = api_key[:12] if len(api_key) >= 12 else api_key
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT k.key_hash, u.id, u.email, u.stripe_customer_id, u.supabase_user_id, u.created_at
                FROM users u
                JOIN api_keys k ON k.user_id = u.id
                WHERE k.key_prefix = $1
                  AND k.revoked_at IS NULL
                  AND (k.expires_at IS NULL OR k.expires_at > NOW())
                """,
                key_prefix,
            )
            for row in rows:
                if hmac.compare_digest(row["key_hash"], key_hash):
                    return self._row_to_user(row)
            return None

    async def create_api_key(self, user_id: UUID, key: str, name: str | None = None) -> APIKey:
        """Create a new API key."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_prefix = key[:12]  # vi_sk_xxxx...
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO api_keys (user_id, key_hash, key_prefix, name)
                VALUES ($1, $2, $3, $4)
                RETURNING id, user_id, key_prefix, name, created_at, last_used_at, expires_at, revoked_at
                """,
                user_id,
                key_hash,
                key_prefix,
                name,
            )
            return self._row_to_api_key(row)

    async def revoke_api_key(self, key_id: UUID, user_id: UUID) -> bool:
        """Revoke an API key (ownership check via user_id)."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE api_keys SET revoked_at = NOW() WHERE id = $1 AND user_id = $2",
                key_id,
                user_id,
            )
            return result == "UPDATE 1"

    async def list_api_keys(self, user_id: UUID) -> list[APIKey]:
        """List all API keys for a user."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, user_id, key_prefix, name, created_at, last_used_at, expires_at, revoked_at
                FROM api_keys
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id,
            )
            return [self._row_to_api_key(row) for row in rows]

    async def create_api_key_atomic(
        self, user_id: UUID, key: str, name: str | None = None, max_keys: int = 10
    ) -> APIKey | None:
        """Create a new API key with atomic max-key enforcement.

        Returns None if the user already has max_keys active keys.
        Uses CTE-based INSERT to prevent TOCTOU race conditions.
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_prefix = key[:12]  # vi_sk_xxxx...
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                WITH active AS (
                    SELECT COUNT(*) AS cnt FROM api_keys
                    WHERE user_id = $1 AND revoked_at IS NULL
                )
                INSERT INTO api_keys (user_id, key_hash, key_prefix, name)
                SELECT $1, $2, $3, $4 FROM active WHERE cnt < $5
                RETURNING id, user_id, key_prefix, name, created_at, last_used_at, expires_at, revoked_at
                """,
                user_id,
                key_hash,
                key_prefix,
                name,
                max_keys,
            )
            return self._row_to_api_key(row) if row else None

    # ─── Subscription Operations ───────────────────────────────────────────

    async def get_subscription(self, user_id: UUID) -> Subscription | None:
        """Get active subscription for user."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, stripe_subscription_id, stripe_price_id, tier, status,
                       current_period_start, current_period_end, cancel_at_period_end
                FROM subscriptions
                WHERE user_id = $1 AND status IN ('active', 'trialing', 'past_due')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                user_id,
            )
            return self._row_to_subscription(row) if row else None

    async def upsert_subscription(
        self,
        user_id: UUID,
        stripe_subscription_id: str,
        stripe_price_id: str,
        tier: Tier,
        status: str,
        period_start: datetime,
        period_end: datetime,
        cancel_at_period_end: bool = False,
    ) -> Subscription:
        """Create or update subscription from Stripe webhook."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO subscriptions
                    (user_id, stripe_subscription_id, stripe_price_id, tier, status,
                     current_period_start, current_period_end, cancel_at_period_end)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (stripe_subscription_id) DO UPDATE SET
                    tier = EXCLUDED.tier,
                    status = EXCLUDED.status,
                    current_period_start = EXCLUDED.current_period_start,
                    current_period_end = EXCLUDED.current_period_end,
                    cancel_at_period_end = EXCLUDED.cancel_at_period_end
                RETURNING id, user_id, stripe_subscription_id, stripe_price_id, tier, status,
                          current_period_start, current_period_end, cancel_at_period_end
                """,
                user_id,
                stripe_subscription_id,
                stripe_price_id,
                tier.value,
                status,
                period_start,
                period_end,
                cancel_at_period_end,
            )
            return self._row_to_subscription(row)

    async def cancel_subscription(self, stripe_subscription_id: str) -> None:
        """Mark subscription as canceled."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE subscriptions SET status = 'canceled' WHERE stripe_subscription_id = $1",
                stripe_subscription_id,
            )

    # ─── Usage Period Operations ───────────────────────────────────────────

    async def get_or_create_usage_period(self, user_id: UUID, tier: Tier) -> UsagePeriod:
        """Get current usage period or create new one."""
        tier_config = get_tier_config(tier)
        now = datetime.now(timezone.utc)

        async with self._pool.acquire() as conn:
            # Try to get existing period
            row = await conn.fetchrow(
                """
                SELECT id, user_id, period_start, period_end, videos_used, videos_limit
                FROM usage_periods
                WHERE user_id = $1 AND period_start <= $2 AND period_end > $2
                """,
                user_id,
                now,
            )

            if row:
                return self._row_to_usage_period(row)

            # Create new period (monthly from now)
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Next month
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

            row = await conn.fetchrow(
                """
                INSERT INTO usage_periods (user_id, period_start, period_end, videos_limit)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, period_start) DO UPDATE SET
                    videos_limit = GREATEST(usage_periods.videos_limit, EXCLUDED.videos_limit)
                RETURNING id, user_id, period_start, period_end, videos_used, videos_limit
                """,
                user_id,
                period_start,
                period_end,
                tier_config.videos_per_month,
            )
            return self._row_to_usage_period(row)

    async def increment_usage(
        self, usage_period_id: UUID, video_count: int = 1, enforce_limit: bool = False
    ) -> UsagePeriod | None:
        """Atomically increment usage counter.

        When enforce_limit=True, returns None if increment would exceed videos_limit.
        """
        async with self._pool.acquire() as conn:
            if enforce_limit:
                row = await conn.fetchrow(
                    """
                    UPDATE usage_periods
                    SET videos_used = videos_used + $2
                    WHERE id = $1 AND videos_used + $2 <= videos_limit
                    RETURNING id, user_id, period_start, period_end, videos_used, videos_limit
                    """,
                    usage_period_id,
                    video_count,
                )
                return self._row_to_usage_period(row) if row else None
            else:
                row = await conn.fetchrow(
                    """
                    UPDATE usage_periods
                    SET videos_used = videos_used + $2
                    WHERE id = $1
                    RETURNING id, user_id, period_start, period_end, videos_used, videos_limit
                    """,
                    usage_period_id,
                    video_count,
                )
                return self._row_to_usage_period(row)

    # SECURITY FIX: Whitelist thresholds to prevent SQL injection
    _THRESHOLD_COLUMNS: dict[int, str] = {90: "notification_90_sent_at"}

    async def try_claim_notification(self, usage_period_id: UUID, threshold: int) -> bool:
        """Atomically check-and-set notification flag. Returns True if this caller won the claim."""
        column = self._THRESHOLD_COLUMNS.get(threshold)
        if column is None:
            raise ValueError(
                f"Invalid threshold: {threshold}. Must be one of {set(self._THRESHOLD_COLUMNS.keys())}"
            )
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"UPDATE usage_periods SET {column} = NOW() "
                f"WHERE id = $1 AND {column} IS NULL "
                f"RETURNING id",
                usage_period_id,
            )
            return row is not None

    async def was_notification_sent(self, usage_period_id: UUID, threshold: int) -> bool:
        """Check if notification was already sent for threshold."""
        column = self._THRESHOLD_COLUMNS.get(threshold)
        if column is None:
            raise ValueError(
                f"Invalid threshold: {threshold}. Must be one of {set(self._THRESHOLD_COLUMNS.keys())}"
            )
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT {column} FROM usage_periods WHERE id = $1",
                usage_period_id,
            )
            return row is not None and row[column] is not None

    # ─── Webhook Idempotency ───────────────────────────────────────────────

    async def mark_webhook_processed(self, stripe_event_id: str) -> None:
        """Mark webhook event as fully processed (processing → processed)."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE stripe_webhook_events
                SET status = 'processed', processed_at = NOW()
                WHERE stripe_event_id = $1 AND status = 'processing'
                """,
                stripe_event_id,
            )

    async def claim_webhook(
        self, stripe_event_id: str, event_type: str,
    ) -> bool:
        """Atomic claim: INSERT or re-claim from received/failed → processing.

        Returns True if this instance won the claim. False = duplicate/already processing.
        Increments attempt_count on re-claim.
        Auto-quarantines after 5 failed attempts.
        """
        MAX_ATTEMPTS = 5
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Try INSERT first (new webhook)
                row = await conn.fetchrow(
                    """
                    INSERT INTO stripe_webhook_events
                        (stripe_event_id, event_type, received_at, status, claimed_at,
                         attempt_count)
                    VALUES ($1, $2, NOW(), 'processing', NOW(), 1)
                    ON CONFLICT (stripe_event_id) DO NOTHING
                    RETURNING id
                    """,
                    stripe_event_id, event_type,
                )
                if row is not None:
                    return True  # New webhook, claimed

                # Try re-claim from received/failed (Stripe retry)
                row = await conn.fetchrow(
                    """
                    UPDATE stripe_webhook_events
                    SET status = CASE
                            WHEN attempt_count + 1 >= $2 THEN 'quarantined'
                            ELSE 'processing'
                        END,
                        claimed_at = NOW(),
                        attempt_count = attempt_count + 1
                    WHERE stripe_event_id = $1
                      AND status IN ('received', 'failed')
                    RETURNING id, status
                    """,
                    stripe_event_id, MAX_ATTEMPTS,
                )
                if row is not None:
                    if row["status"] == "quarantined":
                        logger.warning(
                            "Auto-quarantined webhook %s after %d attempts",
                            stripe_event_id, MAX_ATTEMPTS,
                        )
                    return row["status"] == "processing"  # False if auto-quarantined
                return False  # Already processing/processed/quarantined

    async def mark_webhook_failed(self, stripe_event_id: str, error: str) -> None:
        """Transition processing → failed with error detail."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE stripe_webhook_events
                SET status = 'failed', last_error = $2
                WHERE stripe_event_id = $1 AND status = 'processing'
                """,
                stripe_event_id, error[:1000],
            )

    async def mark_webhook_quarantined(self, stripe_event_id: str, reason: str) -> None:
        """Transition processing → quarantined."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE stripe_webhook_events
                SET status = 'quarantined', last_error = $2
                WHERE stripe_event_id = $1 AND status = 'processing'
                """,
                stripe_event_id, reason[:1000],
            )

    # ─── Row Mapping ───────────────────────────────────────────────────────

    @staticmethod
    def _row_to_user(row) -> User:
        return User(
            id=row["id"],
            email=row["email"],
            stripe_customer_id=row["stripe_customer_id"],
            supabase_user_id=row.get("supabase_user_id"),
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_api_key(row) -> APIKey:
        return APIKey(
            id=row["id"],
            user_id=row["user_id"],
            key_prefix=row["key_prefix"],
            name=row["name"],
            created_at=row["created_at"],
            last_used_at=row["last_used_at"],
            expires_at=row["expires_at"],
            is_active=row["revoked_at"] is None,
        )

    @staticmethod
    def _row_to_subscription(row) -> Subscription:
        return Subscription(
            id=row["id"],
            user_id=row["user_id"],
            stripe_subscription_id=row["stripe_subscription_id"],
            tier=Tier(row["tier"]),
            status=row["status"],
            current_period_start=row["current_period_start"],
            current_period_end=row["current_period_end"],
            cancel_at_period_end=row["cancel_at_period_end"],
        )

    @staticmethod
    def _row_to_usage_period(row) -> UsagePeriod:
        return UsagePeriod(
            id=row["id"],
            user_id=row["user_id"],
            period_start=row["period_start"],
            period_end=row["period_end"],
            videos_used=row["videos_used"],
            videos_limit=row["videos_limit"],
        )
