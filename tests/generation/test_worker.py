"""Tests for GenerationWorker."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4

import pytest

from src.generation.config import GenerationSettings
from src.generation.exceptions import GenerationError
from src.generation.grok_client import (
    ClipResult,
    GrokAPIUnavailableError,
    GrokModerationBlockedError,
)
from src.generation.worker import GenerationWorker


def _make_settings(**overrides) -> GenerationSettings:
    defaults = {
        "xai_api_key": "test-key",
        "generation_enabled": True,
        "poll_interval_seconds": 0.01,
        "poll_timeout_seconds": 1.0,
        "max_generation_deadline_seconds": 60,
        "cost_per_second_cents_480p": 5,
        "cost_per_second_cents_720p": 7,
        "reservation_ttl_seconds": 900,
    }
    defaults.update(overrides)
    return GenerationSettings(**defaults)


def _make_repo_mock(conn_mock=None):
    """Build a repo mock with _acquire_connection as an async context manager."""
    repo = MagicMock()
    conn = conn_mock or AsyncMock()
    repo._acquire_connection = MagicMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=conn),
        __aexit__=AsyncMock(return_value=False),
    ))
    # Default async methods
    repo.check_cancellation = AsyncMock(return_value=False)
    repo.update_job_status = AsyncMock()
    repo.update_cadre_status = AsyncMock()
    return repo, conn


def _make_worker(
    repo=None,
    storage=None,
    grok=None,
    composition=None,
    credit_service=None,
    settings=None,
):
    default_grok = grok
    if default_grok is None:
        default_grok = MagicMock()
        default_grok.reset_circuit_breaker = MagicMock()
    return GenerationWorker(
        repository=repo or _make_repo_mock()[0],
        storage=storage or MagicMock(),
        client=default_grok,
        composition_service=composition or AsyncMock(),
        credit_service=credit_service or AsyncMock(),
        settings=settings or _make_settings(),
    )


def _make_job_row(job_id=None, user_id=None, status="pending", total_cadres=2):
    jid = job_id or uuid4()
    uid = user_id or uuid4()
    return {
        "id": jid,
        "user_id": uid,
        "status": status,
        "total_cadres": total_cadres,
        "composition_spec": json.dumps({
            "cadres": [
                {"index": i, "prompt": f"prompt {i}", "duration_seconds": 3}
                for i in range(total_cadres)
            ],
            "resolution": "480p",
        }),
        "cancellation_requested": False,
        "claimed_at": None,
        "r2_key": None,
        "error": None,
    }


def _make_cadre_row(cadre_id=None, job_id=None, index=0, status="pending"):
    return {
        "id": cadre_id or uuid4(),
        "job_id": job_id or uuid4(),
        "cadre_index": index,
        "prompt": f"prompt {index}",
        "duration_seconds": 3,
        "transition": "fade",
        "status": status,
        "r2_key": None,
        "cost_cents": None,
        "reservation_id": None,
        "grok_request_id": None,
        "error": None,
        "frame_r2_key": None,
    }


class TestWorkerClaim:
    @pytest.mark.asyncio
    async def test_skip_already_claimed(self):
        """Worker should skip if atomic claim returns no rows."""
        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = None  # No rows = already claimed
        conn_mock.fetch.return_value = []

        repo, _ = _make_repo_mock(conn_mock)

        worker = _make_worker(repo=repo)
        await worker.process_job(uuid4())
        # Should return without processing
        repo.update_job_status.assert_not_called()


class TestWorkerCancellation:
    @pytest.mark.asyncio
    async def test_cancellation_stops_processing(self):
        """Worker should stop and mark cancelled when cancellation_requested."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=2)
        cadres = [
            _make_cadre_row(job_id=job_id, index=0),
            _make_cadre_row(job_id=job_id, index=1),
        ]

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)
        repo.check_cancellation = AsyncMock(return_value=True)

        worker = _make_worker(repo=repo)
        await worker.process_job(job_id)

        repo.update_job_status.assert_called_once_with(job_id, "cancelled")


