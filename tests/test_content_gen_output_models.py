"""JSON-roundtrip coverage for the 5 frozen content_gen output models."""

from __future__ import annotations

from src.content_gen.output_models import (
    AdCopyVariant,
    NewsletterContent,
    RewriteVariant,
    ScriptSection,
    SocialPost,
    VideoScript,
)


def test_social_post_roundtrip() -> None:
    original = SocialPost(
        platform="x",
        body="Launch day.",
        hashtags=["#launch", "#ai"],
        suggested_media_type="image",
        character_count=11,
    )
    restored = SocialPost.model_validate_json(original.model_dump_json())
    assert restored == original


def test_newsletter_content_roundtrip() -> None:
    original = NewsletterContent(
        subject="Weekly recap",
        preview_text="Highlights from the week.",
        body_html="<p>Hello</p>",
    )
    restored = NewsletterContent.model_validate_json(original.model_dump_json())
    assert restored == original


def test_video_script_roundtrip_with_nested_sections() -> None:
    original = VideoScript(
        hook="The 3-second pitch.",
        body_sections=[
            ScriptSection(heading="Setup", content="Frame the problem.", duration_seconds=15),
            ScriptSection(heading="Reveal", content="Show the fix.", duration_seconds=30),
        ],
        cta="Subscribe.",
        total_duration_estimate=60,
        shot_suggestions=["talking head", "screen recording"],
    )
    restored = VideoScript.model_validate_json(original.model_dump_json())
    assert restored == original
    assert restored.body_sections[0].heading == "Setup"


def test_ad_copy_variant_roundtrip() -> None:
    original = AdCopyVariant(
        platform="meta",
        headline="Ship faster.",
        body="The toolkit your team needs.",
        cta="Start free",
        display_url=None,
    )
    restored = AdCopyVariant.model_validate_json(original.model_dump_json())
    assert restored == original


def test_rewrite_variant_roundtrip() -> None:
    original = RewriteVariant(
        tone="formal",
        content="The proposal has been received.",
        target_platform="email",
        character_count=31,
    )
    restored = RewriteVariant.model_validate_json(original.model_dump_json())
    assert restored == original
