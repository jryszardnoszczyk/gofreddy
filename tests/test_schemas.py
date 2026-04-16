"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from src.schemas import (
    AgeBucket,
    AgeDistribution,
    AudienceDemographics,
    CategoryVertical,
    ContentCategory,
    CreativePatterns,
    GenderDistribution,
    GeographyInference,
    IncomeBucket,
    IncomeDistribution,
    InferredInterests,
    ModerationClass,
    ModerationDetection,
    RiskCategory,
    RiskDetection,
    Severity,
    SponsoredContent,
    VideoAnalysis,
)


class TestRiskCategory:
    """Test RiskCategory enum."""

    def test_all_categories_exist(self):
        """Verify all expected risk categories are defined."""
        expected = [
            "controversial_statement",
            "hate_symbols",
            "substance_use",
            "violence",
            "political_content",
            "adult_content",
            "competitor_product",
        ]
        actual = [cat.value for cat in RiskCategory]
        assert sorted(actual) == sorted(expected)


class TestSeverity:
    """Test Severity enum."""

    def test_all_severities_exist(self):
        """Verify all expected severity levels are defined."""
        expected = ["none", "low", "medium", "high", "critical"]
        actual = [sev.value for sev in Severity]
        assert sorted(actual) == sorted(expected)

    def test_severity_none_exists(self):
        """Verify NONE severity level exists for PR-009."""
        assert Severity.NONE.value == "none"


class TestRiskDetection:
    """Test RiskDetection model."""

    def test_valid_risk_detection(self):
        """Test creating a valid risk detection."""
        risk = RiskDetection(
            category=RiskCategory.VIOLENCE,
            severity=Severity.HIGH,
            confidence=0.9,
            timestamp_start="1:30",
            timestamp_end="1:45",
            description="Fighting scene",
            evidence="Two people fighting in the video",
        )
        assert risk.category == RiskCategory.VIOLENCE
        assert risk.severity == Severity.HIGH
        assert risk.confidence == 0.9

    def test_timestamp_validation_valid_formats(self):
        """Test valid timestamp formats."""
        valid_timestamps = ["0:00", "0:45", "1:23", "12:34", "00:45"]
        for ts in valid_timestamps:
            risk = RiskDetection(
                category=RiskCategory.VIOLENCE,
                severity=Severity.LOW,
                confidence=0.5,
                timestamp_start=ts,
                description="Test",
                evidence="Test evidence",
            )
            assert risk.timestamp_start == ts

    def test_timestamp_validation_invalid_formats(self):
        """Test invalid timestamp formats are rejected."""
        invalid_timestamps = ["1:2", "123:45", "1:234", "abc", "1:2:3", ""]
        for ts in invalid_timestamps:
            with pytest.raises(ValidationError):
                RiskDetection(
                    category=RiskCategory.VIOLENCE,
                    severity=Severity.LOW,
                    confidence=0.5,
                    timestamp_start=ts,
                    description="Test",
                    evidence="Test evidence",
                )

    def test_timestamp_none_allowed(self):
        """Test that None timestamps are allowed."""
        risk = RiskDetection(
            category=RiskCategory.VIOLENCE,
            severity=Severity.LOW,
            confidence=0.5,
            timestamp_start=None,
            timestamp_end=None,
            description="Test",
            evidence="Test evidence",
        )
        assert risk.timestamp_start is None
        assert risk.timestamp_end is None

    def test_confidence_range_validation(self):
        """Test confidence must be between 0 and 1."""
        with pytest.raises(ValidationError):
            RiskDetection(
                category=RiskCategory.VIOLENCE,
                severity=Severity.LOW,
                confidence=1.5,  # Invalid
                description="Test",
                evidence="Test evidence",
            )

        with pytest.raises(ValidationError):
            RiskDetection(
                category=RiskCategory.VIOLENCE,
                severity=Severity.LOW,
                confidence=-0.1,  # Invalid
                description="Test",
                evidence="Test evidence",
            )


