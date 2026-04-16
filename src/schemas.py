"""Pydantic schemas for brand safety analysis."""

import re
from enum import Enum, StrEnum
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ─── Type Aliases ─────────────────────────────────────────────────────────────

Confidence = Annotated[float, Field(ge=0.0, le=1.0)]


# ─── Legacy Enums (Backward Compatible) ───────────────────────────────────────


class RiskCategory(str, Enum):
    """Brand safety risk categories aligned with GARM framework.

    Note: Kept for backward compatibility. New code should use ModerationClass.
    """

    CONTROVERSIAL = "controversial_statement"
    HATE_SYMBOLS = "hate_symbols"
    SUBSTANCE_USE = "substance_use"
    VIOLENCE = "violence"
    POLITICAL = "political_content"
    ADULT = "adult_content"
    COMPETITOR = "competitor_product"


class Severity(str, Enum):
    """Risk severity levels."""

    NONE = "none"  # Checked, not detected
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ─── New Moderation Enums (PR-009) ────────────────────────────────────────────


class ModerationClass(StrEnum):
    """75 moderation classes aligned with GARM framework."""

    # ═══════════════════════════════════════════════════════════════════════════
    # GARM CATEGORY 1: ADULT & EXPLICIT SEXUAL CONTENT (8 classes)
    # ═══════════════════════════════════════════════════════════════════════════
    # Core (existing)
    ADULT_SEXUAL = "adult_sexual"  # Explicit sexual content
    NUDITY = "nudity"  # Full/partial nudity
    # Expanded
    SEXUAL_SUGGESTIVE = "sexual_suggestive"  # Suggestive poses, implied sexuality
    SEXUAL_TEXT = "sexual_text"  # Sexual text overlays/captions
    SEXUAL_AUDIO = "sexual_audio"  # Sexual audio/speech
    LINGERIE_REVEALING = "lingerie_revealing"  # Revealing clothing
    ANIMATED_SEXUAL = "animated_sexual"  # Animated/cartoon sexual content
    DATING_CONTENT = "dating_content"  # Dating app promotion, hookup content

    # ═══════════════════════════════════════════════════════════════════════════
    # GARM CATEGORY 2: ARMS & AMMUNITION (6 classes)
    # ═══════════════════════════════════════════════════════════════════════════
    FIREARM_THREATENING = "firearm_threatening"  # Weapon pointed at person
    FIREARM_DISPLAYED = "firearm_displayed"  # Weapon visible, not threatening
    FIREARM_ANIMATED = "firearm_animated"  # Animated/game firearms
    KNIFE_THREATENING = "knife_threatening"  # Knife/blade used threateningly
    EXPLOSIVE_DEVICE = "explosive_device"  # Bombs, IEDs, explosives
    WEAPON_MODIFICATION = "weapon_modification"  # Illegal weapon mods, instructions

    # ═══════════════════════════════════════════════════════════════════════════
    # GARM CATEGORY 3: CRIME & HARMFUL ACTS (8 classes)
    # ═══════════════════════════════════════════════════════════════════════════
    PHYSICAL_ASSAULT = "physical_assault"  # Real physical attack
    DOMESTIC_VIOLENCE = "domestic_violence"  # Partner/family violence
    ANIMAL_CRUELTY = "animal_cruelty"  # Harm to animals
    THEFT_ROBBERY = "theft_robbery"  # Stealing, burglary
    VANDALISM = "vandalism"  # Property destruction
    DOXXING = "doxxing"  # Sharing private info
    REVENGE_CONTENT = "revenge_content"  # Revenge porn, humiliation
    ILLEGAL_ACTIVITY = "illegal_activity"  # Other illegal acts

    # ═══════════════════════════════════════════════════════════════════════════
    # GARM CATEGORY 4: DEATH, INJURY & MILITARY CONFLICT (8 classes)
    # ═══════════════════════════════════════════════════════════════════════════
    # Core (existing)
    VIOLENCE_GRAPHIC = "violence_graphic"  # Graphic real violence
    VIOLENCE_MILD = "violence_mild"  # Mild violence, scuffles
    GORE = "gore"  # Blood, injury, body parts
    # Expanded
    CORPSE_VISIBLE = "corpse_visible"  # Dead bodies shown
    ACCIDENT_AFTERMATH = "accident_aftermath"  # Crash/accident scenes
    MEDICAL_GRAPHIC = "medical_graphic"  # Graphic medical procedures
    MILITARY_COMBAT = "military_combat"  # War footage, combat
    TORTURE = "torture"  # Torture, extreme suffering

    # ═══════════════════════════════════════════════════════════════════════════
    # GARM CATEGORY 5: ONLINE PIRACY (3 classes)
    # ═══════════════════════════════════════════════════════════════════════════
    PIRACY_PROMOTION = "piracy_promotion"  # Promoting pirated content
    PIRACY_LINKS = "piracy_links"  # Links to pirated material
    COPYRIGHT_VIOLATION = "copyright_violation"  # Clear copyright infringement

    # ═══════════════════════════════════════════════════════════════════════════
    # GARM CATEGORY 6: HATE SPEECH & ACTS OF AGGRESSION (8 classes)
    # ═══════════════════════════════════════════════════════════════════════════
    # Core (existing)
    HATE_SPEECH = "hate_speech"  # Hateful speech targeting groups
    DISCRIMINATION = "discrimination"  # Discriminatory content
    HARASSMENT = "harassment"  # Bullying, personal attacks
    # Expanded
    NAZI_SYMBOLS = "nazi_symbols"  # Swastikas, Nazi imagery
    WHITE_SUPREMACY = "white_supremacy"  # White nationalist content
    TERRORIST_SYMBOLS = "terrorist_symbols"  # ISIS flags, terror imagery
    RACIAL_SLURS = "racial_slurs"  # Explicit racial epithets
    RELIGIOUS_HATE = "religious_hate"  # Anti-religious hate content

    # ═══════════════════════════════════════════════════════════════════════════
    # GARM CATEGORY 7: OBSCENITY & PROFANITY (4 classes)
    # ═══════════════════════════════════════════════════════════════════════════
    # Core (existing)
    PROFANITY_STRONG = "profanity_strong"  # F-word, severe profanity
    PROFANITY_MILD = "profanity_mild"  # Mild profanity, crude language
    # Expanded
    GESTURE_OFFENSIVE = "gesture_offensive"  # Middle finger, obscene gestures
    INSULT_DEGRADING = "insult_degrading"  # Severe insults, degradation

    # ═══════════════════════════════════════════════════════════════════════════
    # GARM CATEGORY 8: DRUGS/TOBACCO/ALCOHOL (8 classes)
    # ═══════════════════════════════════════════════════════════════════════════
    # Core (existing)
    DRUGS_ILLEGAL = "drugs_illegal"  # Illegal drug use/promotion
    ALCOHOL_EXCESSIVE = "alcohol_excessive"  # Excessive alcohol consumption
    TOBACCO = "tobacco"  # Tobacco/vaping promotion
    # Expanded
    DRUG_MANUFACTURING = "drug_manufacturing"  # Making drugs, instructions
    DRUG_DEALING = "drug_dealing"  # Drug sales, trafficking
    DRUG_PARAPHERNALIA = "drug_paraphernalia"  # Pipes, bongs, needles
    PRESCRIPTION_ABUSE = "prescription_abuse"  # Prescription drug misuse
    INTOXICATION = "intoxication"  # Extreme drunkenness

    # ═══════════════════════════════════════════════════════════════════════════
    # GARM CATEGORY 9: SPAM & HARMFUL CONTENT (6 classes)
    # ═══════════════════════════════════════════════════════════════════════════
    # Core (existing)
    SPAM = "spam"  # Spam, scam, misleading
    # Expanded
    PHISHING = "phishing"  # Phishing attempts
    FINANCIAL_SCAM = "financial_scam"  # Money scams, pyramid schemes
    FAKE_GIVEAWAY = "fake_giveaway"  # Fake contests/giveaways
    IMPERSONATION = "impersonation"  # Impersonating others
    CLICKBAIT_MISLEADING = "clickbait_misleading"  # Deceptive clickbait

    # ═══════════════════════════════════════════════════════════════════════════
    # GARM CATEGORY 10: TERRORISM (5 classes)
    # ═══════════════════════════════════════════════════════════════════════════
    # Core (existing)
    TERRORISM = "terrorism"  # Terrorist content
    # Expanded
    TERRORIST_PROPAGANDA = "terrorist_propaganda"  # Terror group propaganda
    TERRORIST_ATTACK = "terrorist_attack"  # Attack footage
    EXTREMIST_RECRUITMENT = "extremist_recruitment"  # Recruiting for extremism
    BOMB_MAKING = "bomb_making"  # Explosive instructions

    # ═══════════════════════════════════════════════════════════════════════════
    # GARM CATEGORY 11: SENSITIVE SOCIAL ISSUES (8 classes)
    # ═══════════════════════════════════════════════════════════════════════════
    # Core (existing)
    POLITICAL = "political"  # Partisan political content
    CONTROVERSIAL = "controversial"  # Divisive topics
    MISINFORMATION = "misinformation"  # False/misleading claims
    # Expanded
    ELECTION_MISINFO = "election_misinfo"  # Election-related misinfo
    HEALTH_MISINFO = "health_misinfo"  # Medical misinformation
    CONSPIRACY_HARMFUL = "conspiracy_harmful"  # Dangerous conspiracy theories
    MANIPULATED_MEDIA = "manipulated_media"  # Deepfakes, doctored content
    CRISIS_MISINFO = "crisis_misinfo"  # Disaster/emergency misinfo

    # ═══════════════════════════════════════════════════════════════════════════
    # SAFETY CLASSES (5 classes)
    # Not GARM but required for user safety
    # ═══════════════════════════════════════════════════════════════════════════
    # Core (existing)
    SELF_HARM = "self_harm"  # Self-injury, eating disorders
    CHILD_SAFETY = "child_safety"  # Content exploiting minors (NCMEC trigger)
    DANGEROUS_ACTIVITIES = "dangerous_activities"  # Dangerous stunts/challenges
    # Expanded
    SUICIDE_PROMOTION = "suicide_promotion"  # Promoting/glorifying suicide
    EATING_DISORDER_PRO = "eating_disorder_pro"  # Pro-ana/pro-mia content

    # ═══════════════════════════════════════════════════════════════════════════
    # BRAND SUITABILITY (3 classes)
    # Not GARM but important for advertisers
    # ═══════════════════════════════════════════════════════════════════════════
    GAMBLING = "gambling"  # Gambling promotion
    CRYPTOCURRENCY_PROMO = "cryptocurrency_promo"  # Crypto promotion
    COUNTERFEIT = "counterfeit"  # Fake/counterfeit products


