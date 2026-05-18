"""Pre-publish review service (U7)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from autoresearch.events import read_events
from src.clients.config import (
    BrandAssetsConfig,
    ClientConfig,
    PrePublishReviewerConfig,
    PrePublishReviewerSecondaryConfig,
)
from src.review.service import (
    ALLOWED_DECISIONS,
    InvalidTokenError,
    ReviewService,
    TokenExpiredError,
    TokenReusedError,
)


HMAC_SECRET = "test-secret-rotation-2026q2"


@pytest.fixture(autouse=True)
def _hmac_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide a stable HMAC secret for every test."""
    monkeypatch.setenv("REVIEW_HMAC_SECRET", HMAC_SECRET)


def _build_client(
    *,
    slug: str = "fixture-client",
    sla: str = "48h_business_us",
    with_secondary: bool = False,
) -> ClientConfig:
    return ClientConfig.model_validate({
        "slug": slug,
        "display_name": "Fixture Client",
        "archetype": "b2b_saas",
        "voice_persona_ref": "fixture_persona",
        "reviewer_assist_checklists": ["gdpr_eu"],
        "enabled_channels": ["article_engine"],
        "pre_publish_reviewer": {
            "email": "primary@example.com",
            "display_name": "Primary Reviewer",
            "sla": sla,
        },
        "pre_publish_reviewer_secondary": (
            {
                "email": "secondary@example.com",
                "display_name": "Secondary Reviewer",
                "escalate_at_pct_sla": 50,
            } if with_secondary else None
        ),
        "weekly_publish_target": 5,
        "brand_assets": {
            "style_guide": "fixture/brand/style-guide.md",
            "logo": "fixture/brand/logo.svg",
            "palette": "fixture/brand/palette.json",
        },
    })


@pytest.fixture
def fake_sender() -> Any:
    """Capture every send_email call without touching the network."""
    sent: list[dict] = []

    def _sender(*, to: str, subject: str, html: str, **kwargs) -> str:
        sent.append({"to": to, "subject": subject, "html": html, **kwargs})
        return "fake-email-id"

    _sender.sent = sent  # type: ignore[attr-defined]
    return _sender


# ---------------------------------------------------------------------------
# submit_for_review — happy path + email + audit
# ---------------------------------------------------------------------------


def test_submit_for_review_sends_email_and_emits_audit_event(
    tmp_path: Path, fake_sender,
) -> None:
    """Per plan U7 happy path: submit → email sent + review_required event recorded."""
    client = _build_client()
    svc = ReviewService(
        repo_root=tmp_path,
        email_sender=fake_sender,
        token_url_prefix="http://test.example/review",
    )

    req = svc.submit_for_review(
        artifact_id="art-001",
        artifact_text="Some content to be reviewed.",
        client=client,
    )

    assert req.artifact_id == "art-001"
    assert req.primary_email == "primary@example.com"
    assert req.primary_url_approve.startswith("http://test.example/review/approve/")
    assert req.primary_url_reject.startswith("http://test.example/review/reject/")
    assert len(fake_sender.sent) == 1
    assert fake_sender.sent[0]["to"] == "primary@example.com"

    # Audit event landed in the per-client log
    log_path = tmp_path / "clients" / client.slug / "audit" / "events.jsonl"
    assert log_path.is_file()
    events = list(read_events(path=log_path))
    assert len(events) == 1
    assert events[0]["kind"] == "review_required"
    assert events[0]["client_id"] == client.slug


def test_submit_for_review_with_soft_warn_pages_secondary_at_submit(
    tmp_path: Path, fake_sender,
) -> None:
    """Per D14: soft-warn flags trigger parallel email to secondary at submit
    (distinct from the secondary-escalation flow which fires at 50% SLA)."""
    client = _build_client(with_secondary=True)
    svc = ReviewService(
        repo_root=tmp_path, email_sender=fake_sender,
        token_url_prefix="http://test/review",
    )
    svc.submit_for_review(
        artifact_id="art-001",
        artifact_text="x",
        client=client,
        compliance_flags=[
            {"rule_id": "soft_rule", "severity": "soft_warn", "prose": "p"},
        ],
    )
    recipients = {e["to"] for e in fake_sender.sent}
    assert recipients == {"primary@example.com", "secondary@example.com"}


def test_submit_for_review_without_secondary_does_not_send_secondary_email(
    tmp_path: Path, fake_sender,
) -> None:
    client = _build_client(with_secondary=False)
    svc = ReviewService(
        repo_root=tmp_path, email_sender=fake_sender,
        token_url_prefix="http://test/review",
    )
    svc.submit_for_review(
        artifact_id="art-001", artifact_text="x", client=client,
        compliance_flags=[
            {"rule_id": "soft_rule", "severity": "soft_warn", "prose": "p"},
        ],
    )
    assert {e["to"] for e in fake_sender.sent} == {"primary@example.com"}


