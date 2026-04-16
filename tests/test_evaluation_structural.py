"""Tests for structural gate validation."""

import json

from src.evaluation.structural import structural_gate


class TestGeoStructural:
    """GEO domain structural validation."""

    def test_valid_geo_passes(self):
        result = structural_gate("geo", {
            "optimized/ahrefs.md": "# Ahrefs Review\n\nContent here with real analysis.",
        })
        assert result.passed is True

    def test_no_optimized_files_fails(self):
        result = structural_gate("geo", {
            "pages/ahrefs.json": '{"url": "https://ahrefs.com"}',
        })
        assert result.passed is False
        assert any("No optimized/" in f for f in result.failures)

    def test_empty_content_fails(self):
        result = structural_gate("geo", {
            "optimized/empty.md": "",
        })
        assert result.passed is False

    def test_invalid_json_ld_fails(self):
        result = structural_gate("geo", {
            "optimized/page.md": (
                '# Page\n<script type="application/ld+json">'
                '{invalid json}'
                '</script>'
            ),
        })
        assert result.passed is False
        assert any("JSON-LD" in f for f in result.failures)

    def test_valid_json_ld_passes(self):
        result = structural_gate("geo", {
            "optimized/page.md": (
                '# Page\n<script type="application/ld+json">'
                '{"@type": "FAQPage", "mainEntity": []}'
                '</script>'
            ),
        })
        assert result.passed is True


class TestCompetitiveStructural:
    """Competitive Intelligence domain structural validation."""

    def test_valid_brief_passes(self):
        result = structural_gate("competitive", {
            "brief.md": "# Competitive Brief\n\n## Thesis\nThe client should focus on AI-native positioning.\n\n## Findings\nCompetitors are moving fast in this space with significant investment.\n\n## Recommendations\nPrioritize speed-to-market over feature completeness.",
        })
        assert result.passed is True

    def test_no_brief_fails(self):
        result = structural_gate("competitive", {
            "competitors/acme.json": '{"name": "Acme"}',
        })
        assert result.passed is False

    def test_brief_too_short_fails(self):
        result = structural_gate("competitive", {
            "brief.md": "Short.",
        })
        assert result.passed is False

    def test_too_few_sections_fails(self):
        result = structural_gate("competitive", {
            "brief.md": "# Brief\n\n" + "x" * 200,
        })
        assert result.passed is False
        assert any("section headers" in f for f in result.failures)


class TestMonitoringStructural:
    """Monitoring domain structural validation (absorbs digest check)."""

    def _make_complete_outputs(self) -> dict[str, str]:
        """Helper: create minimally valid monitoring outputs."""
        results = [
            {"type": "select_mentions", "sources": 3},
            {"type": "cluster_stories"},
            {"type": "synthesize", "attempt": 1},
            {"type": "recommend", "status": "kept"},
        ]
        return {
            "session.md": "# Session\n\n## Status: COMPLETE\n\nDone.",
            "results.jsonl": "\n".join(json.dumps(r) for r in results),
            "digest.md": "# Weekly Digest\n\nContent here.",
            "findings.md": "# Findings\n\nContent here.",
            "stories/story-1.json": '{"id": 1}',
            "synthesized/story-1.md": "# Story 1\n\nSynthesized.",
            "recommendations/executive_summary.md": "# Summary",
            "recommendations/action_items.md": "# Actions",
        }

    def test_complete_session_passes(self):
        result = structural_gate("monitoring", self._make_complete_outputs())
        assert result.passed is True
        assert result.dqs_score is not None
        assert result.dqs_score == 1.0

    def test_missing_digest_fails(self):
        outputs = self._make_complete_outputs()
        del outputs["digest.md"]
        result = structural_gate("monitoring", outputs)
        assert result.passed is False
        assert any("digest_exists" in f for f in result.failures)

    def test_missing_session_md_fails(self):
        outputs = self._make_complete_outputs()
        del outputs["session.md"]
        result = structural_gate("monitoring", outputs)
        assert result.passed is False

    def test_incomplete_status_without_digest_fails(self):
        outputs = self._make_complete_outputs()
        outputs["session.md"] = "# Session\n\n## Status: IN_PROGRESS"
        del outputs["digest.md"]
        result = structural_gate("monitoring", outputs)
        assert result.passed is False
        assert any("status_complete" in f for f in result.failures)

    def test_dqs_score_computed(self):
        """DQS is computed even when some assertions fail."""
        outputs = self._make_complete_outputs()
        del outputs["digest.md"]
        result = structural_gate("monitoring", outputs)
        assert result.dqs_score is not None
        assert 0.0 < result.dqs_score < 1.0

    def test_low_volume_digest_only_passes(self):
        """Low-volume week: only select_mentions in results.jsonl, no stories,
        but digest.md + findings.md present. Must pass structural gate."""
        results = [{"type": "select_mentions", "sources": 3}]
        outputs = {
            "session.md": "# Session\n\n## Status: BLOCKED_PERSIST_FAILED",
            "results.jsonl": json.dumps(results[0]),
            "digest.md": "# Weekly Digest\n\nLow-volume week summary.",
            "findings.md": "# Findings\n\nNo significant findings.",
        }
        result = structural_gate("monitoring", outputs)
        assert result.passed is True
        assert result.dqs_score is not None
        assert result.dqs_score > 0.8

    def test_blocked_persist_with_digest_passes(self):
        """BLOCKED_PERSIST_FAILED + digest.md passes status_complete."""
        outputs = self._make_complete_outputs()
        outputs["session.md"] = "# Session\n\n## Status: BLOCKED_PERSIST_FAILED"
        result = structural_gate("monitoring", outputs)
        assert result.passed is True

    def test_in_progress_with_digest_passes(self):
        """IN_PROGRESS + digest.md passes status_complete."""
        outputs = self._make_complete_outputs()
        outputs["session.md"] = "# Session\n\n## Status: IN_PROGRESS"
        result = structural_gate("monitoring", outputs)
        assert result.passed is True