class CategoryVertical(str, Enum):
    """Top-level content verticals (10 groups)."""

    ENTERTAINMENT = "entertainment"  # Comedy, Music, Entertainment
    LIFESTYLE = "lifestyle"  # Beauty, Fashion, Lifestyle
    EDUCATION = "education"  # Education, Science, Business
    SPORTS_FITNESS = "sports_fitness"  # Sports, Fitness, Health
    TECHNOLOGY = "technology"  # Tech, Gaming
    FOOD_TRAVEL = "food_travel"  # Food, Travel
    NEWS_POLITICS = "news_politics"  # News, Finance
    FAMILY = "family"  # Parenting, Pets
    CREATIVE = "creative"  # Art, DIY, Automotive
    OTHER = "other"  # Religion, Real Estate, Other


# ─── Timestamp Validation Helper ──────────────────────────────────────────────


def _validate_timestamp(v: str | None) -> str | None:
    """Validate timestamp format (M:SS, MM:SS, or H:MM:SS).

    Shared validator for RiskDetection and ModerationDetection.
    Accepts formats: "0:45", "00:45", "1:23", "12:34", "0:04:53", "1:23:45"
    """
    if v is None:
        return None
    if not re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", v):
        raise ValueError(f"Timestamp must be M:SS, MM:SS, or H:MM:SS format, got: {v}")
    return v


