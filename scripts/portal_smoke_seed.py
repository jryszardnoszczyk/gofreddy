"""Portal v1 visual smoke — seeds a test tenant + synthetic events.

Boots zero servers. Assumes:
  * Supabase is running on 127.0.0.1:54321 (run `supabase start` if not)
  * gofreddy backend is running on 127.0.0.1:8000 (or wherever you point your browser)

What it does (idempotent — safe to re-run):
  1. Signs up a Supabase user (or reuses if email exists)
  2. Inserts a clients row + user_client_memberships row
  3. Appends ~10 synthetic events to clients/<slug>/audit/events.jsonl
     spanning the full kind palette so every UI section has data

Prints at the end:
  * the URL to open
  * the email + password to sign in with
  * the path you can `tail -f` to watch live events flow into the transcript

Usage:
  python scripts/portal_smoke_seed.py                          # default tenant
  python scripts/portal_smoke_seed.py --slug acme --reset      # different slug, wipe prior events
  python scripts/portal_smoke_seed.py --drip 20                # append 1 event/sec for 20s
                                                                 (open the page first, watch it stream)
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
import uuid
from pathlib import Path

# Make sibling autoresearch/ importable when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncpg
import httpx

from autoresearch.events import client_events_path, log_event

LOCAL_API = "http://127.0.0.1:54321"
LOCAL_DB = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
LOCAL_ANON = "sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH"


def signup_or_reuse(email: str, password: str) -> str:
    """Return the Supabase user id. Idempotent — reuses if email exists."""
    r = httpx.post(
        f"{LOCAL_API}/auth/v1/signup",
        headers={"apikey": LOCAL_ANON, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=10.0,
    )
    if r.status_code in (200, 201):
        return r.json()["user"]["id"]
    # already exists → sign in to fetch id
    r = httpx.post(
        f"{LOCAL_API}/auth/v1/token?grant_type=password",
        headers={"apikey": LOCAL_ANON, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=10.0,
    )
    r.raise_for_status()
    return r.json()["user"]["id"]


async def seed_tenant_rows(
    supabase_user_id: str, email: str, slug: str, client_name: str
) -> None:
    """Idempotently upsert users + clients + memberships rows."""
    conn = await asyncpg.connect(LOCAL_DB)
    try:
        user_id = await conn.fetchval(
            """
            INSERT INTO users (email, supabase_user_id) VALUES ($1, $2)
            ON CONFLICT (email) DO UPDATE SET supabase_user_id = EXCLUDED.supabase_user_id
            RETURNING id
            """,
            email,
            supabase_user_id,
        )
        client_id = await conn.fetchval(
            """
            INSERT INTO clients (slug, name) VALUES ($1, $2)
            ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            slug,
            client_name,
        )
        await conn.execute(
            """
            INSERT INTO user_client_memberships (user_id, client_id, role)
            VALUES ($1, $2, 'owner')
            ON CONFLICT (user_id, client_id) DO UPDATE SET role = EXCLUDED.role
            """,
            user_id,
            client_id,
        )
    finally:
        await conn.close()


