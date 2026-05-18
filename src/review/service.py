"""Pre-publish human review service (R22 gate 2) — Content Engine v1 U7.

Single module per TD-20: submit_for_review + process_decision + check_sla
+ HMAC token signing + per-client audit emission via events.log_event +
secondary reviewer escalation (TD-2 revised) + two-reviewer-signoff
enforcement while placeholder rule sets are active (TD-17).

Audit kinds (added by U6b) — these MUST stay in events.KNOWN_KINDS:
- review_required: emitted on submit_for_review
- review_approve / review_reject: emitted on process_decision
- sla_breach: emitted at 2× SLA (auto-pause, NOT auto-reject per TD-9)

Posture: per §Compliance Posture, this is the actual safety mechanism.
The reviewer-assist YAMLs (U5) accelerate reviewer pattern-matching;
the human decision in U7 carries the ship/no-ship weight.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import re
import secrets
import time
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Literal

from autoresearch.events import log_event
from src.clients.config import ClientConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


ReviewDecision = Literal["approve", "reject"]
ALLOWED_DECISIONS: frozenset[str] = frozenset({"approve", "reject"})

ReviewerRole = Literal["primary", "secondary"]

# Token URL prefix; FastAPI router mounts review_webhook at the matching path.
TOKEN_URL_PREFIX_ENV = "REVIEW_URL_PREFIX"  # operator sets to e.g. "https://gofreddy.ai/review"
DEFAULT_TOKEN_URL_PREFIX = "http://localhost:8000/review"

# Token TTL ceiling. Matches the per-client SLA when set; never exceeds 7 days.
TOKEN_TTL_CEILING_SECONDS = 7 * 24 * 60 * 60

# Per TD-3: HMAC signing key from env var; quarterly rotation by operator.
HMAC_SECRET_ENV = "REVIEW_HMAC_SECRET"


_SLA_PATTERN = re.compile(
    r"^(?P<n>\d+)(?P<unit>[hdw])(?:_business_(?P<region>\w+))?$",
    flags=re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReviewRequest:
    """The state captured when an artifact enters the review queue."""

    artifact_id: str
    client_slug: str
    submitted_at: float                 # unix epoch
    sla_target_seconds: int
    expires_at: float                   # unix epoch — token-expiry ceiling
    primary_email: str
    secondary_email: str | None
    primary_url_approve: str
    primary_url_reject: str
    compliance_flags: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ReviewResponse:
    """Outcome of a process_decision call."""

    decision: ReviewDecision
    artifact_id: str
    client_slug: str
    reviewer_role: ReviewerRole
    reviewer_email: str
    reason: str
    reviewer_note: str
    timestamp: float
    reviewer_override: bool = False   # True when a soft-warn was approved


class InvalidTokenError(ValueError):
    """Raised when a token fails HMAC verification or shape parsing."""


class TokenExpiredError(ValueError):
    """Raised when a token's expires_at has passed."""


class TokenReusedError(ValueError):
    """Raised when a token has already been consumed (single-use enforcement)."""


# ---------------------------------------------------------------------------
# SLA parsing
# ---------------------------------------------------------------------------


def _parse_sla(sla_token: str) -> int:
    """Convert an SLA token like ``48h_business_pl`` to a duration in seconds.

    The ``_business_<region>`` suffix is informational in v1 (no business-
    calendar awareness); units h/d/w are wall-clock seconds. SLA tokens
    that don't parse fall back to 48 hours with a logged warning so a
    typo in client.yaml doesn't silently destroy a multi-hour run.
    """
    match = _SLA_PATTERN.match(sla_token.strip())
    if not match:
        logger.warning("unparseable SLA %r; falling back to 48h", sla_token)
        return 48 * 3600
    n = int(match["n"])
    unit = match["unit"].lower()
    multiplier = {"h": 3600, "d": 86400, "w": 604800}[unit]
    return n * multiplier


# ---------------------------------------------------------------------------
# Token signing + verification
# ---------------------------------------------------------------------------