# ─── Legacy Risk Detection ────────────────────────────────────────────────────


class RiskDetection(BaseModel):
    """A single detected risk in a video (legacy, for backward compatibility)."""

    category: RiskCategory
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence 0-1")
    timestamp_start: Optional[str] = Field(None, description="Start time MM:SS")
    timestamp_end: Optional[str] = Field(None, description="End time MM:SS")
    description: str = Field(description="What was detected")
    evidence: str = Field(description="Quote or visual description as evidence")

    @field_validator("timestamp_start", "timestamp_end", mode="before")
    @classmethod
    def validate_timestamp(cls, v: str | None) -> str | None:
        return _validate_timestamp(v)


# ─── Content Categorization (PR-009) ──────────────────────────────────────────


class ContentCategory(BaseModel):
    """Content categorization result."""

    vertical: CategoryVertical
    sub_category: str = Field(
        description="Specific category: beauty, fitness, gaming, food, travel, "
        "fashion, tech, comedy, education, music, sports, lifestyle, "
        "parenting, finance, news, pets, diy, automotive, real_estate, "
        "health, entertainment, business, science, art, religion"
    )
    confidence: Confidence
    is_primary: bool = Field(default=False)


# ─── Moderation Detection (PR-009) ────────────────────────────────────────────


class ModerationDetection(BaseModel):
    """A single moderation flag detection."""

    moderation_class: ModerationClass
    severity: Severity
    confidence: Confidence
    timestamp_start: str | None = None
    timestamp_end: str | None = None
    description: str = Field(max_length=500)  # Prevent response bloat
    evidence: str = Field(max_length=500)

    @field_validator("timestamp_start", "timestamp_end", mode="before")
    @classmethod
    def validate_timestamp(cls, v: str | None) -> str | None:
        return _validate_timestamp(v)


