"""Tests for structural gate validation."""

import json

import pytest

from src.evaluation.structural import structural_gate


@pytest.fixture(autouse=True)
def _no_sonnet_claims(monkeypatch):
    """Stub the claim-grounding Sonnet call so tests are deterministic.

    R-#37 wired an async Sonnet call into the monitoring validator. The
    unit-test suite never exercises the agent behaviour itself — it
    covers deterministic structural rules — so we replace the agent
    with a no-op that returns "no claims found". Tests that need to
    exercise a specific claim verdict should override this fixture.
    """
    async def _no_claims(session_md, outputs, *, timeout=None):  # noqa: ARG001
        return []

    monkeypatch.setattr(
        "src.evaluation.structural_agent.verify_claims_async",
        _no_claims,
    )


class TestGeoStructural:
    """GEO domain structural validation."""

    async def test_valid_geo_passes(self):
        result = await structural_gate("geo", {
            "optimized/ahrefs.md": "# Ahrefs Review\n\nContent here with real analysis.",
        })
        assert result.passed is True

    async def test_no_optimized_files_fails(self):
        result = await structural_gate("geo", {
            "pages/ahrefs.json": '{"url": "https://ahrefs.com"}',
        })
        assert result.passed is False
        assert any("No optimized/" in f for f in result.failures)

    async def test_empty_content_fails(self):
        result = await structural_gate("geo", {
            "optimized/empty.md": "",
        })
        assert result.passed is False

    async def test_invalid_json_ld_fails(self):
        result = await structural_gate("geo", {
            "optimized/page.md": (
                '# Page\n<script type="application/ld+json">'
                '{invalid json}'
                '</script>'
            ),
        })
        assert result.passed is False
        assert any("JSON-LD" in f for f in result.failures)

    async def test_valid_json_ld_passes(self):
        result = await structural_gate("geo", {
            "optimized/page.md": (
                '# Page\n<script type="application/ld+json">'
                '{"@type": "FAQPage", "mainEntity": []}'
                '</script>'
            ),
        })
        assert result.passed is True


class TestCompetitiveStructural:
    """Competitive Intelligence domain structural validation.

    R-#35 dropped the `<500 chars` and `<3 headers` gates — length and
    header count are not quality signals. Remaining structural rules:
    brief file exists, >50-char non-whitespace floor, at least one
    parseable competitors/*.json.
    """

    async def test_valid_brief_passes(self):
        result = await structural_gate("competitive", {
            "brief.md": (
                "# Competitive Brief\n\n"
                "## Thesis\nThe client should focus on AI-native positioning.\n\n"
                "## Findings\nCompetitors are moving fast in this space with significant investment.\n\n"
                "## Recommendations\nPrioritize speed-to-market over feature completeness."
            ),
            "competitors/acme.json": '{"name": "Acme"}',
        })
        assert result.passed is True

    async def test_no_brief_fails(self):
        result = await structural_gate("competitive", {
            "competitors/acme.json": '{"name": "Acme"}',
        })
        assert result.passed is False

    async def test_empty_brief_fails(self):
        """A brief file that is empty or effectively empty still fails."""
        result = await structural_gate("competitive", {
            "brief.md": "",
            "competitors/acme.json": '{"name": "Acme"}',
        })
        assert result.passed is False
        assert any("empty" in f.lower() for f in result.failures)

    async def test_trivial_brief_fails_char_floor(self):
        """A brief under 50 chars is treated as effectively empty."""
        result = await structural_gate("competitive", {
            "brief.md": "Short.",
            "competitors/acme.json": '{"name": "Acme"}',
        })
        assert result.passed is False

    async def test_short_brief_with_few_headers_passes(self):
        """R-#35: a brief with >50 chars and few headers now passes
        structural — length + header count are quality questions for
        the gradient + calibration judges, not structural gates."""
        result = await structural_gate("competitive", {
            "brief.md": "# Brief\n\n" + "x" * 200,
            "competitors/acme.json": '{"name": "Acme"}',
        })
        assert result.passed is True

    async def test_no_competitors_fails(self):
        result = await structural_gate("competitive", {
            "brief.md": "# Brief\n\n" + "x" * 200,
        })
        assert result.passed is False
        assert any("competitors" in f for f in result.failures)


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

    async def test_complete_session_passes(self):
        result = await structural_gate("monitoring", self._make_complete_outputs())
        assert result.passed is True
        assert result.dqs_score is not None
        assert result.dqs_score == 1.0

    async def test_missing_digest_fails(self):
        outputs = self._make_complete_outputs()
        del outputs["digest.md"]
        result = await structural_gate("monitoring", outputs)
        assert result.passed is False
        assert any("digest_exists" in f for f in result.failures)

    async def test_missing_session_md_fails(self):
        outputs = self._make_complete_outputs()
        del outputs["session.md"]
        result = await structural_gate("monitoring", outputs)
        assert result.passed is False

    async def test_incomplete_status_without_digest_fails(self):
        outputs = self._make_complete_outputs()
        outputs["session.md"] = "# Session\n\n## Status: IN_PROGRESS"
        del outputs["digest.md"]
        result = await structural_gate("monitoring", outputs)
        assert result.passed is False
        assert any("status_complete" in f for f in result.failures)

    async def test_dqs_score_computed(self):
        """DQS is computed even when some assertions fail."""
        outputs = self._make_complete_outputs()
        del outputs["digest.md"]
        result = await structural_gate("monitoring", outputs)
        assert result.dqs_score is not None
        assert 0.0 < result.dqs_score < 1.0

    async def test_low_volume_digest_only_passes(self):
        """Low-volume week: only select_mentions in results.jsonl, no stories,
        but digest.md + findings.md present. Must pass structural gate."""
        results = [{"type": "select_mentions", "sources": 3}]
        outputs = {
            "session.md": "# Session\n\n## Status: BLOCKED_PERSIST_FAILED",
            "results.jsonl": json.dumps(results[0]),
            "digest.md": "# Weekly Digest\n\nLow-volume week summary.",
            "findings.md": "# Findings\n\nNo significant findings.",
        }
        result = await structural_gate("monitoring", outputs)
        assert result.passed is True
        assert result.dqs_score is not None
        assert result.dqs_score > 0.8

    async def test_blocked_persist_with_digest_passes(self):
        """BLOCKED_PERSIST_FAILED + digest.md passes status_complete."""
        outputs = self._make_complete_outputs()
        outputs["session.md"] = "# Session\n\n## Status: BLOCKED_PERSIST_FAILED"
        result = await structural_gate("monitoring", outputs)
        assert result.passed is True

    async def test_in_progress_with_digest_passes(self):
        """IN_PROGRESS + digest.md passes status_complete."""
        outputs = self._make_complete_outputs()
        outputs["session.md"] = "# Session\n\n## Status: IN_PROGRESS"
        result = await structural_gate("monitoring", outputs)
        assert result.passed is True


