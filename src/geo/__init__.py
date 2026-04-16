"""GEO (Generative Engine Optimization) audit service.

Provides AI search visibility auditing: SCRAPE → DETECT → ANALYZE → GENERATE → FORMAT.
"""

from .config import GeoSettings
from .exceptions import GeoAuditError, ProviderUnavailableError

__all__ = [
    "GeoSettings",
    "GeoAuditError",
    "ProviderUnavailableError",
]
