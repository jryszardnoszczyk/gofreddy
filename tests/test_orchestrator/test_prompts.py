"""Tests for build_system_prompt dynamic prompt builder."""

from src.orchestrator.prompts import build_system_prompt
from src.orchestrator.tools import ToolDefinition, ToolRegistry


async def _noop(**kwargs):
    return {}


def _make_registry(*tool_names: str) -> ToolRegistry:
    """Create a registry with named dummy tools."""
    reg = ToolRegistry()
    for name in tool_names:
        reg.register(ToolDefinition(
            name=name,
            description=f"Description for {name}",
            parameters={"x": {"type": "string"}},
            required_params=["x"],
            handler=_noop,
        ))
    return reg


class TestBuildSystemPrompt:
    def test_includes_all_registered_tools(self):
        reg = _make_registry("search", "analyze_video", "creator_profile")
        prompt = build_system_prompt(reg)
        assert "search" in prompt
        assert "analyze_video" in prompt
        assert "creator_profile" in prompt

    def test_excludes_unregistered_tools_from_tool_list(self):
        reg = _make_registry("search")
        prompt = build_system_prompt(reg)
        assert "**search**" in prompt
        # analyze_video should not appear in the numbered tool list
        assert "**analyze_video**" not in prompt

    def test_empty_registry_no_tools(self):
        reg = ToolRegistry()
        prompt = build_system_prompt(reg)
        assert "No analysis tools" in prompt
        assert "search" not in prompt

    def test_chaining_patterns_conditional(self):
        # With search: search accumulation chain should appear
        reg = _make_registry("search", "analyze_video")
        prompt = build_system_prompt(reg)
        assert "Search accumulation" in prompt

    def test_chaining_missing_tools_excluded(self):
        # Without search: no chain patterns should appear
        reg = _make_registry("analyze_video")
        prompt = build_system_prompt(reg)
        assert "Search accumulation" not in prompt
        assert "Tool Chaining" not in prompt

    def test_chains_present_with_creator_profile(self):
        reg = _make_registry("analyze_video", "creator_profile")
        prompt = build_system_prompt(reg)
        # creator_profile has standalone chains
        assert "Tool Chaining" in prompt
        assert "Search accumulation" not in prompt

    def test_prompt_mentions_platform_video_id_rule(self):
        reg = _make_registry("analyze_video")
        prompt = build_system_prompt(reg)
        assert "platform" in prompt
        assert "video_id" in prompt

    def test_tool_count_dynamic(self):
        reg = _make_registry("a", "b", "c")
        prompt = build_system_prompt(reg)
        assert "3 specialized tools" in prompt

    def test_restricted_tools_section(self):
        """Restricted tools (free tier) shown in Pro Features section."""
        reg = _make_registry("search")
        restricted = {
            "analyze_video": "Video analysis with deepfake detection",
            "creator_profile": "Creator intelligence",
        }
        prompt = build_system_prompt(reg, restricted_tools=restricted)
        assert "Pro Features" in prompt
        assert "analyze_video" in prompt
        assert "creator_profile" in prompt
        assert "Never attempt to use these tools" in prompt

    def test_no_restricted_tools_no_section(self):
        """No restricted tools → no Pro Features section."""
        reg = _make_registry("search")
        prompt = build_system_prompt(reg)
        assert "Pro Features" not in prompt

    def test_workspace_state_section(self):
        """Workspace state injected into prompt."""
        reg = _make_registry("search", "workspace")
        workspace_state = {
            "collections": [
                {"name": "TikTok cooking", "count": 15, "filters": {"platform": "tiktok"}},
            ],
            "active_collection": "TikTok cooking",
        }
        prompt = build_system_prompt(reg, workspace_state=workspace_state)
        assert "Workspace" in prompt
        assert "TikTok cooking" in prompt
        assert "15 items" in prompt
        assert "workspace" in prompt

    def test_workspace_state_empty_collections(self):
        """Empty workspace state shows placeholder."""
        reg = _make_registry("search")
        workspace_state = {"collections": [], "active_collection": "none"}
        prompt = build_system_prompt(reg, workspace_state=workspace_state)
        assert "no collections yet" in prompt

    def test_tier_state_section(self):
        """Tier state injected into prompt."""
        reg = _make_registry("search")
        tier_state = {"tier": "free", "messages_remaining": 15}
        prompt = build_system_prompt(reg, tier_state=tier_state)
        assert "User Context" in prompt
        assert "free" in prompt
        assert "15" in prompt

    def test_no_tier_state_no_section(self):
        """No tier state → no User Context section."""
        reg = _make_registry("search")
        prompt = build_system_prompt(reg)
        assert "User Context" not in prompt

    def test_tier_state_includes_all_four_fields(self):
        """Tier state includes max_batch_size, max_search_results, and daily_limit_resets."""
        reg = _make_registry("search")
        tier_state = {
            "tier": "free",
            "messages_remaining": 15,
            "max_batch_size": 5,
            "max_search_results": 25,
        }
        prompt = build_system_prompt(reg, tier_state=tier_state)
        assert "max_batch_size: 5" in prompt
        assert "max_search_results: 25" in prompt
        assert "daily_limit_resets: midnight UTC" in prompt
        assert "messages_remaining_today: 15" in prompt

    def test_tier_state_partial_defaults_gracefully(self):
        """Partial tier_state uses 'unknown' defaults."""
        reg = _make_registry("search")
        tier_state = {"tier": "pro"}
        prompt = build_system_prompt(reg, tier_state=tier_state)
        assert "tier: pro" in prompt
        assert "messages_remaining_today: unknown" in prompt
        assert "max_batch_size: unknown" in prompt
        assert "max_search_results: unknown" in prompt
        assert "daily_limit_resets: midnight UTC" in prompt

    def test_tier_section_uses_h3_heading(self):
        """Tier section uses ### (h3) heading, not ## (h2)."""
        reg = _make_registry("search")
        tier_state = {"tier": "free", "messages_remaining": 10}
        prompt = build_system_prompt(reg, tier_state=tier_state)
        assert "### User Context" in prompt

    def test_workspace_state_renders_summary_stats(self):
        """Summary stats (platform breakdown, engagement, top creators) rendered in prompt."""
        reg = _make_registry("search", "workspace")
        workspace_state = {
            "collections": [
                {
                    "id": "abc",
                    "name": "Beauty skincare",
                    "count": 19,
                    "filters": None,
                    "summary": {
                        "platform_breakdown": {"tiktok": 9, "instagram": 8, "youtube": 2},
                        "engagement_percentiles": {"p25": 0.03, "median": 0.05, "p75": 0.09},
                        "top_creators": [
                            {"handle": "maabble", "count": 3},
                            {"handle": "slavicskin", "count": 2},
                        ],
                    },
                },
            ],
            "active_collection": "Beauty skincare",
        }
        prompt = build_system_prompt(reg, workspace_state=workspace_state)
        assert "tiktok 9" in prompt
        assert "instagram 8" in prompt
        assert "median=0.05" in prompt
        assert "p25=0.03" in prompt
        assert "@maabble (3)" in prompt
        assert "@slavicskin (2)" in prompt

    def test_workspace_state_no_summary_graceful(self):
        """Collections without summary stats still render correctly."""
        reg = _make_registry("search")
        workspace_state = {
            "collections": [
                {"id": "abc", "name": "Test", "count": 5, "filters": None},
            ],
            "active_collection": "Test",
        }
        prompt = build_system_prompt(reg, workspace_state=workspace_state)
        assert "Test" in prompt
        assert "5 items" in prompt

    def test_workspace_includes_query_strategy_guidance(self):
        """Workspace section includes digest/query guidance."""
        reg = _make_registry("search")
        workspace_state = {"collections": [], "active_collection": "none"}
        prompt = build_system_prompt(reg, workspace_state=workspace_state)
        assert "DIGEST" in prompt
        assert "workspace" in prompt
        assert "Never extrapolate" in prompt

    def test_workspace_first_resolution_rule(self):
        """Workspace-first resolution rule always present in Important Rules."""
        reg = _make_registry("search", "analyze_video")
        prompt = build_system_prompt(reg)
        assert "Workspace-first resolution" in prompt
        assert "check the workspace FIRST" in prompt

    def test_target_collection_critical_rule_with_search(self):
        """Strengthened target_collection rule present when search available."""
        reg = _make_registry("search")
        prompt = build_system_prompt(reg)
        assert "ALWAYS pass its name as target_collection" in prompt
        assert "for ANY search" in prompt

    def test_top_creators_empty_list_graceful(self):
        """Empty top_creators list doesn't render creators line."""
        reg = _make_registry("search")
        workspace_state = {
            "collections": [
                {
                    "id": "abc",
                    "name": "Empty collection",
                    "count": 0,
                    "filters": None,
                    "summary": {
                        "platform_breakdown": {},
                        "engagement_percentiles": {"p25": 0.0, "median": 0.0, "p75": 0.0},
                        "top_creators": [],
                    },
                },
            ],
            "active_collection": "Empty collection",
        }
        prompt = build_system_prompt(reg, workspace_state=workspace_state)
        assert "Empty collection" in prompt
        assert "creators:" not in prompt

    def test_reuse_analysis_id_hint(self):
        """Prompt includes hint to reuse existing analysis_id."""
        reg = _make_registry("analyze_video")
        prompt = build_system_prompt(reg)
        assert "reuse the existing analysis_id" in prompt

    def test_agency_section_when_content_tool_registered(self):
        """Agency section appears when generate_content is registered."""
        reg = _make_registry("search", "generate_content")
        prompt = build_system_prompt(reg)
        assert "Agency Workflows" in prompt
        assert "Content Generation" in prompt
        assert "Creator Vetting" in prompt
        assert "Agency Services" in prompt
        assert "reuse the returned collection_name" in prompt

    def test_no_agency_section_without_content_tool(self):
        """Agency section NOT included when generate_content is absent."""
        reg = _make_registry("search", "analyze_video", "detect_fraud")
        prompt = build_system_prompt(reg)
        assert "Agency Workflows" not in prompt
        assert "Creator Vetting" not in prompt

    def test_content_generation_chain_requires_both_tools(self):
        """Content generation chain only appears when both search and generate_content are registered."""
        # Both present
        reg = _make_registry("search", "generate_content")
        prompt = build_system_prompt(reg)
        assert "Content generation:" in prompt

        # Only search — no content generation chain
        reg2 = _make_registry("search")
        prompt2 = build_system_prompt(reg2)
        assert "Content generation:" not in prompt2

        # Only generate_content — no content generation chain
        reg3 = _make_registry("generate_content")
        prompt3 = build_system_prompt(reg3)
        assert "Content generation:" not in prompt3

    def test_creator_discovery_preserves_explicit_platform_requests(self):
        reg = _make_registry("discover_creators")
        prompt = build_system_prompt(reg)

        assert "pass exactly those platforms" in prompt
        assert "Never substitute Instagram or YouTube for an explicit TikTok request." in prompt
        assert 'platforms=["tiktok"]' in prompt