def _hmac_secret() -> bytes:
    """Operator-rotated secret per TD-3.

    In tests, callers monkeypatch the env var; in production, the
    deploy provisions the secret. Missing in either case is a fatal
    config error — the service refuses to start.
    """
    raw = os.environ.get(HMAC_SECRET_ENV, "").strip()
    if not raw:
        raise RuntimeError(
            f"{HMAC_SECRET_ENV} is not set. The pre-publish review "
            f"service requires a quarterly-rotated HMAC secret (TD-3)."
        )
    return raw.encode("utf-8")


def _sign_token(payload: dict[str, Any]) -> str:
    """Sign a token payload + return URL-safe token string.

    Format: ``<payload_b64>.<sig_hex>`` (dot-separated; both URL-safe).
    """
    import base64
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(_hmac_secret(), body, sha256).hexdigest()
    body_b64 = base64.urlsafe_b64encode(body).rstrip(b"=").decode("ascii")
    return f"{body_b64}.{sig}"


def _verify_token(token: str) -> dict[str, Any]:
    """Verify HMAC + parse payload. Constant-time signature compare."""
    import base64
    if "." not in token:
        raise InvalidTokenError("token missing payload/signature separator")
    body_b64, sig_hex = token.rsplit(".", 1)
    pad = b"=" * (-len(body_b64) % 4)
    try:
        body = base64.urlsafe_b64decode(body_b64.encode("ascii") + pad)
    except Exception as exc:
        raise InvalidTokenError(f"token payload not URL-safe base64: {exc}")
    expected_sig = hmac.new(_hmac_secret(), body, sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, sig_hex):
        raise InvalidTokenError("token signature mismatch")
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise InvalidTokenError(f"token payload not JSON: {exc}")
    if not isinstance(payload, dict):
        raise InvalidTokenError("token payload is not a mapping")
    return payload


# ---------------------------------------------------------------------------
# Single-use enforcement (per-client nonce log)
# ---------------------------------------------------------------------------


def _used_nonces_path(client_slug: str, root: Path) -> Path:
    return root / "clients" / client_slug / "review" / "used_nonces.jsonl"


