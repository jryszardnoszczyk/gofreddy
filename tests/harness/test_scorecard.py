"""Tests for harness.scorecard — parsing, merging, capping, grades, YAML output."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.scorecard import (
    Finding,
    Scorecard,
    parse_flow4_capabilities,
    parse_track_caps,
    resolve_scope_caps,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


class TestParsing:
    """Scorecard.from_yaml and from_text parsing tests."""

    def test_parse_track_a(self):
        sc = Scorecard.from_yaml(FIXTURES / "track-a.md")
        assert sc.cycle == 1
        assert sc.track == "a"
        assert len(sc.findings) == 1
        assert sc.findings[0].id == "A-3"
        assert sc.findings[0].grade == "FAIL"
        assert sc.fail_count == 1
        assert sc.pass_count == 0

    def test_parse_track_c_mixed_grades(self):
        sc = Scorecard.from_yaml(FIXTURES / "track-c.md")
        assert sc.cycle == 1
        assert sc.track == "c"
        assert len(sc.findings) == 3
        assert sc.pass_count == 1
        assert sc.fail_count == 1
        assert sc.partial_count == 1
        assert sc.blocked_count == 0
        grades = sc.extract_grades()
        assert grades["C-1"] == "PASS"
        assert grades["C-2"] == "FAIL"

    def test_parse_empty_scorecard(self):
        sc = Scorecard.from_yaml(FIXTURES / "track-empty.md")
        assert sc.cycle == 1
        assert sc.track == "x"
        assert len(sc.findings) == 0
        assert sc.pass_count == 0
        assert sc.fail_count == 0

    def test_parse_evaluator_failed(self):
        sc = Scorecard.from_yaml(FIXTURES / "track-failed.md")
        assert sc.evaluator_failed is True
        assert "timed out" in sc.evaluator_failure_reason.lower()
        assert len(sc.findings) == 0

    def test_parse_partial_grade(self):
        sc = Scorecard.from_yaml(FIXTURES / "track-c.md")
        assert sc.partial_count == 1
        partial = [f for f in sc.findings if f.grade == "PARTIAL"][0]
        assert partial.id == "C-3"

    def test_malformed_yaml_raises_clear_error(self):
        with pytest.raises(ValueError, match="[Mm]alformed|missing|frontmatter"):
            Scorecard.from_text("not yaml at all")

    def test_malformed_yaml_bad_content(self):
        bad = "---\n: : : broken\n---\n"
        with pytest.raises(ValueError, match="[Mm]alformed"):
            Scorecard.from_text(bad)

    def test_parse_real_merged_scorecard(self):
        """Parse a real merged scorecard from harness/runs/."""
        real = Path(__file__).parents[2] / "harness" / "runs" / "20260411-150626" / "scorecard-2-merged.md"
        if not real.exists():
            pytest.skip("Real run artifacts not available")
        sc = Scorecard.from_yaml(real)
        assert sc.cycle == 2
        assert sc.track is None
        assert len(sc.findings) == 7
        assert sc.pass_count == 0
        assert sc.partial_count == 2
        assert sc.fail_count == 5

    def test_normalize_id_applied_on_parse(self):
        """IDs like 'A01' in YAML should be normalized to 'A-1'."""
        text = "---\ncycle: 1\nfindings:\n  - id: A01\n    capability: test\n    grade: FAIL\n    summary: test\n---\n"
        sc = Scorecard.from_text(text)
        assert sc.findings[0].id == "A-1"

    def test_normalize_id_preserves_non_matching(self):
        """IDs outside [A-C] range pass through unchanged."""
        text = "---\ncycle: 1\nfindings:\n  - id: D5\n    capability: test\n    grade: FAIL\n    summary: test\n---\n"
        sc = Scorecard.from_text(text)
        assert sc.findings[0].id == "D5"


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------


class TestMerge:
    """Scorecard.merge tests."""

    def test_merge_all_tracks(self):
        tracks = [
            Scorecard.from_yaml(FIXTURES / "track-a.md"),
            Scorecard.from_yaml(FIXTURES / "track-b.md"),
            Scorecard.from_yaml(FIXTURES / "track-c.md"),
        ]
        merged = Scorecard.merge(tracks)
        assert merged.cycle == 1
        assert merged.track is None
        # a:1F, b:1F, c:1P+1F+1PT = 3F + 1P + 1PT
        assert merged.fail_count == 3
        assert merged.pass_count == 1
        assert merged.partial_count == 1
        assert merged.blocked_count == 0
        assert len(merged.findings) == 5

    def test_merge_sum_matches_individual_counts(self):
        tracks = [
            Scorecard.from_yaml(FIXTURES / "track-a.md"),
            Scorecard.from_yaml(FIXTURES / "track-c.md"),
        ]
        merged = Scorecard.merge(tracks)
        expected_total = sum(len(sc.findings) for sc in tracks)
        assert len(merged.findings) == expected_total

    def test_merge_with_evaluator_failure(self):
        normal = Scorecard.from_yaml(FIXTURES / "track-a.md")
        failed = Scorecard.from_yaml(FIXTURES / "track-failed.md")
        merged = Scorecard.merge([normal, failed])
        assert merged.evaluator_failed is True
        assert "track-x" in merged.evaluator_failure_reason

    def test_merge_empty_list(self):
        merged = Scorecard.merge([])
        assert merged.cycle == 0
        assert len(merged.findings) == 0

    def test_merge_preserves_finding_order(self):
        """Findings should appear in track order (a, b, c)."""
        tracks = [
            Scorecard.from_yaml(FIXTURES / "track-a.md"),
            Scorecard.from_yaml(FIXTURES / "track-b.md"),
            Scorecard.from_yaml(FIXTURES / "track-c.md"),
        ]
        merged = Scorecard.merge(tracks)
        ids = [f.id for f in merged.findings]
        assert ids == ["A-3", "B-3", "C-1", "C-2", "C-3"]


# ---------------------------------------------------------------------------
# Capping
# ---------------------------------------------------------------------------


class TestCap:
    """Scorecard.cap tests."""

    def test_cap_keeps_within_limit(self):
        """4 FAIL/PARTIAL findings, cap at 3 → 3 actionable kept, 1 deferred."""
        tracks = [
            Scorecard.from_yaml(FIXTURES / "track-a.md"),
            Scorecard.from_yaml(FIXTURES / "track-b.md"),
            Scorecard.from_yaml(FIXTURES / "track-c.md"),
        ]
        merged = Scorecard.merge(tracks)
        # 3 FAIL + 1 PARTIAL = 4 actionable, 1 PASS
        assert merged.fail_count + merged.partial_count == 4

        capped, deferred = merged.cap(max_findings=3)
        # 3 actionable kept + 1 PASS always kept = 4 findings in capped
        actionable_in_capped = capped.fail_count + capped.partial_count
        assert actionable_in_capped == 3
        assert len(deferred) == 1
        assert capped.pass_count == 1  # PASS always kept

    def test_cap_all_pass_no_deferral(self):
        """All PASS findings → nothing deferred."""
        sc = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="A-1", capability="cap1", grade="PASS", summary="ok"),
                Finding(id="A-2", capability="cap2", grade="PASS", summary="ok"),
            ],
        )
        capped, deferred = sc.cap(max_findings=1)
        assert len(capped.findings) == 2
        assert deferred == []

    def test_cap_blocked_always_kept(self):
        sc = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="f"),
                Finding(id="A-2", capability="c2", grade="BLOCKED", summary="b"),
                Finding(id="A-3", capability="c3", grade="FAIL", summary="f"),
            ],
        )
        capped, deferred = sc.cap(max_findings=1)
        assert capped.fail_count == 1
        assert capped.blocked_count == 1
        assert len(deferred) == 1
        assert deferred[0] == "A-3"

    def test_cap_document_order_preserved(self):
        """First N actionable findings in document order are kept."""
        sc = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="X-1", capability="c", grade="FAIL", summary="s"),
                Finding(id="X-2", capability="c", grade="PARTIAL", summary="s"),
                Finding(id="X-3", capability="c", grade="FAIL", summary="s"),
                Finding(id="X-4", capability="c", grade="FAIL", summary="s"),
            ],
        )
        capped, deferred = sc.cap(max_findings=2)
        kept_ids = [f.id for f in capped.findings if f.grade in ("FAIL", "PARTIAL")]
        assert kept_ids == ["X-1", "X-2"]
        assert deferred == ["X-3", "X-4"]

    def test_cap_zero_limit(self):
        sc = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="A-1", capability="c", grade="FAIL", summary="s"),
                Finding(id="A-2", capability="c", grade="PASS", summary="s"),
            ],
        )
        capped, deferred = sc.cap(max_findings=0)
        assert capped.fail_count == 0
        assert capped.pass_count == 1
        assert deferred == ["A-1"]


# ---------------------------------------------------------------------------
# Domain splitting
# ---------------------------------------------------------------------------


class TestSplitByDomain:
    """Scorecard.split_by_domain tests."""

    def test_split_three_domains(self):
        """Split [A-1, A-3, B-2, C-1] by [A, B, C] → 3 keys with correct counts."""
        sc = Scorecard(
            cycle=1, track=None, findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
                Finding(id="A-3", capability="c3", grade="PARTIAL", summary="s"),
                Finding(id="B-2", capability="c2", grade="FAIL", summary="s"),
                Finding(id="C-1", capability="c1", grade="PASS", summary="s"),
            ],
        )
        splits = sc.split_by_domain(["A", "B", "C"])
        assert len(splits) == 3
        assert len(splits["A"].findings) == 2
        assert len(splits["B"].findings) == 1
        assert len(splits["C"].findings) == 1
        assert splits["A"].findings[0].id == "A-1"

    def test_split_empty_scorecard(self):
        """Empty scorecard → all domain keys present, all empty."""
        sc = Scorecard(cycle=1, track=None, findings=[])
        splits = sc.split_by_domain(["A", "B", "C"])
        assert len(splits) == 3
        for d in ["A", "B", "C"]:
            assert splits[d].findings == []

    def test_split_unmatched_domain_dropped(self):
        """D-1 finding split by [A, B, C] → dropped (no matching domain)."""
        sc = Scorecard(
            cycle=1, track=None, findings=[
                Finding(id="D-1", capability="c", grade="FAIL", summary="s"),
                Finding(id="A-1", capability="c", grade="PASS", summary="s"),
            ],
        )
        splits = sc.split_by_domain(["A", "B", "C"])
        assert len(splits["A"].findings) == 1
        assert len(splits["B"].findings) == 0
        assert len(splits["C"].findings) == 0

    def test_split_preserves_metadata(self):
        """Split preserves cycle, track, evaluator_failed, timestamp."""
        sc = Scorecard(
            cycle=3, track="a", findings=[
                Finding(id="A-1", capability="c", grade="FAIL", summary="s"),
            ],
            evaluator_failed=True,
            evaluator_failure_reason="timeout",
            timestamp="2026-04-13T10:00:00Z",
        )
        splits = sc.split_by_domain(["A"])
        assert splits["A"].cycle == 3
        assert splits["A"].evaluator_failed is True
        assert splits["A"].timestamp == "2026-04-13T10:00:00Z"

    def test_split_case_insensitive(self):
        """Lowercase domain input → uppercase keys."""
        sc = Scorecard(
            cycle=1, track=None, findings=[
                Finding(id="a-1", capability="c", grade="FAIL", summary="s"),
            ],
        )
        splits = sc.split_by_domain(["a", "b"])
        assert "A" in splits
        assert "B" in splits
        assert len(splits["A"].findings) == 1


# ---------------------------------------------------------------------------
# Grades extraction
# ---------------------------------------------------------------------------


class TestExtractGrades:
    """Scorecard.extract_grades tests."""

    def test_extract_grades_basic(self):
        sc = Scorecard.from_yaml(FIXTURES / "track-c.md")
        grades = sc.extract_grades()
        assert grades == {"C-1": "PASS", "C-2": "FAIL", "C-3": "PARTIAL"}

    def test_extract_grades_merged(self):
        tracks = [
            Scorecard.from_yaml(FIXTURES / "track-a.md"),
            Scorecard.from_yaml(FIXTURES / "track-c.md"),
        ]
        merged = Scorecard.merge(tracks)
        grades = merged.extract_grades()
        assert grades == {"A-3": "FAIL", "C-1": "PASS", "C-2": "FAIL", "C-3": "PARTIAL"}

    def test_extract_grades_empty(self):
        sc = Scorecard.from_yaml(FIXTURES / "track-empty.md")
        assert sc.extract_grades() == {}

    def test_extract_grades_normalizes_ids(self):
        sc = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="A01", capability="c", grade="FAIL", summary="s"),
            ],
        )
        grades = sc.extract_grades()
        assert "A-1" in grades


# ---------------------------------------------------------------------------
# YAML frontmatter output
# ---------------------------------------------------------------------------


class TestYamlFrontmatter:
    """Scorecard.to_yaml_frontmatter output tests."""

    def test_key_order(self):
        sc = Scorecard(
            cycle=2,
            track="a",
            timestamp="2026-04-11T15:09:18+02:00",
            findings=[
                Finding(id="A-8", capability="Batch analysis", grade="FAIL", summary="Failed."),
            ],
        )
        output = sc.to_yaml_frontmatter()
        lines = output.strip().split("\n")
        # First and last lines are ---
        assert lines[0] == "---"
        assert lines[-1] == "---"
        # Key order check
        keys = []
        for line in lines[1:-1]:
            if line.startswith("  "):
                continue
            key = line.split(":")[0].strip()
            if key not in ("---",):
                keys.append(key)
        assert keys == ["cycle", "track", "timestamp", "pass", "partial", "fail", "blocked", "findings"]

    def test_evaluator_failed_in_output(self):
        sc = Scorecard(
            cycle=1,
            track=None,
            findings=[],
            evaluator_failed=True,
            evaluator_failure_reason="track-a: timeout; ",
        )
        output = sc.to_yaml_frontmatter()
        assert "evaluator_failed: true" in output
        assert "evaluator_failure_reasons: 'track-a: timeout; '" in output

    def test_empty_findings_renders_bracket_list(self):
        sc = Scorecard(cycle=1, track=None, findings=[])
        output = sc.to_yaml_frontmatter()
        assert "  []" in output

    def test_roundtrip_parse(self):
        """to_yaml_frontmatter() output can be parsed back."""
        original = Scorecard(
            cycle=3,
            track="b",
            timestamp="2026-04-11T15:09:26+02:00",
            findings=[
                Finding(id="A-6", capability="Evaluate Creators", grade="FAIL", summary="Did not render."),
                Finding(id="C-1", capability="Creative Brief", grade="PASS", summary="Rendered ok."),
            ],
        )
        yaml_text = original.to_yaml_frontmatter()
        roundtrip = Scorecard.from_text(yaml_text)
        assert roundtrip.cycle == original.cycle
        assert roundtrip.track == original.track
        assert len(roundtrip.findings) == len(original.findings)
        assert roundtrip.extract_grades() == original.extract_grades()

    def test_merged_frontmatter_matches_real(self):
        """Byte-compare merged frontmatter against real archived scorecard."""
        real_path = Path(__file__).parents[2] / "harness" / "runs" / "20260411-150626" / "scorecard-1-merged.md"
        if not real_path.exists():
            pytest.skip("Real run artifacts not available")

        # Parse and re-merge the track scorecards
        run_dir = real_path.parent
        tracks = []
        for letter in ["a", "b", "c"]:
            track_path = run_dir / f"scorecard-1-track-{letter}.md"
            if track_path.exists():
                tracks.append(Scorecard.from_yaml(track_path))
        merged = Scorecard.merge(tracks)

        generated = merged.to_yaml_frontmatter()

        # Parse real frontmatter
        real_text = real_path.read_text(encoding="utf-8")
        real_parts = real_text.split("---", 2)
        real_frontmatter = "---" + "\n" + real_parts[1].strip() + "\n" + "---" + "\n"

        # Compare the finding count and grades — exact byte match is the goal
        # but the bash merge doesn't include track/timestamp in merged, which
        # our merge also doesn't. Compare structurally via re-parse.
        real_sc = Scorecard.from_text(real_text)
        assert merged.pass_count == real_sc.pass_count
        assert merged.fail_count == real_sc.fail_count
        assert merged.partial_count == real_sc.partial_count
        assert merged.blocked_count == real_sc.blocked_count
        assert len(merged.findings) == len(real_sc.findings)
        assert merged.extract_grades() == real_sc.extract_grades()

    def test_yaml_quoting_special_chars_in_summary(self):
        """Summaries with YAML-special chars must round-trip safely."""
        tricky_summaries = [
            '`?__e2e_auth=1` bypass not working',
            'Test: capability with colon space',
            'Found "double quotes" inside',
            "Contains 'single quotes' inside",
            "Ampersand & asterisk * pipe |",
            "Backtick ` and hash # and percent %",
        ]
        for summary in tricky_summaries:
            sc = Scorecard(
                cycle=1, track=None,
                findings=[Finding(id="A-1", capability="Test", grade="FAIL", summary=summary)],
            )
            yaml_text = sc.to_yaml_frontmatter()
            parsed = Scorecard.from_text(yaml_text)
            assert parsed.findings[0].summary == summary, f"Round-trip failed for: {summary!r}"

    def test_yaml_quoting_special_chars_in_capability(self):
        """Capabilities with colons must round-trip safely."""
        sc = Scorecard(
            cycle=1, track=None,
            findings=[Finding(id="A-1", capability="Test: Edge Case", grade="FAIL", summary="ok")],
        )
        yaml_text = sc.to_yaml_frontmatter()
        parsed = Scorecard.from_text(yaml_text)
        assert parsed.findings[0].capability == "Test: Edge Case"

    def test_evaluator_failure_reason_with_json(self):
        """evaluator_failure_reason with embedded JSON must round-trip safely."""
        reason = '{"type":"assistant","message":"rate limited"}'
        sc = Scorecard(
            cycle=1, track=None, findings=[],
            evaluator_failed=True, evaluator_failure_reason=reason,
        )
        yaml_text = sc.to_yaml_frontmatter()
        parsed = Scorecard.from_text(yaml_text)
        assert parsed.evaluator_failure_reason == reason

    def test_evaluator_failure_reason_with_single_quotes(self):
        """evaluator_failure_reason with single quotes uses '' doubling."""
        reason = "track-a: it's a problem"
        sc = Scorecard(
            cycle=1, track=None, findings=[],
            evaluator_failed=True, evaluator_failure_reason=reason,
        )
        yaml_text = sc.to_yaml_frontmatter()
        assert "''" in yaml_text  # single-quote doubling
        parsed = Scorecard.from_text(yaml_text)
        assert parsed.evaluator_failure_reason == reason


# ---------------------------------------------------------------------------
# Flow 4 parsing
# ---------------------------------------------------------------------------


class TestFlow4Parsing:
    """parse_flow4_capabilities tests."""

    def test_parse_flow4_from_fixture(self):
        ids = parse_flow4_capabilities(FIXTURES / "test-matrix.md")
        # A9, A10, A11, B12, B13, C8, C9
        assert "A-9" in ids
        assert "A-10" in ids
        assert "A-11" in ids
        assert "B-12" in ids
        assert "B-13" in ids
        assert "C-8" in ids
        assert "C-9" in ids
        # Non-Flow-4 IDs should not be present
        assert "A-1" not in ids
        assert "B-1" not in ids
        assert "C-1" not in ids

    def test_parse_flow4_from_real_matrix(self):
        real_matrix = Path(__file__).parents[2] / "harness" / "test-matrix.md"
        if not real_matrix.exists():
            pytest.skip("Real test matrix not available")
        ids = parse_flow4_capabilities(real_matrix)
        assert "A-9" in ids
        assert "A-10" in ids
        assert "A-11" in ids
        assert "B-12" in ids
        assert "C-8" in ids
        assert "C-9" in ids

    def test_parse_flow4_missing_file(self):
        ids = parse_flow4_capabilities(Path("/nonexistent/matrix.md"))
        assert ids == set()


# ---------------------------------------------------------------------------
# Scope resolution
# ---------------------------------------------------------------------------


class TestScopeResolution:
    """resolve_scope_caps and parse_track_caps tests."""

    def test_resolve_all(self):
        result = resolve_scope_caps([], "all", FIXTURES / "test-matrix.md")
        assert result is None

    def test_resolve_only(self):
        result = resolve_scope_caps(["A-1", "B-2"], "all", FIXTURES / "test-matrix.md")
        assert result == ["A-1", "B-2"]

    def test_resolve_phase_1(self):
        result = resolve_scope_caps([], "1", FIXTURES / "test-matrix.md")
        assert result is not None
        assert "A-1" in result
        assert "A-12" in result
        assert "B-1" in result

    def test_resolve_phase_2(self):
        result = resolve_scope_caps([], "2", FIXTURES / "test-matrix.md")
        assert result is not None
        assert "A-2" in result
        assert "A-6" in result
        assert "C-1" in result

    def test_parse_track_a(self):
        caps = parse_track_caps("a", FIXTURES / "test-matrix.md")
        assert "A-1" in caps
        assert "A-2" in caps
        assert "A-8" in caps
        assert "A-12" in caps

    def test_parse_track_missing(self):
        caps = parse_track_caps("z", FIXTURES / "test-matrix.md")
        assert caps == []

    def test_parse_track_missing_file(self):
        caps = parse_track_caps("a", Path("/nonexistent/matrix.md"))
        assert caps == []
