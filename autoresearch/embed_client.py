"""Thin OpenAI embeddings wrapper for novelty rejection (Stream C C1).

Wraps ``POST https://api.openai.com/v1/embeddings`` against the
``text-embedding-3-small`` model (1536-dim, ~$0.02/1M tokens). Kept
deliberately small: a single function, an in-process LRU cache, no
implicit retries (callers decide). Raises ``EmbeddingUnavailable`` on
any failure so the novelty-rejection path can degrade gracefully
(accept-by-default) rather than crash the evolve loop.
"""
from __future__ import annotations

import os
from functools import lru_cache


_EMBED_MODEL = "text-embedding-3-small"
_EMBED_DIM = 1536
_EMBED_ENDPOINT = "https://api.openai.com/v1/embeddings"
# OpenAI's 8192-token cap converts to roughly 30KB of English prose. Cap
# the input bytes well above that — text-embedding-3-small truncates
# server-side anyway, but a byte cap keeps our payloads under any
# upstream proxy budget.
_MAX_INPUT_BYTES = 1_500_000


class EmbeddingUnavailable(RuntimeError):
    """Raised when an embedding cannot be fetched (auth / network / quota)."""


def embed_text(text: str, *, timeout: float = 30.0) -> list[float]:
    """Return the embedding vector for ``text`` (1536-dim list of floats).

    Backed by an in-process LRU cache keyed on the input string so that
    repeated calls within a single evolve run (e.g., embedding the same
    sibling variant on every generation) skip the network round-trip.
    """
    return list(_cached_embed(text, timeout))


@lru_cache(maxsize=512)
def _cached_embed(text: str, timeout: float) -> tuple[float, ...]:
    if not text:
        raise EmbeddingUnavailable("cannot embed empty text")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise EmbeddingUnavailable(
            "OPENAI_API_KEY is unset; novelty rejection requires "
            "text-embedding-3-small via OpenAI."
        )
    payload_text = text
    if len(payload_text.encode("utf-8")) > _MAX_INPUT_BYTES:
        payload_text = payload_text.encode("utf-8")[:_MAX_INPUT_BYTES].decode(
            "utf-8", errors="ignore",
        )

    import httpx  # noqa: PLC0415 — lazy import keeps module-load surface small
    try:
        response = httpx.post(
            _EMBED_ENDPOINT,
            json={"model": _EMBED_MODEL, "input": payload_text},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise EmbeddingUnavailable(f"network error: {exc}") from exc
    if response.status_code >= 400:
        raise EmbeddingUnavailable(
            f"OpenAI embeddings HTTP {response.status_code}: "
            f"{response.text[:200]}"
        )
    try:
        data = response.json()
        embedding = data["data"][0]["embedding"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise EmbeddingUnavailable(f"malformed embeddings response: {exc}") from exc
    if not isinstance(embedding, list) or len(embedding) != _EMBED_DIM:
        raise EmbeddingUnavailable(
            f"unexpected embedding shape: got {type(embedding).__name__} of "
            f"length {len(embedding) if hasattr(embedding, '__len__') else '?'}"
        )
    return tuple(float(x) for x in embedding)