class TestVideoAnalysis:
    """Test VideoAnalysis model."""

    def test_valid_video_analysis_safe(self):
        """Test creating a valid safe video analysis."""
        analysis = VideoAnalysis(
            video_id="test_001",
            overall_safe=True,
            overall_confidence=0.95,
            risks_detected=[],
            summary="No risks detected in this video.",
        )
        assert analysis.video_id == "test_001"
        assert analysis.overall_safe is True
        assert len(analysis.risks_detected) == 0

    def test_valid_video_analysis_unsafe(self):
        """Test creating a valid unsafe video analysis."""
        risk = RiskDetection(
            category=RiskCategory.VIOLENCE,
            severity=Severity.HIGH,
            confidence=0.9,
            description="Violence detected",
            evidence="Fighting scene at 1:30",
        )
        analysis = VideoAnalysis(
            video_id="test_002",
            overall_safe=False,
            overall_confidence=0.85,
            risks_detected=[risk],
            summary="Violence detected in video.",
        )
        assert analysis.overall_safe is False
        assert len(analysis.risks_detected) == 1
        assert analysis.risks_detected[0].category == RiskCategory.VIOLENCE

    def test_default_values(self):
        """Test default values are set correctly."""
        analysis = VideoAnalysis(
            video_id="test_003",
            overall_safe=True,
            overall_confidence=0.9,
            summary="Test summary",
        )
        assert analysis.processing_time_seconds == 0.0
        assert analysis.token_count == 0
        assert analysis.error is None
        assert analysis.risks_detected == []

    def test_error_field(self):
        """Test error field for failed analysis."""
        analysis = VideoAnalysis(
            video_id="test_004",
            overall_safe=False,
            overall_confidence=0.0,
            summary="Analysis failed",
            error="API timeout",
        )
        assert analysis.error == "API timeout"


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_risk_detection_to_dict(self):
        """Test RiskDetection serialization."""
        risk = RiskDetection(
            category=RiskCategory.VIOLENCE,
            severity=Severity.HIGH,
            confidence=0.9,
            description="Test",
            evidence="Test evidence",
        )
        data = risk.model_dump()
        assert data["category"] == "violence"
        assert data["severity"] == "high"

    def test_video_analysis_to_dict(self):
        """Test VideoAnalysis serialization."""
        analysis = VideoAnalysis(
            video_id="test_001",
            overall_safe=True,
            overall_confidence=0.95,
            summary="Safe video",
        )
        data = analysis.model_dump()
        assert data["video_id"] == "test_001"
        assert data["overall_safe"] is True
        assert "risks_detected" in data

    def test_video_analysis_from_dict(self):
        """Test VideoAnalysis deserialization."""
        data = {
            "video_id": "test_001",
            "overall_safe": True,
            "overall_confidence": 0.95,
            "risks_detected": [],
            "summary": "Safe video",
        }
        analysis = VideoAnalysis(**data)
        assert analysis.video_id == "test_001"
        assert analysis.overall_safe is True


# ─── PR-009: Content Categorization + Moderation Tests ────────────────────────


