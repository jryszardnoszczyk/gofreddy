"""Publishing module exceptions."""


class PublishError(Exception):
    """Base exception for publishing domain."""


class ConnectionNotFoundError(PublishError):
    """Platform connection not found or user lacks access."""


class QueueItemNotFoundError(PublishError):
    """Publish queue item not found or user lacks access."""


class QueueLimitExceededError(PublishError):
    """Org has reached maximum queue item count."""


class CredentialError(PublishError):
    """Credential decryption or validation failed."""


class AdapterError(PublishError):
    """Platform adapter failed to publish content."""


class TokenExpiredError(CredentialError):
    """OAuth token has expired and needs refresh."""


class ContentTooLargeError(AdapterError):
    """Content exceeds platform size limits."""


class ContentValidationError(PublishError):
    """Content failed platform-specific validation."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Content validation failed: {'; '.join(errors)}")


class PlatformRateLimitError(AdapterError):
    """Platform rate limit exceeded."""


class OAuthFlowError(PublishError):
    """OAuth device/authorization flow error."""


class QuotaExhaustedError(AdapterError):
    """Platform quota (e.g. YouTube daily uploads) exhausted."""
