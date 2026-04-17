-- =============================================================================
-- gofreddy: auth + portal schema
-- =============================================================================
-- Runs against the Supabase Postgres instance.
-- Supabase manages auth.users; we maintain our own users row keyed by supabase_user_id.
-- Idempotent: safe to run multiple times.
-- =============================================================================

-- ─── Extensions ─────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- gen_random_uuid()

-- ─── Triggers (extracted from freddy/scripts/setup_test_db.sql L105-111) ────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ─── users + api_keys (extracted verbatim from freddy/scripts/setup_test_db.sql L125-153) ─
-- ─── 4.1 users (no deps) ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) UNIQUE,
    supabase_user_id VARCHAR(255) UNIQUE,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Idempotent backfill for existing test databases that pre-date the
-- preferences column. Without this, GET /v1/preferences raises
-- `column "preferences" does not exist` and returns a bare 500 that
-- bypasses the CORS middleware in the browser's eyes.
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB NOT NULL DEFAULT '{}'::jsonb;

-- ─── 4.2 api_keys (depends on users) ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    key_prefix VARCHAR(12) NOT NULL,
    name VARCHAR(100),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    CONSTRAINT api_keys_active_check CHECK (revoked_at IS NULL OR revoked_at > created_at)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id) WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_supabase_user_id ON users(supabase_user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ─── clients (gofreddy-specific) ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT clients_slug_format CHECK (slug ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]$')
);

-- ─── user_client_memberships (many-to-many) ──────────────────────────────────
-- Roles: 'admin' (JR, full access), 'owner', 'editor', 'viewer'
CREATE TABLE IF NOT EXISTS user_client_memberships (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, client_id),
    CONSTRAINT role_valid CHECK (role IN ('admin', 'owner', 'editor', 'viewer'))
);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON user_client_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_client ON user_client_memberships(client_id);

DROP TRIGGER IF EXISTS update_clients_updated_at ON clients;
CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
