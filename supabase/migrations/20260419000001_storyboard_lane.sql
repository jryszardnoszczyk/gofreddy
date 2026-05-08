-- =============================================================================
-- gofreddy: storyboard lane backend tables
-- =============================================================================
-- Additive/idempotent schema for the autoresearch storyboard lane:
-- conversations, video analysis cache/access, creative patterns, video projects,
-- preview scene state, and the minimal generation_jobs surface referenced by
-- VideoProjectRepository.latest_generation_job().
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Creators + Analysis Cache

CREATE TABLE IF NOT EXISTS creators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL CHECK (platform IN ('tiktok', 'instagram', 'youtube', 'twitch', 'twitter', 'onlyfans')),
    username TEXT NOT NULL,
    platform_user_id TEXT,
    display_name TEXT,
    follower_count BIGINT,
    video_count INTEGER,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_analyzed_at TIMESTAMPTZ,
    cached_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ic_user_id TEXT,
    ic_profile JSONB,
    niche_class TEXT[],
    niche_sub_class TEXT[],
    income_min BIGINT,
    income_max BIGINT,
    follower_growth_6mo JSONB,
    posting_frequency NUMERIC(8,2),
    is_business_account BOOLEAN,
    engagement_rate_percent NUMERIC(7,2),
    CONSTRAINT creators_follower_count_nonnegative
        CHECK (follower_count IS NULL OR follower_count >= 0),
    CONSTRAINT creators_video_count_nonnegative
        CHECK (video_count IS NULL OR video_count >= 0),
    UNIQUE(platform, username)
);

CREATE INDEX IF NOT EXISTS idx_creators_platform_username ON creators(platform, username);

CREATE TABLE IF NOT EXISTS video_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    cache_key VARCHAR(500) NOT NULL UNIQUE,
    overall_safe BOOLEAN NOT NULL,
    overall_confidence DOUBLE PRECISION NOT NULL,
    risks_detected JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary TEXT DEFAULT '',
    content_categories JSONB DEFAULT '[]'::jsonb,
    moderation_flags JSONB DEFAULT '[]'::jsonb,
    sponsored_content JSONB DEFAULT NULL,
    processing_time_seconds DOUBLE PRECISION,
    token_count INTEGER,
    error TEXT,
    model_version VARCHAR(100) NOT NULL,
    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    analysis_cost_usd DOUBLE PRECISION,
    creator_id UUID REFERENCES creators(id) ON DELETE SET NULL,
    title TEXT,
    CONSTRAINT content_categories_is_array CHECK (jsonb_typeof(content_categories) = 'array'),
    CONSTRAINT moderation_flags_is_array CHECK (jsonb_typeof(moderation_flags) = 'array')
);

ALTER TABLE video_analysis ADD COLUMN IF NOT EXISTS creator_id UUID REFERENCES creators(id) ON DELETE SET NULL;
ALTER TABLE video_analysis ADD COLUMN IF NOT EXISTS title TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'video_analysis' AND column_name = 'platform'
    ) THEN
        ALTER TABLE video_analysis
            ADD COLUMN platform TEXT GENERATED ALWAYS AS (split_part(cache_key, ':', 1)) STORED;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_video_analysis_platform ON video_analysis (platform);
