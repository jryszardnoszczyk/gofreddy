"""Regression tests for VideoAnalysisResult mapper field completeness."""

import ast
from pathlib import Path


# Mapper files that construct VideoAnalysisResult
_MAPPER_FILES = [
    Path("src/api/routers/videos.py"),
    Path("src/api/routers/creators.py"),
    Path("src/api/routers/analysis.py"),
]

_REQUIRED_FIELDS = {"content_categories", "moderation_flags", "sponsored_content"}


class TestMapperFieldCompleteness:
    """Regression guard: all VideoAnalysisResult construction sites must include the 3 fields."""

    def test_all_mappers_include_required_fields(self):
        """Assert all VideoAnalysisResult() calls include content_categories, moderation_flags, sponsored_content."""
        for filepath in _MAPPER_FILES:
            source = filepath.read_text()
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    # Match VideoAnalysisResult(...) calls
                    name = None
                    if isinstance(func, ast.Name):
                        name = func.id
                    elif isinstance(func, ast.Attribute):
                        name = func.attr

                    if name == "VideoAnalysisResult":
                        keywords = {kw.arg for kw in node.keywords if kw.arg is not None}
                        missing = _REQUIRED_FIELDS - keywords
                        assert not missing, (
                            f"{filepath}:{node.lineno} — VideoAnalysisResult() missing: {missing}"
                        )

    def test_agent_tool_includes_required_fields(self):
        """Assert agent analyze_video tool response includes the 3 fields."""
        tools_path = Path("src/orchestrator/tools.py")
        source = tools_path.read_text()
        # Simple text search — the return dict should include these keys
        for field in ["content_categories", "moderation_flags", "sponsored_content"]:
            assert f'"{field}"' in source, (
                f"src/orchestrator/tools.py missing '{field}' in analyze_video response"
            )
