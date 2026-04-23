"""Root pytest configuration.

Scope: tell pytest which files to skip at collection so `pytest --collect-only`
returns zero errors. Shared fixtures live in per-directory conftests
(`tests/test_api/conftest.py`, `tests/competitive/conftest.py`, etc.);
nothing global is currently needed beyond the ignore list.

## Orphaned test ignore list

The files below import modules not yet ported from the freddy → gofreddy pivot.
They stay on disk so their coverage is recoverable when the module lands — see
`docs/plans/2026-04-23-002-agency-integration-research-record.md` for which
bundle owns each port. To re-enable a file, port the module it imports, then
remove the file from `collect_ignore` (or the directory from `collect_ignore_glob`).

Each entry is a path relative to this conftest (i.e., under `tests/`).
"""

from __future__ import annotations

# Files whose source modules await porting. Keep alphabetized per group.
collect_ignore = [
    # Bundle 2 — client platform (billing, accounts)
    "test_accounts_router.py",                  # src.api.routers.accounts
    "test_clients_service.py",                  # src.clients
    "test_manage_client_tool.py",               # src.clients + src.orchestrator
    "test_pr057_ssrf_path_traversal.py",        # src.stories + src.publishing
    "test_pr059_auth_hardening.py",             # already runs but keep on watch
    # Bundle 3 — CI triangle (competitive brief, newsletter, reports)
    "test_analysis_repository.py",              # src.analysis.repository
    "test_analysis_service.py",                 # src.analysis.service
    "test_analytics_service.py",                # src.monitoring.analytics_service
    "test_brief_generator.py",                  # src.competitive.brief
    "test_brands.py",                           # src.brands
    "test_brands_exposure.py",                  # src.brands
    "test_ci_prompts.py",                       # src.newsletter
    "test_competitive_router.py",               # src.competitive.brief
    "test_newsletter_service.py",               # src.newsletter
    "test_partnerships.py",                     # src.competitive.intelligence.partnerships
    "test_reports_brief.py",                    # src.api.routers.reports
    # Bundle 4 — creator ops (fraud, discover, demographics, IC)
    "test_demographics.py",                     # src.demographics
    "test_discover_defaults.py",                # src.api.routers.discover
    "test_expanded_moderation.py",              # src.api.routers.fraud
    "test_fraud_ic_enrichment.py",              # src.api.routers.fraud
    "test_pr082_ic_search.py",                  # src.api.routers.fraud
    # Bundle 4 — deepfake service
    "deepfake/test_router.py",                  # src.deepfake.service
    "deepfake/test_service.py",                 # src.deepfake.service
    # Bundle 5 — content factory (publishing, voice, articles)
    "test_article_tracking.py",                 # src.seo.article_tracking_service
    "test_content_generation.py",               # src.content_gen.config
    "test_content_normalizer.py",               # src.content_gen.voice_models
    "test_publish_dispatcher.py",               # src.publishing.dispatcher
    "test_publishing_oauth.py",                 # src.publishing.service
    "test_publishing_service.py",               # src.publishing.service
    "test_rss_monitor.py",                      # src.publishing.rss_monitor
    "test_transcript_routing.py",               # src.content_gen
    "test_voice_profile.py",                    # src.content_gen.voice_models
    "publishing/test_repository.py",            # src.publishing.repository
    # Bundle 5 — Instagram stories
    "test_instagram_stories.py",                # src.stories
    # Bundle 6 — video studio (generation, storyboard, avatar)
    "generation/test_avatar_service.py",        # src.generation
    "generation/test_bg_removal_service.py",    # src.generation
    "generation/test_pipeline_integration.py",  # src.generation
    "generation/test_service.py",               # src.generation
    "generation/test_storyboard_tools.py",      # src.generation
    "generation/test_worker.py",                # src.generation.worker
    "test_video_project_service.py",            # src.video_projects.service
    # Bundle 7 — workers + schedulers (jobs, batch, SSE)
    "test_auto_logging.py",                     # src.jobs
    "test_auto_title_sse.py",                   # src.batch.worker
    "test_job_service.py",                      # src.jobs
    "test_job_worker.py",                       # src.jobs
    "test_pr025_durability.py",                 # src.jobs + src.stories
    "test_pr052_resume_cache.py",               # src.prompts
    "batch/test_repository.py",                 # src.batch.repository
    "batch/test_service.py",                    # src.batch.service
    "batch/test_worker.py",                     # src.batch.worker
    # Bundle 8 — orchestrator + skills framework
    "test_pr051_batch_workspace.py",            # src.orchestrator
    "test_pr071_intelligence_layer.py",         # src.monitoring.workspace_bridge
    "test_pr072_agent_monitoring_tools.py",     # src.orchestrator
    "test_pr073_intelligence_agent_tools.py",   # src.orchestrator
    "test_search_optimization_tool.py",         # src.orchestrator + src.search.cache_repository
    "test_tool_catalog.py",                     # src.orchestrator
    "competitive/test_tool.py",                 # src.orchestrator
    # Bundle 8 — Canvas workspace + SEO/GEO scrape routers
    "test_pr035_canvas_workspace_polish.py",    # src.api.routers.agent
    "test_geo_detect_scrape.py",                # src.api.routers.agent
    "test_seo_service.py",                      # src.seo.service
    # Scripts directory — obsolete harness helpers
    "test_scripts/test_e2e_seed_auth_tokens.py",  # scripts.* not packaged
    "test_scripts/test_env_doctor.py",            # scripts.env_doctor
]
