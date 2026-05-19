"""Unified transcript tailer — in-process asyncio task.

Watches both ``~/.claude/projects/<encoded-cwd>/*.jsonl`` and
``~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl`` for new agent
sessions; emits ``session_start`` / ``session_end`` to the appropriate
per-client (or operator-internal) wide log via cwd-only attribution; and
maintains the per-client session registry that the drill-down route
(Unit 6) consults for its IDOR guard.

Design constraints (from plan §Unit 2):

* **Polling, not inotify.** Mirrors ``tail_events_sse``'s polling style
  for portability (no Linux-only inotify dependency).
* **Bounded session-of-interest set.** Only sessions whose JSONL mtime
  is within the last 24h are eligible for active tail; older files are
  registered once (so the drill-down IDOR guard can resolve them) but
  emit no ``session_start``/``session_end`` to the wide log.
* **No held file descriptors.** Each tick opens, reads what it needs,
  closes.
* **cwd-only attribution.** The tailer never reads env hints; CC hook
  is the env-first path. cwd contains ``clients/<slug>/`` → attribute
  to slug (after validating against the ``clients`` DB table); else
  operator-internal.
* **Defense in depth.** Every ``file_path`` is ``Path.resolve(strict=True)``-d
  and asserted under ``CC_ROOT``/``CODEX_ROOT`` before being persisted
  to the session registry. Paths leaving the roots via symlink emit a
  ``kind="alert"`` operator-internal log and are dropped.
* **No `emit_moment` wrapper.** Per TD-56 reconciliation, all moment
  emission is direct ``log_event(kind="moment", ...)``.

The slug-validation seam is intentionally **injectable** so tests can
substitute a fake without standing up a real asyncpg pool. Production
wiring (in ``src/api/main.py``) supplies a callable that queries the
``clients`` table via ``app.state.db_pool``.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from autoresearch.events import client_events_path, log_event

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tunables (env-overridable, plus safe constructor overrides for tests).
# ---------------------------------------------------------------------------

_DEFAULT_POLL_INTERVAL_S = 1.5
_MIN_POLL_INTERVAL_S = 0.25
_MAX_POLL_INTERVAL_S = 60.0

# Sessions whose JSONL mtime is older than this are registered once but
# not actively tailed (no session_start/session_end emission).
_DEFAULT_ACTIVE_WINDOW_S = 24 * 3600  # 24h

# Idle-timeout: how long a session JSONL can sit with unchanged mtime
# (and no size growth across 3 consecutive ticks) before we emit
# session_end with reason="idle_timeout".
_DEFAULT_IDLE_TIMEOUT_S = 10 * 60  # 10 minutes
_IDLE_TIMEOUT_STABLE_TICKS = 3

# Slug validation pattern — kept in sync with the portal route patterns
# (`^[a-z0-9-]{1,64}$`). Anchored: full string must match.
_SLUG_RE = re.compile(r"^[a-z0-9-]{1,64}$")

# Codex events that close a session mid-tail.
_CODEX_TERMINAL_EVENTS: frozenset[str] = frozenset({
    "task_completed",
    "task_aborted",
})

# How many leading lines to parse from a Codex JSONL when looking for
# session_meta (cwd field). Same cap used for CC sanity-parse.
_LEADING_LINES_TO_PARSE = 10


# ---------------------------------------------------------------------------
# Path helpers — CC and Codex roots, encoded-cwd decoder.
# ---------------------------------------------------------------------------


def cc_root() -> Path:
    """``~/.claude/projects`` resolved at call time (honors Path.home() patches)."""
    return Path.home() / ".claude" / "projects"


def codex_root() -> Path:
    """``~/.codex/sessions`` resolved at call time."""
    return Path.home() / ".codex" / "sessions"


def operator_internal_path() -> Path:
    """``~/.local/share/gofreddy/events.jsonl`` — fallback log for operator-internal."""
    return Path.home() / ".local" / "share" / "gofreddy" / "events.jsonl"


def encode_cwd_for_cc(cwd: Path) -> str:
    """Encode a cwd into CC's project-dir naming.

    CC stores ``~/.claude/projects/<cwd-with-slashes-as-dashes>/*.jsonl``.
    Leading `/` becomes the leading `-` marker. This is the inverse of
    :func:`decode_cc_dirname`. Mirrors ``viable_resume_id`` (autoresearch.sessions).
    """
    return str(cwd).replace("/", "-")


def decode_cc_dirname(dirname: str) -> Path:
    """Decode a CC project-dir name back to an absolute cwd Path.

    CC's encoding (``/`` → ``-``) is **not perfectly reversible** when the
    real path legitimately contains ``-``. We anchor on the resulting path
    existing on disk:

    1. Replace every ``-`` with ``/`` to get a candidate absolute path.
    2. The leading ``-`` marker becomes a leading ``/`` (i.e. ``/Users/...``).
    3. Caller is responsible for asserting the result exists.

    Returns the best-effort decoded Path. May not exist; caller checks.
    """
    if not dirname.startswith("-"):
        # CC always prefixes with `-` because cwd always starts with `/`.
        # If we see a dirname that doesn't, fall back to literal interpretation.
        return Path(dirname.replace("-", "/"))
    return Path("/" + dirname[1:].replace("-", "/"))


# ---------------------------------------------------------------------------
# Slug attribution.
# ---------------------------------------------------------------------------


# Type alias for the slug-validation seam. Tests inject a stub; production
# wires the real asyncpg query at lifespan-attach time.
SlugValidator = Callable[[str], Awaitable[bool]]


def extract_slug_from_cwd(cwd: Path) -> str | None:
    """Return the slug if the cwd contains a ``clients/<slug>/`` segment.

    Returns ``None`` if the path has no such segment. Does NOT validate
    the slug pattern or check it against the ``clients`` table — those
    are downstream gates (see :func:`attribute_session`).
    """
    parts = cwd.parts
    for i, part in enumerate(parts):
        if part == "clients" and i + 1 < len(parts):
            return parts[i + 1]
    return None


@dataclass(frozen=True)
class Attribution:
    """Outcome of attribute_session: where the session_start lands."""

    client_id: str | None  # None == operator-internal
    reason: str | None  # set when downgraded from a candidate slug to operator-internal

    @property
    def is_operator_internal(self) -> bool:
        return self.client_id is None


async def attribute_session(
    cwd: Path, *, is_slug_valid: SlugValidator
) -> Attribution:
    """Map a session's cwd to a client slug or operator-internal.

    Two failure modes are downgraded to operator-internal **and** logged
    as ``kind="moment"`` / ``moment_kind="attribution_conflict"`` per
    R5.5:

    * **slug_invalid** — cwd contains a ``clients/<slug>/`` segment but
      ``<slug>`` doesn't match the ``[a-z0-9-]{1,64}`` pattern.
    * **slug_unknown** — slug matches the pattern but is not in the
      ``clients`` DB table.
    """
    candidate = extract_slug_from_cwd(cwd)
    if candidate is None:
        # No clients/<slug>/ segment in cwd → operator-internal. Not a
        # conflict — this is the normal autoresearch-internal case.
        return Attribution(client_id=None, reason=None)

    if not _SLUG_RE.match(candidate):
        log_event(
            "moment",
            path=client_events_path(None),
            metadata={
                "moment_kind": "attribution_conflict",
                "title": "Slug failed pattern validation",
                "reason": "slug_invalid",
                "candidate": candidate,
                "cwd": str(cwd),
            },
        )
        return Attribution(client_id=None, reason="slug_invalid")

    valid = await is_slug_valid(candidate)
    if not valid:
        log_event(
            "moment",
            path=client_events_path(None),
            metadata={
                "moment_kind": "attribution_conflict",
                "title": "Slug not in clients table",
                "reason": "slug_unknown",
                "candidate": candidate,
                "cwd": str(cwd),
            },
        )
        return Attribution(client_id=None, reason="slug_unknown")

    return Attribution(client_id=candidate, reason=None)


# ---------------------------------------------------------------------------
# Sanity parse — confirms a JSONL is a real CC/Codex session before we
# emit any session_start event. Also extracts the Codex cwd.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SanityResult:
    is_session: bool
    codex_cwd: Path | None = None


def sanity_parse_jsonl(path: Path, *, source: str) -> SanityResult:
    """Inspect the first ~10 lines of a JSONL.

    * CC: any ``{"type": ...}`` line is enough.
    * Codex: looks for a ``session_meta``-shaped event with a ``cwd`` or
      ``payload.cwd`` field.

    Returns SanityResult(is_session=False) when the file appears mid-write
    or otherwise unparseable — caller retries next tick.
    """
    try:
        with path.open("r") as handle:
            lines: list[str] = []
            for _ in range(_LEADING_LINES_TO_PARSE):
                line = handle.readline()
                if not line:
                    break
                lines.append(line)
    except (OSError, UnicodeDecodeError):
        return SanityResult(is_session=False)

    if not lines:
        return SanityResult(is_session=False)

    if source == "cc":
        for raw in lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and "type" in obj:
                return SanityResult(is_session=True)
        return SanityResult(is_session=False)

    # codex: scan for session_meta with cwd
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        # session_meta can appear at top level (type=session_meta) or nested
        # under a payload field with a type discriminator. Be lenient.
        is_meta = (
            obj.get("type") == "session_meta"
            or (
                isinstance(obj.get("payload"), dict)
                and obj["payload"].get("type") == "session_meta"
            )
        )
        if not is_meta:
            continue
        cwd_val = obj.get("cwd")
        if cwd_val is None and isinstance(obj.get("payload"), dict):
            cwd_val = obj["payload"].get("cwd")
        if isinstance(cwd_val, str) and cwd_val:
            return SanityResult(is_session=True, codex_cwd=Path(cwd_val))
        # session_meta seen but no cwd: still a session — caller will treat
        # it as operator-internal (no cwd → no clients/<slug>/ extraction).
        return SanityResult(is_session=True, codex_cwd=None)

    return SanityResult(is_session=False)


def session_id_from_cc_path(path: Path) -> str:
    """CC stores files as ``<dir>/<session_id>.jsonl``."""
    return path.stem


# Codex rollout naming: ``rollout-<YYYY-MM-DDTHH-MM-SS>-<sid>.jsonl``.
# The sid is a UUID containing internal `-`s, so we strip the fixed-shape
# timestamp prefix and treat everything after as the session_id. The
# timestamp regex is anchored: 4 digits, 3 of "-DD" pairs, T, 3 of "-DD".
_CODEX_TIMESTAMP_PREFIX_RE = re.compile(
    r"^rollout-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-(?P<sid>.+)$"
)
# Fallback for test rollouts using shorter sids (no UUID dashes) where the
# strict-timestamp pattern is overkill. Keeps the existing test ergonomic.
_CODEX_ROLLOUT_FALLBACK_RE = re.compile(r"^rollout-.+-(?P<sid>[A-Za-z0-9]+)$")


def session_id_from_codex_path(path: Path) -> str | None:
    """Codex stores files as ``rollout-<timestamp>-<session_id>.jsonl``.

    The session_id is typically a UUID containing internal ``-``s; we
    anchor on the fixed-shape timestamp prefix to recover it. Falls back
    to a simpler trailing-segment match for short test fixtures.
    """
    stem = path.stem
    m = _CODEX_TIMESTAMP_PREFIX_RE.match(stem)
    if m is not None:
        return m.group("sid")
    m = _CODEX_ROLLOUT_FALLBACK_RE.match(stem)
    if m is None:
        return None
    return m.group("sid")


# ---------------------------------------------------------------------------
# Codex-end detection — scan trailing lines for task_completed/aborted.
# ---------------------------------------------------------------------------


def detect_codex_terminal_event(path: Path) -> str | None:
    """Return ``"task_completed"`` or ``"task_aborted"`` if the JSONL contains
    such an event, else None.

    Cheap full-file scan: codex rollouts are small enough that this is fine
    for v1. If a real session crosses 100MB we'll need a smarter approach,
    but the bounded active-set already caps total work per tick.
    """
    try:
        with path.open("r") as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                ev_type = obj.get("type")
                if ev_type in _CODEX_TERMINAL_EVENTS:
                    return ev_type
                payload = obj.get("payload")
                if isinstance(payload, dict):
                    p_type = payload.get("type")
                    if p_type in _CODEX_TERMINAL_EVENTS:
                        return p_type
    except OSError:
        return None
    return None


# ---------------------------------------------------------------------------
# Session registry — JSONL append-only, two row shapes.
# ---------------------------------------------------------------------------


def session_registry_path(client_id: str | None) -> Path:
    """Where the session registry lives for a given attribution.

    * client_id == None → ``~/.local/share/gofreddy/sessions.jsonl``
    * client_id == "acme" → ``clients/acme/audit/sessions.jsonl``

    Mirrors :func:`client_events_path` layout intentionally so the IDOR
    guard (Unit 6) resolves the same way.
    """
    if client_id is None:
        return Path.home() / ".local" / "share" / "gofreddy" / "sessions.jsonl"
    return Path("clients") / client_id / "audit" / "sessions.jsonl"


@dataclass
class RegistryRow:
    """In-memory view of a session's latest-row state.

    Built by rebuilding from sessions.jsonl on startup (latest-row-per-
    session-id rule) and updated as the tailer emits new rows.
    """

    session_id: str
    client_id: str | None
    source: str  # "cc" | "codex"
    file_path: str
    started_at: str
    hook_emitted: bool = False
    ended_at: str | None = None
    end_reason: str | None = None

    # Tick-loop bookkeeping (NOT persisted):
    last_seen_mtime: float = 0.0
    last_seen_size: int = 0
    stable_ticks: int = 0  # consecutive ticks with no growth


def _append_registry_row(registry_path: Path, row: dict[str, Any]) -> None:
    """Append a single JSON row to the registry, creating parent dirs."""
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with registry_path.open("a") as handle:
        handle.write(json.dumps(row) + "\n")


def rebuild_registry_from_disk(
    registry_paths: list[Path],
) -> dict[str, RegistryRow]:
    """Walk every sessions.jsonl and reconstruct the in-memory registry.

    Latest-row-per-session-id wins. Start rows define
    ``(client_id, source, file_path, started_at)``; end rows overlay
    ``ended_at`` + ``end_reason``.

    Returns ``{session_id: RegistryRow}``.
    """
    state: dict[str, RegistryRow] = {}
    for registry_path in registry_paths:
        if not registry_path.is_file():
            continue
        with registry_path.open("r") as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                sid = obj.get("session_id")
                if not isinstance(sid, str) or not sid:
                    continue
                if "started_at" in obj:
                    # Start row — overwrites any previous start (latest wins).
                    state[sid] = RegistryRow(
                        session_id=sid,
                        client_id=obj.get("client_id"),
                        source=obj.get("source", "cc"),
                        file_path=obj.get("file_path", ""),
                        started_at=obj.get("started_at", ""),
                        hook_emitted=bool(obj.get("hook_emitted", False)),
                    )
                elif "ended_at" in obj:
                    existing = state.get(sid)
                    if existing is None:
                        # Stray end row with no matching start — keep a stub.
                        state[sid] = RegistryRow(
                            session_id=sid,
                            client_id=None,
                            source="cc",
                            file_path="",
                            started_at="",
                            ended_at=obj.get("ended_at"),
                            end_reason=obj.get("reason"),
                        )
                    else:
                        existing.ended_at = obj.get("ended_at")
                        existing.end_reason = obj.get("reason")
    return state


# ---------------------------------------------------------------------------
# Dedup (R8.3) — scan the per-client wide log for an existing session_start.
# ---------------------------------------------------------------------------


def is_session_already_started(
    *, log_path: Path, session_id: str
) -> bool:
    """True if the wide log already contains ``kind="session_start"`` with
    matching ``metadata.session_id``.

    Reads the current file only — rotated segments are out of scope (a
    rotated session is by definition already long-since started). Uses
    streaming + early-return for cheap negative cases.
    """
    if not log_path.is_file():
        return False
    try:
        with log_path.open("r") as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if obj.get("kind") != "session_start":
                    continue
                metadata = obj.get("metadata") or {}
                if metadata.get("session_id") == session_id:
                    return True
    except OSError:
        return False
    return False


# ---------------------------------------------------------------------------
# Path canonicalization gate — drop anything that resolves outside the roots.
# ---------------------------------------------------------------------------


def canonicalize_under_roots(path: Path) -> Path | None:
    """Resolve ``path`` strictly and assert it lives under CC_ROOT or
    CODEX_ROOT. Returns the resolved Path on success, None on failure.

    Failure mode emits ``kind="alert"`` operator-internal with
    ``metadata.reason="path_outside_roots"``. The tailer drops the
    offending JSONL — no registry row written, no session_start emitted.
    """
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError):
        return None

    cc = cc_root()
    codex = codex_root()
    try:
        cc_resolved = cc.resolve(strict=False)
        codex_resolved = codex.resolve(strict=False)
    except (OSError, RuntimeError):
        return None

    if resolved.is_relative_to(cc_resolved) or resolved.is_relative_to(codex_resolved):
        return resolved

    log_event(
        "alert",
        path=client_events_path(None),
        metadata={
            "reason": "path_outside_roots",
            "path": str(path),
            "resolved": str(resolved),
        },
    )
    return None


# ---------------------------------------------------------------------------
# Glob helpers.
# ---------------------------------------------------------------------------


def iter_cc_jsonl_files() -> list[Path]:
    """All CC session JSONLs under ``~/.claude/projects``."""
    root = cc_root()
    if not root.is_dir():
        return []
    return list(root.glob("*/*.jsonl"))