class TestModerationClass:
    """Test ModerationClass enum (PR-014: 80 GARM-aligned classes)."""

    def test_all_80_moderation_classes_exist(self):
        """Verify all 80 moderation classes are defined (PR-014)."""
        actual = [mc.value for mc in ModerationClass]
        assert len(actual) == 80, f"Expected 80 classes, got {len(actual)}"

    def test_garm_category_coverage(self):
        """Verify all GARM categories have expected class counts."""
        all_classes = [mc.value for mc in ModerationClass]

        # Define expected classes per category
        garm_adult = ["adult_sexual", "nudity", "sexual_suggestive", "sexual_text",
                      "sexual_audio", "lingerie_revealing", "animated_sexual", "dating_content"]
        garm_arms = ["firearm_threatening", "firearm_displayed", "firearm_animated",
                     "knife_threatening", "explosive_device", "weapon_modification"]
        garm_crime = ["physical_assault", "domestic_violence", "animal_cruelty",
                      "theft_robbery", "vandalism", "doxxing", "revenge_content", "illegal_activity"]
        garm_death = ["violence_graphic", "violence_mild", "gore", "corpse_visible",
                      "accident_aftermath", "medical_graphic", "military_combat", "torture"]
        garm_piracy = ["piracy_promotion", "piracy_links", "copyright_violation"]
        garm_hate = ["hate_speech", "discrimination", "harassment", "nazi_symbols",
                     "white_supremacy", "terrorist_symbols", "racial_slurs", "religious_hate"]
        garm_profanity = ["profanity_strong", "profanity_mild", "gesture_offensive", "insult_degrading"]
        garm_drugs = ["drugs_illegal", "alcohol_excessive", "tobacco", "drug_manufacturing",
                      "drug_dealing", "drug_paraphernalia", "prescription_abuse", "intoxication"]
        garm_spam = ["spam", "phishing", "financial_scam", "fake_giveaway", "impersonation", "clickbait_misleading"]
        garm_terrorism = ["terrorism", "terrorist_propaganda", "terrorist_attack",
                          "extremist_recruitment", "bomb_making"]
        garm_social = ["political", "controversial", "misinformation", "election_misinfo",
                       "health_misinfo", "conspiracy_harmful", "manipulated_media", "crisis_misinfo"]
        safety = ["self_harm", "child_safety", "dangerous_activities", "suicide_promotion", "eating_disorder_pro"]
        brand = ["gambling", "cryptocurrency_promo", "counterfeit"]

        # Verify each category
        assert len(garm_adult) == 8, "Adult category should have 8 classes"
        assert len(garm_arms) == 6, "Arms category should have 6 classes"
        assert len(garm_crime) == 8, "Crime category should have 8 classes"
        assert len(garm_death) == 8, "Death category should have 8 classes"
        assert len(garm_piracy) == 3, "Piracy category should have 3 classes"
        assert len(garm_hate) == 8, "Hate category should have 8 classes"
        assert len(garm_profanity) == 4, "Profanity category should have 4 classes"
        assert len(garm_drugs) == 8, "Drugs category should have 8 classes"
        assert len(garm_spam) == 6, "Spam category should have 6 classes"
        assert len(garm_terrorism) == 5, "Terrorism category should have 5 classes"
        assert len(garm_social) == 8, "Social category should have 8 classes"
        assert len(safety) == 5, "Safety category should have 5 classes"
        assert len(brand) == 3, "Brand category should have 3 classes"

        # Verify all classes exist in enum
        all_expected = (garm_adult + garm_arms + garm_crime + garm_death + garm_piracy +
                        garm_hate + garm_profanity + garm_drugs + garm_spam + garm_terrorism +
                        garm_social + safety + brand)
        for cls in all_expected:
            assert cls in all_classes, f"Missing class: {cls}"

        # Verify total count (80 = 21 original + 59 new)
        assert len(all_expected) == 80

    def test_core_21_classes_exist(self):
        """Verify core 21 classes (original PR-009) are still present."""
        core_classes = [
            "adult_sexual", "nudity", "violence_graphic", "violence_mild", "gore",
            "hate_speech", "discrimination", "harassment", "profanity_strong",
            "profanity_mild", "drugs_illegal", "alcohol_excessive", "tobacco",
            "terrorism", "self_harm", "child_safety", "political", "controversial",
            "misinformation", "dangerous_activities", "spam",
        ]
        actual = [mc.value for mc in ModerationClass]
        for cls in core_classes:
            assert cls in actual, f"Core class missing: {cls}"

    def test_moderation_class_is_strenum(self):
        """Verify ModerationClass uses StrEnum for cleaner serialization."""
        assert ModerationClass.ADULT_SEXUAL == "adult_sexual"
        assert str(ModerationClass.ADULT_SEXUAL) == "adult_sexual"

    def test_new_classes_exist(self):
        """Verify new expanded classes (PR-014) are present."""
        new_classes = [
            "sexual_suggestive", "sexual_text", "sexual_audio",
            "firearm_threatening", "firearm_displayed",
            "physical_assault", "domestic_violence",
            "nazi_symbols", "white_supremacy",
            "phishing", "financial_scam",
            "terrorist_propaganda", "bomb_making",
            "election_misinfo", "health_misinfo",
            "suicide_promotion", "eating_disorder_pro",
            "gambling", "cryptocurrency_promo", "counterfeit",
        ]
        actual = [mc.value for mc in ModerationClass]
        for cls in new_classes:
            assert cls in actual, f"New class missing: {cls}"


