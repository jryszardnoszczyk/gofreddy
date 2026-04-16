"""Tests for the tool catalog — single source of truth for tool definitions."""

import ast
import inspect
import re
import textwrap

import pytest

from src.orchestrator.tool_catalog import all_specs, get_spec
from src.orchestrator.agent import VideoIntelligenceAgent


class TestToolCatalogCompleteness:
    """Verify spec completeness and validity."""

    def test_spec_count(self):
        """All 20 tools are defined."""
        specs = all_specs()
        assert len(specs) == 20

    def test_all_specs_have_required_fields(self):
        """Each spec has name, description, and parameters."""
        for spec in all_specs():
            assert spec.name, f"Spec missing name"
            assert spec.description, f"{spec.name} missing description"
            assert spec.parameters, f"{spec.name} missing parameters"

    def test_parameters_are_valid_json_schema(self):
        """Each spec's parameters dict is valid JSON Schema with type=object and properties."""
        for spec in all_specs():
            schema = spec.to_json_schema()
            assert schema.get("type") == "object", f"{spec.name}: parameters must have type=object"
            assert "properties" in schema or schema.get("properties") == {}, (
                f"{spec.name}: parameters must have properties key"
            )

    def test_no_duplicate_names(self):
        """No duplicate tool names."""
        names = [s.name for s in all_specs()]
        assert len(names) == len(set(names)), f"Duplicate names: {[n for n in names if names.count(n) > 1]}"

    def test_action_tools_have_matching_enum(self):
        """Action-based tools have actions list matching their parameters' action.enum values."""
        for spec in all_specs():
            if spec.actions is None:
                continue
            props = spec.parameters.get("properties", {})
            action_prop = props.get("action", {})
            action_enum = action_prop.get("enum", [])
            assert set(spec.actions) == set(action_enum), (
                f"{spec.name}: actions {spec.actions} != enum {action_enum}"
            )

    def test_get_spec_returns_correct_spec(self):
        """get_spec() returns the correct spec by name."""
        spec = get_spec("search")
        assert spec.name == "search"

    def test_get_spec_raises_for_unknown(self):
        """get_spec() raises KeyError for unknown tool."""
        with pytest.raises(KeyError):
            get_spec("nonexistent_tool")


class TestToolSpecMethods:
    """Test ToolSpec utility methods."""

    def test_to_json_schema(self):
        """to_json_schema() returns the parameters dict."""
        spec = get_spec("search")
        schema = spec.to_json_schema()
        assert schema["type"] == "object"
        assert "query" in schema["properties"]

    def test_to_skill_md_basic(self):
        """to_skill_md() produces readable markdown with parameter table."""
        spec = get_spec("detect_fraud")
        md = spec.to_skill_md()
        assert "## detect_fraud" in md
        assert "| platform |" in md
        assert "| username |" in md
        assert "Yes" in md  # required params

    def test_to_skill_md_with_guidance(self):
        """to_skill_md() includes guidance when provided."""
        spec = get_spec("search")
        md = spec.to_skill_md(guidance="## Custom Guidance\nSome tips here.")
        assert "### Guidance" in md
        assert "Custom Guidance" in md

    def test_to_skill_md_shows_cost(self):
        """to_skill_md() shows cost for paid tools."""
        spec = get_spec("seo_audit")
        md = spec.to_skill_md()
        assert "8 credits" in md

    def test_to_skill_md_shows_tier(self):
        """to_skill_md() shows tier for Pro tools."""
        spec = get_spec("manage_monitor")
        md = spec.to_skill_md()
        assert "pro" in md.lower()

    def test_to_skill_md_shows_actions(self):
        """to_skill_md() shows actions for action-based tools."""
        spec = get_spec("workspace")
        md = spec.to_skill_md()
        assert "`query`" in md
        assert "`filter`" in md

    def test_to_cli_stub_basic(self):
        """to_cli_stub() produces valid Python-like CLI stub."""
        spec = get_spec("detect_fraud")
        stub = spec.to_cli_stub()
        assert "import typer" in stub
        assert "app = typer.Typer(" in stub
        assert "@handle_errors" in stub
        assert "from ..api import" in stub
        assert "_require_config" in stub

    def test_to_cli_stub_has_registration_comment(self):
        """to_cli_stub() includes registration comment."""
        spec = get_spec("search")
        stub = spec.to_cli_stub()
        assert "# Registration:" in stub
        assert "app.add_typer" in stub

    def test_to_cli_stub_action_based(self):
        """Action-based tools generate sub-commands."""
        spec = get_spec("manage_policy")
        stub = spec.to_cli_stub()
        # Should have sub-commands for each action
        assert "@app.command('create')" in stub
        assert "@app.command('list')" in stub
        assert "@app.command('evaluate')" in stub