# ─── Sponsored Content Detection (PR-009) ─────────────────────────────────────


class SponsoredContent(BaseModel):
    """Sponsored content detection result."""

    is_sponsored: bool
    confidence: Confidence
    disclosure_detected: bool = Field(default=False)
    disclosure_clarity_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Informational score indicating disclosure clarity (0=hidden, 1=prominent). "
        "NOT a legal determination of FTC compliance.",
    )
    signals: list[str] = Field(
        default_factory=list,
        max_length=10,  # Limit number of signals
        description="Detected signals: hashtag_ad, verbal_disclosure, platform_label, "
        "product_placement, brand_mention, discount_code",
    )
    brands_detected: list[str] = Field(default_factory=list, max_length=20)

    # ── Raw Gemini signals (extracted via structured output) ──
    disclosure_placement: Literal[
        "first_3_seconds", "middle", "end", "absent"
    ] | None = Field(default=None, description="Where disclosure appears in video")
    disclosure_visibility: Literal[
        "verbal", "text_overlay", "hashtag_only", "none"
    ] | None = Field(default=None, description="How disclosure is presented")
    disclosure_before_product: bool | None = Field(
        default=None, description="True if disclosure appears before product mention"
    )

    # ── Computed compliance scores (deterministic, not Gemini-generated) ──
    placement_score: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="Disclosure placement score. Informational assessment only.",
    )
    visibility_score: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="Disclosure visibility score. Informational assessment only.",
    )
    timing_score: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="Disclosure timing score. Informational assessment only.",
    )
    compliance_grade: Literal["A", "B", "C", "D", "F"] | None = Field(
        default=None,
        description="Overall compliance grade A-F. Informational assessment only.",
    )
    improvement_suggestions: list[str] = Field(
        default_factory=list,
        description="Rule-based improvement suggestions.",
    )
    jurisdiction: str = Field(
        default="US",
        description="Geographic jurisdiction for compliance assessment. v1: US (FTC guidelines).",
    )


