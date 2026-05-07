"""Billing exceptions."""


class BillingError(Exception):
    """Base exception for billing errors."""

    pass


class InvalidAPIKey(BillingError):
    """Raised when API key is invalid or revoked."""

    pass


class UserNotFound(BillingError):
    """Raised when user is not found by ID."""

    pass


class UsageLimitExceeded(BillingError):
    """Raised when user exceeds their tier's usage limit."""

    pass


class FeatureNotAvailable(BillingError):
    """Raised when user's tier doesn't include requested feature."""

    pass
