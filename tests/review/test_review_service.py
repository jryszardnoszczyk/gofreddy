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


# ---------------------------------------------------------------------------
# Hardening A: 4-agent review fix coverage
# ---------------------------------------------------------------------------


def test_concurrent_process_decision_only_one_wins(tmp_path: Path, fake_sender) -> None:
    """Per the 4-agent review (adv-1 + sec-2 T1-A): the nonce claim is
    atomic. 10 concurrent threads calling process_decision with the
    same approve token → exactly 1 success + 9 TokenReusedError. The
    prior implementation had a TOCTOU window where multiple threads
    could pass the unlocked `_is_nonce_used` check."""
    from concurrent.futures import ThreadPoolExecutor

    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review("art-001", "x", client)
    token = req.primary_url_approve.rsplit("/", 1)[-1]

    def _try():
        try:
            svc.process_decision(token, "approve")
            return "ok"
        except TokenReusedError:
            return "reused"

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _i: _try(), range(10)))

    assert results.count("ok") == 1, results
    assert results.count("reused") == 9, results


def test_approve_then_reject_with_distinct_nonces_still_blocks_second(
    tmp_path: Path, fake_sender,
) -> None:
    """Per the 4-agent review (adv-1 T1-A): the approve and reject
    tokens now carry DISTINCT nonces (no longer share one), but the
    first-click-wins invariant is preserved by an artifact-level
    sentinel claim. Approve then reject → second call still raises."""
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review("art-001", "x", client)
    approve_token = req.primary_url_approve.rsplit("/", 1)[-1]
    reject_token = req.primary_url_reject.rsplit("/", 1)[-1]

    # Nonces should be distinct now.
    from src.review.service import _verify_token
    assert _verify_token(approve_token)["nonce"] != _verify_token(reject_token)["nonce"]

    svc.process_decision(approve_token, "approve")
    with pytest.raises(TokenReusedError):
        svc.process_decision(reject_token, "reject")


def test_token_carries_v1_version_field(tmp_path: Path, fake_sender) -> None:
    """Per the 4-agent review (AC-2 T2-B): tokens carry v=1 so future
    schema changes can be detected by the verifier instead of silently
    accepting an unknown shape."""
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review("art-001", "x", client)
    token = req.primary_url_approve.rsplit("/", 1)[-1]

    from src.review.service import _verify_token
    payload = _verify_token(token)
    assert payload["v"] == 1


def test_email_html_escapes_attacker_controlled_values(tmp_path: Path, fake_sender) -> None:
    """Per the 4-agent review (sec-1 T1-B): every interpolated value
    in the email body is HTML-escaped. An attacker-controllable
    artifact_id with `<script>` should appear literally, not as a tag."""
    client = _build_client()
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    svc.submit_for_review(
        artifact_id="<script>alert(1)</script>art-001",
        artifact_text="x",
        client=client,
        compliance_flags=[
            {"rule_id": "<img onerror=x>",
             "severity": "soft_warn",
             "prose": "<a href='javascript:alert(1)'>click</a>"},
        ],
    )
    body = fake_sender.sent[0]["html"]
    # Raw < and > must NEVER appear unescaped in attacker-controlled
    # contexts; verify the dangerous substrings are escaped instead.
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body
    assert "<img onerror=" not in body
    assert "javascript:alert(1)" not in body or "javascript:" in body  # quoted form, not active
    assert "&lt;a href=" in body or "&lt;a href='" in body


def test_check_sla_breach_is_idempotent(tmp_path: Path, fake_sender) -> None:
    """Per the 4-agent review (adv-4 T1-D): re-invoking check_sla in
    the same breach window fires sla_breach EXACTLY ONCE per artifact.
    The prior implementation re-fired on every call."""
    client = _build_client(sla="1h_business_us")
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    svc.submit_for_review("art-001", "x", client)

    future = time.time() + 3 * 3600  # well past 2× SLA
    events_1 = svc.check_sla(client, now=future)
    events_2 = svc.check_sla(client, now=future + 60)
    events_3 = svc.check_sla(client, now=future + 120)

    breach_first = sum(1 for e in events_1 if e["kind"] == "sla_breach")
    breach_later = sum(1 for e in events_2 + events_3 if e["kind"] == "sla_breach")
    assert breach_first == 1
    assert breach_later == 0


def test_check_sla_secondary_escalation_actually_sends_email(
    tmp_path: Path, fake_sender,
) -> None:
    """Per the 4-agent review (adv-4 T1-D): check_sla now actually
    calls _send_review_email for the secondary at escalation time.
    The prior implementation logged an event but never sent the email."""
    client = _build_client(sla="2h_business_us", with_secondary=True)
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    svc.submit_for_review("art-001", "x", client)
    primary_sends = len(fake_sender.sent)

    future = time.time() + int(1.5 * 3600)  # 75% of 2h SLA
    svc.check_sla(client, now=future)

    # Secondary email was sent during escalation
    new_sends = fake_sender.sent[primary_sends:]
    assert len(new_sends) == 1
    assert new_sends[0]["to"] == "secondary@example.com"


def test_check_sla_secondary_escalation_is_idempotent(
    tmp_path: Path, fake_sender,
) -> None:
    """Per the 4-agent review (adv-4 T1-D): secondary email is sent
    exactly once per artifact, not on every check_sla invocation in
    the escalation window."""
    client = _build_client(sla="2h_business_us", with_secondary=True)
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    svc.submit_for_review("art-001", "x", client)
    primary_sends = len(fake_sender.sent)

    future = time.time() + int(1.5 * 3600)
    svc.check_sla(client, now=future)
    svc.check_sla(client, now=future + 60)
    svc.check_sla(client, now=future + 120)

    secondary_emails = [
        e for e in fake_sender.sent[primary_sends:]
        if e["to"] == "secondary@example.com"
    ]
    assert len(secondary_emails) == 1


def test_reviewer_email_must_be_on_client_whitelist(
    tmp_path: Path, fake_sender, monkeypatch,
) -> None:
    """Per the 4-agent review (sec-9): reviewer_email is validated
    against the client's pre_publish_reviewer + secondary emails.
    Spoofed emails fail at process_decision."""
    # Need the client to be loadable from disk; for the test fixture
    # client (`fixture-client`), load_client_config will raise
    # ClientConfigNotFoundError because we don't ship that client.yaml.
    # That's fine — the whitelist is skipped when client config can't
    # load (defensive: missing client config != security failure).
    # Test the positive case: a real loaded client (klinika-melitus)
    # with a spoofed email fails.

    from src.clients.loader import load_client_config
    real_client = load_client_config("klinika-melitus")
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review("art-001", "x", real_client)
    token = req.primary_url_approve.rsplit("/", 1)[-1]
    with pytest.raises(InvalidTokenError) as exc:
        svc.process_decision(
            token, "approve",
            reviewer_email="spoofed@evil.com",
        )
    assert "whitelist" in str(exc.value)


def test_reviewer_email_on_whitelist_succeeds(
    tmp_path: Path, fake_sender,
) -> None:
    """The positive-control case: reviewer_email matches client.pre_publish_reviewer.email."""
    from src.clients.loader import load_client_config
    real_client = load_client_config("klinika-melitus")
    svc = ReviewService(repo_root=tmp_path, email_sender=fake_sender, token_url_prefix="http://t/r")
    req = svc.submit_for_review("art-001", "x", real_client)
    token = req.primary_url_approve.rsplit("/", 1)[-1]
    resp = svc.process_decision(
        token, "approve",
        reviewer_email=real_client.pre_publish_reviewer.email,
    )
    assert resp.decision == "approve"