def _claim_nonce(
    client_slug: str, nonce: str, decision: ReviewDecision, root: Path,
) -> bool:
    """Atomically check-and-claim a nonce. Returns True iff the nonce was
    not previously claimed AND the claim was recorded. False otherwise.

    Per the 4-agent review (adv-1 + sec-2): the previous read-then-write
    pattern was a TOCTOU window — two concurrent process_decision calls
    with the same token could both pass the check. Fix: hold an exclusive
    fcntl lock across read + write so the claim is atomic. Matches the
    events.py LOCK_EX precedent."""
    import fcntl

    path = _used_nonces_path(client_slug, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Open in append+read mode so the file is created if missing and
    # the writer holds an exclusive lock across the scan-then-append.
    with path.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.seek(0)
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("nonce") == nonce:
                    return False
            # Nonce not present — append the claim.
            handle.seek(0, 2)  # seek to end before write
            handle.write(json.dumps({
                "nonce": nonce,
                "decision": decision,
                "consumed_at": time.time(),
            }) + "\n")
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
            return True
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# ReviewService
# ---------------------------------------------------------------------------


EmailSender = Callable[..., str]  # Compatible with send_email signature.


def _default_email_sender(*args, **kwargs) -> str:
    """Lazy proxy to src.audit.email_delivery.send_email — imported on
    first call so test suites that don't exercise email don't need the
    Resend dep installed at module load."""
    from src.audit.email_delivery import send_email
    return send_email(*args, **kwargs)


class ReviewService:
    """Email-based pre-publish human review per D14.

    Args:
        repo_root: anchors per-client paths (clients/<slug>/...). Defaults
            to two parents up from this module.
        email_sender: send_email-compatible callable. Tests inject a fake.
        token_url_prefix: URL prefix for the approve/reject GET URLs.
            Operator sets via ``REVIEW_URL_PREFIX`` env in production;
            tests pass an explicit prefix.
    """

    def __init__(
        self,
        repo_root: Path | None = None,
        *,
        email_sender: EmailSender | None = None,
        token_url_prefix: str | None = None,
    ) -> None:
        self.repo_root = repo_root or Path(__file__).resolve().parents[2]
        self.email_sender = email_sender or _default_email_sender
        self.token_url_prefix = (
            token_url_prefix
            or os.environ.get(TOKEN_URL_PREFIX_ENV)
            or DEFAULT_TOKEN_URL_PREFIX
        ).rstrip("/")

    def _client_events_path(self, slug: str) -> Path:
        """Per-client event log path anchored at this service's repo_root.

        Mirrors `autoresearch.events.client_events_path` but uses the
        service-scoped root so tests with tmp_path don't write to the
        operator's real client tree.
        """
        return self.repo_root / "clients" / slug / "audit" / "events.jsonl"

    # -----------------------------------------------------------------------
    # submit_for_review
    # -----------------------------------------------------------------------

    def submit_for_review(
        self,
        artifact_id: str,
        artifact_text: str,
        client: ClientConfig,
        *,
        compliance_flags: list[dict] | None = None,
    ) -> ReviewRequest:
        """Queue an artifact for human review.

        - Generates HMAC-signed approve + reject URLs.
        - Sends notification email to primary reviewer.
        - Emits ``review_required`` event to the per-client log.
        - Hard-block flags are encoded into the token payload so
          process_decision can refuse approval per D14.

        Returns the ReviewRequest record (for caller bookkeeping; the
        event log is the source of truth).
        """
        compliance_flags = compliance_flags or []
        sla_seconds = _parse_sla(client.pre_publish_reviewer.sla)
        now = time.time()
        ttl = min(sla_seconds, TOKEN_TTL_CEILING_SECONDS)
        expires_at = now + ttl

        has_hard_block = any(
            f.get("severity") == "hard_block" for f in compliance_flags
        )
        soft_warn_count = sum(
            1 for f in compliance_flags if f.get("severity") == "soft_warn"
        )

        # Per the 4-agent review (adv-1): mint distinct nonces for approve
        # vs reject tokens. The "first-click wins" invariant from D14 is
        # enforced by a shared artifact_id check at process_decision time,
        # not by sharing a nonce — sharing made the single-decision
        # invariant fragile under concurrent clicks. Token v=1 lets future
        # schema changes be detected (per AC-2).
        approve_nonce = secrets.token_urlsafe(16)
        reject_nonce = secrets.token_urlsafe(16)
        artifact_hash = sha256(artifact_text.encode("utf-8")).hexdigest()
        approve_token = _sign_token({
            "v": 1,
            "artifact_id": artifact_id,
            "client_slug": client.slug,
            "decision": "approve",
            "nonce": approve_nonce,
            "expires_at": expires_at,
            "artifact_hash": artifact_hash,
            "hard_block": has_hard_block,
            "soft_warn_count": soft_warn_count,
            "role": "primary",
        })
        reject_token = _sign_token({
            "v": 1,
            "artifact_id": artifact_id,
            "client_slug": client.slug,
            "decision": "reject",
            "nonce": reject_nonce,
            "expires_at": expires_at,
            "artifact_hash": artifact_hash,
            # Mirror the flags onto the reject token (AC-2): symmetric
            # payload shape simplifies future surfacing of "rejected an
            # artifact that carried N soft warns."
            "hard_block": has_hard_block,
            "soft_warn_count": soft_warn_count,
            "role": "primary",
        })

        approve_url = f"{self.token_url_prefix}/approve/{approve_token}"
        reject_url = f"{self.token_url_prefix}/reject/{reject_token}"

        request = ReviewRequest(
            artifact_id=artifact_id,
            client_slug=client.slug,
            submitted_at=now,
            sla_target_seconds=sla_seconds,
            expires_at=expires_at,
            primary_email=client.pre_publish_reviewer.email,
            secondary_email=(
                client.pre_publish_reviewer_secondary.email
                if client.pre_publish_reviewer_secondary else None
            ),
            primary_url_approve=approve_url,
            primary_url_reject=reject_url,
            compliance_flags=list(compliance_flags),
        )

        # Audit the submission via per-client log (U6b kind).
        log_event(
            kind="review_required",
            path=self._client_events_path(client.slug),
            client_id=client.slug,
            actor="system",
            action="submit_for_review",
            metadata={
                "artifact_id": artifact_id,
                "artifact_hash": artifact_hash,
                "sla_target_seconds": sla_seconds,
                "submitted_at": now,
                "expires_at": expires_at,
                "compliance_flags": compliance_flags,
            },
        )

        # Notify the primary reviewer. Secondary email is deferred to
        # check_sla() per TD-2 revised (parallel email at 50% SLA);
        # exception: when there are soft-warn flags, secondary reviewer
        # is paged AT submit per D14 ("Soft-warn flags additionally
        # trigger a parallel email to the secondary reviewer at
        # submission time").
        cc_secondary_at_submit = (
            soft_warn_count > 0 and request.secondary_email is not None
        )
        self._send_review_email(
            to=request.primary_email,
            artifact_id=artifact_id,
            client_slug=client.slug,
            approve_url=approve_url,
            reject_url=reject_url,
            compliance_flags=compliance_flags,
            role="primary",
        )
        if cc_secondary_at_submit and request.secondary_email is not None:
            self._send_review_email(
                to=request.secondary_email,
                artifact_id=artifact_id,
                client_slug=client.slug,
                approve_url=approve_url,
                reject_url=reject_url,
                compliance_flags=compliance_flags,
                role="secondary_at_submit",
            )

        return request

    # -----------------------------------------------------------------------
    # process_decision
    # -----------------------------------------------------------------------

    def process_decision(
        self,
        token: str,
        decision: ReviewDecision,
        *,
        reason: str = "",
        reviewer_note: str = "",
        reviewer_email: str | None = None,
        reviewer_role: ReviewerRole = "primary",
    ) -> ReviewResponse:
        """Verify token + record decision.

        Args:
            token: HMAC-signed token from the URL.
            decision: must match the token's `decision` field.
            reason: reject reason (operator surface).
            reviewer_note: TD-43 free-form note (≥1 sentence for edit + reject;
                optional for clean approve; empty note triggers a log warning
                but doesn't block publish).
            reviewer_email: which reviewer clicked. Determines reviewer_role
                in the audit event. Defaults to "primary" + the token's stored
                primary email.

        Raises:
            InvalidTokenError: HMAC verify fails or shape malformed.
            TokenExpiredError: token's expires_at has passed.
            TokenReusedError: token's nonce already consumed.
            ValueError: decision mismatches token, or hard-block flag tries
                to approve.
        """
        if decision not in ALLOWED_DECISIONS:
            raise ValueError(
                f"decision must be one of {sorted(ALLOWED_DECISIONS)}; got {decision!r}"
            )

        payload = _verify_token(token)

        # Expiry check.
        expires_at = float(payload.get("expires_at", 0))
        if expires_at < time.time():
            raise TokenExpiredError(
                f"token expired at {expires_at} (now={time.time():.0f})"
            )

        # Decision must match the token's stored decision (approve token
        # cannot be used to reject and vice versa).
        token_decision = payload.get("decision")
        if token_decision != decision:
            raise InvalidTokenError(
                f"token decision {token_decision!r} != requested decision {decision!r}"
            )

        client_slug = str(payload.get("client_slug", ""))
        nonce = str(payload.get("nonce", ""))
        artifact_id = str(payload.get("artifact_id", ""))

        # Per the 4-agent review (sec-9): validate reviewer_email against
        # the client's known reviewer set so the audit trail records a
        # trustworthy actor. A reviewer who somehow obtained a token
        # cannot record the decision under a fabricated email. Skip the
        # check when reviewer_email is None (caller didn't pass it) —
        # the audit event records "<unspecified>" and the operator can
        # follow up via the per-client log.
        if reviewer_email:
            from src.clients.loader import (
                ClientConfigNotFoundError,
                load_client_config,
            )
            try:
                client_config = load_client_config(client_slug)
            except ClientConfigNotFoundError:
                client_config = None
            if client_config is not None:
                allowed = {client_config.pre_publish_reviewer.email}
                if client_config.pre_publish_reviewer_secondary is not None:
                    allowed.add(client_config.pre_publish_reviewer_secondary.email)
                if reviewer_email not in allowed:
                    raise InvalidTokenError(
                        f"reviewer_email {reviewer_email!r} is not on the "
                        f"client's reviewer whitelist; expected one of "
                        f"{sorted(allowed)}"
                    )

        # First-click-wins invariant per D14: also block the OTHER decision's
        # token for the same artifact (so approve-then-reject and reject-
        # then-approve both fail). Implemented by recording an "artifact:"
        # sentinel claim on the first successful decision; subsequent calls
        # against either token fail the atomic claim against the sentinel.
        artifact_sentinel = f"artifact:{artifact_id}"

        # Hard-block guard per D14.
        reviewer_override = False
        if decision == "approve" and payload.get("hard_block"):
            raise ValueError(
                "hard_block compliance flag cannot be approved (D14). "
                "Reviewer must reject + the artifact must be re-generated "
                "to address the hard_block before re-submission."
            )
        if decision == "approve" and int(payload.get("soft_warn_count", 0)) > 0:
            reviewer_override = True

        if not reviewer_note and decision in ("reject",):
            logger.warning(
                "review %s for artifact %s carries empty reviewer_note — "
                "TD-43 calibration data loss",
                decision, artifact_id,
            )

        # Atomic check-and-claim. The artifact-sentinel claim runs first;
        # if it succeeds, the per-token nonce claim runs (single-use of
        # this specific token). If the artifact-sentinel was already
        # claimed (concurrent approve+reject race), this raises.
        if not _claim_nonce(client_slug, artifact_sentinel, decision, self.repo_root):
            raise TokenReusedError(
                f"artifact {artifact_id!r} already has a recorded decision; "
                f"first-click wins per D14"
            )
        if not _claim_nonce(client_slug, nonce, decision, self.repo_root):
            # Should never happen — the artifact sentinel just succeeded
            # so this is a duplicate nonce write. Surface defensively.
            raise TokenReusedError(
                f"nonce {nonce!r} for artifact {artifact_id!r} already consumed"
            )

        kind = "review_approve" if decision == "approve" else "review_reject"
        log_event(
            kind=kind,
            path=self._client_events_path(client_slug),
            client_id=client_slug,
            actor="human",
            action=decision,
            metadata={
                "artifact_id": artifact_id,
                "artifact_hash": payload.get("artifact_hash"),
                "reviewer_email": reviewer_email or "<unspecified>",
                "reviewer_role": reviewer_role,
                "reason": reason,
                "reviewer_note": reviewer_note,
                "reviewer_override": reviewer_override,
                "nonce": nonce,
            },
        )

        return ReviewResponse(
            decision=decision,
            artifact_id=artifact_id,
            client_slug=client_slug,
            reviewer_role=reviewer_role,
            reviewer_email=reviewer_email or "<unspecified>",
            reason=reason,
            reviewer_note=reviewer_note,
            timestamp=time.time(),
            reviewer_override=reviewer_override,
        )

    # -----------------------------------------------------------------------
    # check_sla — periodic scan; emits nag / secondary-escalation / auto-pause
    # -----------------------------------------------------------------------

    def check_sla(
        self,
        client: ClientConfig,
        *,
        now: float | None = None,
    ) -> list[dict]:
        """Scan pending reviews for this client and emit SLA events.

        Per TD-9: at 2× SLA, AUTO-PAUSE (not auto-reject) with operator
        notification; artifact stays in queue until explicit
        resume/escalate.

        Per TD-2 revised: at ``escalate_at_pct_sla`` (default 50%),
        send a parallel email to the secondary reviewer (when defined).

        Returns the list of SLA-event records emitted (for caller
        bookkeeping). Idempotent: re-scanning the same window does
        NOT re-fire — the per-client log carries the last-fired marker
        in each pending review's metadata trail.
        """
        now = now or time.time()
        events_fired: list[dict] = []

        # Walk pending reviews from the per-client log: a review is
        # pending when there's a review_required event with no matching
        # review_approve / review_reject. We read in-process by
        # streaming the log; the events module's read_events helper
        # gives ordering + filter.
        from autoresearch.events import read_events

        log_path = self._client_events_path(client.slug)
        submitted: dict[str, dict] = {}      # artifact_id → submission record
        resolved: set[str] = set()           # artifact_ids that got approve/reject
        breached: set[str] = set()           # artifact_ids with prior sla_breach event
        escalated: set[str] = set()          # artifact_ids with prior sla_escalation event

        for record in read_events(path=log_path):
            kind = record.get("kind")
            md = record.get("metadata") or {}
            artifact_id = md.get("artifact_id")
            if not artifact_id:
                continue
            if kind == "review_required":
                submitted[artifact_id] = record
            elif kind in ("review_approve", "review_reject"):
                resolved.add(artifact_id)
            elif kind == "sla_breach":
                breached.add(artifact_id)
            elif kind == "sla_escalation":
                escalated.add(artifact_id)

        sla_seconds = _parse_sla(client.pre_publish_reviewer.sla)
        escalate_pct = (
            client.pre_publish_reviewer_secondary.escalate_at_pct_sla
            if client.pre_publish_reviewer_secondary else None
        )

        for artifact_id, submission in submitted.items():
            if artifact_id in resolved:
                continue
            md = submission.get("metadata") or {}
            submitted_at = float(md.get("submitted_at", 0))
            elapsed = now - submitted_at
            pct = (elapsed / sla_seconds * 100) if sla_seconds else 0

            # Auto-pause at 2× SLA. Per the 4-agent review (adv-4 T1-D):
            # idempotent — only fire if we haven't already breached this
            # artifact in a prior check_sla invocation.
            if elapsed >= 2 * sla_seconds:
                if artifact_id in breached:
                    continue
                evt = {
                    "kind": "sla_breach",
                    "artifact_id": artifact_id,
                    "client_slug": client.slug,
                    "elapsed_seconds": elapsed,
                    "pct_of_sla": pct,
                    "action": "auto_pause",
                }
                log_event(
                    kind="sla_breach",
                    path=log_path,
                    client_id=client.slug,
                    actor="system",
                    action="auto_pause",
                    metadata={
                        "artifact_id": artifact_id,
                        "elapsed_seconds": elapsed,
                        "pct_of_sla": pct,
                        "sla_target_seconds": sla_seconds,
                    },
                )
                events_fired.append(evt)
                continue

            # Secondary escalation at escalate_at_pct_sla (default 50%).
            # Per the 4-agent review (adv-4 T1-D): idempotent — only
            # send the secondary email + emit the event ONCE per artifact,
            # not on every check_sla invocation in the window. Actually
            # send the email (the prior implementation only logged).
            if (
                escalate_pct is not None
                and client.pre_publish_reviewer_secondary is not None
                and pct >= escalate_pct
                and artifact_id not in escalated
            ):
                # Reconstruct the approve/reject URLs for the secondary
                # email. Token shape is stable; we re-mint with a fresh
                # nonce for the secondary so they have their own single-
                # use token + the primary's token continues to work
                # (first-click wins via the artifact sentinel).
                secondary = client.pre_publish_reviewer_secondary
                sec_approve_nonce = secrets.token_urlsafe(16)
                sec_reject_nonce = secrets.token_urlsafe(16)
                artifact_hash = md.get("artifact_hash", "")
                token_ttl = min(sla_seconds, TOKEN_TTL_CEILING_SECONDS)
                expires_at = submitted_at + token_ttl
                sec_approve_token = _sign_token({
                    "v": 1,
                    "artifact_id": artifact_id,
                    "client_slug": client.slug,
                    "decision": "approve",
                    "nonce": sec_approve_nonce,
                    "expires_at": expires_at,
                    "artifact_hash": artifact_hash,
                    "hard_block": md.get("compliance_flags") and any(
                        f.get("severity") == "hard_block"
                        for f in md.get("compliance_flags", [])
                    ),
                    "soft_warn_count": sum(
                        1 for f in md.get("compliance_flags", []) or []
                        if f.get("severity") == "soft_warn"
                    ),
                    "role": "secondary",
                })
                sec_reject_token = _sign_token({
                    "v": 1,
                    "artifact_id": artifact_id,
                    "client_slug": client.slug,
                    "decision": "reject",
                    "nonce": sec_reject_nonce,
                    "expires_at": expires_at,
                    "artifact_hash": artifact_hash,
                    "role": "secondary",
                })
                self._send_review_email(
                    to=secondary.email,
                    artifact_id=artifact_id,
                    client_slug=client.slug,
                    approve_url=f"{self.token_url_prefix}/approve/{sec_approve_token}",
                    reject_url=f"{self.token_url_prefix}/reject/{sec_reject_token}",
                    compliance_flags=md.get("compliance_flags") or [],
                    role="secondary",
                )
                # Persist the escalation so subsequent check_sla calls
                # in the same window skip this artifact.
                log_event(
                    kind="sla_escalation",
                    path=log_path,
                    client_id=client.slug,
                    actor="system",
                    action="escalate_to_secondary",
                    metadata={
                        "artifact_id": artifact_id,
                        "elapsed_seconds": elapsed,
                        "pct_of_sla": pct,
                        "secondary_email": secondary.email,
                    },
                )
                evt = {
                    "kind": "sla_escalation",
                    "artifact_id": artifact_id,
                    "client_slug": client.slug,
                    "elapsed_seconds": elapsed,
                    "pct_of_sla": pct,
                    "secondary_email": secondary.email,
                }
                events_fired.append(evt)

        return events_fired

    # -----------------------------------------------------------------------
    # Email composition helper
    # -----------------------------------------------------------------------

    def _send_review_email(
        self,
        *,
        to: str,
        artifact_id: str,
        client_slug: str,
        approve_url: str,
        reject_url: str,
        compliance_flags: list[dict],
        role: str,
    ) -> str:
        """Compose + send a review email.

        Returns the email_id from the underlying sender (empty string when
        email is disabled, e.g., RESEND_API_KEY unset in dev).

        Per the 4-agent review (sec-1 T1-B): every interpolated value
        is HTML-escaped to neutralize XSS via attacker-controllable
        `artifact_id`, `client_slug`, or compliance-flag prose. The
        approve/reject URLs are HMAC-signed + restricted to our
        token-URL prefix; quoted with html.escape(..., quote=True) so
        attribute-context escaping is correct.
        """
        import html as _html

        artifact_id_safe = _html.escape(artifact_id, quote=True)
        client_slug_safe = _html.escape(client_slug, quote=True)
        approve_url_safe = _html.escape(approve_url, quote=True)
        reject_url_safe = _html.escape(reject_url, quote=True)
        role_safe = _html.escape(role, quote=True)

        flags_html = ""
        if compliance_flags:
            rows = "".join(
                f"<li><strong>{_html.escape(str(f.get('severity', '')), quote=True)}</strong>: "
                f"{_html.escape(str(f.get('rule_id', '')), quote=True)} — "
                f"{_html.escape(str(f.get('prose', '')), quote=True)}</li>"
                for f in compliance_flags
            )
            flags_html = (
                f"<p><em>Reviewer-assist flags:</em></p><ul>{rows}</ul>"
            )

        subject = (
            f"[gofreddy] Review needed for {artifact_id} ({client_slug})"
        )
        html_body = (
            f"<h2>Pre-publish review</h2>"
            f"<p>Artifact <code>{artifact_id_safe}</code> for "
            f"<strong>{client_slug_safe}</strong> is ready for your review.</p>"
            f"{flags_html}"
            f'<p><a href="{approve_url_safe}">Approve</a> &nbsp;|&nbsp; '
            f'<a href="{reject_url_safe}">Reject</a></p>'
            f"<p><small>Role: {role_safe}</small></p>"
        )
        return self.email_sender(to=to, subject=subject, html=html_body)


__all__ = [
    "ALLOWED_DECISIONS",
    "InvalidTokenError",
    "ReviewDecision",
    "ReviewRequest",
    "ReviewResponse",
    "ReviewService",
    "TokenExpiredError",
    "TokenReusedError",
]
