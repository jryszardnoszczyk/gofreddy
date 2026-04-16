"""Tests for voice profile deterministic metrics and system instruction builder."""

from src.content_gen.voice_models import TextVoiceMetrics, TextVoiceQualitative
from src.content_gen.voice_service import (
    build_system_instruction,
    compute_deterministic_metrics,
)


class TestComputeDeterministicMetrics:
    def test_basic_posts(self):
        posts = [
            "Hello world! This is a test post. #testing #hello",
            "Another post with emoji 😊 and a link https://example.com",
            "WHY NOT ask a question? It works! #testing",
            "Short post.",
            "This is a longer post with more words to test the average length calculation.",
        ]
        metrics = compute_deterministic_metrics(posts)
        assert metrics.avg_post_length_words > 0
        assert metrics.avg_hashtag_count > 0
        assert metrics.question_frequency > 0
        assert metrics.link_usage_frequency > 0
        assert "short" in metrics.sentence_length_buckets
        assert "medium" in metrics.sentence_length_buckets
        assert "long" in metrics.sentence_length_buckets
        assert "#testing" in metrics.top_hashtags

    def test_empty_posts(self):
        metrics = compute_deterministic_metrics([])
        assert metrics.avg_post_length_words == 0
        assert metrics.emoji_frequency == 0

    def test_emoji_frequency(self):
        posts = ["😊😊😊 hello world"]
        metrics = compute_deterministic_metrics(posts)
        assert metrics.emoji_frequency > 0

    def test_no_emojis(self):
        posts = ["Plain text with no special characters"]
        metrics = compute_deterministic_metrics(posts)
        assert metrics.emoji_frequency == 0

    def test_all_uppercase_capitalization(self):
        posts = ["THIS IS ALL CAPS POST WITH MANY WORDS"]
        metrics = compute_deterministic_metrics(posts)
        assert metrics.capitalization_ratio > 0.5

    def test_question_frequency(self):
        posts = [
            "Is this working?",
            "This is not a question.",
            "Does this count?",
        ]
        metrics = compute_deterministic_metrics(posts)
        assert abs(metrics.question_frequency - 2 / 3) < 0.01


class TestBuildSystemInstruction:
    def _make_metrics(self) -> TextVoiceMetrics:
        return TextVoiceMetrics(
            avg_post_length_words=50.0,
            emoji_frequency=0.03,
            avg_hashtag_count=3.0,
            capitalization_ratio=0.02,
            question_frequency=0.2,
            avg_sentence_length=15.0,
            link_usage_frequency=0.1,
            sentence_length_buckets={"short": 0.3, "medium": 0.5, "long": 0.2},
            top_hashtags=["#marketing", "#ai"],
        )

    def _make_qualitative(self) -> TextVoiceQualitative:
        return TextVoiceQualitative(
            tone="conversational and analytical",
            rhetorical_devices=["rhetorical questions", "tricolon"],
            humor_style="dry wit",
            signature_phrases=["game-changer", "let me explain"],
            vocabulary_level="intermediate",
            writing_structure="short punchy sentences alternating with medium explanations",
            emotional_range="measured enthusiasm",
        )

    def test_produces_valid_instruction(self):
        instruction = build_system_instruction(
            "testuser", self._make_metrics(), self._make_qualitative()
        )
        assert "VOICE PROFILE" in instruction
        assert "@testuser" in instruction
        assert "conversational and analytical" in instruction
        assert "QUANTITATIVE GUARDRAILS" in instruction
        assert "~50 words" in instruction
        assert "moderate" in instruction  # emoji_frequency 0.03

    def test_emoji_descriptions(self):
        metrics = self._make_metrics()
        qualitative = self._make_qualitative()

        # Low emoji
        m_low = TextVoiceMetrics(**{**{f.name: getattr(metrics, f.name) for f in metrics.__dataclass_fields__.values()}, "emoji_frequency": 0.005})
        instr = build_system_instruction("u", m_low, qualitative)
        assert "rare" in instr

        # High emoji
        m_high = TextVoiceMetrics(**{**{f.name: getattr(metrics, f.name) for f in metrics.__dataclass_fields__.values()}, "emoji_frequency": 0.1})
        instr = build_system_instruction("u", m_high, qualitative)
        assert "frequent" in instr
