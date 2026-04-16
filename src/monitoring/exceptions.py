"""Monitoring module exceptions."""


class MonitoringError(Exception):
    """Base exception for monitoring domain."""


class MonitorNotFoundError(MonitoringError):
    """Monitor does not exist or user lacks access."""


class MonitorLimitExceededError(MonitoringError):
    """User has reached maximum monitor count."""


class MentionFetchError(MonitoringError):
    """Adapter failed to fetch mentions from source."""


class CursorError(MonitoringError):
    """Cursor state is invalid or corrupted."""


class AlertRuleNotFoundError(MonitoringError):
    """Alert rule does not exist or user lacks access."""


class AlertRuleLimitError(MonitoringError):
    """User has reached maximum alert rules."""


class WebhookDeliveryError(MonitoringError):
    """Webhook delivery failed after retries."""


class ClassificationCapExceededError(MonitoringError):
    """Daily classification limit reached for a monitor."""


class InsufficientMentionsError(MonitoringError):
    """Not enough mentions for the requested operation."""


class AnalyticsError(MonitoringError):
    """Base exception for analytics operations."""


class ICUnavailableError(MonitoringError):
    """IC (Influencers.club) API is unavailable."""
