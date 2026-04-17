-- M1: sessions schema for agency visibility dashboard
-- Ported from freddy/scripts/setup_test_db.sql L1561-1645
-- Tweaks vs freddy:
--   * agent_sessions gains inline client_id (ON DELETE SET NULL) + idx_sessions_client_tenant
--   * Drops freddy's operator_id -> org_id RENAME block (fresh table, no legacy state)
--   * Drops freddy's DROP INDEX idx_sessions_operator block (no legacy indexes to remove)
-- Idempotent against a DB shared with freddy (where agent_sessions already
-- exists): CREATE TABLE IF NOT EXISTS is a no-op, and the ALTER TABLE below
-- adds the new client_id column without touching existing rows.

CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES users(id) ON DELETE SET NULL,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    client_name TEXT NOT NULL DEFAULT 'default',
    source TEXT NOT NULL DEFAULT 'cli',
    session_type TEXT NOT NULL DEFAULT 'ad_hoc',
    purpose TEXT,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed')),
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT now(),
    summary TEXT,
    action_count INT DEFAULT 0
        CHECK (action_count >= 0),
    total_credits INT DEFAULT 0
        CHECK (total_credits >= 0),
    transcript TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Idempotent add-column for DBs where agent_sessions pre-exists without client_id.
ALTER TABLE agent_sessions
    ADD COLUMN IF NOT EXISTS client_id UUID REFERENCES clients(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_sessions_org ON agent_sessions (org_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_client ON agent_sessions (client_name, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_client_tenant ON agent_sessions (client_id, started_at DESC)
    WHERE client_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_running ON agent_sessions (status) WHERE status = 'running';

CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_one_running_per_org_client
    ON agent_sessions (org_id, client_name)
    WHERE status = 'running';

DROP TRIGGER IF EXISTS update_agent_sessions_updated_at ON agent_sessions;
CREATE TRIGGER update_agent_sessions_updated_at
    BEFORE UPDATE ON agent_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS action_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    input_summary JSONB,
    output_summary JSONB,
    duration_ms INT,
    cost_credits INT DEFAULT 0
        CHECK (cost_credits >= 0),
    status TEXT NOT NULL DEFAULT 'success',
    error_code TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_actions_session ON action_log (session_id, created_at);

CREATE TABLE IF NOT EXISTS iteration_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    iteration_number INT NOT NULL CHECK (iteration_number >= 1),
    iteration_type TEXT,
    status TEXT NOT NULL DEFAULT 'success',
    exit_code INT,
    duration_ms INT,
    state_snapshot TEXT,
    result_entry JSONB,
    log_output TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_iterations_session ON iteration_log (session_id, iteration_number);
