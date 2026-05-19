"""JSON-backed cache for verified claim+URL pairs (AE-3 / TD-44).

Caches the verifier's `{verified, confidence, rationale, degraded}`
result so repeated runs over the same citation don't re-spend
claude/opus tokens. Per TD-44: cached indefinitely; the
`freddy autoresearch verify-citations --fresh` CLI flag clears the
cache when the operator wants a re-verification pass.

Key shape: SHA-256 hash of `claim\\n\\nurl` (newline-delimited to avoid
collisions where claim ends with the URL). Value: the verification
dict + an ISO-8601 timestamp for audit.

The cache file path defaults to `cache/citation_verifications.json` at
the repo root; callers may pass an explicit path for tests or
per-client isolation.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CACHE_PATH = _REPO_ROOT / "cache" / "citation_verifications.json"


class CitationCache:
    """JSON-file-backed key-value store for citation verifications.

    Thread-safety: this v1 implementation is NOT thread-safe — callers
    that need concurrent access must serialize externally. Article
    generation runs single-threaded per lane, so the simple shape is
    sufficient for v1.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _DEFAULT_CACHE_PATH
        self._data: dict[str, Any] | None = None

    def _key(self, claim: str, url: str) -> str:
        """SHA-256 hash of newline-joined (claim, url). Newline avoids
        accidental collisions between (a + b, c) and (a, b + c) shapes."""
        payload = f"{claim}\n\n{url}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _load(self) -> dict[str, Any]:
        if self._data is not None:
            return self._data
        if not self.path.is_file():
            self._data = {}
            return self._data
        try:
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            # Corrupted cache file: log + start fresh. The cache is a
            # cost-saving optimisation, not authoritative state — losing
            # entries to corruption is acceptable; crashing the lane on a
            # malformed cache file is not.
            logger.warning(
                "citation cache at %s is unreadable (%s); starting fresh",
                self.path, exc,
            )
            self._data = {}
        return self._data

    def _flush(self) -> None:
        if self._data is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def get(self, claim: str, url: str) -> dict[str, Any] | None:
        """Return the cached verification dict for (claim, url), or
        None when no entry exists."""
        entry = self._load().get(self._key(claim, url))
        if entry is None:
            return None
        return entry.get("verification")

    def set(self, claim: str, url: str, verification: dict[str, Any]) -> None:
        """Store a verification result for (claim, url). Overwrites
        any prior entry — re-verification under `--fresh` produces a
        fresh entry on the next call."""
        data = self._load()
        data[self._key(claim, url)] = {
            "verification": verification,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        self._flush()

    def clear(self) -> None:
        """Wipe the cache. Invoked by `--fresh` CLI flag."""
        self._data = {}
        if self.path.is_file():
            self.path.unlink()
