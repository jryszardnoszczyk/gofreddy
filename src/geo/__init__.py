"""GEO (Generative Engine Optimization) audit service.

Provides AI search visibility auditing: SCRAPE → DETECT → ANALYZE → GENERATE → FORMAT.
"""

from .config import GeoSettings
from .exceptions import GeoAuditError, ProviderUnavailableError
from .service import GeoService

__all__ = [
    "GeoSettings",
    "GeoAuditError",
    "ProviderUnavailableError",
    "GeoService",
]