class TestWorkerModerationBlock:
    @pytest.mark.asyncio
    async def test_moderation_block_refunds(self):
        """Moderation block should void credits and fail the job."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=1)
        cadres = [_make_cadre_row(job_id=job_id, index=0)]

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = AsyncMock()
        grok.generate_clip.side_effect = GrokModerationBlockedError("blocked")
        grok.reset_circuit_breaker = MagicMock()

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(repo=repo, grok=grok, credit_service=credit)
        await worker.process_job(job_id)

        credit.void_usage.assert_called_once_with(reservation.id)
        repo.update_job_status.assert_called_with(
            job_id, "failed", error="moderation_blocked"
        )


class TestWorkerCircuitBreaker:
    @pytest.mark.asyncio
    async def test_circuit_breaker_fails_job(self):
        """Circuit breaker trip should fail job and void remaining."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=2)
        cadres = [
            _make_cadre_row(job_id=job_id, index=0),
            _make_cadre_row(job_id=job_id, index=1),
        ]

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = AsyncMock()
        grok.generate_clip.side_effect = GrokAPIUnavailableError("breaker tripped")
        grok.reset_circuit_breaker = MagicMock()

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(repo=repo, grok=grok, credit_service=credit)
        await worker.process_job(job_id)

        repo.update_job_status.assert_called_with(
            job_id, "failed", error="api_unavailable"
        )


