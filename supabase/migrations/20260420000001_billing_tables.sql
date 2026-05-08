-- Billing tables for storyboard-lane port (subscriptions, usage_periods,
-- stripe_webhook_events). Required by src/billing/repository.py against
-- which storyboard agents call /v1/conversations + /v1/video-projects.
--
-- Source: freddy-claude/scripts/setup_test_db.sql §4.3-4.5 (DDL kept verbatim
-- to match the asyncpg query shapes in src/billing/repository.py:269-526).
--
-- Surfaced 2026-05-08 when Gossip.Goblin storyboard fixture BLOCKED on
-- /v1/video-projects/storyboard 500 → root cause was billing_unavailable
-- (subscriptions table missing → asyncpg.exceptions.UndefinedTableError →
-- swallowed by dependencies.py:376-381 generic except → 503).

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_price_id VARCHAR(255) NOT NULL,
    tier VARCHAR(20) NOT NULL CHECK (tier IN ('free', 'pro')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'past_due', 'canceled', 'trialing', 'unpaid',
                                                    'incomplete', 'incomplete_expired', 'paused')),
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);

CREATE TABLE IF NOT EXISTS usage_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    videos_used INTEGER NOT NULL DEFAULT 0 CHECK (videos_used >= 0),
    videos_limit INTEGER NOT NULL CHECK (videos_limit > 0),
    notification_90_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, period_start)
);

CREATE INDEX IF NOT EXISTS idx_usage_periods_user_id ON usage_periods(user_id);

CREATE TABLE IF NOT EXISTS stripe_webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'received'
        CHECK (status IN ('received', 'processing', 'processed', 'failed', 'quarantined')),
    claimed_at TIMESTAMPTZ,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    payload_hash TEXT
);

CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_stripe_event_id ON stripe_webhook_events(stripe_event_id);
CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_status ON stripe_webhook_events(status);
