"""5-provider signal aggregator (R17 / U15 / TD-42)."""
from src.ads.signal_aggregator.aggregator import (
    SignalBundle,
    all_meta_sources_degraded,
    gather_signals,
)
from src.ads.signal_aggregator.merger import merge_ad_signals
from src.ads.signal_aggregator.providers import (
    AdSignal,
    AdyntelProvider,
    ForeplayProvider,
    GscProvider,
    MetaAdLibraryProvider,
    SearchSignal,
    SerpApiProvider,
)

__all__ = [
    "AdSignal",
    "AdyntelProvider",
    "ForeplayProvider",
    "GscProvider",
    "MetaAdLibraryProvider",
    "SearchSignal",
    "SerpApiProvider",
    "SignalBundle",
    "all_meta_sources_degraded",
    "gather_signals",
    "merge_ad_signals",
]