CREATE INDEX IF NOT EXISTS idx_va_title_trgm ON video_analysis USING gin (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_va_analyzed_at_id ON video_analysis (analyzed_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_video_analysis_categories_gin
    ON video_analysis USING GIN (content_categories jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_video_analysis_moderation_gin
    ON video_analysis USING GIN (moderation_flags jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_video_analysis_creator_date
    ON video_analysis(creator_id, analyzed_at DESC)
    WHERE creator_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS video_analysis_access (
    video_analysis_id UUID NOT NULL REFERENCES video_analysis(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (video_analysis_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_video_analysis_access_user
    ON video_analysis_access(user_id, video_analysis_id);

CREATE TABLE IF NOT EXISTS creative_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_analysis_id UUID NOT NULL REFERENCES video_analysis(id) ON DELETE CASCADE,
    patterns JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(video_analysis_id)
);

DROP TRIGGER IF EXISTS set_updated_at ON creative_patterns;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON creative_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Conversations

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_expires_at ON conversations(expires_at);

DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_message_content_length CHECK (LENGTH(content) <= 100000)
);

CREATE INDEX IF NOT EXISTS idx_conv_messages_conversation_id ON conversation_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conv_messages_created_at ON conversation_messages(conversation_id, created_at);

-- Minimal Generation Job Surface

CREATE TABLE IF NOT EXISTS generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'generating', 'composing', 'completed', 'partial', 'failed', 'cancelled')),
    composition_spec JSONB NOT NULL DEFAULT '{}'::jsonb,
    total_cadres INT NOT NULL DEFAULT 1 CHECK (total_cadres >= 1 AND total_cadres <= 20),
    r2_key TEXT,
    error TEXT CHECK (error IS NULL OR LENGTH(error) <= 500),
    cancellation_requested BOOLEAN NOT NULL DEFAULT FALSE,
    claimed_at TIMESTAMPTZ,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    video_project_id UUID,
    project_revision INT CHECK (project_revision IS NULL OR project_revision >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gen_jobs_user_active
    ON generation_jobs(user_id, status)
    WHERE status IN ('pending', 'generating', 'composing');

ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS video_project_id UUID;
ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS project_revision INT;
ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;
ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0;

-- Video Projects

CREATE TABLE IF NOT EXISTS video_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN (
            'draft',
            'previewing_anchor',
            'previewing_scenes',
            'ready_to_render',
            'rendering',
            'render_complete',
            'failed',
            'archived'
        )),
    revision INT NOT NULL DEFAULT 0 CHECK (revision >= 0),
    source_analysis_ids UUID[] NOT NULL DEFAULT '{}',
    style_brief_summary TEXT NOT NULL DEFAULT '',
    aspect_ratio TEXT NOT NULL DEFAULT '9:16'
        CHECK (aspect_ratio IN ('9:16', '16:9', '1:1')),
    resolution TEXT NOT NULL DEFAULT '720p'
        CHECK (resolution IN ('480p', '720p', '1080p')),
    anchor_scene_id UUID,
    last_error TEXT,
    protagonist_description TEXT NOT NULL DEFAULT '',
    target_emotion_arc TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE video_projects ADD COLUMN IF NOT EXISTS protagonist_description TEXT NOT NULL DEFAULT '';
ALTER TABLE video_projects ADD COLUMN IF NOT EXISTS target_emotion_arc TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_video_projects_conversation_updated
    ON video_projects(conversation_id, updated_at DESC);

DROP TRIGGER IF EXISTS update_video_projects_updated_at ON video_projects;
CREATE TRIGGER update_video_projects_updated_at BEFORE UPDATE ON video_projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS video_project_scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES video_projects(id) ON DELETE CASCADE,
    position INT NOT NULL CHECK (position >= 0 AND position < 20),
    title TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    prompt TEXT NOT NULL DEFAULT '',
    duration_seconds INT NOT NULL CHECK (duration_seconds >= 1 AND duration_seconds <= 30),
    transition TEXT NOT NULL DEFAULT 'fade'
        CHECK (transition IN ('fade', 'cut', 'dissolve', 'wipe')),
    caption TEXT NOT NULL DEFAULT '',
    audio_direction TEXT NOT NULL DEFAULT '',
    shot_type TEXT NOT NULL DEFAULT 'medium',
    camera_movement TEXT NOT NULL DEFAULT 'static',
    beat TEXT NOT NULL DEFAULT 'setup',
    preview_status TEXT NOT NULL DEFAULT 'idle'
        CHECK (preview_status IN ('idle', 'generating', 'verifying', 'ready', 'failed')),
    preview_storage_key TEXT,
    preview_qa_score INT CHECK (preview_qa_score IS NULL OR (preview_qa_score >= 1 AND preview_qa_score <= 10)),
    preview_qa_feedback TEXT,
    preview_scene_score INT CHECK (preview_scene_score IS NULL OR (preview_scene_score >= 1 AND preview_scene_score <= 10)),
    preview_style_score INT CHECK (preview_style_score IS NULL OR (preview_style_score >= 1 AND preview_style_score <= 10)),
    preview_improvement_suggestion TEXT,
    preview_approved BOOLEAN NOT NULL DEFAULT FALSE,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT video_project_scenes_project_position_key
        UNIQUE(project_id, position)
        DEFERRABLE INITIALLY DEFERRED
);

ALTER TABLE video_project_scenes ADD COLUMN IF NOT EXISTS audio_direction TEXT NOT NULL DEFAULT '';
ALTER TABLE video_project_scenes ADD COLUMN IF NOT EXISTS shot_type TEXT NOT NULL DEFAULT 'medium';
ALTER TABLE video_project_scenes ADD COLUMN IF NOT EXISTS camera_movement TEXT NOT NULL DEFAULT 'static';
ALTER TABLE video_project_scenes ADD COLUMN IF NOT EXISTS beat TEXT NOT NULL DEFAULT 'setup';
ALTER TABLE video_project_scenes ADD COLUMN IF NOT EXISTS preview_scene_score INT;
ALTER TABLE video_project_scenes ADD COLUMN IF NOT EXISTS preview_style_score INT;
ALTER TABLE video_project_scenes ADD COLUMN IF NOT EXISTS preview_improvement_suggestion TEXT;

CREATE INDEX IF NOT EXISTS idx_video_project_scenes_project_position
    ON video_project_scenes(project_id, position);

DROP TRIGGER IF EXISTS update_video_project_scenes_updated_at ON video_project_scenes;
CREATE TRIGGER update_video_project_scenes_updated_at BEFORE UPDATE ON video_project_scenes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DO $$
BEGIN
    ALTER TABLE video_projects
        ADD CONSTRAINT fk_video_projects_anchor_scene
        FOREIGN KEY (anchor_scene_id)
        REFERENCES video_project_scenes(id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS video_project_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES video_projects(id) ON DELETE CASCADE,
    analysis_id UUID REFERENCES video_analysis(id) ON DELETE SET NULL,
    source_video_id TEXT,
    platform TEXT,
    title TEXT NOT NULL,
    thumbnail_url TEXT,
    creator_handle TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        analysis_id IS NOT NULL
        OR (source_video_id IS NOT NULL AND platform IS NOT NULL)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_video_project_refs_analysis
    ON video_project_references(project_id, analysis_id)
    WHERE analysis_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_video_project_refs_source
    ON video_project_references(project_id, platform, source_video_id)
    WHERE source_video_id IS NOT NULL AND platform IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'generation_jobs_video_project_id_fkey'
          AND conrelid = 'generation_jobs'::regclass
    ) THEN
        ALTER TABLE generation_jobs
            ADD CONSTRAINT generation_jobs_video_project_id_fkey
            FOREIGN KEY (video_project_id)
            REFERENCES video_projects(id)
            ON DELETE SET NULL
            NOT VALID;
    END IF;
EXCEPTION
    WHEN duplicate_object OR invalid_foreign_key THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE generation_jobs VALIDATE CONSTRAINT generation_jobs_video_project_id_fkey;
EXCEPTION
    WHEN undefined_object OR invalid_foreign_key THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_generation_jobs_video_project_created
    ON generation_jobs(video_project_id, created_at DESC)
    WHERE video_project_id IS NOT NULL;