class TestCategoryVertical:
    """Test CategoryVertical enum (PR-009)."""

    def test_all_10_verticals_exist(self):
        """Verify all 10 category verticals are defined."""
        expected = [
            "entertainment",
            "lifestyle",
            "education",
            "sports_fitness",
            "technology",
            "food_travel",
            "news_politics",
            "family",
            "creative",
            "other",
        ]
        actual = [cv.value for cv in CategoryVertical]
        assert sorted(actual) == sorted(expected)
        assert len(actual) == 10


class TestContentCategory:
    """Test ContentCategory model (PR-009)."""

    def test_valid_content_category(self):
        """Test creating a valid content category."""
        category = ContentCategory(
            vertical=CategoryVertical.TECHNOLOGY,
            sub_category="gaming",
            confidence=0.85,
            is_primary=True,
        )
        assert category.vertical == CategoryVertical.TECHNOLOGY
        assert category.sub_category == "gaming"
        assert category.confidence == 0.85
        assert category.is_primary is True

    def test_confidence_validation(self):
        """Test confidence must be between 0 and 1."""
        with pytest.raises(ValidationError):
            ContentCategory(
                vertical=CategoryVertical.TECHNOLOGY,
                sub_category="gaming",
                confidence=1.5,
            )

    def test_default_is_primary_false(self):
        """Test is_primary defaults to False."""
        category = ContentCategory(
            vertical=CategoryVertical.LIFESTYLE,
            sub_category="beauty",
            confidence=0.7,
        )
        assert category.is_primary is False


class TestModerationDetection:
    """Test ModerationDetection model (PR-009)."""

    def test_valid_moderation_detection(self):
        """Test creating a valid moderation detection."""
        detection = ModerationDetection(
            moderation_class=ModerationClass.VIOLENCE_GRAPHIC,
            severity=Severity.HIGH,
            confidence=0.9,
            timestamp_start="1:30",
            timestamp_end="1:45",
            description="Graphic violence in scene",
            evidence="Blood visible, physical assault",
        )
        assert detection.moderation_class == ModerationClass.VIOLENCE_GRAPHIC
        assert detection.severity == Severity.HIGH
        assert detection.confidence == 0.9

    def test_timestamp_validation(self):
        """Test timestamp format validation."""
        with pytest.raises(ValidationError):
            ModerationDetection(
                moderation_class=ModerationClass.PROFANITY_STRONG,
                severity=Severity.MEDIUM,
                confidence=0.8,
                timestamp_start="invalid",
                description="Profanity detected",
                evidence="F-word used",
            )

    def test_description_max_length(self):
        """Test description max length constraint."""
        long_description = "x" * 501
        with pytest.raises(ValidationError):
            ModerationDetection(
                moderation_class=ModerationClass.SPAM,
                severity=Severity.LOW,
                confidence=0.6,
                description=long_description,
                evidence="Short",
            )

    def test_severity_none_allowed(self):
        """Test NONE severity is valid for checked-but-not-detected."""
        detection = ModerationDetection(
            moderation_class=ModerationClass.TERRORISM,
            severity=Severity.NONE,
            confidence=0.95,
            description="Checked, not detected",
            evidence="No terrorist content found",
        )
        assert detection.severity == Severity.NONE


class TestSponsoredContent:
    """Test SponsoredContent model (PR-009)."""

    def test_valid_sponsored_content(self):
        """Test creating valid sponsored content detection."""
        sponsored = SponsoredContent(
            is_sponsored=True,
            confidence=0.9,
            disclosure_detected=True,
            disclosure_clarity_score=0.8,
            signals=["hashtag_ad", "verbal_disclosure"],
            brands_detected=["Nike", "Apple"],
        )
        assert sponsored.is_sponsored is True
        assert sponsored.confidence == 0.9
        assert sponsored.disclosure_detected is True
        assert sponsored.disclosure_clarity_score == 0.8
        assert "hashtag_ad" in sponsored.signals

    def test_not_sponsored_content(self):
        """Test non-sponsored content detection."""
        sponsored = SponsoredContent(
            is_sponsored=False,
            confidence=0.95,
        )
        assert sponsored.is_sponsored is False
        assert sponsored.disclosure_detected is False
        assert sponsored.disclosure_clarity_score is None
        assert sponsored.signals == []
        assert sponsored.brands_detected == []

    def test_disclosure_clarity_score_range(self):
        """Test disclosure_clarity_score must be 0-1."""
        with pytest.raises(ValidationError):
            SponsoredContent(
                is_sponsored=True,
                confidence=0.8,
                disclosure_clarity_score=1.5,
            )


