"""GEO audit data models."""

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    """Severity level for missing GEO factors."""

    CRITICAL = "critical"  # Blocks AI visibility
    IMPORTANT = "important"  # Significant impact
    RECOMMENDED = "recommended"  # Moderate impact
    OPTIONAL = "optional"  # Nice-to-have


class Finding(BaseModel):
    """Single GEO factor detection result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    factor_id: str = Field(..., description="Factor identifier (e.g., 'citations')")
    factor_name: str = Field(..., description="Human-readable name")
    detected: bool | None = Field(
        ..., description="True=present, False=absent, None=unable to check"
    )
    severity: Severity = Field(..., description="Severity if factor is missing")
    count: int | None = Field(default=None, ge=0, description="Count of detected items")
    evidence: tuple[str, ...] = Field(
        default_factory=tuple, description="Examples of found patterns"
    )
    details: str | None = Field(
        default=None, max_length=500, description="Additional context"
    )


class AuditFindings(BaseModel):
    """Output of DETECT step."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    findings: tuple[Finding, ...] = Field(..., description="All factor findings")
    factors_checked: int = Field(..., ge=0)
    factors_detected: int = Field(..., ge=0)
    factors_missing: int = Field(..., ge=0)
    factors_unable_to_check: int = Field(default=0, ge=0)
    detection_time_ms: int = Field(..., ge=0)

    # Summary counts by severity
    critical_missing: int = Field(default=0, ge=0)
    important_missing: int = Field(default=0, ge=0)
    recommended_missing: int = Field(default=0, ge=0)
    optional_missing: int = Field(default=0, ge=0)


class PageContent(BaseModel):
    """Structured content extracted from a scraped page.

    This is the output of the SCRAPE step and input to DETECT step.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        frozen=True,
    )

    # URL info (required)
    url: str = Field(..., max_length=2048, description="Original requested URL")
    final_url: str = Field(..., max_length=2048, description="URL after redirects")

    # Main content
    text: str = Field(default="", max_length=100_000, description="Extracted text content")
    raw_html: str = Field(default="", max_length=500_000, description="Raw HTML for DOM-based detection")
    word_count: int = Field(default=0, ge=0, description="Count AFTER text truncation")

    # Headings (DETECT uses for structure analysis)
    h1: str | None = Field(default=None, max_length=500)
    h2s: list[str] = Field(default_factory=list)
    h3s: list[str] = Field(default_factory=list)

    # Metadata
    title: str | None = Field(default=None, max_length=200)
    meta_description: str | None = Field(default=None, max_length=500)

    # Structured data (JSON-LD) - DETECT uses for schema presence
    schema_types: list[str] = Field(default_factory=list)
    json_ld_objects: list[dict] = Field(default_factory=list)

    # Fetch metadata
    js_rendered: bool = Field(default=False, description="Whether JS rendering was used")
    status_code: int = Field(default=200, ge=100, le=599)
    fetch_duration_ms: int = Field(default=0, ge=0)

    # Internal link structure (populated by extract_internal_links)
    internal_links: list[dict] = Field(default_factory=list, description="Internal links with href + anchor_text")


class ScrapeResult(BaseModel):
    """Result of the complete SCRAPE step."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    success: bool
    page_content: PageContent | None = None
    error_code: str | None = Field(default=None, pattern=r"^[A-Z_]+$")
    error_message: str | None = Field(default=None, max_length=500)


# =============================================================================
# ANALYZE Step Models
# =============================================================================


class CitedPageData(BaseModel):
    """Single cited page from monitoring data."""

    model_config = ConfigDict(frozen=True)

    url_normalized: str
    domain: str
    h2_texts: tuple[str, ...] = Field(default=())
    schema_types: tuple[str, ...] = Field(default=())
    has_comparison_table: bool = False
    publish_date: date | None = None
    last_modified: date | None = None
    scraped_at: datetime
    query_topic: str
    platform_citations: dict[str, int] = Field(default_factory=dict)


class CitabilityScore(BaseModel):
    """Deterministic citability score based on content signals."""

    model_config = ConfigDict(frozen=True)

    faq_pairs: int = Field(default=0, ge=0)
    comparison_tables: int = Field(default=0, ge=0)
    statistics_density: float = Field(default=0.0, ge=0.0)
    howto_steps: int = Field(default=0, ge=0)
    self_contained_answers: int = Field(default=0, ge=0)
    named_entity_matches: int = Field(default=0, ge=0)
    overall: float = Field(default=0.0, ge=0.0, le=1.0)