# ─── Complete Video Analysis ──────────────────────────────────────────────────


class VideoAnalysis(BaseModel):
    """Complete analysis result for a video."""

    video_id: str = Field(description="Unique identifier for the video")
    overall_safe: bool = Field(description="True if no high/critical risks detected")
    overall_confidence: float = Field(ge=0.0, le=1.0)

    # Legacy (backward compatible)
    risks_detected: list[RiskDetection] = Field(default_factory=list)
    summary: str = Field(description="Human-readable summary of findings")

    # NEW: Content Categorization (PR-009)
    content_categories: list[ContentCategory] = Field(default_factory=list)

    # NEW: Moderation Flags (PR-009)
    moderation_flags: list[ModerationDetection] = Field(default_factory=list)

    # NEW: Sponsored Content (PR-009)
    sponsored_content: SponsoredContent | None = None

    # Processing metadata
    processing_time_seconds: float = Field(default=0.0)
    token_count: int = Field(default=0)
    error: Optional[str] = Field(default=None, description="Error message if analysis failed")


# ─── Audience Demographics (PR-010) ──────────────────────────────────────────


class AgeBucket(StrEnum):
    """Age range buckets for audience inference."""

    TEEN = "13-17"
    YOUNG_ADULT = "18-24"
    ADULT = "25-34"
    MID_ADULT = "35-44"
    MATURE = "45+"


class IncomeBucket(StrEnum):
    """Income level buckets."""

    LOW = "low"  # <$30K
    MIDDLE = "middle"  # $30K-$75K
    MIDDLE_UPPER = "middle_upper"  # $75K-$150K
    HIGH = "high"  # >$150K


class InferredInterests(BaseModel):
    """Inferred audience interests from video content."""

    primary: list[str] = Field(default_factory=list, max_length=5, description="Top 3-5 interests")
    confidence: Confidence
    evidence: list[str] = Field(default_factory=list, max_length=5, description="Specific signals detected")


class AgeDistribution(BaseModel):
    """Age distribution probabilities."""

    model_config = ConfigDict(populate_by_name=True)

    teen_13_17: float = Field(ge=0.0, le=1.0, alias="13-17")
    young_adult_18_24: float = Field(ge=0.0, le=1.0, alias="18-24")
    adult_25_34: float = Field(ge=0.0, le=1.0, alias="25-34")
    mid_adult_35_44: float = Field(ge=0.0, le=1.0, alias="35-44")
    mature_45_plus: float = Field(ge=0.0, le=1.0, alias="45+")
    primary_bucket: AgeBucket
    confidence: Confidence
    evidence: list[str] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def validate_distribution_sums(self) -> "AgeDistribution":
        """Distribution probabilities should sum to ~1.0."""
        total = (
            self.teen_13_17
            + self.young_adult_18_24
            + self.adult_25_34
            + self.mid_adult_35_44
            + self.mature_45_plus
        )
        if not (0.95 <= total <= 1.05):
            raise ValueError(f"Age distribution must sum to ~1.0, got {total:.3f}")
        return self


class GenderDistribution(BaseModel):
    """Gender distribution probabilities."""

    male: float = Field(ge=0.0, le=1.0)
    female: float = Field(ge=0.0, le=1.0)
    confidence: Confidence
    evidence: list[str] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def validate_distribution_sums(self) -> "GenderDistribution":
        """Male + female should sum to ~1.0."""
        total = self.male + self.female
        if not (0.95 <= total <= 1.05):
            raise ValueError(f"Gender distribution must sum to ~1.0, got {total:.3f}")
        return self


class CountryProbability(BaseModel):
    """Single country with its probability."""

    country: str
    probability: Confidence