class TestWorkerInsufficientCredits:
    @pytest.mark.asyncio
    async def test_insufficient_credits_short_circuits(self):
        """InsufficientCredits should short-circuit remaining cadres."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=3)
        cadres = [
            _make_cadre_row(job_id=job_id, index=0, status="completed"),
            _make_cadre_row(job_id=job_id, index=1),
            _make_cadre_row(job_id=job_id, index=2),
        ]
        cadres[0]["r2_key"] = "generated/uid/jid/cadre_0.mp4"

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        credit = AsyncMock()
        from src.billing.credits.exceptions import InsufficientCredits
        credit.authorize_usage.side_effect = InsufficientCredits("not enough")

        worker = _make_worker(repo=repo, credit_service=credit)
        await worker.process_job(job_id)

        # Should result in partial (one cadre completed)
        # Check that update_job_status was called with partial
        calls = [c for c in repo.update_job_status.call_args_list]
        final_call = calls[-1]
        assert final_call[0][1] == "partial"  # status


class TestWorkerRetryWithoutImage:
    """Tests for the continuation-image retry logic.

    When cadre 1+ fails with a presigned continuation URL, the worker
    retries once WITHOUT the image_url (standalone generation).
    """

    @pytest.mark.asyncio
    async def test_retry_succeeds_without_continuation_image(self):
        """If generate_clip fails with image_url, retry without it and succeed."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=2)
        cadres = [
            _make_cadre_row(job_id=job_id, index=0),
            _make_cadre_row(job_id=job_id, index=1),
        ]

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        # generate_clip: cadre 0 OK, cadre 1 first call (with image_url) FAILS,
        # cadre 1 second call (without image_url) OK
        call_count = 0

        async def generate_clip_side_effect(prompt, duration, resolution, aspect_ratio="auto", image_url=None):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                # Second call is cadre 1 with image_url — fail
                assert image_url is not None, "Expected image_url on first attempt for cadre 1"
                assert prompt.startswith("Animate this scene from the reference image"), \
                    "I2V prompt should have reference prefix when image_url present"
                raise GenerationError("presigned URL rejected")
            if call_count == 3:
                # Third call is cadre 1 retry without image_url
                assert image_url is None, "Expected no image_url on retry"
                assert not prompt.startswith("Animate this scene from the reference image"), \
                    "T2V prompt should NOT have reference prefix after image fallback"
            return ClipResult(url="https://cdn.x.ai/video.mp4", request_id=f"req-{call_count}")

        grok = AsyncMock()
        grok.generate_clip = AsyncMock(side_effect=generate_clip_side_effect)
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage._generation_key.return_value = "generated/uid/jid/frame_0.png"
        storage.get_presigned_url = AsyncMock(return_value="https://presigned.url/frame")
        storage.upload_video = AsyncMock(return_value="generated/uid/jid/cadre_0.mp4")
        storage._video_storage = MagicMock()
        storage._settings = MagicMock()

        composition = AsyncMock()
        composition.validate_output.return_value = 3.0

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(
            repo=repo, storage=storage, grok=grok,
            composition=composition, credit_service=credit,
        )

        with patch.object(Path, 'read_bytes', return_value=b"fake data"):
            with patch.object(Path, 'unlink'):
                with patch.object(Path, 'exists', return_value=True):
                    with patch.object(Path, 'stat') as mock_stat:
                        mock_stat.return_value = MagicMock(st_size=1000)
                        await worker.process_job(job_id)

        # 3 calls: cadre 0 (ok) + cadre 1 (fail) + cadre 1 retry (ok)
        assert call_count == 3

        # Job should complete (composing path reached)
        status_calls = [c[0] for c in repo.update_job_status.call_args_list]
        assert ("composing",) in [c[1:] for c in status_calls] or any(
            c[0][1] == "composing" for c in repo.update_job_status.call_args_list
        )

    @pytest.mark.asyncio
    async def test_moderation_block_not_retried_on_continuation(self):
        """GrokModerationBlockedError is NOT retried even with image_url."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=2)
        cadres = [
            _make_cadre_row(job_id=job_id, index=0, status="completed"),
            _make_cadre_row(job_id=job_id, index=1),
        ]
        cadres[0]["r2_key"] = "generated/uid/jid/cadre_0.mp4"

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = AsyncMock()
        grok.generate_clip.side_effect = GrokModerationBlockedError("blocked")
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage._generation_key.return_value = "generated/uid/jid/frame_0.png"
        storage.get_presigned_url = AsyncMock(return_value="https://presigned.url/frame")

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(repo=repo, storage=storage, grok=grok, credit_service=credit)

        with patch.object(Path, 'unlink'):
            await worker.process_job(job_id)

        # Only ONE call to generate_clip (no retry)
        assert grok.generate_clip.call_count == 1
        repo.update_job_status.assert_called_with(
            job_id, "failed", error="moderation_blocked"
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_not_retried_on_continuation(self):
        """GrokAPIUnavailableError is NOT retried even with image_url."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=2)
        cadres = [
            _make_cadre_row(job_id=job_id, index=0, status="completed"),
            _make_cadre_row(job_id=job_id, index=1),
        ]
        cadres[0]["r2_key"] = "generated/uid/jid/cadre_0.mp4"

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = AsyncMock()
        grok.generate_clip.side_effect = GrokAPIUnavailableError("breaker open")
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage._generation_key.return_value = "generated/uid/jid/frame_0.png"
        storage.get_presigned_url = AsyncMock(return_value="https://presigned.url/frame")

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(repo=repo, storage=storage, grok=grok, credit_service=credit)

        with patch.object(Path, 'unlink'):
            await worker.process_job(job_id)

        # Only ONE call (no retry)
        assert grok.generate_clip.call_count == 1
        repo.update_job_status.assert_called_with(
            job_id, "failed", error="api_unavailable"
        )

    @pytest.mark.asyncio
    async def test_cadre_0_generation_error_not_retried(self):
        """Cadre 0 has no image_url, so GenerationError is NOT retried."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=1)
        cadres = [_make_cadre_row(job_id=job_id, index=0)]

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = AsyncMock()
        grok.generate_clip.side_effect = GenerationError("api error")
        grok.reset_circuit_breaker = MagicMock()

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(repo=repo, grok=grok, credit_service=credit)

        with patch.object(Path, 'unlink'):
            await worker.process_job(job_id)

        # Only ONE call, no retry (cadre 0 has no image_url)
        assert grok.generate_clip.call_count == 1
        # Should be partial (single cadre failed)
        assert any(
            call.args[:2] == (cadres[0]["id"], "failed")
            and call.kwargs.get("error") == "api error"
            for call in repo.update_cadre_status.call_args_list
        )

    @pytest.mark.asyncio
    async def test_retry_also_fails_marks_cadre_failed(self):
        """If both the original and retry generate_clip fail, cadre is marked failed."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=2)
        cadres = [
            _make_cadre_row(job_id=job_id, index=0, status="completed"),
            _make_cadre_row(job_id=job_id, index=1),
        ]
        cadres[0]["r2_key"] = "generated/uid/jid/cadre_0.mp4"

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        # Both attempts fail
        grok = AsyncMock()
        grok.generate_clip.side_effect = GenerationError("always fails")
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage._generation_key.return_value = "generated/uid/jid/frame_0.png"
        storage.get_presigned_url = AsyncMock(return_value="https://presigned.url/frame")

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(repo=repo, storage=storage, grok=grok, credit_service=credit)

        with patch.object(Path, 'unlink'):
            await worker.process_job(job_id)

        # 2 calls: original with image_url + retry without image_url
        assert grok.generate_clip.call_count == 2
        # Cadre 1 should be marked failed
        assert any(
            call.args[:2] == (cadres[1]["id"], "failed")
            and call.kwargs.get("error") == "always fails"
            for call in repo.update_cadre_status.call_args_list
        )

    @pytest.mark.asyncio
    async def test_timeout_retried_once(self):
        """GenerationTimeoutError gets exactly one bounded retry."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=1)
        cadres = [_make_cadre_row(job_id=job_id, index=0)]

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        from src.generation.exceptions import GenerationTimeoutError

        grok = AsyncMock()
        grok.generate_clip = AsyncMock(side_effect=[
            GenerationTimeoutError("timed out"),
            ClipResult(url="https://cdn.x.ai/video.mp4", request_id="req-2"),
        ])
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage.upload_video = AsyncMock(side_effect=[
            "generated/uid/jid/frame_0.png",
            "generated/uid/jid/cadre_0.mp4",
        ])
        storage._video_storage = MagicMock()
        storage._settings = MagicMock()

        composition = AsyncMock()
        composition.validate_output.return_value = 3.0

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(
            repo=repo, storage=storage, grok=grok, composition=composition, credit_service=credit,
        )
        worker._compose_and_upload = AsyncMock()

        with patch.object(Path, "read_bytes", return_value=b"fake data"):
            with patch.object(Path, "unlink"):
                await worker.process_job(job_id)

        assert grok.generate_clip.call_count == 2

    @pytest.mark.asyncio
    async def test_persists_frame_for_last_cadre(self):
        """Completed last cadre stores frame_r2_key for downstream previews."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=1)
        cadres = [_make_cadre_row(job_id=job_id, index=0)]

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = AsyncMock()
        grok.generate_clip.return_value = ClipResult(
            url="https://cdn.x.ai/video.mp4",
            request_id="req-1",
        )
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage.upload_video = AsyncMock(side_effect=[
            "generated/uid/jid/frame_0.png",
            "generated/uid/jid/cadre_0.mp4",
        ])
        storage._video_storage = MagicMock()
        storage._settings = MagicMock()

        composition = AsyncMock()
        composition.validate_output.return_value = 3.0

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(
            repo=repo, storage=storage, grok=grok, composition=composition, credit_service=credit,
        )
        worker._compose_and_upload = AsyncMock()

        with patch.object(Path, "read_bytes", return_value=b"fake data"):
            with patch.object(Path, "unlink"):
                await worker.process_job(job_id)

        assert any(
            call.args[:2] == (cadres[0]["id"], "completed")
            and call.kwargs.get("frame_r2_key") == "generated/uid/jid/frame_0.png"
            for call in repo.update_cadre_status.call_args_list
        )

    @pytest.mark.asyncio
    async def test_project_render_prefers_approved_preview_seed(self):
        """Project-linked cadres should use the approved preview image as the seed."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=1)
        cadres = [_make_cadre_row(job_id=job_id, index=0)]
        cadres[0]["seed_image_storage_key"] = "previews/user-id/0123456789abcdef0123456789abcdef.png"

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = AsyncMock()
        grok.generate_clip.return_value = ClipResult(
            url="https://cdn.x.ai/video.mp4",
            request_id="req-1",
        )
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage.get_preview_url = AsyncMock(return_value="https://preview.example.com/scene-0.png")
        storage.upload_video = AsyncMock(side_effect=[
            "generated/uid/jid/frame_0.png",
            "generated/uid/jid/cadre_0.mp4",
        ])
        storage._video_storage = MagicMock()
        storage._settings = MagicMock()

        composition = AsyncMock()
        composition.validate_output.return_value = 3.0

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(
            repo=repo, storage=storage, grok=grok, composition=composition, credit_service=credit,
        )
        worker._compose_and_upload = AsyncMock()

        with patch.object(Path, "read_bytes", return_value=b"fake data"):
            with patch.object(Path, "unlink"):
                await worker.process_job(job_id)

        assert grok.generate_clip.await_args.kwargs["image_url"] == "https://preview.example.com/scene-0.png"
        # With a seed image, prompt should have I2V prefix
        actual_prompt = grok.generate_clip.await_args.kwargs["prompt"]
        assert actual_prompt.startswith("Animate this scene from the reference image")
        storage.get_preview_url.assert_awaited_once_with(
            "previews/user-id/0123456789abcdef0123456789abcdef.png",
            expiry=1800,
        )

    @pytest.mark.asyncio
    async def test_preview_seed_failure_falls_back_to_previous_frame(self):
        """If a preview seed cannot be presigned, fall back to the previous cadre frame."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=2)
        cadres = [
            _make_cadre_row(job_id=job_id, index=0, status="completed"),
            _make_cadre_row(job_id=job_id, index=1),
        ]
        cadres[0]["r2_key"] = "generated/uid/jid/cadre_0.mp4"
        cadres[1]["seed_image_storage_key"] = "previews/user-id/0123456789abcdef0123456789abcdef.png"

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = AsyncMock()
        grok.generate_clip.return_value = ClipResult(
            url="https://cdn.x.ai/video.mp4",
            request_id="req-1",
        )
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage.get_preview_url = AsyncMock(side_effect=RuntimeError("preview missing"))
        storage._generation_key.return_value = "generated/uid/jid/frame_0.png"
        storage.get_presigned_url = AsyncMock(return_value="https://frames.example.com/frame-0.png")
        storage.upload_video = AsyncMock(return_value="generated/uid/jid/cadre.mp4")
        storage._video_storage = MagicMock()
        storage._settings = MagicMock()

        composition = AsyncMock()
        composition.validate_output.return_value = 3.0

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(
            repo=repo, storage=storage, grok=grok, composition=composition, credit_service=credit,
        )
        worker._compose_and_upload = AsyncMock()

        with patch.object(Path, "read_bytes", return_value=b"fake data"):
            with patch.object(Path, "unlink"):
                await worker.process_job(job_id)

        assert grok.generate_clip.await_args.kwargs["image_url"] == "https://frames.example.com/frame-0.png"
        storage.get_presigned_url.assert_awaited_once_with(
            "generated/uid/jid/frame_0.png",
            expiry=1800,
        )