class TestStoryboardStructural:
    """Storyboard domain structural validation."""

    async def test_valid_story_passes(self):
        story = {
            "title": "Test Story",
            "scene_count": 2,
            "scenes": [
                {"prompt": "A person walking", "camera": "wide", "transition": "cut"},
                {"prompt": "Close up", "camera": "close", "transition": "fade"},
            ],
        }
        result = await structural_gate("storyboard", {
            "stories/story-1.json": json.dumps(story),
        })
        assert result.passed is True

    async def test_no_stories_fails(self):
        result = await structural_gate("storyboard", {
            "patterns/style.json": '{"style": "cinematic"}',
        })
        assert result.passed is False

    async def test_invalid_json_fails(self):
        result = await structural_gate("storyboard", {
            "stories/story-1.json": "not json {",
        })
        assert result.passed is False

    async def test_missing_camera_field_fails(self):
        """Scene without a camera field (or any of its aliases) fails
        — prompt + camera are the two mandatory scene fields in the
        current storyboard validator. `transition` is not a structural
        gate."""
        story = {
            "scenes": [
                {"prompt": "A scene"},  # missing camera/camera_motion
            ],
        }
        result = await structural_gate("storyboard", {
            "stories/story-1.json": json.dumps(story),
        })
        assert result.passed is False
        assert any("camera" in f for f in result.failures)

    async def test_scene_count_mismatch_fails(self):
        story = {
            "scene_count": 5,
            "scenes": [
                {"prompt": "Scene", "camera": "wide", "transition": "cut"},
            ],
        }
        result = await structural_gate("storyboard", {
            "stories/story-1.json": json.dumps(story),
        })
        assert result.passed is False
        assert any("scene_count" in f for f in result.failures)

    async def test_empty_prompt_fails(self):
        story = {
            "scenes": [
                {"prompt": "", "camera": "wide", "transition": "cut"},
            ],
        }
        result = await structural_gate("storyboard", {
            "stories/story-1.json": json.dumps(story),
        })
        assert result.passed is False


class TestUnknownDomain:
    """Unknown domain handling."""

    async def test_unknown_domain_fails(self):
        result = await structural_gate("nonexistent", {"file.txt": "content"})
        assert result.passed is False
        assert any("Unknown domain" in f for f in result.failures)


class TestCanary:
    """Structural canary: malformed artifact should be caught."""

    async def test_canary_scene_count_mismatch(self):
        """Canary: declared scene_count doesn't match actual scenes."""
        story = {
            "scene_count": 10,
            "scenes": [
                {"prompt": "Only one scene", "camera": "wide", "transition": "cut"},
            ],
        }
        result = await structural_gate("storyboard", {
            "stories/canary.json": json.dumps(story),
        })
        assert result.passed is False
