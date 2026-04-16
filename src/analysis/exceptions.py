"""Analysis module exceptions."""

# Re-export from common so existing importers keep working.
from ..common.exceptions import PoolExhaustedError  # noqa: F401


class AnalysisError(Exception):
    """Base exception for analysis errors."""

    pass


class GeminiRateLimitError(AnalysisError):
    """Gemini API rate limit exceeded."""

    pass


class VideoProcessingError(AnalysisError):
    """Video could not be processed by Gemini."""

    pass


class ConnectionError(AnalysisError):
    """Database connection failed."""

    pass


class IntegrityError(AnalysisError):
    """Database integrity constraint violated."""

    def __init__(self, constraint: str, detail: str) -> None:
        self.constraint = constraint
        self.detail = detail
        super().__init__(f"Integrity error ({constraint}): {detail}")