class TestVideoAnalysisExtended:
    """Test extended VideoAnalysis model (PR-009)."""

    def test_video_analysis_with_new_fields(self):
        """Test VideoAnalysis with content categories, moderation, and sponsored."""
        category = ContentCategory(
            vertical=CategoryVertical.ENTERTAINMENT,
            sub_category="comedy",
            confidence=0.9,
            is_primary=True,
        )
        moderation = ModerationDetection(
            moderation_class=ModerationClass.PROFANITY_MILD,
            severity=Severity.LOW,
            confidence=0.7,
            description="Mild profanity",
            evidence="Crude language used",
        )
        sponsored = SponsoredContent(
            is_sponsored=False,
            confidence=0.95,
        )

        analysis = VideoAnalysis(
            video_id="test_extended",
            overall_safe=True,
            overall_confidence=0.9,
            summary="Safe comedy video with mild language",
            content_categories=[category],
            moderation_flags=[moderation],
            sponsored_content=sponsored,
        )

        assert len(analysis.content_categories) == 1
        assert analysis.content_categories[0].vertical == CategoryVertical.ENTERTAINMENT
        assert len(analysis.moderation_flags) == 1
        assert analysis.moderation_flags[0].moderation_class == ModerationClass.PROFANITY_MILD
        assert analysis.sponsored_content is not None
        assert analysis.sponsored_content.is_sponsored is False

    def test_video_analysis_defaults_for_new_fields(self):
        """Test new fields default to empty lists/None."""
        analysis = VideoAnalysis(
            video_id="test_defaults",
            overall_safe=True,
            overall_confidence=0.95,
            summary="Test",
        )
        assert analysis.content_categories == []
        assert analysis.moderation_flags == []
        assert analysis.sponsored_content is None

    def test_video_analysis_serialization_with_new_fields(self):
        """Test serialization includes new fields."""
        analysis = VideoAnalysis(
            video_id="test_serialize",
            overall_safe=True,
            overall_confidence=0.9,
            summary="Test",
            content_categories=[
                ContentCategory(
                    vertical=CategoryVertical.TECHNOLOGY,
                    sub_category="tech",
                    confidence=0.8,
                    is_primary=True,
                )
            ],
        )
        data = analysis.model_dump()
        assert "content_categories" in data
        assert "moderation_flags" in data
        assert "sponsored_content" in data
        assert len(data["content_categories"]) == 1
        assert data["content_categories"][0]["vertical"] == "technology"


# ─── PR-010: Audience Demographics Tests ───────────────────────────────────────


class TestAgeBucket:
    """Test AgeBucket enum (PR-010)."""

    def test_all_age_buckets_exist(self):
        """Verify all age buckets are defined."""
        expected = ["13-17", "18-24", "25-34", "35-44", "45+"]
        actual = [ab.value for ab in AgeBucket]
        assert sorted(actual) == sorted(expected)

    def test_age_bucket_is_strenum(self):
        """Verify AgeBucket uses StrEnum."""
        assert AgeBucket.TEEN == "13-17"
        assert str(AgeBucket.YOUNG_ADULT) == "18-24"


class TestIncomeBucket:
    """Test IncomeBucket enum (PR-010)."""

    def test_all_income_buckets_exist(self):
        """Verify all income buckets are defined."""
        expected = ["low", "middle", "middle_upper", "high"]
        actual = [ib.value for ib in IncomeBucket]
        assert sorted(actual) == sorted(expected)


