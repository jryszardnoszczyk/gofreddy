"""Tests for evaluation scoring math — hand-calculated expected values."""

import math

import pytest

from src.evaluation.judges import geometric_mean, normalize_checklist, normalize_gradient
from src.evaluation.service import compute_length_factor


class TestNormalization:
    """Gradient and checklist normalization."""

    def test_gradient_score_1(self):
        assert normalize_gradient(1) == 0.0

    def test_gradient_score_3(self):
        assert normalize_gradient(3) == 0.5

    def test_gradient_score_5(self):
        assert normalize_gradient(5) == 1.0

    def test_gradient_score_2(self):
        assert normalize_gradient(2) == 0.25

    def test_gradient_score_4(self):
        assert normalize_gradient(4) == 0.75

    def test_checklist_all_pass(self):
        assert normalize_checklist(4) == 1.0

    def test_checklist_none_pass(self):
        assert normalize_checklist(0) == 0.0

    def test_checklist_half_pass(self):
        assert normalize_checklist(2) == 0.5

    def test_checklist_three_pass(self):
        assert normalize_checklist(3) == 0.75


class TestGeometricMean:
    """Geometric mean with floored-zero edge cases."""

    def test_all_ones(self):
        assert geometric_mean([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]) == 1.0

    def test_all_zeros(self):
        assert geometric_mean([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) == pytest.approx(0.01)

    def test_single_zero_is_floored_not_zeroed(self):
        """One zero dimension is heavily penalized but no longer kills the entire domain."""
        expected = math.prod([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.01]) ** (1 / 8)
        assert geometric_mean([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0]) == pytest.approx(expected)

    def test_uniform_values(self):
        """Geometric mean of identical values = that value."""
        assert geometric_mean([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]) == pytest.approx(0.5)

    def test_mixed_values(self):
        """Hand-calculated: geomean([0.25, 0.5, 0.75, 1.0, 0.25, 0.5, 0.75, 1.0])."""
        scores = [0.25, 0.5, 0.75, 1.0, 0.25, 0.5, 0.75, 1.0]
        expected = math.prod(scores) ** (1 / 8)
        assert geometric_mean(scores) == pytest.approx(expected, rel=1e-6)

    def test_single_weak_dimension(self):
        """One weak dimension significantly drops the score (geometric mean property)."""
        strong = geometric_mean([0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9])
        weak = geometric_mean([0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.1])
        assert weak < strong * 0.8  # Weak dimension drags score down significantly

    def test_empty_list(self):
        assert geometric_mean([]) == 0.0

    def test_geometric_vs_arithmetic(self):
        """Geometric mean <= arithmetic mean (always)."""
        scores = [0.3, 0.5, 0.7, 0.9, 0.4, 0.6, 0.8, 1.0]
        geo = geometric_mean(scores)
        arith = sum(scores) / len(scores)
        assert geo <= arith


class TestLengthNormalization:
    """Length normalization — double-sided penalty."""

    def test_within_range_no_penalty(self):
        """Content within word count range gets factor 1.0."""
        # GEO range: 800-2000 words
        text = " ".join(["word"] * 1500)
        assert compute_length_factor("geo", text) == 1.0

    def test_within_upper_buffer_no_penalty(self):
        """Content within 1.5x upper bound gets factor 1.0."""
        # GEO upper: 2000 * 1.5 = 3000
        text = " ".join(["word"] * 2800)
        assert compute_length_factor("geo", text) == 1.0

    def test_too_short_penalized(self):
        """Content below minimum gets linear penalty."""
        # GEO min: 800
        text = " ".join(["word"] * 400)
        factor = compute_length_factor("geo", text)
        assert factor == pytest.approx(0.5, rel=0.05)  # 400/800

    def test_too_long_penalized(self):
        """Content above upper buffer gets linear penalty."""
        # GEO upper buffer: 2000 * 1.5 = 3000
        text = " ".join(["word"] * 4500)
        factor = compute_length_factor("geo", text)
        assert factor < 1.0
        assert factor >= 0.3  # Floor

    def test_floor_enforced(self):
        """Very short content still gets floor value (never zero)."""
        text = "word"  # 1 word
        factor = compute_length_factor("geo", text)
        assert factor == 0.3  # Floor

    def test_unknown_domain_no_penalty(self):
        """Unknown domain gets no length penalty."""
        text = "word"
        assert compute_length_factor("unknown", text) == 1.0

    def test_storyboard_range(self):
        """Storyboard has shorter word range (300-800)."""
        text = " ".join(["word"] * 500)
        assert compute_length_factor("storyboard", text) == 1.0

    def test_competitive_range(self):
        """CI has longer word range (2000-5000)."""
        text = " ".join(["word"] * 3000)
        assert compute_length_factor("competitive", text) == 1.0


class TestCompositeScore:
    """Composite score = arithmetic mean of domain scores (DGM-H paper)."""

    def test_arithmetic_mean_four_domains(self):
        """Composite = arithmetic mean, NOT geometric mean."""
        domain_scores = {"geo": 0.8, "competitive": 0.6, "monitoring": 0.7, "storyboard": 0.5}
        composite = sum(domain_scores.values()) / len(domain_scores)
        assert composite == pytest.approx(0.65)

    def test_one_zero_domain_survives(self):
        """Arithmetic mean keeps variants alive when one domain = 0.
        This is why we use arithmetic for composite, not geometric."""
        domain_scores = {"geo": 0.9, "competitive": 0.8, "monitoring": 0.7, "storyboard": 0.0}
        composite = sum(domain_scores.values()) / len(domain_scores)
        assert composite == pytest.approx(0.6)
        # Geometric mean still penalizes the zero domain heavily, but the
        # floor prevents the entire variant from collapsing to exact zero.
        geo = geometric_mean(list(domain_scores.values()))
        assert geo > 0.0
        assert geo < composite