class TestStoryboardStructural:
    """Storyboard domain structural validation."""

    def test_valid_story_passes(self):
        story = {
            "title": "Test Story",
            "scene_count": 2,
            "scenes": [
                {"prompt": "A person walking", "camera": "wide", "transition": "cut"},
                {"prompt": "Close up", "camera": "close", "transition": "fade"},
            ],
        }
        result = structural_gate("storyboard", {
            "stories/story-1.json": json.dumps(story),
        })
        assert result.passed is True

    def test_no_stories_fails(self):
        result = structural_gate("storyboard", {
            "patterns/style.json": '{"style": "cinematic"}',
        })
        assert result.passed is False

    def test_invalid_json_fails(self):
        result = structural_gate("storyboard", {
            "stories/story-1.json": "not json {",
        })
        assert result.passed is False

    def test_missing_scene_fields_fails(self):
        story = {
            "scenes": [
                {"prompt": "A scene", "camera": "wide"},  # missing transition
            ],
        }
        result = structural_gate("storyboard", {
            "stories/story-1.json": json.dumps(story),
        })
        assert result.passed is False
        assert any("transition" in f for f in result.failures)

    def test_scene_count_mismatch_fails(self):
        story = {
            "scene_count": 5,
            "scenes": [
                {"prompt": "Scene", "camera": "wide", "transition": "cut"},
            ],
        }
        result = structural_gate("storyboard", {
            "stories/story-1.json": json.dumps(story),
        })
        assert result.passed is False
        assert any("scene_count" in f for f in result.failures)

    def test_empty_prompt_fails(self):
        story = {
            "scenes": [
                {"prompt": "", "camera": "wide", "transition": "cut"},
            ],
        }
        result = structural_gate("storyboard", {
            "stories/story-1.json": json.dumps(story),
        })
        assert result.passed is False


class TestUnknownDomain:
    """Unknown domain handling."""

    def test_unknown_domain_fails(self):
        result = structural_gate("nonexistent", {"file.txt": "content"})
        assert result.passed is False
        assert any("Unknown domain" in f for f in result.failures)


class TestCanary:
    """Structural canary: malformed artifact should be caught."""

    def test_canary_scene_count_mismatch(self):
        """Canary: declared scene_count doesn't match actual scenes."""
        story = {
            "scene_count": 10,
            "scenes": [
                {"prompt": "Only one scene", "camera": "wide", "transition": "cut"},
            ],
        }
        result = structural_gate("storyboard", {
            "stories/canary.json": json.dumps(story),
        })
        assert result.passed is False