class TestInferredInterests:
    """Test InferredInterests model (PR-010)."""

    def test_valid_inferred_interests(self):
        """Test creating valid inferred interests."""
        interests = InferredInterests(
            primary=["fitness", "health", "wellness"],
            confidence=0.82,
            evidence=["gym footage", "protein shake visible"],
        )
        assert len(interests.primary) == 3
        assert interests.confidence == 0.82
        assert "gym footage" in interests.evidence

    def test_max_interests_limit(self):
        """Test primary interests max length constraint."""
        # 5 should be fine
        interests = InferredInterests(
            primary=["a", "b", "c", "d", "e"],
            confidence=0.7,
            evidence=[],
        )
        assert len(interests.primary) == 5


class TestAgeDistribution:
    """Test AgeDistribution model (PR-010)."""

    def test_valid_age_distribution(self):
        """Test creating a valid age distribution."""
        age_dist = AgeDistribution(
            teen_13_17=0.05,
            young_adult_18_24=0.45,
            adult_25_34=0.35,
            mid_adult_35_44=0.10,
            mature_45_plus=0.05,
            primary_bucket=AgeBucket.YOUNG_ADULT,
            confidence=0.68,
            evidence=["Gen Z slang", "college setting"],
        )
        assert age_dist.teen_13_17 == 0.05
        assert age_dist.primary_bucket == AgeBucket.YOUNG_ADULT
        assert age_dist.confidence == 0.68

    def test_age_distribution_sum_validation_valid(self):
        """Test that distribution summing to 1.0 passes."""
        age_dist = AgeDistribution(
            teen_13_17=0.2,
            young_adult_18_24=0.2,
            adult_25_34=0.2,
            mid_adult_35_44=0.2,
            mature_45_plus=0.2,
            primary_bucket=AgeBucket.ADULT,
            confidence=0.5,
            evidence=[],
        )
        # Sum = 1.0, should pass
        assert age_dist.teen_13_17 + age_dist.young_adult_18_24 == 0.4

    def test_age_distribution_sum_validation_fails(self):
        """Test that distribution NOT summing to ~1.0 fails."""
        with pytest.raises(ValidationError) as exc_info:
            AgeDistribution(
                teen_13_17=0.5,
                young_adult_18_24=0.5,
                adult_25_34=0.5,  # Sum = 1.5
                mid_adult_35_44=0.0,
                mature_45_plus=0.0,
                primary_bucket=AgeBucket.ADULT,
                confidence=0.7,
                evidence=[],
            )
        assert "sum to ~1.0" in str(exc_info.value)

    def test_age_distribution_alias_support(self):
        """Test age distribution supports alias field names."""
        # Using aliases
        data = {
            "13-17": 0.1,
            "18-24": 0.3,
            "25-34": 0.3,
            "35-44": 0.2,
            "45+": 0.1,
            "primary_bucket": "18-24",
            "confidence": 0.7,
            "evidence": [],
        }
        age_dist = AgeDistribution.model_validate(data)
        assert age_dist.teen_13_17 == 0.1
        assert age_dist.young_adult_18_24 == 0.3

    def test_age_distribution_tolerance(self):
        """Test that distribution within 0.95-1.05 tolerance passes."""
        # Sum = 0.99, should pass
        age_dist = AgeDistribution(
            teen_13_17=0.19,
            young_adult_18_24=0.2,
            adult_25_34=0.2,
            mid_adult_35_44=0.2,
            mature_45_plus=0.2,
            primary_bucket=AgeBucket.ADULT,
            confidence=0.5,
            evidence=[],
        )
        total = (
            age_dist.teen_13_17
            + age_dist.young_adult_18_24
            + age_dist.adult_25_34
            + age_dist.mid_adult_35_44
            + age_dist.mature_45_plus
        )
        assert 0.95 <= total <= 1.05


class TestGenderDistribution:
    """Test GenderDistribution model (PR-010)."""

    def test_valid_gender_distribution(self):
        """Test creating a valid gender distribution."""
        gender_dist = GenderDistribution(
            male=0.55,
            female=0.45,
            confidence=0.62,
            evidence=["fitness content typically 55-60% male"],
        )
        assert gender_dist.male == 0.55
        assert gender_dist.female == 0.45
        assert gender_dist.confidence == 0.62

    def test_gender_distribution_sum_validation_fails(self):
        """Test that gender distribution NOT summing to ~1.0 fails."""
        with pytest.raises(ValidationError) as exc_info:
            GenderDistribution(
                male=0.6,
                female=0.6,  # Sum = 1.2
                confidence=0.5,
                evidence=[],
            )
        assert "sum to ~1.0" in str(exc_info.value)