# ---------------------------------------------------------------------------
# process_decision — happy paths
# ---------------------------------------------------------------------------


def test_approve_records_audit_event(tmp_path: Path, fake_sender) -> None:
    """Plan U7 happy path: reviewer clicks approve → kind="review_approve" event recorded."""
    client = _build_client()
    svc = ReviewService(
        repo_root=tmp_path, email_sender=fake_sender,
        token_url_prefix="http://test/review",
    )
    req = svc.submit_for_review("art-001", "content", client)

    # Extract the approve token from the URL
    token = req.primary_url_approve.rsplit("/", 1)[-1]
    resp = svc.process_decision(
        token, "approve",
        reviewer_email="primary@example.com",
        reviewer_note="Looks good, clean voice.",
    )
    assert resp.decision == "approve"
    assert resp.artifact_id == "art-001"

    events = list(read_events(path=tmp_path / "clients" / client.slug / "audit" / "events.jsonl"))
    kinds = [e["kind"] for e in events]
    assert kinds == ["review_required", "review_approve"]


def test_reject_with_reason_records_event(tmp_path: Path, fake_sender) -> None:
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review("art-002", "content", client)
    token = req.primary_url_reject.rsplit("/", 1)[-1]
    resp = svc.process_decision(
        token, "reject",
        reason="Voice doesn't match Dr. Maria's register.",
        reviewer_note="Para 3 reads too marketing-casual.",
    )
    assert resp.decision == "reject"
    events = list(read_events(path=tmp_path / "clients" / client.slug / "audit" / "events.jsonl"))
    reject_evt = next(e for e in events if e["kind"] == "review_reject")
    assert "Dr. Maria" in reject_evt["metadata"]["reason"]


# ---------------------------------------------------------------------------
# process_decision — token errors
# ---------------------------------------------------------------------------


def test_tampered_token_raises_invalid(tmp_path: Path, fake_sender) -> None:
    """Plan U7 error path: tampered token → signature verification fails."""
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review("art-001", "x", client)
    token = req.primary_url_approve.rsplit("/", 1)[-1]

    body_b64, sig = token.rsplit(".", 1)
    tampered = f"{body_b64}.{'0' * len(sig)}"
    with pytest.raises(InvalidTokenError):
        svc.process_decision(tampered, "approve")


def test_expired_token_raises(tmp_path: Path, fake_sender, monkeypatch) -> None:
    """Plan U7 edge case: reviewer clicks expired token → token expired."""
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")

    # Submit a request, then fast-forward time past the SLA ceiling.
    req = svc.submit_for_review("art-001", "x", client)
    token = req.primary_url_approve.rsplit("/", 1)[-1]

    # Mock time to be far in the future
    real_time = time.time
    monkeypatch.setattr(time, "time", lambda: real_time() + (48 * 3600) + 60)
    with pytest.raises(TokenExpiredError):
        svc.process_decision(token, "approve")


def test_reused_token_raises(tmp_path: Path, fake_sender) -> None:
    """Plan U7 edge case: single-use nonce enforcement."""
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review("art-001", "x", client)
    token = req.primary_url_approve.rsplit("/", 1)[-1]
    svc.process_decision(token, "approve")
    with pytest.raises(TokenReusedError):
        svc.process_decision(token, "approve")


def test_approve_then_reject_with_different_token_fails(
    tmp_path: Path, fake_sender,
) -> None:
    """Approve consumes the nonce; the matching reject URL (same nonce)
    also fails — first click wins per D14."""
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review("art-001", "x", client)
    approve_token = req.primary_url_approve.rsplit("/", 1)[-1]
    reject_token = req.primary_url_reject.rsplit("/", 1)[-1]

    svc.process_decision(approve_token, "approve")
    with pytest.raises(TokenReusedError):
        svc.process_decision(reject_token, "reject")


def test_decision_mismatch_with_token_raises(tmp_path: Path, fake_sender) -> None:
    """Using the approve token to call process_decision(... 'reject') fails."""
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review("art-001", "x", client)
    approve_token = req.primary_url_approve.rsplit("/", 1)[-1]
    with pytest.raises(InvalidTokenError):
        svc.process_decision(approve_token, "reject")


# ---------------------------------------------------------------------------
# Hard-block guard (D14)
# ---------------------------------------------------------------------------


