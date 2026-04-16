"""Tests for policy evaluation logic (evaluate() function)."""

from datetime import datetime, UTC
from uuid import uuid4

from src.policies.models import BrandPolicyResponse, PolicyRule
from src.policies.service import DISCLAIMER, evaluate
from src.schemas import ModerationClass, Severity


def _make_policy(rules: list[PolicyRule], name: str = "Test Policy") -> BrandPolicyResponse:
    """Create a BrandPolicyResponse for testing."""
    return BrandPolicyResponse(
        id=uuid4(),
        user_id=uuid4(),
        policy_name=name,
        rules=rules,
        is_preset=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestAllRulesPass:
    def test_no_detected_flags(self):
        """No detected flags -> all rules pass -> overall 'pass'."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.NONE, action="block"),
            PolicyRule(moderation_class=ModerationClass.VIOLENCE_GRAPHIC, max_severity=Severity.LOW, action="flag"),
        ])
        result = evaluate(policy, [])
        assert result.overall_verdict == "pass"
        assert all(r.passed for r in result.rules)

    def test_flags_below_threshold(self):
        """Detected severity <= max_severity -> passes."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.MEDIUM, action="block"),
        ])
        flags = [{"moderation_class": "hate_speech", "severity": "low"}]
        result = evaluate(policy, flags)
        assert result.overall_verdict == "pass"
        assert result.rules[0].passed is True
        assert result.rules[0].detected_severity == "low"


class TestSingleRuleBlocks:
    def test_block_action(self):
        """One rule exceeded with action='block' -> overall 'block'."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.NONE, action="block"),
        ])
        flags = [{"moderation_class": "hate_speech", "severity": "high"}]
        result = evaluate(policy, flags)
        assert result.overall_verdict == "block"
        assert result.rules[0].passed is False
        assert result.rules[0].detected_severity == "high"


class TestSingleRuleFlags:
    def test_flag_action(self):
        """One rule exceeded with action='flag' -> overall 'flag'."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.VIOLENCE_GRAPHIC, max_severity=Severity.LOW, action="flag"),
        ])
        flags = [{"moderation_class": "violence_graphic", "severity": "high"}]
        result = evaluate(policy, flags)
        assert result.overall_verdict == "flag"
        assert result.rules[0].passed is False


class TestBlockBeatsFlag:
    def test_most_restrictive_wins(self):
        """Both block and flag rules fail -> overall 'block' (most restrictive)."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.NONE, action="flag"),
            PolicyRule(moderation_class=ModerationClass.VIOLENCE_GRAPHIC, max_severity=Severity.NONE, action="block"),
        ])
        flags = [
            {"moderation_class": "hate_speech", "severity": "medium"},
            {"moderation_class": "violence_graphic", "severity": "low"},
        ]
        result = evaluate(policy, flags)
        assert result.overall_verdict == "block"


class TestMissingClassPasses:
    def test_rule_for_undetected_class(self):
        """Rule references class not in flags -> passes (not detected = safe)."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.NONE, action="block"),
        ])
        flags = [{"moderation_class": "violence_graphic", "severity": "high"}]
        result = evaluate(policy, flags)
        assert result.overall_verdict == "pass"
        assert result.rules[0].passed is True
        assert result.rules[0].detected_severity == "none"


class TestEmptyModerationFlags:
    def test_empty_list(self):
        """No flags at all -> all rules pass."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.NONE, action="block"),
            PolicyRule(moderation_class=ModerationClass.VIOLENCE_GRAPHIC, max_severity=Severity.NONE, action="flag"),
        ])
        result = evaluate(policy, [])
        assert result.overall_verdict == "pass"
        assert all(r.passed for r in result.rules)


class TestMultipleDetectionsSameClass:
    def test_max_severity_used(self):
        """Two detections of same class at different severities -> max used."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.LOW, action="block"),
        ])
        flags = [
            {"moderation_class": "hate_speech", "severity": "low"},
            {"moderation_class": "hate_speech", "severity": "high"},
        ]
        result = evaluate(policy, flags)
        assert result.overall_verdict == "block"
        assert result.rules[0].passed is False
        assert result.rules[0].detected_severity == "high"


class TestAllowActionNoEscalation:
    def test_allow_exceeded_no_escalation(self):
        """Rule with action='allow' exceeded -> does NOT change overall verdict."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.NONE, action="allow"),
        ])
        flags = [{"moderation_class": "hate_speech", "severity": "critical"}]
        result = evaluate(policy, flags)
        assert result.overall_verdict == "pass"
        assert result.rules[0].passed is False

    def test_allow_with_other_flag(self):
        """Allow action doesn't escalate even with other failing flag rules."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.NONE, action="allow"),
            PolicyRule(moderation_class=ModerationClass.VIOLENCE_GRAPHIC, max_severity=Severity.NONE, action="flag"),
        ])
        flags = [
            {"moderation_class": "hate_speech", "severity": "critical"},
            {"moderation_class": "violence_graphic", "severity": "low"},
        ]
        result = evaluate(policy, flags)
        assert result.overall_verdict == "flag"  # only flag, not block


class TestSeverityBoundary:
    def test_equal_severity_passes(self):
        """detected == max_severity -> passes (<=, not <)."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.MEDIUM, action="block"),
        ])
        flags = [{"moderation_class": "hate_speech", "severity": "medium"}]
        result = evaluate(policy, flags)
        assert result.overall_verdict == "pass"
        assert result.rules[0].passed is True


class TestDisclaimerPresent:
    def test_disclaimer_in_result(self):
        """Disclaimer string in every result."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.NONE, action="block"),
        ])
        result = evaluate(policy, [])
        assert result.disclaimer == DISCLAIMER
        assert "not legal" in result.disclaimer.lower()


class TestDefensiveLowerCase:
    def test_uppercase_severity_handled(self):
        """Severity strings with unusual casing are lowered before lookup."""
        policy = _make_policy([
            PolicyRule(moderation_class=ModerationClass.HATE_SPEECH, max_severity=Severity.LOW, action="block"),
        ])
        flags = [{"moderation_class": "hate_speech", "severity": "HIGH"}]
        result = evaluate(policy, flags)
        assert result.rules[0].passed is False
        assert result.rules[0].detected_severity == "high"