class TestGeographyInference:
    """Test GeographyInference model (PR-010)."""

    def test_valid_geography_inference(self):
        """Test creating a valid geography inference."""
        geo = GeographyInference(
            primary_countries=[
                {"country": "US", "probability": 0.70},
                {"country": "UK", "probability": 0.15},
            ],
            primary_language="English (American)",
            confidence=0.75,
            evidence=["American accent", "USD pricing"],
        )
        assert len(geo.primary_countries) == 2
        assert geo.primary_language == "English (American)"
        assert geo.confidence == 0.75

    def test_geography_country_probability_validation(self):
        """Test country probability structure validation."""
        with pytest.raises(ValidationError):
            GeographyInference(
                primary_countries=[
                    {"country": "US"},  # Missing probability
                ],
                primary_language="English",
                confidence=0.5,
                evidence=[],
            )

    def test_geography_country_probability_sum_validation(self):
        """Test country probabilities sum validation."""
        with pytest.raises(ValidationError) as exc_info:
            GeographyInference(
                primary_countries=[
                    {"country": "US", "probability": 0.7},
                    {"country": "UK", "probability": 0.5},  # Sum > 1.0
                ],
                primary_language="English",
                confidence=0.5,
                evidence=[],
            )
        assert "sum to <= 1.0" in str(exc_info.value)


class TestIncomeDistribution:
    """Test IncomeDistribution model (PR-010)."""

    def test_valid_income_distribution(self):
        """Test creating a valid income distribution."""
        income = IncomeDistribution(
            low=0.15,
            middle=0.50,
            middle_upper=0.25,
            high=0.10,
            confidence=0.45,
            evidence=["mid-range gym equipment"],
        )
        assert income.low == 0.15
        assert income.middle == 0.50
        assert income.confidence == 0.45

    def test_income_distribution_sum_validation_fails(self):
        """Test that income distribution NOT summing to ~1.0 fails."""
        with pytest.raises(ValidationError) as exc_info:
            IncomeDistribution(
                low=0.4,
                middle=0.4,
                middle_upper=0.4,  # Sum = 1.2
                high=0.0,
                confidence=0.5,
                evidence=[],
            )
        assert "sum to ~1.0" in str(exc_info.value)


