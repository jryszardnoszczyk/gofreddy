"""Unit tests for article generation, schema builders, and post-processing."""

import json

import pytest

from src.geo.models import (
    ArticleResult,
    ArticleSection,
    ExternalLink,
    FAQPair,
    HowToStep,
    YouTubeEmbed,
)
from src.seo.models import DomainRankSnapshot


def _make_article(**overrides) -> ArticleResult:
    """Create a minimal valid ArticleResult for testing."""
    defaults = {
        "title": "Best CRM Software for Small Business in 2026",
        "meta_description": "Discover the top CRM software options for small businesses. Compare features, pricing, and integrations to find the perfect fit for your team and budget.",
        "slug": "best-crm-software-small-business",
        "og_title": "Best CRM Software for Small Business in 2026",
        "og_description": "Compare top CRM software for small businesses with pricing and features.",
        "og_image_prompt": "Professional editorial photo of a modern office desk with CRM dashboard on screen",
        "intro": "Finding the right CRM software is critical for small businesses looking to streamline their customer relationships. " * 5,
        "sections": tuple(
            ArticleSection(
                heading=f"Section {i}: Important Topic",
                body="This is a detailed section about an important topic. " * 15,
            )
            for i in range(5)
        ),
        "conclusion": "In conclusion, choosing the right CRM software depends on your specific business needs. " * 5,
    }
    defaults.update(overrides)
    return ArticleResult(**defaults)


class TestArticleResult:
    """Tests for ArticleResult model validation."""

    def test_valid_article(self):
        article = _make_article()
        assert article.title
        assert len(article.sections) == 5

    def test_title_length_validation(self):
        with pytest.raises(Exception):
            _make_article(title="Short")  # min_length=20

    def test_slug_field(self):
        article = _make_article(slug="my-great-article")
        assert article.slug == "my-great-article"

    def test_optional_fields_default_empty(self):
        article = _make_article()
        assert article.faq_pairs == ()
        assert article.howto_steps == ()
        assert article.internal_link_suggestions == ()
        assert article.external_authority_links == ()
        assert article.twitter_card_type == "summary_large_image"

    def test_with_faq_pairs(self):
        faqs = (
            FAQPair(question="What is CRM?", answer="CRM stands for Customer Relationship Management"),
            FAQPair(question="How much does CRM cost?", answer="CRM costs vary from free to hundreds per user"),
        )
        article = _make_article(faq_pairs=faqs)
        assert len(article.faq_pairs) == 2

    def test_with_howto_steps(self):
        steps = (
            HowToStep(name="Sign up", text="Create an account on the CRM platform"),
            HowToStep(name="Import contacts", text="Upload your existing contact list"),
        )
        article = _make_article(howto_steps=steps)
        assert len(article.howto_steps) == 2

    def test_frozen_model(self):
        article = _make_article()
        with pytest.raises(Exception):
            article.title = "New title"


class TestBuildArticleSchema:
    """Tests for build_article_schema()."""

    def test_valid_json_ld(self):
        from src.geo.generator import build_article_schema

        article = _make_article()
        schema_str = build_article_schema(article)
        schema = json.loads(schema_str)

        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "Article"
        assert schema["headline"] == article.title
        assert schema["description"] == article.meta_description

    def test_with_canonical_url(self):
        from src.geo.generator import build_article_schema

        article = _make_article()
        schema_str = build_article_schema(article, canonical_url="https://example.com/article")
        schema = json.loads(schema_str)

        assert schema["url"] == "https://example.com/article"
        assert schema["mainEntityOfPage"]["@id"] == "https://example.com/article"

    def test_without_canonical_url(self):
        from src.geo.generator import build_article_schema

        article = _make_article()
        schema_str = build_article_schema(article)
        schema = json.loads(schema_str)

        assert "url" not in schema

    def test_with_faq_pairs(self):
        from src.geo.generator import build_article_schema

        faqs = (
            FAQPair(question="What is X?", answer="X is a thing"),
        )
        article = _make_article(faq_pairs=faqs)
        schema_str = build_article_schema(article)
        schema = json.loads(schema_str)

        assert "hasPart" in schema
        assert schema["hasPart"]["@type"] == "FAQPage"


class TestBuildHowtoSchema:
    """Tests for build_howto_schema()."""

    def test_valid_json_ld(self):
        from src.geo.generator import build_howto_schema

        steps = (
            HowToStep(name="Step 1", text="Do the first thing"),
            HowToStep(name="Step 2", text="Do the second thing"),
        )
        schema_str = build_howto_schema(steps, "How to Build a CRM")
        schema = json.loads(schema_str)

        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "HowTo"
        assert schema["name"] == "How to Build a CRM"
        assert len(schema["step"]) == 2
        assert schema["step"][0]["@type"] == "HowToStep"
        assert schema["step"][0]["name"] == "Step 1"

    def test_empty_steps(self):
        from src.geo.generator import build_howto_schema

        schema_str = build_howto_schema((), "Empty HowTo")
        schema = json.loads(schema_str)
        assert schema["step"] == []


class TestDomainRankSnapshot:
    """Tests for DomainRankSnapshot model."""

    def test_basic_snapshot(self):
        from datetime import date

        snapshot = DomainRankSnapshot(
            domain="example.com",
            rank=42,
            backlinks_total=1000,
            referring_domains=50,
            snapshot_date=date(2026, 3, 25),
        )
        assert snapshot.domain == "example.com"
        assert snapshot.rank == 42
        assert snapshot.backlinks_total == 1000

    def test_defaults(self):
        snapshot = DomainRankSnapshot(domain="example.com")
        assert snapshot.rank is None
        assert snapshot.backlinks_total == 0
        assert snapshot.referring_domains == 0
        assert snapshot.snapshot_date is None
        assert snapshot.org_id is None

    def test_frozen(self):
        snapshot = DomainRankSnapshot(domain="example.com")
        with pytest.raises(Exception):
            snapshot.domain = "other.com"
