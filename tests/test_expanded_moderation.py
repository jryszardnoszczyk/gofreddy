"""Tests for PR-014: Expanded Moderation Classes (80 GARM-Aligned)."""

import pytest

from src.analysis.service import (
    CORE_MODERATION_CLASSES,
    filter_moderation_for_tier,
)
from src.schemas import ModerationClass, ModerationDetection, Severity


def create_sample_flag(moderation_class: ModerationClass) -> ModerationDetection:
    """Create a sample moderation flag for testing."""
    return ModerationDetection(
        moderation_class=moderation_class,
        severity=Severity.MEDIUM,
        confidence=0.8,
        timestamp_start=None,
        timestamp_end=None,
        description="Test detection",
        evidence="Test evidence",
    )


class TestCoreModeration21Classes:
    """Test core 21 moderation classes constant."""

    def test_core_classes_count(self):
        """Core set should have exactly 21 classes."""
        assert len(CORE_MODERATION_CLASSES) == 21

    def test_core_classes_are_subset_of_80(self):
        """Core 21 classes should be subset of full 80."""
        all_classes = {mc.value for mc in ModerationClass}
        assert CORE_MODERATION_CLASSES.issubset(all_classes)

    def test_core_classes_match_original_pr009(self):
        """Core classes match original PR-009 implementation."""
        expected_core = {
            "adult_sexual", "nudity", "violence_graphic", "violence_mild", "gore",
            "hate_speech", "discrimination", "harassment", "profanity_strong",
            "profanity_mild", "drugs_illegal", "alcohol_excessive", "tobacco",
            "terrorism", "self_harm", "child_safety", "political", "controversial",
            "misinformation", "dangerous_activities", "spam",
        }
        assert CORE_MODERATION_CLASSES == expected_core


class TestModerationClassEnum:
    """Test ModerationClass enum has 80 GARM-aligned classes.

    Note: Plan header stated 75 but detailed specification shows 80.
    The 80 classes provide complete GARM category coverage.
    """

    def test_enum_count_is_80(self):
        """ModerationClass enum should have exactly 80 values."""
        # 21 original (PR-009) + 59 new (PR-014) = 80 total
        assert len(ModerationClass) == 80

    def test_no_duplicate_values(self):
        """Ensure no duplicate enum values."""
        values = [mc.value for mc in ModerationClass]
        assert len(values) == len(set(values)), "Duplicate enum values found"


class TestTierFiltering:
    """Test filter_moderation_for_tier function."""

    def test_pro_tier_gets_all_80_classes(self):
        """PRO tier should receive all 80 classes."""
        # Create flags with mix of core and expanded classes
        flags = [
            create_sample_flag(ModerationClass.ADULT_SEXUAL),  # core
            create_sample_flag(ModerationClass.SEXUAL_SUGGESTIVE),  # expanded
            create_sample_flag(ModerationClass.GAMBLING),  # expanded
            create_sample_flag(ModerationClass.TERRORISM),  # core
            create_sample_flag(ModerationClass.NAZI_SYMBOLS),  # expanded
        ]
        filtered = filter_moderation_for_tier(flags, tier_moderation_count=80)
        assert len(filtered) == 5  # All flags returned

    def test_free_tier_gets_only_core_classes(self):
        """FREE tier should receive only core 21 classes."""
        flags = [
            create_sample_flag(ModerationClass.ADULT_SEXUAL),  # core
            create_sample_flag(ModerationClass.SEXUAL_SUGGESTIVE),  # expanded - filtered
            create_sample_flag(ModerationClass.GAMBLING),  # expanded - filtered
            create_sample_flag(ModerationClass.TERRORISM),  # core
            create_sample_flag(ModerationClass.NAZI_SYMBOLS),  # expanded - filtered
        ]
        filtered = filter_moderation_for_tier(flags, tier_moderation_count=21)
        assert len(filtered) == 2  # Only core classes
        for flag in filtered:
            assert flag.moderation_class.value in CORE_MODERATION_CLASSES

    def test_free_tier_filters_out_expanded_classes(self):
        """Verify expanded classes are filtered for FREE tier."""
        expanded_classes = [
            ModerationClass.SEXUAL_SUGGESTIVE,
            ModerationClass.FIREARM_THREATENING,
            ModerationClass.NAZI_SYMBOLS,
            ModerationClass.PHISHING,
            ModerationClass.GAMBLING,
        ]
        flags = [create_sample_flag(mc) for mc in expanded_classes]
        filtered = filter_moderation_for_tier(flags, tier_moderation_count=21)
        assert len(filtered) == 0  # All expanded classes filtered out

    def test_free_tier_keeps_all_core_classes(self):
        """Verify core classes are kept for FREE tier."""
        core_classes_sample = [
            ModerationClass.ADULT_SEXUAL,
            ModerationClass.VIOLENCE_GRAPHIC,
            ModerationClass.HATE_SPEECH,
            ModerationClass.TERRORISM,
            ModerationClass.SPAM,
        ]
        flags = [create_sample_flag(mc) for mc in core_classes_sample]
        filtered = filter_moderation_for_tier(flags, tier_moderation_count=21)
        assert len(filtered) == 5  # All core classes kept

    def test_empty_flags_returns_empty(self):
        """Empty flags list returns empty for any tier."""
        assert filter_moderation_for_tier([], tier_moderation_count=21) == []
        assert filter_moderation_for_tier([], tier_moderation_count=80) == []

    def test_filter_preserves_flag_content(self):
        """Filtering preserves all flag attributes."""
        original_flag = ModerationDetection(
            moderation_class=ModerationClass.TERRORISM,
            severity=Severity.CRITICAL,
            confidence=0.95,
            timestamp_start="1:23",
            timestamp_end="1:45",
            description="Specific description",
            evidence="Specific evidence",
        )
        filtered = filter_moderation_for_tier([original_flag], tier_moderation_count=21)
        assert len(filtered) == 1
        result = filtered[0]
        assert result.severity == Severity.CRITICAL
        assert result.confidence == 0.95
        assert result.timestamp_start == "1:23"
        assert result.timestamp_end == "1:45"
        assert result.description == "Specific description"
        assert result.evidence == "Specific evidence"