class TestWorkerCircuitBreakerResetPerCadre:
    """Verify circuit breaker resets after each successful cadre."""

    @pytest.mark.asyncio
    async def test_reset_called_after_each_cadre_success(self):
        """reset_circuit_breaker() is called at job start + after each successful cadre."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=2)
        cadres = [
            _make_cadre_row(job_id=job_id, index=0),
            _make_cadre_row(job_id=job_id, index=1),
        ]

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = MagicMock()
        grok.generate_clip = AsyncMock(return_value=ClipResult(
            url="https://cdn.x.ai/video.mp4", request_id="req-1"
        ))
        grok.reset_circuit_breaker = MagicMock()
        grok.download_video = AsyncMock()

        storage = MagicMock()
        storage._generation_key.return_value = "generated/uid/jid/frame_0.png"
        storage.get_presigned_url = AsyncMock(return_value="https://presigned.url")
        storage.upload_video = AsyncMock(return_value="generated/uid/jid/cadre.mp4")
        storage._video_storage = MagicMock()
        storage._settings = MagicMock()

        composition = AsyncMock()
        composition.validate_output.return_value = 3.0

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(
            repo=repo, storage=storage, grok=grok,
            composition=composition, credit_service=credit,
        )

        with patch.object(Path, 'read_bytes', return_value=b"fake data"):
            with patch.object(Path, 'unlink'):
                with patch.object(Path, 'exists', return_value=True):
                    with patch.object(Path, 'stat') as mock_stat:
                        mock_stat.return_value = MagicMock(st_size=1000)
                        await worker.process_job(job_id)

        # 1 initial reset + 2 per-cadre resets = 3 total
        assert grok.reset_circuit_breaker.call_count == 3

    @pytest.mark.asyncio
    async def test_failure_doesnt_accumulate_across_cadres(self):
        """A failed cadre doesn't prevent subsequent cadres from starting fresh.

        Simulates: cadre 0 OK, cadre 1 fails (GenerationError, no retry since
        cadre 1 has image_url but both attempts fail), cadre 2 should still
        get a fresh circuit breaker.
        """
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=3)
        cadres = [
            _make_cadre_row(job_id=job_id, index=0),
            _make_cadre_row(job_id=job_id, index=1),
            _make_cadre_row(job_id=job_id, index=2),
        ]

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        call_idx = 0

        async def generate_side_effect(prompt, duration, resolution, aspect_ratio="auto", image_url=None):
            nonlocal call_idx
            call_idx += 1
            # Cadre 0 (call 1): OK
            if call_idx == 1:
                return ClipResult(url="https://cdn.x.ai/v0.mp4", request_id="r0")
            # Cadre 1 (calls 2-3): FAIL both attempts (original + retry)
            if call_idx in (2, 3):
                raise GenerationError("transient failure")
            # Cadre 2 (calls 4-5): might be retry from cadre 1, then cadre 2
            # Actually after cadre 1 fails (both attempts), worker moves to cadre 2
            return ClipResult(url="https://cdn.x.ai/v2.mp4", request_id="r2")

        grok = AsyncMock()
        grok.generate_clip = AsyncMock(side_effect=generate_side_effect)
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage._generation_key.return_value = "generated/uid/jid/frame.png"
        storage.get_presigned_url = AsyncMock(return_value="https://presigned.url")
        storage.upload_video = AsyncMock(return_value="generated/uid/jid/cadre.mp4")
        storage._video_storage = MagicMock()
        storage._settings = MagicMock()

        composition = AsyncMock()
        composition.validate_output.return_value = 3.0

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(
            repo=repo, storage=storage, grok=grok,
            composition=composition, credit_service=credit,
        )

        with patch.object(Path, 'read_bytes', return_value=b"fake data"):
            with patch.object(Path, 'unlink'):
                with patch.object(Path, 'exists', return_value=True):
                    with patch.object(Path, 'stat') as mock_stat:
                        mock_stat.return_value = MagicMock(st_size=1000)
                        await worker.process_job(job_id)

        # Cadre 0 succeeded → reset called (initial + after cadre 0 = 2)
        # Cadre 1 failed → no reset for it
        # Cadre 2 succeeded → reset called (after cadre 2 = 1 more)
        # Total = 3 (initial + cadre 0 success + cadre 2 success)
        assert grok.reset_circuit_breaker.call_count == 3

        # Result should be partial (2 of 3 cadres completed)
        final_status = repo.update_job_status.call_args_list[-1]
        assert final_status[0][1] in ("partial",)


class TestWorkerIdempotentResumption:
    @pytest.mark.asyncio
    async def test_skips_completed_cadres(self):
        """Worker should skip cadres marked as completed."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=2)
        cadres = [
            _make_cadre_row(job_id=job_id, index=0, status="completed"),
            _make_cadre_row(job_id=job_id, index=1, status="pending"),
        ]
        cadres[0]["r2_key"] = "generated/uid/jid/cadre_0.mp4"

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = MagicMock()
        grok.generate_clip = AsyncMock(return_value=ClipResult(
            url="https://cdn.x.ai/video.mp4", request_id="req-1"
        ))
        grok.download_video = AsyncMock()
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage._generation_key.return_value = "generated/uid/jid/frame_0.png"
        storage.get_presigned_url = AsyncMock(return_value="https://presigned.url")
        storage.upload_video = AsyncMock(return_value="generated/uid/jid/cadre_1.mp4")
        storage._video_storage = MagicMock()
        storage._settings = MagicMock()

        composition = AsyncMock()
        composition.validate_output.return_value = 3.0
        composition.compose.return_value = Path("/tmp/fake-output.mp4")

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(
            repo=repo,
            storage=storage,
            grok=grok,
            composition=composition,
            credit_service=credit,
        )

        # Patch download_video and file operations
        with patch.object(Path, 'read_bytes', return_value=b"fake video data"):
            with patch.object(Path, 'unlink'):
                with patch.object(Path, 'exists', return_value=True):
                    with patch.object(Path, 'stat') as mock_stat:
                        mock_stat.return_value = MagicMock(st_size=1000)
                        await worker.process_job(job_id)

        # Should only call generate_clip once (for cadre 1, not cadre 0)
        assert grok.generate_clip.call_count == 1