# Synthetic event recipes — covers every UI section of the portal page.
# Designed so a fresh smoke shows: real cost numbers, real lane chips, real
# audit rows in multiple colours, no empty-state spam.
def _seed_events(slug: str) -> None:
    path = client_events_path(slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    common = {"client_id": slug, "source": "autoresearch"}

    # Two cost events (will populate today/week/month rollup)
    log_event(kind="cost", path=path, cost_usd=0.42, model="claude-opus-4-7",
              tokens_in=12_340, tokens_out=2_180, lane="marketing_audit", **common)
    log_event(kind="cost", path=path, cost_usd=1.18, model="gpt-5-5",
              tokens_in=44_120, tokens_out=8_330, lane="x_engine", **common)

    # Agent activity — lime colour
    log_event(kind="session_start", path=path, lane="marketing_audit",
              variant="v007", action="evaluate_session", **common)
    log_event(kind="tool_call", path=path, lane="marketing_audit", action="lighthouse_audit",
              args={"url": f"https://{slug}.example"}, **common)
    log_event(kind="model_call", path=path, lane="marketing_audit", action="critique-1",
              model="claude-opus-4-7", **common)
    log_event(kind="render", path=path, lane="marketing_audit", variant="v007",
              fixture=slug, action="render_judge", status="complete", **common)

    # Human activity — warm colour
    log_event(kind="review_approve", path=path, actor="human", lane="x_engine",
              action="reviewer_approves_x_thread_v007", **common)
    log_event(kind="review_reject", path=path, actor="human", lane="x_engine",
              action="rejects_draft_3_voice_off", **common)

    # System / promotion — dim
    log_event(kind="promotion", path=path, lane="marketing_audit", variant="v007",
              action="promoted_v007", status="complete", **common)
    log_event(kind="alert", path=path, action="judge_unreachable", status="failed", **common)


def drip_events(slug: str, seconds: int) -> None:
    """Append one event per second so you can watch SSE deliver them live."""
    path = client_events_path(slug)
    for i in range(seconds):
        log_event(
            kind="tool_call",
            path=path,
            client_id=slug,
            source="autoresearch",
            actor="agent",
            lane="marketing_audit",
            action=f"drip_step_{i:03d}",
            status="complete",
            cost_usd=round(0.01 * (i + 1), 4),
        )
        print(f"  [{i+1:03d}/{seconds:03d}] appended", flush=True)
        time.sleep(1)


async def _amain(args) -> int:
    suffix = uuid.uuid4().hex[:6]
    slug = args.slug or f"smoke-{suffix}"
    email = args.email or f"smoke-{suffix}@gofreddy.test"

    print(f"== portal smoke seed ==")
    print(f"slug:     {slug}")
    print(f"email:    {email}")
    print()

    if args.reset:
        path = client_events_path(slug)
        if path.exists():
            path.unlink()
            print(f"[reset] removed prior events.jsonl at {path}")

    print("[1/3] supabase signup …", flush=True)
    sup_id = signup_or_reuse(email, args.password)
    print(f"       supabase user id: {sup_id}")

    print("[2/3] seeding clients row + membership …", flush=True)
    await seed_tenant_rows(sup_id, email, slug, args.name)

    print("[3/3] seeding synthetic events …", flush=True)
    _seed_events(slug)
    log_path = client_events_path(slug)
    print(f"       wrote {sum(1 for _ in log_path.open())} events to {log_path}")

    print()
    print("=" * 60)
    print(f"  open in browser:")
    print(f"    {args.portal_url}/portal/{slug}")
    print()
    print(f"  sign in with:")
    print(f"    email:    {email}")
    print(f"    password: {args.password}")
    print()
    print(f"  watch events live:")
    print(f"    tail -f {log_path}")
    print("=" * 60)

    if args.drip > 0:
        print()
        print(f"[drip] appending {args.drip} events at 1/sec — open the page first to see them stream in")
        time.sleep(2)
        drip_events(slug, args.drip)

    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None,
                    help="Client slug (default: smoke-<random suffix>)")
    ap.add_argument("--name", default="Portal Smoke Co",
                    help="Client display name")
    ap.add_argument("--email", default=None,
                    help="Reviewer email (default: smoke-<random>@gofreddy.test)")
    ap.add_argument("--password", default="smoke-pw-2026-supersafe",
                    help="Reviewer password")
    ap.add_argument("--reset", action="store_true",
                    help="Delete prior events.jsonl for this slug before seeding")
    ap.add_argument("--drip", type=int, default=0,
                    help="After seeding, append 1 event/sec for N seconds (watch SSE live)")
    ap.add_argument("--portal-url", default="http://localhost:8000",
                    help="Where the gofreddy backend is running")
    args = ap.parse_args()
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    sys.exit(main())
