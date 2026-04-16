"""Tests for newsletter service."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from pydantic import SecretStr

from src.newsletter.config import NewsletterSettings
from src.newsletter.service import NewsletterService


@pytest.fixture
def newsletter_settings():
    return NewsletterSettings(
        resend_api_key=SecretStr("test_key"),
        default_from="test@example.com",
        webhook_signing_secret=SecretStr("whsec_test"),
        confirmation_url_base="https://test.com/confirm",
        confirmation_token_ttl_hours=48,
    )


@pytest.fixture
def newsletter_repo():
    repo = AsyncMock()
    repo.get_recent_subscribe.return_value = None
    repo.record_consent.return_value = MagicMock(
        id=uuid4(), email="user@test.com", action="subscribe",
        ip_address=None, user_agent=None, consent_token="test_token",
        confirmed_at=None, created_at=datetime.now(timezone.utc),
    )
    return repo


@pytest.mark.mock_required
class TestNewsletterSubscribe:
    @pytest.mark.asyncio
    async def test_subscribe_records_consent_and_sends_email(
        self, newsletter_settings, newsletter_repo,
    ):
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        with patch("src.newsletter.service.resend") as mock_resend:
            mock_resend.Emails.send.return_value = {"id": "email_123"}
            result = await service.subscribe("user@test.com")
            assert result["status"] == "confirmation_sent"
            assert result["email"] == "user@test.com"
            newsletter_repo.record_consent.assert_called_once()
            mock_resend.Emails.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_rate_limits_duplicate(
        self, newsletter_settings, newsletter_repo,
    ):
        newsletter_repo.get_recent_subscribe.return_value = MagicMock()
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        result = await service.subscribe("user@test.com")
        assert result["status"] == "rate_limited"
        newsletter_repo.record_consent.assert_not_called()

    @pytest.mark.asyncio
    async def test_subscribe_returns_error_on_send_failure(
        self, newsletter_settings, newsletter_repo,
    ):
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        with patch("src.newsletter.service.resend") as mock_resend:
            mock_resend.Emails.send.side_effect = RuntimeError("API down")
            result = await service.subscribe("user@test.com")
            assert result["status"] == "error"


@pytest.mark.mock_required
class TestNewsletterConfirm:
    @pytest.mark.asyncio
    async def test_confirm_success(self, newsletter_settings, newsletter_repo):
        # Mock get_consent_by_token to return a valid, recent entry
        newsletter_repo.get_consent_by_token.return_value = MagicMock(
            email="user@test.com",
            created_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        newsletter_repo.confirm_consent.return_value = True
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        result = await service.confirm("valid_token")
        assert result["status"] == "confirmed"
        # Should record a 'confirm' consent entry
        newsletter_repo.record_consent.assert_called_once()
        call_kwargs = newsletter_repo.record_consent.call_args
        assert call_kwargs.kwargs.get("action") == "confirm" or call_kwargs[1].get("action") == "confirm"

    @pytest.mark.asyncio
    async def test_confirm_invalid_token(self, newsletter_settings, newsletter_repo):
        newsletter_repo.get_consent_by_token.return_value = None
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        result = await service.confirm("bad_token")
        assert result["status"] == "invalid"

    @pytest.mark.asyncio
    async def test_confirm_expired_token(self, newsletter_settings, newsletter_repo):
        # Token created 72 hours ago, TTL is 48 hours
        newsletter_repo.get_consent_by_token.return_value = MagicMock(
            email="user@test.com",
            created_at=datetime.now(timezone.utc) - timedelta(hours=72),
        )
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        result = await service.confirm("expired_token")
        assert result["status"] == "expired"
        newsletter_repo.confirm_consent.assert_not_called()


@pytest.mark.mock_required
class TestNewsletterUnsubscribe:
    @pytest.mark.asyncio
    async def test_unsubscribe_records_consent(
        self, newsletter_settings, newsletter_repo,
    ):
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        with patch("src.newsletter.service.resend") as mock_resend:
            mock_resend.Contacts.remove.return_value = {}
            result = await service.unsubscribe("user@test.com")
            assert result["status"] == "unsubscribed"
            newsletter_repo.record_consent.assert_called_once()


@pytest.mark.mock_required
class TestNewsletterListSends:
    @pytest.mark.asyncio
    async def test_list_sends_delegates_to_repo(
        self, newsletter_settings, newsletter_repo,
    ):
        org_id = uuid4()
        newsletter_repo.list_sends.return_value = []
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        result = await service.list_sends(org_id, limit=10, offset=5)
        assert result == []
        newsletter_repo.list_sends.assert_called_once_with(org_id, limit=10, offset=5)


@pytest.mark.mock_required
class TestNewsletterSegments:
    @pytest.mark.asyncio
    async def test_list_segments_returns_static_list(
        self, newsletter_settings, newsletter_repo,
    ):
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        segments = await service.list_segments()
        assert len(segments) == 4
        ids = [s["id"] for s in segments]
        assert "all" in ids
        assert "creators" in ids


@pytest.mark.mock_required
class TestNewsletterWebhook:
    @pytest.mark.asyncio
    async def test_webhook_skips_when_secret_not_configured(
        self, newsletter_repo,
    ):
        settings = NewsletterSettings(
            resend_api_key=SecretStr("test_key"),
            webhook_signing_secret=SecretStr(""),
        )
        service = NewsletterService(
            repository=newsletter_repo, settings=settings,
        )
        # Should return without error when secret is empty
        await service.handle_webhook(
            b'{"type": "test"}', {"svix-id": "x", "svix-timestamp": "1", "svix-signature": "v1,sig"},
        )

    @pytest.mark.asyncio
    async def test_webhook_logs_warning_on_verification_failure(
        self, newsletter_settings, newsletter_repo,
    ):
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        # Mock svix to raise WebhookVerificationError
        mock_wh_cls = MagicMock()

        class FakeVerificationError(Exception):
            pass

        mock_wh_instance = MagicMock()
        mock_wh_instance.verify.side_effect = FakeVerificationError("bad sig")
        mock_wh_cls.return_value = mock_wh_instance

        with patch.dict("sys.modules", {
            "svix": MagicMock(),
            "svix.webhooks": MagicMock(
                Webhook=mock_wh_cls,
                WebhookVerificationError=FakeVerificationError,
            ),
        }):
            # Should NOT raise — just log warning and return
            await service.handle_webhook(
                b'{"type": "test"}',
                {"svix-id": "msg_1", "svix-timestamp": "12345", "svix-signature": "v1,invalid"},
            )

    @pytest.mark.asyncio
    async def test_webhook_processes_delivered_event(
        self, newsletter_settings, newsletter_repo,
    ):
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        mock_wh_cls = MagicMock()

        class FakeVerificationError(Exception):
            pass

        mock_wh_instance = MagicMock()
        mock_wh_instance.verify.return_value = {
            "type": "email.delivered",
            "data": {"email_id": "email_123"},
        }
        mock_wh_cls.return_value = mock_wh_instance

        with patch.dict("sys.modules", {
            "svix": MagicMock(),
            "svix.webhooks": MagicMock(
                Webhook=mock_wh_cls,
                WebhookVerificationError=FakeVerificationError,
            ),
        }):
            await service.handle_webhook(
                b'{"type": "email.delivered"}',
                {"svix-id": "msg_1", "svix-timestamp": "12345", "svix-signature": "v1,valid"},
            )

    @pytest.mark.asyncio
    async def test_webhook_processes_bounced_event(
        self, newsletter_settings, newsletter_repo,
    ):
        service = NewsletterService(
            repository=newsletter_repo, settings=newsletter_settings,
        )
        mock_wh_cls = MagicMock()

        class FakeVerificationError(Exception):
            pass

        mock_wh_instance = MagicMock()
        mock_wh_instance.verify.return_value = {
            "type": "email.bounced",
            "data": {"email_id": "email_456"},
        }
        mock_wh_cls.return_value = mock_wh_instance

        with patch.dict("sys.modules", {
            "svix": MagicMock(),
            "svix.webhooks": MagicMock(
                Webhook=mock_wh_cls,
                WebhookVerificationError=FakeVerificationError,
            ),
        }):
            await service.handle_webhook(
                b'{"type": "email.bounced"}',
                {"svix-id": "msg_2", "svix-timestamp": "12345", "svix-signature": "v1,valid"},
            )
