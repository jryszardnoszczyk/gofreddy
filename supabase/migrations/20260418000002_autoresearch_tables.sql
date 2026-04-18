-- =============================================================================
-- gofreddy: autoresearch backend tables
-- =============================================================================
-- Supports the autoresearch evolutionary scoring pipeline ported from freddy:
--   - evaluation_results (judge cache — mandatory for evaluate_variant)
--   - monitors + mentions + monitor_runs + monitor_source_cursors + monitor_changelog
--   - alert_rules + alert_events (alerts/delivery+evaluator ported)
--   - weekly_digests (digest lane)
--   - geo_audits (geo lane persistence)
--
-- Most blocks extracted verbatim from freddy/scripts/setup_test_db.sql.
-- weekly_digests + geo_audits are inferred from the repository SQL because
-- setup_test_db.sql never carried their CREATE TABLE (freddy ran against a
-- dev DB that had them already).
-- Idempotent (IF NOT EXISTS throughout) so safe to re-run.
-- =============================================================================

-- ─── Extensions (already created by init migration, repeat is no-op) ────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── 1. monitors (freddy setup_test_db.sql:1362-1383) ──────────────────────
CREATE TABLE IF NOT EXISTS monitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name TEXT NOT NULL CHECK (LENGTH(name) BETWEEN 1 AND 200),
    keywords TEXT[] NOT NULL DEFAULT '{}',
    boolean_query TEXT CHECK (boolean_query IS NULL OR LENGTH(boolean_query) <= 2000),
    sources TEXT[] NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    competitor_brands TEXT[] NOT NULL DEFAULT '{}',
    next_run_at TIMESTAMPTZ,
    last_user_edit_at TIMESTAMPTZ,
    last_analysis_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── 2. mentions (freddy setup_test_db.sql:1386-1446) ──────────────────────
CREATE TABLE IF NOT EXISTS mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monitor_id UUID NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
    source TEXT NOT NULL CHECK (LENGTH(source) BETWEEN 1 AND 50),
    source_id TEXT NOT NULL CHECK (LENGTH(source_id) BETWEEN 1 AND 500),
    author_handle TEXT,
    author_name TEXT,
    content TEXT NOT NULL DEFAULT '',
    url TEXT,
    published_at TIMESTAMPTZ,
    sentiment_score REAL CHECK (sentiment_score IS NULL OR sentiment_score BETWEEN -1.0 AND 1.0),
    sentiment_label TEXT CHECK (sentiment_label IS NULL OR sentiment_label IN ('positive', 'negative', 'neutral', 'mixed')),
    engagement_likes INT NOT NULL DEFAULT 0 CHECK (engagement_likes >= 0),
    engagement_shares INT NOT NULL DEFAULT 0 CHECK (engagement_shares >= 0),
    engagement_comments INT NOT NULL DEFAULT 0 CHECK (engagement_comments >= 0),
    reach_estimate INT CHECK (reach_estimate IS NULL OR reach_estimate >= 0),
    language TEXT NOT NULL DEFAULT 'en',
    geo_country TEXT CHECK (geo_country IS NULL OR LENGTH(geo_country) = 2),
    media_urls TEXT[] NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    intent TEXT,
    classified_at TIMESTAMPTZ,
    search_vector TSVECTOR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_mentions_monitor_source'
    ) THEN
        ALTER TABLE mentions ADD CONSTRAINT uq_mentions_monitor_source
            UNIQUE (monitor_id, source, source_id);
    END IF;
END $$;

-- FTS trigger
CREATE OR REPLACE FUNCTION mentions_search_vector_update() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('simple', COALESCE(NEW.author_handle, '')), 'B') ||
        setweight(to_tsvector('simple', COALESCE(NEW.author_name, '')), 'B') ||
        setweight(to_tsvector('simple', COALESCE(NEW.content, '')), 'A');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_mentions_search_vector ON mentions;
CREATE TRIGGER trg_mentions_search_vector
    BEFORE INSERT OR UPDATE OF content, author_handle, author_name
    ON mentions
    FOR EACH ROW
    EXECUTE FUNCTION mentions_search_vector_update();

CREATE INDEX IF NOT EXISTS idx_mentions_search_vector
    ON mentions USING GIN (search_vector);

-- ─── 3. monitor_source_cursors (freddy setup_test_db.sql:1449-1455) ────────
CREATE TABLE IF NOT EXISTS monitor_source_cursors (
    monitor_id UUID NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    cursor_value TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (monitor_id, source)
);