class InfrastructureGate(BaseModel):
    """Pass/fail infrastructure gate for GEO scoring."""

    model_config = ConfigDict(frozen=True)

    passed: bool = Field(default=True)
    failed_checks: tuple[str, ...] = Field(default=())


class TopicExtractionResult(BaseModel):
    """LLM output schema for topic extraction."""

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "topics": ["pricing", "installation guide", "troubleshooting"],
                    "primary_topic": "product overview",
                }
            ]
        },
    )

    topics: tuple[str, ...] = Field(
        default=(), description="Distinct normalized topic names (max 30)"
    )
    primary_topic: str = Field(
        min_length=2, max_length=100, description="Main topic the content focuses on"
    )


class PatternGaps(BaseModel):
    """Pattern comparison between user's page and cited pages."""

    model_config = ConfigDict(frozen=True)

    schema_pct: float | None = Field(
        default=None, ge=0.0, le=100.0, description="% of cited pages with any schema markup"
    )
    faqpage_schema_pct: float | None = Field(
        default=None, ge=0.0, le=100.0, description="% of cited pages with FAQPage schema"
    )
    faq_section_pct: float | None = Field(
        default=None, ge=0.0, le=100.0, description="% of cited pages with FAQ section"
    )
    comparison_table_pct: float | None = Field(
        default=None, ge=0.0, le=100.0, description="% of cited pages with comparison tables"
    )
    cited_median_age_days: int | None = Field(
        default=None, ge=0, description="Median content age of cited pages in days"
    )
    user_content_age_days: int | None = Field(
        default=None, ge=0, description="User's page content age in days"
    )


class ContentGap(BaseModel):
    """A topic gap identified between user content and cited pages."""

    model_config = ConfigDict(frozen=True)

    topic_name: str = Field(min_length=2, max_length=100, description="The missing topic")
    coverage_pct: float = Field(
        ge=50.0, le=100.0, description="% of cited pages covering this topic"
    )
    importance: Literal["critical", "important", "recommended"] = Field(
        description="Based on coverage: >=75% critical, >=60% important, else recommended"
    )
    source: str | None = Field(
        default=None, max_length=50,
        description="Analysis perspective that identified this gap",
    )


class AnalyzeResult(BaseModel):
    """Complete analysis output for GENERATE step."""

    model_config = ConfigDict(frozen=True)

    pattern_gaps: PatternGaps
    content_gaps: tuple[ContentGap, ...] = Field(
        default=(), description="Topics in 50%+ of cited pages but missing from user's page"
    )
    user_topics: tuple[str, ...] = Field(default=(), description="Topics extracted from user's page")

    cited_page_count: int = Field(ge=0, description="Number of cited pages analyzed")
    insufficient_data: bool = Field(default=False, description="True if < 5 cited pages available")
    freshness_warning: bool = Field(default=False, description="True if all citations > 30 days old")
    analysis_time_ms: int = Field(ge=0, description="Time taken for analysis")
    circuit_breaker_open: bool = Field(default=False, description="True if circuit breaker prevented full analysis")


# =============================================================================
# GENERATE Step Models
# =============================================================================


class ImprovedIntro(BaseModel):
    """Improved introduction generated for GEO optimization."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    text: str = Field(
        min_length=200,
        max_length=500,
        description="40-60 word answer-first intro (~200-500 chars)",
    )


class FAQItem(BaseModel):
    """Single FAQ question-answer pair."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    question: str = Field(min_length=10, max_length=200, description="15 words max, conversational")
    answer: str = Field(min_length=100, max_length=500, description="40-60 words, direct answer first")


class FAQGeneration(BaseModel):
    """Generated FAQ section with Q&A pairs."""

    model_config = ConfigDict(frozen=True)

    items: tuple[FAQItem, ...] = Field(min_length=3, max_length=10, description="5-7 Q&A pairs")
    placement: str = Field(max_length=200, description="After which section to place FAQ")


