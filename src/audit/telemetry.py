"""Audit event log + Slack alerts.

Per LHR design doc v1: one JSONL event stream per audit at
`clients/<slug>/audit/events.jsonl` plus Slack alerts on three triggers —
cost breaker, pre-flight gate failure, audit complete.

Design decisions:

- JSONL, not a database. Append-only, crash-safe (each line is self-
  contained), easy to tail + grep + replay. Events are structured dicts
  with a required `event` tag + `ts` ISO timestamp + event-specific
  payload fields.
- No event-type enum at module level — callers pass `event=<string>` and
  we record it verbatim. Keeps the schema open while we learn which event
  types we actually emit; promote to Literal later once the set stabilizes.
- Slack notifier is a best-effort side channel. Network failures are
  logged but never raised — an alert fails-closed to the JSONL log, not
  to the audit itself.
- No dependency on the `slack-sdk` package. One httpx.post to an incoming
  webhook URL is all we need; adding a whole SDK for 5 lines of JSON is
  over-engineering.
- No cross-process locking for the JSONL file — same reasoning as
  checkpointing.py: v1 serializes audits at the worker level per LHR
  design D3. If that changes, an O_APPEND write is atomic on POSIX anyway
  for small lines; portalocker can wrap append() when we outgrow that.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_SLACK_WEBHOOK_ENV = "AUDIT_SLACK_WEBHOOK_URL"


def _utcnow_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def append(events_path: Path, event: str, **payload: Any) -> None:
    """Append one JSON line to the audit events log.

    Missing parent directories are created. `event` becomes the required
    `event` key; `ts` is stamped here so callers don't need to. Payload
    values are serialized via `default=str` so Pydantic HttpUrl / datetime
    round-trip without per-caller converters.
    """
    events_path = Path(events_path)
    events_path.parent.mkdir(parents=True, exist_ok=True)

    record = {"ts": _utcnow_iso(), "event": event, **payload}
    line = json.dumps(record, default=str, sort_keys=True) + "\n"

    # O_APPEND makes single-writer append atomic on POSIX for lines below
    # PIPE_BUF (4 KiB). Stay under that: event payloads should be small
    # metadata, not whole agent transcripts.
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(line)


def notify_slack(
    text: str,
    *,
    webhook_url: str | None = None,
    timeout_s: float = 5.0,
) -> bool:
    """Send a plain-text message to the audit Slack webhook.

    Returns True on HTTP 2xx, False on any failure (network error, non-2xx
    status, misconfigured webhook). Never raises — Slack delivery is
    best-effort and must not block the audit.

    Webhook URL resolution: explicit arg wins over the
    `AUDIT_SLACK_WEBHOOK_URL` env var. If neither is set, returns False
    without attempting the request (not a misconfiguration — expected in
    dev environments).
    """
    url = webhook_url or os.environ.get(_SLACK_WEBHOOK_ENV)
    if not url:
        return False

    try:
        with httpx.Client(timeout=timeout_s) as client:
            response = client.post(url, json={"text": text})
        if 200 <= response.status_code < 300:
            return True
        logger.warning("slack_notify_non_2xx status=%s body=%s", response.status_code, response.text[:200])
        return False
    except httpx.HTTPError as exc:
        logger.warning("slack_notify_failed error=%s", exc)
        return False


# ── Composite helpers — record + alert atomically ─────────────────────────
def record_cost_breaker(
    events_path: Path,
    *,
    client_slug: str,
    spent_usd: float,
    ceiling_usd: float,
    current_stage: str,
    webhook_url: str | None = None,
) -> None:
    """Cost breaker tripped. Always writes JSONL; best-effort Slack alert."""
    append(
        events_path,
        "cost_breaker_tripped",
        client_slug=client_slug,
        spent_usd=round(spent_usd, 4),
        ceiling_usd=ceiling_usd,
        current_stage=current_stage,
    )
    notify_slack(
        f":rotating_light: Audit cost breaker — {client_slug} at ${spent_usd:.2f} "
        f"(ceiling ${ceiling_usd:.0f}) in stage `{current_stage}`. Halted.",
        webhook_url=webhook_url,
    )


def record_preflight_gate(
    events_path: Path,
    *,
    client_slug: str,
    reason: str,
    sitemap_urls: int | None = None,
    subdomains: int | None = None,
    domain_age_days: int | None = None,
    webhook_url: str | None = None,
) -> None:
    """Adversarial pre-flight gate failure (sitemap/subdomain/WHOIS thresholds
    per plan 002). Writes JSONL; best-effort Slack alert.
    """
    append(
        events_path,
        "preflight_gate_blocked",
        client_slug=client_slug,
        reason=reason,
        sitemap_urls=sitemap_urls,
        subdomains=subdomains,
        domain_age_days=domain_age_days,
    )
    notify_slack(
        f":warning: Audit preflight blocked — {client_slug}: {reason}. "
        "JR review required before `freddy audit run --override-preflight`.",
        webhook_url=webhook_url,
    )


def record_audit_complete(
    events_path: Path,
    *,
    client_slug: str,
    total_cost_usd: float,
    duration_s: float,
    finding_count: int,
    health_score: int,
    band: str,
    webhook_url: str | None = None,
) -> None:
    """Audit finished cleanly. Writes JSONL; best-effort Slack alert."""
    append(
        events_path,
        "audit_complete",
        client_slug=client_slug,
        total_cost_usd=round(total_cost_usd, 4),
        duration_s=round(duration_s, 2),
        finding_count=finding_count,
        health_score=health_score,
        band=band,
    )
    notify_slack(
        f":white_check_mark: Audit complete — {client_slug}: "
        f"{finding_count} findings, health {health_score}/100 ({band}), "
        f"${total_cost_usd:.2f} in {duration_s:.0f}s.",
        webhook_url=webhook_url,
    )
