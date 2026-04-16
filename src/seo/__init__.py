"""SEO (Search Engine Optimization) audit service.

Provides technical SEO audits, keyword analysis, performance checks,
backlink snapshots, and content quality analysis via DataForSEO + OSS tools.
"""

from .config import SeoSettings
from .exceptions import SeoAuditError

__all__ = [
    "SeoSettings",
    "SeoAuditError",
]