-- ─── Monitoring indexes (freddy setup_test_db.sql:1458-1468) ───────────────
CREATE INDEX IF NOT EXISTS idx_monitors_user_active
    ON monitors(user_id) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_mentions_monitor_source
    ON mentions(monitor_id, source, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_mentions_monitor_published
    ON mentions(monitor_id, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_mentions_monitor_sentiment
    ON mentions(monitor_id, sentiment_label, published_at DESC)
    WHERE sentiment_label IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mentions_source_id
    ON mentions(source, source_id);

-- Monitoring triggers
DROP TRIGGER IF EXISTS set_updated_at ON monitors;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON monitors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS set_updated_at ON monitor_source_cursors;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON monitor_source_cursors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ─── 4. monitor_runs (freddy setup_test_db.sql:1480-1497) ──────────────────
CREATE TABLE IF NOT EXISTS monitor_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monitor_id UUID NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    trigger TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    mentions_ingested INT NOT NULL DEFAULT 0,
    sources_succeeded INT NOT NULL DEFAULT 0,
    sources_failed INT NOT NULL DEFAULT 0,
    error_details JSONB
);

CREATE INDEX IF NOT EXISTS idx_monitor_runs_monitor_started
    ON monitor_runs (monitor_id, started_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_monitor_runs_one_running_per_monitor
    ON monitor_runs (monitor_id) WHERE status = 'running';

-- ─── 5. alert_rules (freddy setup_test_db.sql:1500-1520) ───────────────────
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monitor_id UUID NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rule_type TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    webhook_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    cooldown_minutes INT NOT NULL DEFAULT 0,
    last_triggered_at TIMESTAMPTZ,
    consecutive_failures INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_rules_monitor ON alert_rules (monitor_id);
CREATE INDEX IF NOT EXISTS idx_alert_rules_user ON alert_rules (user_id);

DROP TRIGGER IF EXISTS set_updated_at ON alert_rules;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON alert_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ─── 6. alert_events (freddy setup_test_db.sql:1523-1538) ──────────────────
CREATE TABLE IF NOT EXISTS alert_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    monitor_id UUID NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    condition_summary TEXT,
    payload JSONB NOT NULL DEFAULT '{}',
    delivery_status TEXT NOT NULL DEFAULT 'pending',
    delivery_attempts INT NOT NULL DEFAULT 0,
    last_delivery_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_events_monitor_triggered
    ON alert_events (monitor_id, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_events_rule ON alert_events (rule_id);

-- ─── 7. monitor_changelog (freddy setup_test_db.sql:1541-1555) ─────────────
CREATE TABLE IF NOT EXISTS monitor_changelog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monitor_id UUID NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
    change_type TEXT NOT NULL,
    change_detail JSONB NOT NULL DEFAULT '{}',
    rationale TEXT,
    autonomy_level TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    applied_by TEXT,
    analysis_run_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_monitor_changelog_monitor_status
    ON monitor_changelog (monitor_id, status);

-- ─── 8. weekly_digests (inferred from src/monitoring/repository.py:1507-1591)
-- Columns inferred from INSERT INTO weekly_digests + _row_to_weekly_digest.
-- The freddy/supabase/migrations/20260413000001_weekly_digests_unique.sql
-- migration adds the UNIQUE (monitor_id, week_ending) constraint — inlined here.
CREATE TABLE IF NOT EXISTS weekly_digests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monitor_id UUID NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    week_ending DATE NOT NULL,
    stories JSONB NOT NULL DEFAULT '[]'::jsonb,
    executive_summary TEXT,
    action_items JSONB NOT NULL DEFAULT '[]'::jsonb,
    dqs_score DOUBLE PRECISION,
    iteration_count INT NOT NULL DEFAULT 1,
    avg_story_delta DOUBLE PRECISION,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    digest_markdown TEXT,
    CONSTRAINT weekly_digests_monitor_week_key UNIQUE (monitor_id, week_ending)
);

CREATE INDEX IF NOT EXISTS idx_weekly_digests_monitor_week
    ON weekly_digests (monitor_id, week_ending DESC);

-- ─── 9. geo_audits (inferred from src/geo/repository.py) ───────────────────
-- Columns inferred from INSERT/SELECT statements + update_completed signature.
-- site_link_graph JSONB added for update_link_graph() method.
CREATE TABLE IF NOT EXISTS geo_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'complete', 'error')),
    overall_score DOUBLE PRECISION,
    report_md TEXT,
    findings JSONB,
    citations JSONB,
    opportunities JSONB,
    optimized_content TEXT,
    keywords TEXT[],
    site_link_graph JSONB,
    error TEXT,
    cost_usd DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_geo_audits_user_created
    ON geo_audits (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_geo_audits_status
    ON geo_audits (status) WHERE status IN ('pending', 'processing');

DROP TRIGGER IF EXISTS set_updated_at ON geo_audits;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON geo_audits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ─── 10. evaluation_results (freddy setup_test_db.sql:1687-1708) ───────────
-- Judge ensemble cache. content_hash is 64-char SHA256 after commit d2ba273
-- dropped the 16-char truncation.
CREATE TABLE IF NOT EXISTS evaluation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id TEXT,
    domain TEXT NOT NULL,
    variant_id TEXT,
    domain_score DOUBLE PRECISION NOT NULL,
    grounding_score DOUBLE PRECISION,
    structural_passed BOOLEAN,
    length_factor DOUBLE PRECISION,
    dimension_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    rubric_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_eval_results_content_hash_rubric
    ON evaluation_results (content_hash, rubric_version);
CREATE INDEX IF NOT EXISTS idx_eval_results_campaign
    ON evaluation_results (campaign_id, created_at);
CREATE INDEX IF NOT EXISTS idx_eval_results_user
    ON evaluation_results (user_id, created_at);

-- =============================================================================
-- DONE
-- =============================================================================
