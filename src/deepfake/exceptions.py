"""Exceptions for deepfake detection."""


class DeepfakeError(Exception):
    """Base exception for deepfake detection."""

    pass


class DeepfakeAPIError(DeepfakeError):
    """External API error."""

    pass


class DeepfakeRateLimitError(DeepfakeError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class DeepfakeTimeoutError(DeepfakeError):
    """Request timeout."""

    pass


class DeepfakeServiceUnavailable(DeepfakeError):
    """Service temporarily unavailable."""

    pass


class NoFaceDetectedError(DeepfakeError):
    """Video has no detectable faces for lip-sync analysis."""

    pass


class VideoTooLongError(DeepfakeError):
    """Video exceeds maximum duration for analysis."""

    def __init__(self, duration: float, max_duration: float):
        super().__init__(
            f"Video duration {duration}s exceeds maximum {max_duration}s"
        )
        self.duration = duration
        self.max_duration = max_duration


class AllProvidersUnavailableError(DeepfakeError):
    """Raised when no deepfake detection provider is reachable."""

    def __init__(self, limitations: list[str]):
        self.limitations = limitations
        super().__init__("All deepfake detection providers unavailable")


class DailySpendLimitExceeded(DeepfakeError):
    """Raised when user exceeds daily deepfake spend limit."""

    def __init__(self, current: int, limit: int):
        self.current_cost_cents = current
        self.limit_cents = limit
        super().__init__(f"Daily limit {limit} cents exceeded (current: {current})")
