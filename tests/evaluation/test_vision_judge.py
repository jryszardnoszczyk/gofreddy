"""U14 — vision_judge primitive (D24 / TD-41).

Per JR's 2026-05-19 model-update: backend is Gemini 3 Flash Preview.
v1 ships with dependency-injected `call_gemini` — same pattern as
citation_verifier. Tests exercise the contract + carousel rollup +
degraded-result fallbacks.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.evaluation.vision_judge import (
    VISUAL_RUBRIC_IDS,
    VisionJudgeError,
    VisionScore,
    roll_up_carousel,
    vision_judge,
)


_DUMMY_PROSE = "IE-1 rubric prose stand-in. Hook visual quality on a 1-5 scale."


def _ok_gemini(prompt: str, image_paths: list[Path]) -> str:
    return (
        '{"score": 4.2, "dimension_scores": {"stop_scroll_strength": 4.0, '
        '"focal_clarity": 4.5, "thumbnail_legibility": 4.0}, '
        '"rationale": "Strong focal subject", "failure_modes_observed": []}'
    )


def _fenced_gemini(prompt: str, image_paths: list[Path]) -> str:
    """Gemini sometimes wraps JSON in markdown fences."""
    return (
        "Here's the verdict:\n"
        "```json\n"
        '{"score": 3.0, "dimension_scores": {"focal_clarity": 3.0}, '
        '"rationale": "ok", "failure_modes_observed": ["generic_palette"]}\n'
        "```\n"
    )


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_unknown_rubric_id_raises() -> None:
    with pytest.raises(VisionJudgeError) as exc:
        vision_judge(
            "IE-4",  # text rubric, not visual
            "prose",
            [Path("/tmp/fake.png")],
            call_gemini=_ok_gemini,
        )
    assert "IE-4" in str(exc.value)
    assert "visual rubric" in str(exc.value)


def test_empty_image_paths_raises() -> None:
    with pytest.raises(VisionJudgeError) as exc:
        vision_judge("IE-1", _DUMMY_PROSE, [], call_gemini=_ok_gemini)
    assert "empty" in str(exc.value).lower()


def test_missing_call_gemini_raises() -> None:
    with pytest.raises(VisionJudgeError) as exc:
        vision_judge(
            "IE-1", _DUMMY_PROSE, [Path("/tmp/x.png")], call_gemini=None,
        )
    assert "call_gemini is required" in str(exc.value)


def test_visual_rubric_ids_set() -> None:
    """Document the visual rubric set. IE-* visual rubrics for U14
    image_engine + SE-1/5/8 added for U15b site_engine. Other IE-* and
    all AE-* / X-* / LI-* IDs route through the text-only judge service."""
    assert VISUAL_RUBRIC_IDS == frozenset({
        "IE-1", "IE-2", "IE-3", "IE-5", "IE-6",  # image_engine
        "SE-1", "SE-5", "SE-8",                    # site_engine
    })


# ---------------------------------------------------------------------------
# Happy path — single image
# ---------------------------------------------------------------------------


def test_single_image_returns_score_and_dimensions() -> None:
    score = vision_judge(
        "IE-1", _DUMMY_PROSE, [Path("/tmp/img.png")],
        call_gemini=_ok_gemini,
    )
    assert isinstance(score, VisionScore)
    assert score.rubric_id == "IE-1"
    assert score.score == pytest.approx(4.2)
    assert score.dimension_scores["focal_clarity"] == pytest.approx(4.5)
    assert score.rationale == "Strong focal subject"
    assert score.degraded is False


def test_fenced_response_parses() -> None:
    """Gemini sometimes wraps JSON in markdown code fences. The regex
    extraction tolerates this."""
    score = vision_judge(
        "IE-2", _DUMMY_PROSE, [Path("/tmp/img.png")],
        call_gemini=_fenced_gemini,
    )
    assert score.score == 3.0
    assert score.failure_modes_observed == ["generic_palette"]


# ---------------------------------------------------------------------------
# Anti-patterns context — gets baked into prompt
# ---------------------------------------------------------------------------


def test_anti_patterns_get_passed_to_gemini() -> None:
    captured: list[str] = []

    def capture(prompt: str, image_paths: list[Path]) -> str:
        captured.append(prompt)
        return '{"score": 5, "dimension_scores": {}, "rationale": "ok", "failure_modes_observed": []}'

    anti_patterns = [
        {"name": "generic_ai_palette", "regex": "lime\\+purple", "why": "AI tell"},
        {"name": "extra_fingers", "regex": "n/a", "why": "Anatomical failure"},
    ]
    vision_judge(
        "IE-5", _DUMMY_PROSE, [Path("/tmp/img.png")],
        call_gemini=capture, anti_patterns=anti_patterns,
    )
    assert len(captured) == 1
    assert "generic_ai_palette" in captured[0]
    assert "extra_fingers" in captured[0]


def test_brand_tokens_serialized_into_prompt() -> None:
    captured: list[str] = []

    def capture(prompt: str, image_paths: list[Path]) -> str:
        captured.append(prompt)
        return '{"score": 5, "dimension_scores": {}, "rationale": "ok", "failure_modes_observed": []}'

    vision_judge(
        "IE-2", _DUMMY_PROSE, [Path("/tmp/img.png")],
        call_gemini=capture,
        context={
            "brand_tokens": {"palette": ["#FF6B35", "#1F3A5F"]},
            "topic": "Botox aftercare",
        },
    )
    assert "#FF6B35" in captured[0]
    assert "Botox aftercare" in captured[0]


# ---------------------------------------------------------------------------
# Degraded modes
# ---------------------------------------------------------------------------


def test_gemini_exception_returns_degraded() -> None:
    def broken_gemini(prompt: str, image_paths: list[Path]) -> str:
        raise RuntimeError("gemini API down")

    score = vision_judge(
        "IE-1", _DUMMY_PROSE, [Path("/tmp/img.png")],
        call_gemini=broken_gemini,
    )
    assert score.degraded is True
    assert score.score == 0.0
    assert "gemini API down" in score.rationale


def test_unparseable_response_returns_degraded() -> None:
    def prose_only(prompt: str, image_paths: list[Path]) -> str:
        return "I cannot evaluate this image with the given context."

    score = vision_judge(
        "IE-1", _DUMMY_PROSE, [Path("/tmp/img.png")],
        call_gemini=prose_only,
    )
    assert score.degraded is True


# ---------------------------------------------------------------------------
# Carousel rollup
# ---------------------------------------------------------------------------


def test_roll_up_carousel_uses_min_score_gate() -> None:
    """One weak slide drags the whole carousel score per TD-41."""
    s1 = VisionScore(
        rubric_id="IE-6", score=4.5, rationale="strong cover",
        dimension_scores={"cover_hook": 4.5},
    )
    s2 = VisionScore(
        rubric_id="IE-6", score=2.0, rationale="weak slide-2",
        dimension_scores={"cover_hook": 2.0},
    )
    s3 = VisionScore(
        rubric_id="IE-6", score=4.0, rationale="ok slide-3",
        dimension_scores={"cover_hook": 4.0},
    )
    rolled = roll_up_carousel([s1, s2, s3])
    assert rolled.score == 2.0  # min gate
    assert rolled.dimension_scores["cover_hook"] == pytest.approx(
        (4.5 + 2.0 + 4.0) / 3,
    )


def test_roll_up_carousel_unions_failure_modes() -> None:
    s1 = VisionScore(
        rubric_id="IE-6", score=4.0, rationale="r1",
        failure_modes_observed=["wall_of_text"],
    )
    s2 = VisionScore(
        rubric_id="IE-6", score=3.0, rationale="r2",
        failure_modes_observed=["wall_of_text", "off_palette"],
    )
    rolled = roll_up_carousel([s1, s2])
    assert set(rolled.failure_modes_observed) == {"wall_of_text", "off_palette"}


def test_roll_up_carousel_degraded_if_any_slide_degraded() -> None:
    s1 = VisionScore(rubric_id="IE-6", score=4.0, rationale="ok")
    s2 = VisionScore(
        rubric_id="IE-6", score=0.0, rationale="degraded", degraded=True,
    )
    rolled = roll_up_carousel([s1, s2])
    assert rolled.degraded is True


def test_roll_up_carousel_rejects_mixed_rubric_ids() -> None:
    s1 = VisionScore(rubric_id="IE-6", score=4.0, rationale="r1")
    s2 = VisionScore(rubric_id="IE-1", score=3.0, rationale="r2")
    with pytest.raises(VisionJudgeError):
        roll_up_carousel([s1, s2])


def test_roll_up_carousel_empty_list_raises() -> None:
    with pytest.raises(VisionJudgeError):
        roll_up_carousel([])