def iter_codex_jsonl_files() -> list[Path]:
    """All Codex rollout JSONLs under ``~/.codex/sessions`` (recursive)."""
    root = codex_root()
    if not root.is_dir():
        return []
    return list(root.rglob("rollout-*.jsonl"))


# ---------------------------------------------------------------------------
# SessionRegistry — the long-lived in-memory state plus the per-tick logic.
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class SessionRegistry:
    """In-memory session state + tick logic.

    Construction is cheap (no I/O); call :meth:`bootstrap` to rebuild from
    disk before the first tick.
    """

    is_slug_valid: SlugValidator
    active_window_s: float = _DEFAULT_ACTIVE_WINDOW_S
    idle_timeout_s: float = _DEFAULT_IDLE_TIMEOUT_S
    # Time source — overridable in tests.
    now: Callable[[], float] = field(default=lambda: __import__("time").time())

    # Populated by bootstrap() / each tick.
    rows: dict[str, RegistryRow] = field(default_factory=dict)
    # session_ids registered-only (older than active_window) — skip on subsequent
    # ticks so we never re-glob the whole filesystem cost on them.
    _registered_only: set[str] = field(default_factory=set)

    # --- Bootstrap ---------------------------------------------------------

    def bootstrap(self) -> None:
        """Reconcile in-memory state with on-disk registries.

        Walks every ``clients/*/audit/sessions.jsonl`` plus the operator-
        internal registry to recover the latest-row-per-session-id state.
        Idempotent.
        """
        registry_paths = self._discover_registry_paths()
        self.rows = rebuild_registry_from_disk(registry_paths)

    def _discover_registry_paths(self) -> list[Path]:
        """Find every sessions.jsonl that exists at bootstrap time."""
        paths: list[Path] = [operator_internal_path().parent / "sessions.jsonl"]
        clients_dir = Path("clients")
        if clients_dir.is_dir():
            for client_dir in clients_dir.iterdir():
                if not client_dir.is_dir():
                    continue
                candidate = client_dir / "audit" / "sessions.jsonl"
                if candidate.is_file():
                    paths.append(candidate)
        return paths

    # --- Tick logic --------------------------------------------------------

    async def tick(self) -> None:
        """One scan of CC + Codex roots. Emits session_start/end as needed."""
        now = self.now()
        cc_files = iter_cc_jsonl_files()
        codex_files = iter_codex_jsonl_files()

        for path in cc_files:
            try:
                await self._handle_cc_file(path, now=now)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 — error-path test scenario
                self._emit_tick_alert(path, source="cc")

        for path in codex_files:
            try:
                await self._handle_codex_file(path, now=now)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                self._emit_tick_alert(path, source="codex")

        # Idle-timeout sweep over active rows.
        self._sweep_idle_timeouts(now=now)

    async def _handle_cc_file(self, path: Path, *, now: float) -> None:
        sid = session_id_from_cc_path(path)
        if not sid:
            return
        if sid in self._registered_only:
            return

        try:
            stat = path.stat()
        except OSError:
            return

        is_active = (now - stat.st_mtime) <= self.active_window_s

        if sid in self.rows:
            # Known session — update activity bookkeeping.
            self._update_activity(self.rows[sid], stat.st_mtime, stat.st_size)
            return

        # New session — sanity-parse + canonicalize before any emission.
        sanity = sanity_parse_jsonl(path, source="cc")
        if not sanity.is_session:
            return  # mid-write or not a real session JSONL; retry next tick.

        canonical = canonicalize_under_roots(path)
        if canonical is None:
            return  # path escaped roots; alert already emitted.

        # Decode the cwd from the parent dir name.
        cwd = decode_cc_dirname(path.parent.name)
        if not cwd.exists():
            # Decoder failed because the actual cwd contains a `-`. We
            # cannot recover a true path — treat as operator-internal with
            # no cwd-based attribution. We can still register the session
            # so the IDOR guard works.
            cwd = None  # type: ignore[assignment]

        attribution = (
            await attribute_session(cwd, is_slug_valid=self.is_slug_valid)
            if cwd is not None
            else Attribution(client_id=None, reason=None)
        )

        if not is_active:
            # Register-only: row in registry so IDOR guard resolves, but
            # NO wide-log session_start. Mark as registered-only so the
            # next tick skips re-globbing this file.
            self._register_only(
                session_id=sid,
                source="cc",
                file_path=canonical,
                attribution=attribution,
                stat=stat,
            )
            return

        await self._emit_session_start(
            session_id=sid,
            source="cc",
            file_path=canonical,
            attribution=attribution,
            stat=stat,
        )

    async def _handle_codex_file(self, path: Path, *, now: float) -> None:
        sid = session_id_from_codex_path(path)
        if not sid:
            return
        if sid in self._registered_only:
            return

        try:
            stat = path.stat()
        except OSError:
            return

        is_active = (now - stat.st_mtime) <= self.active_window_s

        if sid in self.rows:
            row = self.rows[sid]
            self._update_activity(row, stat.st_mtime, stat.st_size)
            # Codex-only mid-tail: check for task_completed/aborted.
            if row.ended_at is None:
                terminal = detect_codex_terminal_event(path)
                if terminal is not None:
                    self._emit_session_end(
                        row=row,
                        reason=terminal,
                    )
            return

        sanity = sanity_parse_jsonl(path, source="codex")
        if not sanity.is_session:
            return

        canonical = canonicalize_under_roots(path)
        if canonical is None:
            return

        cwd = sanity.codex_cwd
        attribution = (
            await attribute_session(cwd, is_slug_valid=self.is_slug_valid)
            if cwd is not None
            else Attribution(client_id=None, reason=None)
        )

        if not is_active:
            self._register_only(
                session_id=sid,
                source="codex",
                file_path=canonical,
                attribution=attribution,
                stat=stat,
            )
            return

        await self._emit_session_start(
            session_id=sid,
            source="codex",
            file_path=canonical,
            attribution=attribution,
            stat=stat,
        )

        # Brand-new session row + immediate terminal-event scan (a fast
        # codex run can complete between ticks).
        terminal = detect_codex_terminal_event(path)
        if terminal is not None:
            row = self.rows.get(sid)
            if row is not None and row.ended_at is None:
                self._emit_session_end(row=row, reason=terminal)

    # --- Emission helpers --------------------------------------------------

    async def _emit_session_start(
        self,
        *,
        session_id: str,
        source: str,
        file_path: Path,
        attribution: Attribution,
        stat: os.stat_result,
    ) -> None:
        """Write registry row + wide-log session_start (with R8.3 dedup)."""
        wide_log = client_events_path(attribution.client_id)
        already_started = is_session_already_started(
            log_path=wide_log, session_id=session_id
        )

        started_at = _now_iso()
        row = RegistryRow(
            session_id=session_id,
            client_id=attribution.client_id,
            source=source,
            file_path=str(file_path),
            started_at=started_at,
            hook_emitted=already_started,
            last_seen_mtime=stat.st_mtime,
            last_seen_size=stat.st_size,
        )
        self.rows[session_id] = row

        registry_path = session_registry_path(attribution.client_id)
        _append_registry_row(
            registry_path,
            {
                "session_id": session_id,
                "client_id": attribution.client_id,
                "source": source,
                "file_path": str(file_path),
                "started_at": started_at,
                "hook_emitted": already_started,
            },
        )

        if already_started:
            # CC hook (or any prior emitter) beat us to the punch — skip
            # the wide-log write but keep the registry row + bookkeeping.
            return

        log_event(
            "session_start",
            path=wide_log,
            client_id=attribution.client_id,
            source=source,
            session_id=session_id,
            metadata={
                "session_id": session_id,
                "source": source,
                "file_path": str(file_path),
            },
        )

    def _emit_session_end(self, *, row: RegistryRow, reason: str) -> None:
        ended_at = _now_iso()
        row.ended_at = ended_at
        row.end_reason = reason

        registry_path = session_registry_path(row.client_id)
        _append_registry_row(
            registry_path,
            {
                "session_id": row.session_id,
                "ended_at": ended_at,
                "reason": reason,
            },
        )

        wide_log = client_events_path(row.client_id)
        log_event(
            "session_end",
            path=wide_log,
            client_id=row.client_id,
            source=row.source,
            session_id=row.session_id,
            metadata={
                "session_id": row.session_id,
                "source": row.source,
                "reason": reason,
            },
        )

    def _register_only(
        self,
        *,
        session_id: str,
        source: str,
        file_path: Path,
        attribution: Attribution,
        stat: os.stat_result,
    ) -> None:
        """Historic session: registry row only, no wide-log event."""
        started_at = _now_iso()
        row = RegistryRow(
            session_id=session_id,
            client_id=attribution.client_id,
            source=source,
            file_path=str(file_path),
            started_at=started_at,
            hook_emitted=False,
            last_seen_mtime=stat.st_mtime,
            last_seen_size=stat.st_size,
        )
        self.rows[session_id] = row
        self._registered_only.add(session_id)

        registry_path = session_registry_path(attribution.client_id)
        _append_registry_row(
            registry_path,
            {
                "session_id": session_id,
                "client_id": attribution.client_id,
                "source": source,
                "file_path": str(file_path),
                "started_at": started_at,
                "hook_emitted": False,
            },
        )

    # --- Activity bookkeeping & idle-timeout sweep --------------------------

    def _update_activity(
        self, row: RegistryRow, mtime: float, size: int
    ) -> None:
        if row.ended_at is not None:
            return  # already closed; no further tracking needed.
        if size > row.last_seen_size or mtime > row.last_seen_mtime:
            row.last_seen_mtime = mtime
            row.last_seen_size = size
            row.stable_ticks = 0
        else:
            row.stable_ticks += 1

    def _sweep_idle_timeouts(self, *, now: float) -> None:
        for row in list(self.rows.values()):
            if row.ended_at is not None:
                continue
            if row.session_id in self._registered_only:
                continue
            stale_mtime = (now - row.last_seen_mtime) >= self.idle_timeout_s
            stable_long_enough = row.stable_ticks >= _IDLE_TIMEOUT_STABLE_TICKS
            if stale_mtime and stable_long_enough:
                self._emit_session_end(row=row, reason="idle_timeout")

    # --- Tick error path ---------------------------------------------------

    def _emit_tick_alert(self, path: Path, *, source: str) -> None:
        """Inner-tick error (e.g. PermissionError) → operator-internal alert."""
        log_event(
            "alert",
            path=client_events_path(None),
            metadata={
                "reason": "tailer_tick_error",
                "source": source,
                "path": str(path),
            },
        )


