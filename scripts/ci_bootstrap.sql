-- CI Bootstrap: Create Supabase-expected roles on plain Postgres (e.g., GitHub Actions).
-- These roles are required by feedback loop migrations (014-016) which use GRANT/REVOKE.
-- Supabase instances already have these roles, so this is only needed for CI.

DO $$ BEGIN CREATE ROLE anon NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE authenticated NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE service_role NOLOGIN SUPERUSER; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
