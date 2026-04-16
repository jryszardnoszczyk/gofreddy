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

__all__ = [
    "DeepfakeConfig",
    "DeepfakeAPIError",
    "DeepfakeError",
    "DeepfakeRateLimitError",
    "DeepfakeServiceUnavailable",
    "DeepfakeTimeoutError",
    "NoFaceDetectedError",
    "VideoTooLongError",
    "Confidence",
    "DeepfakeAnalysisRecord",
    "DeepfakeAnalysisResponse",
    "DeepfakeAnalyzeRequest",
    "DetectionMethod",
    "LipSyncResult",
    "RealityDefenderResult",
    "RiskLevel",
    "Verdict",
    "LIPINCAnalyzer",
    "RealityDefenderClient",
]