def test_hard_block_cannot_be_approved(tmp_path: Path, fake_sender) -> None:
    """D14: hard_block compliance flags refuse approval — reviewer must
    reject + regen."""
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review(
        "art-001", "x", client,
        compliance_flags=[
            {"rule_id": "blocker", "severity": "hard_block", "prose": "Hard rule"},
        ],
    )
    token = req.primary_url_approve.rsplit("/", 1)[-1]
    with pytest.raises(ValueError) as exc:
        svc.process_decision(token, "approve")
    assert "hard_block" in str(exc.value).lower()


def test_soft_warn_approve_records_reviewer_override(
    tmp_path: Path, fake_sender,
) -> None:
    """D14: soft-warn flags MAY be approved; reviewer_override flag in event."""
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review(
        "art-001", "x", client,
        compliance_flags=[
            {"rule_id": "soft", "severity": "soft_warn", "prose": "Soft"},
        ],
    )
    token = req.primary_url_approve.rsplit("/", 1)[-1]
    resp = svc.process_decision(token, "approve", reviewer_email="primary@example.com")
    assert resp.reviewer_override is True

    events = list(read_events(path=tmp_path / "clients" / client.slug / "audit" / "events.jsonl"))
    approve_evt = next(e for e in events if e["kind"] == "review_approve")
    assert approve_evt["metadata"]["reviewer_override"] is True


# ---------------------------------------------------------------------------
# SLA check — auto-pause at 2× SLA per TD-9
# ---------------------------------------------------------------------------


def test_sla_breach_emits_auto_pause_event(tmp_path: Path, fake_sender) -> None:
    """Plan U7 integration: SLA breach at 2× → auto-pause recorded;
    artifact stays in queue (not auto-rejected)."""
    client = _build_client(sla="1h_business_us")  # short SLA so test is fast
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    svc.submit_for_review("art-001", "x", client)

    # Fast-forward 3 hours (>2× SLA)
    future = time.time() + 3 * 3600
    events = svc.check_sla(client, now=future)
    assert any(e["kind"] == "sla_breach" for e in events)

    log = list(read_events(path=tmp_path / "clients" / client.slug / "audit" / "events.jsonl"))
    breach = [e for e in log if e["kind"] == "sla_breach"]
    assert len(breach) == 1
    assert breach[0]["metadata"]["artifact_id"] == "art-001"


def test_sla_secondary_escalation_at_50pct(tmp_path: Path, fake_sender) -> None:
    """Plan U7 / TD-2 revised: at 50% SLA elapsed, secondary email is sent."""
    client = _build_client(sla="2h_business_us", with_secondary=True)
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    svc.submit_for_review("art-001", "x", client)

    # 1.5h elapsed — past the 50% escalation threshold but below 2× breach
    future = time.time() + int(1.5 * 3600)
    events = svc.check_sla(client, now=future)
    esc = [e for e in events if e.get("kind") == "sla_escalation"]
    assert len(esc) == 1
    assert esc[0]["secondary_email"] == "secondary@example.com"


def test_sla_check_is_quiet_when_review_already_resolved(
    tmp_path: Path, fake_sender,
) -> None:
    """A review that's been approved before SLA elapses should NOT fire
    breach/escalation."""
    client = _build_client(sla="1h_business_us")
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review("art-001", "x", client)
    token = req.primary_url_approve.rsplit("/", 1)[-1]
    svc.process_decision(token, "approve")

    future = time.time() + 3 * 3600  # well past 2× SLA
    events = svc.check_sla(client, now=future)
    assert events == []  # no breach/escalation — already approved


# ---------------------------------------------------------------------------
# Config — HMAC secret missing is fatal
# ---------------------------------------------------------------------------


def test_missing_hmac_secret_raises_at_signing(tmp_path, fake_sender, monkeypatch) -> None:
    """Per TD-3: missing REVIEW_HMAC_SECRET is a fatal config error,
    not a silent fallback."""
    monkeypatch.delenv("REVIEW_HMAC_SECRET", raising=False)
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    with pytest.raises(RuntimeError) as exc:
        svc.submit_for_review("art-001", "x", client)
    assert "REVIEW_HMAC_SECRET" in str(exc.value)


# ---------------------------------------------------------------------------
# Drift: ALLOWED_DECISIONS pin
# ---------------------------------------------------------------------------


def test_allowed_decisions_is_approve_or_reject_only() -> None:
    """D14: rejection is terminal (no edit-feedback loop in v1). Drift
    pin so a re-introduction of 'edit' is deliberate."""
    assert ALLOWED_DECISIONS == frozenset({"approve", "reject"})