class TestAudienceDemographics:
    """Test AudienceDemographics model (PR-010)."""

    def test_valid_audience_demographics(self):
        """Test creating a complete audience demographics result."""
        demographics = AudienceDemographics(
            video_id="abc123",
            interests=InferredInterests(
                primary=["fitness", "health"],
                confidence=0.82,
                evidence=["gym footage"],
            ),
            age_distribution=AgeDistribution(
                teen_13_17=0.05,
                young_adult_18_24=0.45,
                adult_25_34=0.35,
                mid_adult_35_44=0.10,
                mature_45_plus=0.05,
                primary_bucket=AgeBucket.YOUNG_ADULT,
                confidence=0.68,
                evidence=["Gen Z slang"],
            ),
            gender_distribution=GenderDistribution(
                male=0.55,
                female=0.45,
                confidence=0.62,
                evidence=["fitness content"],
            ),
            geography=GeographyInference(
                primary_countries=[{"country": "US", "probability": 0.70}],
                primary_language="English (American)",
                confidence=0.75,
                evidence=["American accent"],
            ),
            income_level=IncomeDistribution(
                low=0.15,
                middle=0.50,
                middle_upper=0.25,
                high=0.10,
                confidence=0.45,
                evidence=["mid-range equipment"],
            ),
            overall_confidence=0.66,
        )
        assert demographics.video_id == "abc123"
        assert demographics.overall_confidence == 0.66
        assert demographics.interests.confidence == 0.82
        assert demographics.age_distribution.primary_bucket == AgeBucket.YOUNG_ADULT

    def test_audience_demographics_with_error(self):
        """Test demographics with error message."""
        demographics = AudienceDemographics(
            video_id="test123",
            interests=InferredInterests(primary=[], confidence=0.3, evidence=[]),
            age_distribution=AgeDistribution(
                teen_13_17=0.2,
                young_adult_18_24=0.2,
                adult_25_34=0.2,
                mid_adult_35_44=0.2,
                mature_45_plus=0.2,
                primary_bucket=AgeBucket.ADULT,
                confidence=0.3,
                evidence=[],
            ),
            gender_distribution=GenderDistribution(
                male=0.5, female=0.5, confidence=0.3, evidence=[]
            ),
            geography=GeographyInference(
                primary_countries=[], primary_language="Unknown", confidence=0.3, evidence=[]
            ),
            income_level=IncomeDistribution(
                low=0.25, middle=0.25, middle_upper=0.25, high=0.25, confidence=0.3, evidence=[]
            ),
            overall_confidence=0.3,
            error="low_confidence_warning: insufficient video signals",
        )
        assert demographics.error is not None
        assert "low_confidence" in demographics.error

    def test_audience_demographics_serialization(self):
        """Test demographics serialization to JSON."""
        demographics = AudienceDemographics(
            video_id="serialize_test",
            interests=InferredInterests(
                primary=["tech"], confidence=0.8, evidence=["tech review"]
            ),
            age_distribution=AgeDistribution(
                teen_13_17=0.1,
                young_adult_18_24=0.3,
                adult_25_34=0.3,
                mid_adult_35_44=0.2,
                mature_45_plus=0.1,
                primary_bucket=AgeBucket.YOUNG_ADULT,
                confidence=0.7,
                evidence=[],
            ),
            gender_distribution=GenderDistribution(
                male=0.65, female=0.35, confidence=0.6, evidence=[]
            ),
            geography=GeographyInference(
                primary_countries=[{"country": "US", "probability": 0.8}],
                primary_language="English",
                confidence=0.7,
                evidence=[],
            ),
            income_level=IncomeDistribution(
                low=0.2, middle=0.4, middle_upper=0.3, high=0.1, confidence=0.5, evidence=[]
            ),
            overall_confidence=0.68,
        )
        json_str = demographics.model_dump_json()
        assert "serialize_test" in json_str
        assert "interests" in json_str
        assert "age_distribution" in json_str

        # Round-trip test
        restored = AudienceDemographics.model_validate_json(json_str)
        assert restored.video_id == demographics.video_id
        assert restored.overall_confidence == demographics.overall_confidence


class TestCreativePatterns:
    """Tests for CreativePatterns narrative fields."""

    _NARRATIVE_DEFAULTS = {
        "transcript_summary": "Test transcript",
        "story_arc": "Setup then resolution",
        "emotional_journey": "curiosity to satisfaction",
        "protagonist": "Test subject",
        "theme": "Test theme",
        "visual_style": "Close-up shots",
        "audio_style": "Clear voiceover",
        "scene_beat_map": "(1) HOOK 0-3s: close_up static",
    }

    @pytest.mark.parametrize("field", [
        "story_arc", "theme", "visual_style", "audio_style", "scene_beat_map",
    ])
    def test_accepts_long_fields(self, field):
        """No max_length — arbitrarily long strings are accepted."""
        overrides = {**self._NARRATIVE_DEFAULTS, field: "x" * 5000}
        cp = CreativePatterns(**overrides)
        assert len(getattr(cp, field)) == 5000

    def test_error_field_sentinel(self):
        cp = CreativePatterns(
            **self._NARRATIVE_DEFAULTS,
            error="parse_failure: something went wrong",
        )
        assert cp.error is not None
        assert "parse_failure" in cp.error

    def test_null_narrative_coercion(self):
        """None and empty strings are coerced to 'Not available'."""
        cp = CreativePatterns(
            transcript_summary="Test transcript",
            story_arc=None,
            emotional_journey="curiosity to satisfaction",
            protagonist="Test subject",
            theme=None,
            visual_style="Close-up shots",
            audio_style="Clear voiceover",
            scene_beat_map="(1) HOOK 0-3s: close_up static",
        )
        assert cp.story_arc == "Not available"
        assert cp.theme == "Not available"
