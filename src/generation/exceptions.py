"""Generation module exceptions."""


class GenerationError(Exception):
    """Base exception for generation module."""


class GenerationTimeoutError(GenerationError):
    """Generation exceeded deadline."""


class GenerationDailySpendLimitExceeded(GenerationError):
    """User hit daily generation spend cap."""


class GenerationConcurrentLimitExceeded(GenerationError):
    """User has too many active generation jobs."""


class IdeationError(GenerationError):
    """IdeaService failed to generate a valid CompositionSpec."""


class PreviewError(GenerationError):
    """Image preview generation failed."""


class ModerationBlockedError(GenerationError):
    """Content blocked by provider's moderation system."""


class ProviderUnavailableError(GenerationError):
    """Circuit breaker tripped — provider consistently failing."""


# Backward-compatible aliases (previously defined in grok_client.py)
GrokModerationBlockedError = ModerationBlockedError
GrokAPIUnavailableError = ProviderUnavailableError
