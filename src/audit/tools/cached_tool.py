"""Decorator that wraps a provider method so all calls go through ``cache_or_call``.

Usage::

    from src.audit.tools.cached_tool import cached_tool

    class DataForSeoProvider:
        @cached_tool("dataforseo.technical_audit")
        async def technical_audit(self, url: str) -> TechnicalAuditResult: ...

When invoked, the decorator:

1. Builds the cache key from the bound function's positional + keyword args
   (``self`` is dropped — the cache is shared across provider instances since
   the underlying API responses don't depend on which instance issued the call).
2. Resolves ``cache_dir`` from a thread-local set by Stage 1a fan-out
   (``set_audit_cache_dir(path)``), or from a ``cache_dir=`` kwarg passed at
   call time, in that order.
3. Delegates to ``cache.cache_or_call`` with sync/async detection.

If no ``cache_dir`` is resolvable, the decorator passes through to the wrapped
function unchanged — keeps non-audit callers (CI smoke tests, manual REPL use)
working without forcing them to set up cache scoping.
"""
from __future__ import annotations

import functools
import inspect
import threading
from pathlib import Path
from typing import Any, Awaitable, Callable, TypeVar

from . import cache as _cache

F = TypeVar("F", bound=Callable[..., Any])

# Thread-local audit-scoped cache directory. Stage 1a fan-out sets this once
# per audit run; agent-side filesystem reads in Stage 2 don't use this code
# path (they read cache files directly).
_local = threading.local()


def set_audit_cache_dir(path: Path | str | None) -> None:
    """Bind the active audit's cache directory to the current thread.

    Pass ``None`` to clear the binding (useful for test teardown). Stage 1a's
    ``stage_1_warmup`` calls this once after creating
    ``clients/<slug>/audit/cache/``; the cache dir then propagates implicitly
    through every ``@cached_tool``-decorated method invoked on this thread.
    """
    if path is None:
        if hasattr(_local, "cache_dir"):
            del _local.cache_dir
        return
    _local.cache_dir = Path(path)


def get_audit_cache_dir() -> Path | None:
    return getattr(_local, "cache_dir", None)


def cached_tool(
    tool_name: str,
    *,
    ttl_hours: int = _cache.DEFAULT_TTL_HOURS,
    skip_self: bool = True,
) -> Callable[[F], F]:
    """Decorator factory.

    Parameters
    ----------
    tool_name
        Stable cache namespace (e.g. ``"dataforseo.technical_audit"``).
        Becomes the filename prefix.
    ttl_hours
        TTL passed through to ``cache_or_call``. 24h matches §4.5 default.
    skip_self
        When ``True`` (default), ``self`` is omitted from the cache-key args
        so cache hits across provider instances work as expected.
    """

    def _decorate(fn: F) -> F:
        sig = inspect.signature(fn)
        is_coro = inspect.iscoroutinefunction(fn)

        def _build_args(args: tuple, kwargs: dict) -> tuple[dict, dict, Path | None]:
            # Strip the optional ``cache_dir=`` kwarg before signature-binding
            # so wrapped functions that don't declare it don't error out.
            kwargs = dict(kwargs)
            override = kwargs.pop("cache_dir", None)
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            cache_args = dict(bound.arguments)
            if skip_self:
                cache_args.pop("self", None)
                cache_args.pop("cls", None)
            cache_dir = Path(override) if override is not None else get_audit_cache_dir()
            return cache_args, kwargs, cache_dir

        if is_coro:

            @functools.wraps(fn)
            async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
                cache_args, real_kwargs, cache_dir = _build_args(args, kwargs)
                if cache_dir is None:
                    return await fn(*args, **real_kwargs)

                async def _call(**call_args: Any) -> Any:
                    return await fn(*args, **real_kwargs)

                return await _cache.cache_or_call(
                    tool_name,
                    cache_args,
                    _call,
                    ttl_hours=ttl_hours,
                    cache_dir=cache_dir,
                )

            return _async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def _sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_args, real_kwargs, cache_dir = _build_args(args, kwargs)
            if cache_dir is None:
                return fn(*args, **real_kwargs)

            def _call(**call_args: Any) -> Any:
                return fn(*args, **real_kwargs)

            return _cache.cache_or_call(
                tool_name,
                cache_args,
                _call,
                ttl_hours=ttl_hours,
                cache_dir=cache_dir,
            )

        return _sync_wrapper  # type: ignore[return-value]

    return _decorate