class GeographyInference(BaseModel):
    """Geographic audience inference."""

    primary_countries: list[CountryProbability] = Field(
        default_factory=list,
        max_length=5,
    )
    primary_language: str
    confidence: Confidence
    evidence: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("primary_countries", mode="before")
    @classmethod
    def coerce_country_dicts(cls, v: list) -> list:
        """Accept both CountryProbability objects and plain dicts."""
        return [
            CountryProbability(**item) if isinstance(item, dict) else item
            for item in v
        ]

    @model_validator(mode="after")
    def validate_country_probabilities(self) -> "GeographyInference":
        """Validate country probability structure and sum."""
        total = sum(entry.probability for entry in self.primary_countries)
        if total > 1.05:
            raise ValueError(f"Country probabilities must sum to <= 1.0, got {total:.3f}")
        return self


class IncomeDistribution(BaseModel):
    """Income level distribution."""

    low: float = Field(ge=0.0, le=1.0)
    middle: float = Field(ge=0.0, le=1.0)
    middle_upper: float = Field(ge=0.0, le=1.0)
    high: float = Field(ge=0.0, le=1.0)
    confidence: Confidence
    evidence: list[str] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def validate_distribution_sums(self) -> "IncomeDistribution":
        """Income buckets should sum to ~1.0."""
        total = self.low + self.middle + self.middle_upper + self.high
        if not (0.95 <= total <= 1.05):
            raise ValueError(f"Income distribution must sum to ~1.0, got {total:.3f}")
        return self


class AudienceDemographics(BaseModel):
    """Complete audience demographics inference result."""

    model_config = ConfigDict(populate_by_name=True)

    video_id: str

    # Five dimensions with confidence
    interests: InferredInterests
    age_distribution: AgeDistribution
    gender_distribution: GenderDistribution
    geography: GeographyInference
    income_level: IncomeDistribution

    # Overall confidence (weighted average)
    overall_confidence: Confidence

    # Processing metadata
    processing_time_seconds: float = Field(default=0.0)
    token_count: int = Field(default=0)
    error: str | None = None


# ─── Brand Detection (PR-011) ────────────────────────────────────────────────


class BrandDetectionSource(StrEnum):
    """Source of brand detection."""

    SPEECH = "speech"
    TEXT_OVERLAY = "text_overlay"
    VISUAL_LOGO = "visual_logo"
    HASHTAG = "hashtag"


