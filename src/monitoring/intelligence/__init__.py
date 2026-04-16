"""Intelligence layer for monitoring — sentiment, intent, SOV, analytics."""

from .engagement_predictor import predict_engagement  # noqa: F401
from .metric_computations import compute_date_gaps, compute_engagement_spikes, compute_velocity_flags  # noqa: F401
from .performance_patterns import generate_performance_patterns  # noqa: F401
