from __future__ import annotations

import argparse
import json
from unittest.mock import AsyncMock

import pytest

from scripts import e2e_seed_auth_tokens as seed_tokens


class FakeConnection:
    def __init__(self) -> None:
        self.execute_calls: list[tuple[str, tuple[object, ...]]] = []
        self.closed = False

    async def fetchrow(self, query: str, *args: object) -> dict[str, str]:
        email = str(args[0])
        if email == seed_tokens.FREE_EMAIL:
            return {"id": "11111111-1111-4111-8111-111111111111"}
        if email == seed_tokens.PRO_EMAIL:
            return {"id": "22222222-2222-4222-8222-222222222222"}
        raise AssertionError(f"Unexpected email in fetchrow: {email}")

    async def execute(self, query: str, *args: object) -> None:
        self.execute_calls.append((query, args))

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_clear_analysis_jobs_targets_seeded_user_jobs() -> None:
    conn = AsyncMock()

    await seed_tokens.clear_analysis_jobs(conn, user_id="11111111-1111-4111-8111-111111111111")

    conn.execute.assert_awaited_once_with(
        "DELETE FROM analysis_jobs WHERE user_id = $1::uuid",
        "11111111-1111-4111-8111-111111111111",
    )


@pytest.mark.asyncio
async def test_main_cleans_seeded_users_and_preserves_payload_contract(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    conn = FakeConnection()

    async def fake_connect(db_url: str) -> FakeConnection:
        assert db_url == "postgresql://example/test"
        return conn

    def fake_parse_args() -> argparse.Namespace:
        return argparse.Namespace(
            db_url="postgresql://example/test",
            supabase_url="http://localhost:54321",
            jwt_secret="seed-secret",
        )

    jwt_calls: list[tuple[str, str, str, str]] = []

    def fake_make_jwt(
        *,
        supabase_user_id: str,
        email: str,
        supabase_url: str,
        jwt_secret: str,
    ) -> str:
        jwt_calls.append((supabase_user_id, email, supabase_url, jwt_secret))
        return f"token:{supabase_user_id}"

    monkeypatch.setattr(seed_tokens.asyncpg, "connect", fake_connect)
    monkeypatch.setattr(seed_tokens, "parse_args", fake_parse_args)
    monkeypatch.setattr(seed_tokens, "make_jwt", fake_make_jwt)

    await seed_tokens.main()

    output = capsys.readouterr().out.strip()
    payload = json.loads(output)
    assert set(payload) == {"free_user_id", "pro_user_id", "free_token", "pro_token"}
    assert payload["free_user_id"] == "11111111-1111-4111-8111-111111111111"
    assert payload["pro_user_id"] == "22222222-2222-4222-8222-222222222222"
    assert payload["free_token"] == "token:cp8_e2e_free_user"
    assert payload["pro_token"] == "token:cp8_e2e_pro_user"

    delete_job_calls = [
        args[0]
        for query, args in conn.execute_calls
        if "DELETE FROM analysis_jobs WHERE user_id = $1::uuid" in query
    ]
    assert set(delete_job_calls) == {
        "11111111-1111-4111-8111-111111111111",
        "22222222-2222-4222-8222-222222222222",
    }

    clear_subscriptions_index = next(
        idx for idx, (query, _) in enumerate(conn.execute_calls) if "DELETE FROM subscriptions" in query
    )
    ensure_pro_subscription_index = next(
        idx for idx, (query, _) in enumerate(conn.execute_calls) if "INSERT INTO subscriptions" in query
    )
    delete_job_indices = [
        idx
        for idx, (query, _) in enumerate(conn.execute_calls)
        if "DELETE FROM analysis_jobs WHERE user_id = $1::uuid" in query
    ]
    assert len(delete_job_indices) == 2
    assert all(idx < clear_subscriptions_index for idx in delete_job_indices)
    assert all(idx < ensure_pro_subscription_index for idx in delete_job_indices)

    assert jwt_calls == [
        (
            seed_tokens.FREE_SUPABASE_USER_ID,
            seed_tokens.FREE_EMAIL,
            "http://localhost:54321",
            "seed-secret",
        ),
        (
            seed_tokens.PRO_SUPABASE_USER_ID,
            seed_tokens.PRO_EMAIL,
            "http://localhost:54321",
            "seed-secret",
        ),
    ]
    assert conn.closed is True