class BrandSentiment(StrEnum):
    """Sentiment toward detected brand."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class BrandContext(StrEnum):
    """Context of brand mention."""

    ENDORSEMENT = "endorsement"
    COMPARISON = "comparison"
    BACKGROUND = "background"
    CRITICISM = "criticism"
    SPONSORED = "sponsored"
    REVIEW = "review"


class BrandMention(BaseModel):
    """Single brand mention with full metadata.

    Simplification: Merged CompetitorMention into BrandMention with `is_competitor` flag.
    """

    brand_name: str = Field(max_length=100)
    detection_source: BrandDetectionSource
    confidence: Confidence
    timestamp_start: str | None = Field(default=None, description="M:SS format")
    timestamp_end: str | None = Field(default=None, description="M:SS format — when brand disappears")
    sentiment: BrandSentiment
    context: BrandContext
    evidence: str = Field(max_length=500, description="Quote or description")
    is_competitor: bool = Field(
        default=False, description="True if this brand is a competitor to the primary brand"
    )

    @field_validator("timestamp_start", "timestamp_end", mode="before")
    @classmethod
    def validate_timestamp(cls, v: str | None) -> str | None:
        return _validate_timestamp(v)


class BrandExposureSummary(BaseModel):
    """Per-brand exposure metrics for a single video."""

    brand_name: str
    total_mentions: int
    total_screen_time_seconds: int
    source_breakdown: dict[str, int]
    sentiment_distribution: dict[str, float]
    context_distribution: dict[str, int]
    is_competitor: bool


class MultiVideoBrandExposure(BaseModel):
    """Aggregated brand exposure across multiple videos."""

    total_mentions: int
    total_screen_time_seconds: int
    average_screen_time_per_video: float
    videos_appearing_in: int
    sentiment_trend: dict[str, str]
    source_breakdown: dict[str, int]
    sentiment_distribution: dict[str, float]
    is_competitor: bool


class MultiVideoExposureResponse(BaseModel):
    """Multi-video brand exposure aggregation."""

    brands: dict[str, MultiVideoBrandExposure]
    video_count: int
    analysis_ids: list[str]


class CreativePatterns(BaseModel):
    """Creative structure analysis of a video."""

    hook_type: Literal[
        "question", "shock_curiosity", "trend_audio", "storytelling",
        "product_reveal", "challenge", "none"
    ] = "none"
    hook_duration_seconds: int | None = None
    narrative_structure: Literal[
        "tutorial", "review", "unboxing", "day_in_life",
        "transformation", "comparison", "listicle", "skit", "vlog", "other"
    ] = "other"
    cta_type: Literal["follow", "like", "comment", "link_in_bio", "shop", "none"] = "none"
    cta_placement: Literal["early", "middle", "end", "repeated", "none"] = "none"
    pacing: Literal["fast_cut", "moderate", "slow_cinematic", "single_take"] = "moderate"
    music_usage: Literal["trending_audio", "trending", "original", "none", "voiceover_only"] = "none"
    text_overlay_density: Literal["none", "minimal", "moderate", "heavy"] = "none"

    hook_confidence: Confidence = 0.0
    narrative_confidence: Confidence = 0.0
    cta_confidence: Confidence = 0.0
    pacing_confidence: Confidence = 0.0
    music_confidence: Confidence = 0.0
    text_overlay_confidence: Confidence = 0.0

    # Story & Narrative (extracted from video content)
    transcript_summary: str = Field(min_length=1, description="Complete transcript of ALL dialogue, narration, and voiceover with delivery notes")
    story_arc: str = Field(min_length=1, description="Setup → conflict → resolution narrative arc")
    emotional_journey: str = Field(min_length=1, description="Emotional progression: e.g., curiosity → tension → surprise → satisfaction")
    protagonist: str = Field(min_length=1, description="Who is the main character/subject and what do they want?")
    theme: str = Field(min_length=1, description="Core message or takeaway")

    # Production style (structured data previously buried in theme/transcript_summary prose)
    visual_style: str = Field(
        min_length=1,
        description="Visual production style: dominant shot types, camera movements, color palette, lighting, composition patterns, signature visual elements",
    )
    audio_style: str = Field(
        min_length=1,
        description="Audio production style: voiceover delivery/persona, sound effects, ambient sounds, music integration, signature audio elements",
    )
    scene_beat_map: str = Field(
        min_length=1,
        description="Scene-by-scene production breakdown: beat type, shot type, camera movement, duration per scene",
    )

    @field_validator(
        "transcript_summary", "story_arc", "emotional_journey", "protagonist", "theme",
        "visual_style", "audio_style", "scene_beat_map",
        mode="before",
    )
    @classmethod
    def _coerce_empty_narrative(cls, v: str | None) -> str:
        """Convert None/empty to sentinel — preserves old DB data while requiring new writes to be populated."""
        if not v:
            return "Not available"
        return v

    processing_time_seconds: float = 0.0
    token_count: int = 0
    error: str | None = None


class BrandAnalysis(BaseModel):
    """Complete brand analysis for a video."""

    video_id: str

    # All detected brands (use is_competitor flag to filter competitors)
    brand_mentions: list[BrandMention] = Field(default_factory=list, max_length=50)

    # Summary
    primary_brand: str | None = Field(default=None, description="Most prominently featured brand")
    overall_sentiment: BrandSentiment | None = None

    # Sponsored content signals (complements SponsoredContent detection)
    has_sponsorship_signals: bool = False
    sponsoring_brand: str | None = None

    # Overall confidence
    overall_confidence: Confidence

    # Processing metadata
    processing_time_seconds: float = 0.0
    token_count: int = 0
    error: str | None = None

    # Computed on read, not stored in JSONB
    exposure_summary: dict[str, BrandExposureSummary] | None = None

    # Computed properties
    @property
    def competitor_mentions(self) -> list[BrandMention]:
        """Get only competitor brand mentions."""
        return [m for m in self.brand_mentions if m.is_competitor]