class TestCrossCheckWithRegistry:
    """Cross-check tool catalog against build_default_registry() tool names.

    After the tools.py decomposition (handler code moved to tool_handlers/),
    build_default_registry() no longer contains inline ToolDefinition calls.
    These tests use runtime registry introspection instead of source-code
    parsing: instantiate a registry with mock services and compare.
    """

    @staticmethod
    def _build_full_registry():
        """Build a registry with all services mocked to register every tool."""
        from unittest.mock import MagicMock
        from uuid import uuid4

        from src.billing.tiers import Tier
        from src.orchestrator.tools import build_default_registry

        # Provide a mock for every service parameter so all tools register
        registry, _ = build_default_registry(
            search_service=MagicMock(),
            analysis_service=MagicMock(),
            brand_service=MagicMock(),
            demographics_service=MagicMock(),
            deepfake_service=MagicMock(),
            evolution_service=MagicMock(),
            trend_service=MagicMock(),
            story_service=MagicMock(),
            video_storage=MagicMock(),
            fetchers={MagicMock(): MagicMock()},
            fraud_service=MagicMock(),
            billing_service=MagicMock(),
            workspace_service=MagicMock(),
            conversation_id=uuid4(),
            tier=Tier.PRO,
            batch_service=MagicMock(),
            batch_repository=MagicMock(),
            workspace_repository=MagicMock(),
            batch_settings=MagicMock(),
            analysis_repository=MagicMock(),
            policy_service=MagicMock(),
            creative_service=MagicMock(),
            generation_service=MagicMock(),
            idea_service=MagicMock(),
            video_project_service=MagicMock(),
            credit_service=MagicMock(),
            credit_settings=MagicMock(),
            billing_flags=MagicMock(),
            gemini_client=MagicMock(),
            ic_backend=MagicMock(),
            image_preview_service=MagicMock(),
            monitoring_service=MagicMock(),
            xpoz_adapters={"twitter": MagicMock(), "instagram": MagicMock(), "reddit": MagicMock()},
            bluesky_adapter=MagicMock(),
            newsdata_adapter=MagicMock(),
            podcast_adapter=MagicMock(),
            geo_service=MagicMock(),
            seo_service=MagicMock(),
            client_service=MagicMock(),
            ad_service=MagicMock(),
            brief_generator=MagicMock(),
            content_generation_service=MagicMock(),
            comment_service=MagicMock(),
        )
        return registry

    def test_catalog_names_match_registry(self):
        """Tool catalog names match runtime-registered tool names."""
        registry = self._build_full_registry()
        registry_names = set(registry.names)
        catalog_names = {s.name for s in all_specs()}

        assert catalog_names == registry_names, (
            f"Mismatch!\n"
            f"  In catalog but not registry: {catalog_names - registry_names}\n"
            f"  In registry but not catalog: {registry_names - catalog_names}"
        )

    def test_catalog_parameter_keys_match_registry(self):
        """ToolSpec parameter property keys match runtime ToolDefinition parameter keys."""
        registry = self._build_full_registry()

        # Build {name: set(param_keys)} from the registry
        registry_params: dict[str, set[str]] = {}
        for tool_name in registry.names:
            tool_def = registry.get(tool_name)
            if tool_def:
                registry_params[tool_name] = set(tool_def.parameters.keys())

        catalog_specs = {s.name: s for s in all_specs()}

        # Compare parameter keys per tool
        mismatches: list[str] = []
        for tool_name in sorted(catalog_specs):
            if tool_name not in registry_params:
                mismatches.append(f"  {tool_name}: not in registry")
                continue
            spec_keys = set(catalog_specs[tool_name].parameters.get("properties", {}).keys())
            reg_keys = registry_params[tool_name]
            if spec_keys != reg_keys:
                only_in_spec = spec_keys - reg_keys
                only_in_reg = reg_keys - spec_keys
                parts = [f"  {tool_name}:"]
                if only_in_spec:
                    parts.append(f"    in ToolSpec only: {sorted(only_in_spec)}")
                if only_in_reg:
                    parts.append(f"    in ToolDefinition only: {sorted(only_in_reg)}")
                mismatches.append("\n".join(parts))

        assert not mismatches, (
            "Parameter key mismatch between ToolSpec and ToolDefinition:\n"
            + "\n".join(mismatches)
        )


class TestNeedsUserIdMatch:
    """Verify needs_user_id matches _USER_ID_TOOLS in agent.py."""

    def test_needs_user_id_matches_agent(self):
        """Specs with needs_user_id=True match _USER_ID_TOOLS frozenset."""
        catalog_user_id_tools = {s.name for s in all_specs() if s.needs_user_id}
        agent_user_id_tools = VideoIntelligenceAgent._USER_ID_TOOLS

        assert catalog_user_id_tools == agent_user_id_tools, (
            f"Mismatch!\n"
            f"  In catalog but not agent: {catalog_user_id_tools - agent_user_id_tools}\n"
            f"  In agent but not catalog: {agent_user_id_tools - catalog_user_id_tools}"
        )


class TestCodegenScript:
    """Test the build_tool_artifacts.py script."""

    def test_dry_run(self):
        """--dry-run prints planned output without writing."""
        import subprocess
        result = subprocess.run(
            ["python", "scripts/build_tool_artifacts.py", "--dry-run"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Would write" in result.stdout
        assert "20 tools" in result.stdout

    def test_verify_passes_after_generation(self):
        """--verify passes when generated files exist and match."""
        import subprocess
        # First generate
        gen_result = subprocess.run(
            ["python", "scripts/build_tool_artifacts.py"],
            capture_output=True, text=True,
        )
        assert gen_result.returncode == 0

        # Then verify
        verify_result = subprocess.run(
            ["python", "scripts/build_tool_artifacts.py", "--verify"],
            capture_output=True, text=True,
        )
        assert verify_result.returncode == 0, f"Verify failed: {verify_result.stdout}"