class TestBuildVideoPrompt:
    """Tests for I2V vs T2V prompt adaptation."""

    def test_t2v_returns_prompt_unchanged(self):
        worker = _make_worker()
        result = worker._build_video_prompt("A sunset over the ocean", has_seed_image=False)
        assert result == "A sunset over the ocean"

    def test_i2v_prepends_reference_prefix(self):
        worker = _make_worker()
        result = worker._build_video_prompt("A sunset over the ocean", has_seed_image=True)
        assert result.startswith("Animate this scene from the reference image")
        assert "A sunset over the ocean" in result

    def test_i2v_prefix_dropped_on_retry_without_image(self):
        """Simulate the retry path: first call with image, retry without."""
        worker = _make_worker()
        with_image = worker._build_video_prompt("Camera pans left", has_seed_image=True)
        without_image = worker._build_video_prompt("Camera pans left", has_seed_image=False)
        assert with_image.startswith("Animate this scene from the reference image")
        assert without_image == "Camera pans left"

    @pytest.mark.asyncio
    async def test_generate_clip_receives_i2v_prompt_with_seed_image(self):
        """When a seed image is present, generate_clip receives the I2V-adapted prompt."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=1)
        cadres = [_make_cadre_row(job_id=job_id, index=0)]
        cadres[0]["seed_image_storage_key"] = "previews/user-id/abc.png"

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = AsyncMock()
        grok.generate_clip.return_value = ClipResult(
            url="https://cdn.x.ai/video.mp4", request_id="req-1",
        )
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage.get_preview_url = AsyncMock(return_value="https://preview.example.com/img.png")
        storage.upload_video = AsyncMock(side_effect=[
            "generated/uid/jid/frame_0.png",
            "generated/uid/jid/cadre_0.mp4",
        ])
        storage._video_storage = MagicMock()
        storage._settings = MagicMock()

        composition = AsyncMock()
        composition.validate_output.return_value = 3.0

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(
            repo=repo, storage=storage, grok=grok,
            composition=composition, credit_service=credit,
        )
        worker._compose_and_upload = AsyncMock()

        with patch.object(Path, "read_bytes", return_value=b"fake data"):
            with patch.object(Path, "unlink"):
                await worker.process_job(job_id)

        actual_prompt = grok.generate_clip.await_args.kwargs["prompt"]
        assert actual_prompt.startswith("Animate this scene from the reference image")
        assert "prompt 0" in actual_prompt

    @pytest.mark.asyncio
    async def test_generate_clip_receives_raw_prompt_without_seed_image(self):
        """Without a seed image, generate_clip receives the raw prompt."""
        job_id = uuid4()
        user_id = uuid4()
        job_row = _make_job_row(job_id=job_id, user_id=user_id, total_cadres=1)
        cadres = [_make_cadre_row(job_id=job_id, index=0)]

        conn_mock = AsyncMock()
        conn_mock.fetchrow.return_value = job_row
        conn_mock.fetch.return_value = cadres

        repo, _ = _make_repo_mock(conn_mock)

        grok = AsyncMock()
        grok.generate_clip.return_value = ClipResult(
            url="https://cdn.x.ai/video.mp4", request_id="req-1",
        )
        grok.reset_circuit_breaker = MagicMock()

        storage = MagicMock()
        storage.upload_video = AsyncMock(side_effect=[
            "generated/uid/jid/frame_0.png",
            "generated/uid/jid/cadre_0.mp4",
        ])
        storage._video_storage = MagicMock()
        storage._settings = MagicMock()

        composition = AsyncMock()
        composition.validate_output.return_value = 3.0

        credit = AsyncMock()
        reservation = MagicMock()
        reservation.id = uuid4()
        credit.authorize_usage.return_value = reservation

        worker = _make_worker(
            repo=repo, storage=storage, grok=grok,
            composition=composition, credit_service=credit,
        )
        worker._compose_and_upload = AsyncMock()

        with patch.object(Path, "read_bytes", return_value=b"fake data"):
            with patch.object(Path, "unlink"):
                await worker.process_job(job_id)

        actual_prompt = grok.generate_clip.await_args.kwargs["prompt"]
        assert actual_prompt == "prompt 0"
        assert "reference image" not in actual_prompt