# ---------------------------------------------------------------------------
# The asyncio task itself — long-running, env-tunable interval, kept simple.
# ---------------------------------------------------------------------------


def _resolve_poll_interval() -> float:
    """Read ``GOFREDDY_TAILER_INTERVAL_S``, clamp to [min, max], else default."""
    raw = os.environ.get("GOFREDDY_TAILER_INTERVAL_S")
    if raw is None:
        return _DEFAULT_POLL_INTERVAL_S
    try:
        value = float(raw)
    except ValueError:
        logger.warning(
            "GOFREDDY_TAILER_INTERVAL_S=%r is not a float; using default %s",
            raw, _DEFAULT_POLL_INTERVAL_S,
        )
        return _DEFAULT_POLL_INTERVAL_S
    if value < _MIN_POLL_INTERVAL_S:
        return _MIN_POLL_INTERVAL_S
    if value > _MAX_POLL_INTERVAL_S:
        return _MAX_POLL_INTERVAL_S
    return value


async def run_tailer(
    *,
    is_slug_valid: SlugValidator,
    pool_is_ready: Callable[[], bool],
    poll_interval_s: float | None = None,
    registry: SessionRegistry | None = None,
) -> None:
    """Long-running asyncio task — wired by the FastAPI lifespan.

    ``pool_is_ready`` is checked at the top of every tick; the tick is
    a no-op while it returns False. Production wires this to
    ``lambda: app.state.db_pool is not None`` so the tailer doesn't crash
    on a race against startup.

    Catches ``Exception`` (not ``BaseException``) inside the loop so
    ``asyncio.CancelledError`` propagates and the lifespan shuts down
    cleanly.
    """
    if registry is None:
        registry = SessionRegistry(is_slug_valid=is_slug_valid)
    interval = poll_interval_s if poll_interval_s is not None else _resolve_poll_interval()
    registry.bootstrap()
    logger.info("transcript tailer started (interval=%.2fs)", interval)
    try:
        while True:
            try:
                if pool_is_ready():
                    await registry.tick()
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 — per plan: catch broadly, alert, keep going.
                logger.exception("transcript tailer tick failed")
                log_event(
                    "alert",
                    path=client_events_path(None),
                    metadata={
                        "reason": "tailer_loop_error",
                    },
                )
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("transcript tailer cancelled — shutting down")
        raise


# ---------------------------------------------------------------------------
# Production slug-validator factory — used by the lifespan.
# ---------------------------------------------------------------------------


def make_slug_validator(pool: Any) -> SlugValidator:
    """Build an :data:`SlugValidator` backed by the asyncpg pool.

    Separated from the rest of the module so tests don't need a real
    pool — they pass their own ``SlugValidator`` callable.
    """

    async def _validate(slug: str) -> bool:
        async with pool.acquire() as conn:
            return bool(
                await conn.fetchval(
                    "SELECT TRUE FROM clients WHERE slug = $1 LIMIT 1",
                    slug,
                )
            )

    return _validate
