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


class TestCompetitiveStructuralV33:
    """v3.3 9-check expansion (env-gated CI_STRUCTURAL_V33=1).

    Spec: docs/handoffs/2026-05-17-judge-design-step1-competitive.md §3.
    Existing 2 checks (brief exists, competitors parse) + 2 new shape
    checks (word count, Klue spine) + 5 anti-hallucination checks.
    """

    @pytest.fixture(autouse=True)
    def _enable_v33(self, monkeypatch):
        monkeypatch.setenv("CI_STRUCTURAL_V33", "1")

    @staticmethod
    def _make_v33_brief(*, target_words: int = 900) -> str:
        """Compose a v3.3-compliant brief (passes all 9 checks).

        Builds a brief approximately ``target_words`` long with the Klue
        5-section spine, an "as of" marker, a recent date, a competitor
        mention matching the default fixture below, and no fabricated
        quotes / URLs. Filler is sized so the result lands in the
        800–2,000 word band; keep ``target_words`` inside that band.
        """
        base = (
            "# Headline-as-claim: Acme is the dominant Q3 retention threat\n\n"
            "Brief written for the founder/CEO evaluating a roadmap response. "
            "As of 2026-05-15, the most consequential competitive development "
            "is Acme's vertical-SaaS pricing reset, validated against three "
            "independent signals.\n\n"
            "## Rationale\n\n"
            "The retention risk is structural, not opportunistic. Acme's "
            "data shows a 12% pricing advantage in the SMB tier on May 10, 2026.\n\n"
            "## Comparison vs other competitors\n\n"
            "Acme leads on price discipline; the alternatives in our research "
            "set lag on packaging clarity.\n\n"
            "## Implications: what to do now, where this goes next\n\n"
            "If we do nothing, the SMB-tier churn we observed in April "
            "compounds. The follow-up signal to watch is Acme's June pricing.\n\n"
            "## Recommendations\n\n"
            "Defend the SMB tier by accelerating the loyalty program. "
            "Cost: defer the analytics dashboard by one quarter."
        )
        # Pad to target_words. Each filler token contributes 1 word; insert
        # them under Comparison so the spine + dates stay intact.
        base_word_count = len(base.split())
        filler_needed = max(0, target_words - base_word_count)
        if filler_needed:
            filler = " " + (" ".join(["trajectory"] * filler_needed))
            base = base.replace(
                "Acme leads on price discipline; the alternatives in our research "
                "set lag on packaging clarity.",
                "Acme leads on price discipline; the alternatives in our research "
                "set lag on packaging clarity." + filler,
            )
        return base

    @staticmethod
    def _make_v33_outputs(**overrides) -> dict[str, str]:
        return {
            "brief.md": overrides.get(
                "brief",
                TestCompetitiveStructuralV33._make_v33_brief(),
            ),
            "competitors/acme.json": overrides.get(
                "acme",
                json.dumps({
                    "name": "Acme",
                    "summary": "Vertical-SaaS pricing reset on May 10, 2026.",
                }),
            ),
        }

    # ─── happy path ──────────────────────────────────────────────────

    async def test_v33_compliant_brief_passes_all_9_checks(self):
        result = await structural_gate("competitive", self._make_v33_outputs())
        assert result.passed is True, f"unexpected failures: {result.failures}"

    # ─── shape check #3: word count band ─────────────────────────────

    async def test_v33_word_count_below_floor_fails(self):
        short = "# Headline\n\n## Rationale\n\n## Comparison\n\n## Implications\n\n## Recommendations\n\n" + ("x " * 50)
        result = await structural_gate("competitive", self._make_v33_outputs(brief=short))
        assert result.passed is False
        assert any("word count" in f and "below floor" in f for f in result.failures)

    async def test_v33_word_count_above_ceiling_fails(self):
        long_brief = (
            "# Headline\n\n## Rationale\n\n## Comparison\n\n## Implications\n\n## Recommendations\n\n"
            + ("word " * 3000)
        )
        result = await structural_gate("competitive", self._make_v33_outputs(brief=long_brief))
        assert result.passed is False
        assert any("above ceiling" in f for f in result.failures)

    # ─── shape check #4: Klue spine ─────────────────────────────────

    async def test_v33_missing_klue_section_fails(self):
        # Drop the Recommendations section entirely.
        brief = self._make_v33_brief().replace("## Recommendations", "## TBD")
        result = await structural_gate("competitive", self._make_v33_outputs(brief=brief))
        assert result.passed is False
        assert any("Klue 5-section spine" in f and "recommendations" in f for f in result.failures)

    # ─── anti-hallucination #5: URL syntactic validity ─────────────

    async def test_v33_malformed_url_fails(self):
        brief = self._make_v33_brief() + "\n\nSource: http://example (no TLD)"
        result = await structural_gate("competitive", self._make_v33_outputs(brief=brief))
        assert result.passed is False
        assert any("URL" in f and "invalid" in f for f in result.failures)

    async def test_v33_well_formed_url_passes_url_check(self):
        brief = self._make_v33_brief() + "\n\nSource: https://acme.com/pricing-2026"
        result = await structural_gate("competitive", self._make_v33_outputs(brief=brief))
        assert result.passed is True

    # ─── anti-hallucination #6: quote-grep ──────────────────────────

    async def test_v33_fabricated_quote_fails(self):
        brief = self._make_v33_brief() + (
            "\n\nAcme's CEO said \"we will demolish the SMB market by Q4 next year\"."
        )
        result = await structural_gate("competitive", self._make_v33_outputs(brief=brief))
        assert result.passed is False
        assert any("quote" in f.lower() and "competitor data corpus" in f for f in result.failures)

    async def test_v33_grounded_quote_passes(self):
        # Quote is in the competitor JSON corpus.
        acme = json.dumps({
            "name": "Acme",
            "quotes": ["Vertical-SaaS pricing reset on May 10, 2026 across our entire SMB tier."],
        })
        brief = self._make_v33_brief() + (
            '\n\nAcme stated: "Vertical-SaaS pricing reset on May 10, 2026 '
            'across our entire SMB tier."'
        )
        outputs = self._make_v33_outputs(brief=brief, acme=acme)
        result = await structural_gate("competitive", outputs)
        assert result.passed is True, f"unexpected failures: {result.failures}"

    # ─── anti-hallucination #7: entity-existence ────────────────────

    async def test_v33_brief_does_not_mention_any_researched_competitor_fails(self):
        # Strip "Acme" references entirely.
        brief = self._make_v33_brief().replace("Acme", "Mystery Co")
        result = await structural_gate("competitive", self._make_v33_outputs(brief=brief))
        assert result.passed is False
        assert any("none of the researched competitor entities" in f for f in result.failures)

    # ─── anti-hallucination #8: "as of" date marker ─────────────────

    async def test_v33_missing_as_of_marker_fails(self):
        brief = self._make_v33_brief().replace("As of 2026-05-15, ", "")
        result = await structural_gate("competitive", self._make_v33_outputs(brief=brief))
        assert result.passed is False
        assert any('"as of <date>" freshness marker' in f for f in result.failures)

    # ─── anti-hallucination #9: ≥1 cited date within 90 days ────────

    async def test_v33_only_stale_dates_fails(self):
        # All dates are >90 days old (relative to test fixture's now).
        brief = (
            "# Headline-as-claim about Acme\n\n"
            "As of 2024-01-15, Acme has been doing the same thing since 2024-01-01.\n\n"
            "## Rationale\n\nLegacy posture from 2024-01-01.\n\n"
            "## Comparison\n\nAcme on 2024-01-15.\n\n"
            "## Implications\n\nStill from 2024-01-15.\n\n"
            "## Recommendations\n\nReset by 2024-01-31.\n\n"
            + ("filler word " * 400)
        )
        result = await structural_gate("competitive", self._make_v33_outputs(brief=brief))
        assert result.passed is False
        assert any("most recent cited date" in f and "days old" in f for f in result.failures)

    async def test_v33_no_dates_at_all_fails(self):
        brief = (
            "# Headline-as-claim about Acme\n\n"
            "Brief with no dates anywhere.\n\n"
            "## Rationale\n\nReasoning.\n\n"
            "## Comparison\n\nAcme.\n\n"
            "## Implications\n\nImpact.\n\n"
            "## Recommendations\n\nDo X.\n\n"
            + ("filler word " * 400)
        )
        result = await structural_gate("competitive", self._make_v33_outputs(brief=brief))
        assert result.passed is False
        assert any("no parseable dates" in f for f in result.failures)


class TestCompetitiveStructuralLegacyEnvDefault:
    """Verify env-default behaviour: when CI_STRUCTURAL_V33 is unset, the
    v3.3 checks are skipped and the legacy 2-check contract holds."""

    async def test_legacy_path_unaffected_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("CI_STRUCTURAL_V33", raising=False)
        # A brief that would fail every v3.3 check (no Klue spine, no word
        # count, no quotes, no dates, no competitor mention) but passes
        # the legacy 2 checks.
        result = await structural_gate("competitive", {
            "brief.md": "# Brief\n\n" + ("x " * 100),
            "competitors/acme.json": '{"name": "Acme"}',
        })
        assert result.passed is True


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
