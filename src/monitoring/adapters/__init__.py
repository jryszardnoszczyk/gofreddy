"""Monitoring data source adapters.

Each adapter extends BaseMentionFetcher and implements _do_fetch()
to map platform-specific API responses to RawMention DTOs.

Adapters with optional pip dependencies use lazy imports so that
missing packages (e.g. xpoz) don't crash the entire application.
"""

from ._common import parse_date, rating_to_sentiment
from .bluesky import BlueskyMentionFetcher
from .news import NewsDataAdapter


def __getattr__(name: str):
    """Lazy-import adapters that depend on optional packages."""
    _lazy = {
        "XpozAdapter": ".xpoz",
        "ICContentAdapter": ".ic_content",
        "TikTokAdapter": ".tiktok",
        "FacebookMentionFetcher": ".facebook",
        "LinkedInMentionFetcher": ".linkedin",
        "GoogleTrendsAdapter": ".google_trends",
        "PodEngineAdapter": ".podcasts",
        "TrustpilotAdapter": ".reviews",
        "AppStoreAdapter": ".reviews",
        "PlayStoreAdapter": ".reviews",
    }
    if name in _lazy:
        import importlib
        mod = importlib.import_module(_lazy[name], package=__name__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BlueskyMentionFetcher",
    "FacebookMentionFetcher",
    "LinkedInMentionFetcher",
    "GoogleTrendsAdapter",
    "ICContentAdapter",
    "NewsDataAdapter",
    "PodEngineAdapter",
    "TikTokAdapter",
    "TrustpilotAdapter",
    "AppStoreAdapter",
    "PlayStoreAdapter",
    "XpozAdapter",
    "parse_date",
    "rating_to_sentiment",
]