class StructuralSuggestion(BaseModel):
    """Structural improvement recommendation."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    suggestion_type: Literal["add_table", "add_list", "add_heading", "reorganize"]
    description: str = Field(max_length=300, description="What to add/change")
    evidence: str = Field(max_length=200, description="Why recommended based on findings")


class ContentFillIn(BaseModel):
    """Generated content to fill a topic gap."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    topic_name: str = Field(max_length=100, description="The missing topic being addressed")
    coverage_pct: float = Field(ge=0, le=100, description="% of cited pages covering this topic")
    importance: Literal["critical", "important", "recommended"]
    generated_paragraphs: str = Field(
        min_length=200, max_length=2000, description="2-3 paragraphs of content"
    )
    placement_after: str = Field(
        max_length=200, description="~50 chars of surrounding text for placement context"
    )


class GenerateResult(BaseModel):
    """Complete output of GENERATE step."""

    model_config = ConfigDict(frozen=True)

    improved_intro: ImprovedIntro | None = Field(default=None)
    faq_generation: FAQGeneration | None = Field(default=None)
    structural_suggestions: tuple[StructuralSuggestion, ...] = Field(default=())
    content_fillins: tuple[ContentFillIn, ...] = Field(default=())

    model_used: str = Field(description="Model that generated content")
    generation_time_ms: int = Field(ge=0, description="Time taken for generation")


# =============================================================================
# FORMAT Step Models
# =============================================================================


class FormatResult(BaseModel):
    """Result from FORMAT step - the final Markdown report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    report_md: str = Field(
        ...,
        min_length=100,
        description="Complete Markdown report with YAML frontmatter",
    )
    severity_counts: dict[str, int] = Field(
        ...,
        description="Count of findings by severity",
    )
    word_count: int = Field(
        ...,
        ge=0,
        description="Report word count for size tracking",
    )


# =============================================================================
# Article Generation Models (PR-102)
# =============================================================================


class ExternalLink(BaseModel):
    """Suggested external authority link for article content."""

    model_config = ConfigDict(frozen=True)

    url: str = Field(max_length=2048)
    anchor_text: str = Field(max_length=200)
    section_heading: str = Field(max_length=200)


class YouTubeEmbed(BaseModel):
    """Suggested YouTube video embed for article section."""

    model_config = ConfigDict(frozen=True)

    search_query: str = Field(max_length=200)
    section_heading: str = Field(max_length=200)


class ArticleSection(BaseModel):
    """Single H2 section of a generated article."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    heading: str = Field(max_length=200)
    body: str = Field(min_length=200, max_length=5000)


class FAQPair(BaseModel):
    """FAQ question-answer pair for article."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    question: str = Field(max_length=300)
    answer: str = Field(max_length=1000)


class HowToStep(BaseModel):
    """Single step in a HowTo sequence."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    name: str = Field(max_length=200)
    text: str = Field(max_length=1000)


class ArticleResult(BaseModel):
    """Complete structured article output from Gemini Flash."""

    model_config = ConfigDict(frozen=True)

    title: str = Field(min_length=20, max_length=70, description="50-60 chars")
    meta_description: str = Field(min_length=100, max_length=170, description="150-160 chars")
    slug: str = Field(max_length=200)
    og_title: str = Field(max_length=70)
    og_description: str = Field(max_length=200)
    og_image_prompt: str = Field(max_length=500, description="Prompt for OG image generation")
    intro: str = Field(min_length=200, max_length=2000)
    sections: tuple[ArticleSection, ...] = Field(min_length=5, max_length=8)
    conclusion: str = Field(min_length=200, max_length=2000)
    faq_pairs: tuple[FAQPair, ...] = Field(default=(), max_length=10)
    howto_steps: tuple[HowToStep, ...] = Field(default=(), max_length=20)
    internal_link_suggestions: tuple[str, ...] = Field(default=(), description="URLs from SiteLinkGraph")
    external_authority_links: tuple[ExternalLink, ...] = Field(default=(), max_length=5)
    image_placement_prompts: tuple[str, ...] = Field(default=(), max_length=5)
    youtube_embed_queries: tuple[YouTubeEmbed, ...] = Field(default=(), max_length=3)
    twitter_card_type: str = Field(default="summary_large_image")
    # Set after generation
    model_used: str = Field(default="")
    generation_time_ms: int = Field(default=0, ge=0)
