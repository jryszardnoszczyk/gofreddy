"""Audit tool helpers.

Public surface (master plan §4.5 + §4.4):

- ``cache.cache_or_call`` — hash-dedup cache wrapper used by Stage 1a Python
  fan-out and by Stage 2 agents (filesystem reads of cache files).
- ``cached_tool.cached_tool`` — decorator that wraps a provider method so
  every call routes through ``cache_or_call``.
- ``martech.fingerprint_martech_stack`` — Wappalyzer-next port wrapper.
- ``rendered_fetcher.RenderedFetcher`` — Playwright Chromium headless wrapper.

All four were Phase 1.5 build items in the master plan. None of these modules
existed on disk before L2. See §4.9 for sequencing + estimates.
"""
