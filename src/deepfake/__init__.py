"""PR-017: Advanced Deepfake Detection module."""

from .config import DeepfakeConfig
from .exceptions import (
    DeepfakeAPIError,
    DeepfakeError,
    DeepfakeRateLimitError,
    DeepfakeServiceUnavailable,
    DeepfakeTimeoutError,
    NoFaceDetectedError,
    VideoTooLongError,
)
from .lipinc import LIPINCAnalyzer
from .models import (
    Confidence,
    DeepfakeAnalysisRecord,
    DeepfakeAnalysisResponse,
    DeepfakeAnalyzeRequest,
    DetectionMethod,
    LipSyncResult,
    RealityDefenderResult,
    RiskLevel,
    Verdict,
)
from .reality_defender import RealityDefenderClient
from .repository import PostgresDeepfakeRepository
from .service import DeepfakeService

__all__ = [
    # Config
    "DeepfakeConfig",
    # Exceptions
    "DeepfakeAPIError",
    "DeepfakeError",
    "DeepfakeRateLimitError",
    "DeepfakeServiceUnavailable",
    "DeepfakeTimeoutError",
    "NoFaceDetectedError",
    "VideoTooLongError",
    # Models
    "Confidence",
    "DeepfakeAnalysisRecord",
    "DeepfakeAnalysisResponse",
    "DeepfakeAnalyzeRequest",
    "DetectionMethod",
    "LipSyncResult",
    "RealityDefenderResult",
    "RiskLevel",
    "Verdict",
    # Clients
    "LIPINCAnalyzer",
    "RealityDefenderClient",
    # Repository
    "PostgresDeepfakeRepository",
    # Service
    "DeepfakeService",
]