class TestGARMCategoryCoverage:
    """Test GARM category coverage in 80-class taxonomy."""

    def test_all_11_garm_categories_covered(self):
        """Verify all 11 GARM categories have classes."""
        # Category indicators - at least one class from each
        garm_indicators = {
            1: ModerationClass.ADULT_SEXUAL,  # Adult content
            2: ModerationClass.FIREARM_THREATENING,  # Arms
            3: ModerationClass.PHYSICAL_ASSAULT,  # Crime
            4: ModerationClass.VIOLENCE_GRAPHIC,  # Death/injury
            5: ModerationClass.PIRACY_PROMOTION,  # Piracy
            6: ModerationClass.HATE_SPEECH,  # Hate speech
            7: ModerationClass.PROFANITY_STRONG,  # Profanity
            8: ModerationClass.DRUGS_ILLEGAL,  # Drugs
            9: ModerationClass.SPAM,  # Spam
            10: ModerationClass.TERRORISM,  # Terrorism
            11: ModerationClass.POLITICAL,  # Social issues
        }
        all_values = [mc.value for mc in ModerationClass]
        for category_id, indicator in garm_indicators.items():
            assert indicator.value in all_values, f"GARM category {category_id} missing indicator"

    def test_safety_classes_exist(self):
        """Verify safety classes (non-GARM) exist."""
        safety_classes = [
            ModerationClass.SELF_HARM,
            ModerationClass.CHILD_SAFETY,
            ModerationClass.DANGEROUS_ACTIVITIES,
            ModerationClass.SUICIDE_PROMOTION,
            ModerationClass.EATING_DISORDER_PRO,
        ]
        all_values = [mc.value for mc in ModerationClass]
        for cls in safety_classes:
            assert cls.value in all_values, f"Safety class {cls.value} missing"

    def test_brand_suitability_classes_exist(self):
        """Verify brand suitability classes exist."""
        brand_classes = [
            ModerationClass.GAMBLING,
            ModerationClass.CRYPTOCURRENCY_PROMO,
            ModerationClass.COUNTERFEIT,
        ]
        all_values = [mc.value for mc in ModerationClass]
        for cls in brand_classes:
            assert cls.value in all_values, f"Brand class {cls.value} missing"


class TestEnumSanityCheck:
    """Sanity check that total enums stay under Gemini limit."""

    def test_enum_count_under_limit(self):
        """Total enums should stay under Gemini's ~100-120 limit."""
        from src.schemas import CategoryVertical

        total_enums = len(ModerationClass) + len(CategoryVertical)
        # 80 moderation + 10 category verticals = 90 total
        assert total_enums == 90
        # Safe margin under ~100-120 limit
        assert total_enums <= 100
