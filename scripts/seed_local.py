"""Seed the local Supabase with:
  - a demo client (slug=demo-clinic)
  - an admin user (email, password) — signed up via GoTrue, then linked + granted admin role

Only runs against the local Supabase stack (localhost:54322). Not safe for prod.
"""
from __future__ import annotations

import asyncio
import os
import sys

import asyncpg
import httpx

LOCAL_DB = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
LOCAL_API = "http://127.0.0.1:54321"
LOCAL_ANON = "sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH"

ADMIN_EMAIL = "jr@local.gofreddy.ai"
ADMIN_PASSWORD = "letmein-localonly-2026"
DEMO_CLIENT_SLUG = "demo-clinic"
DEMO_CLIENT_NAME = "Demo Dermatology Clinic"


async def main() -> None:
    # 1. Sign up admin user via GoTrue (signup is enabled by default locally)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{LOCAL_API}/auth/v1/signup",
            headers={"apikey": LOCAL_ANON, "Content-Type": "application/json"},
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        if resp.status_code == 200:
            body = resp.json()
            sup_id = body.get("user", {}).get("id") or body.get("id")
            print(f"  signup ok · supabase user_id = {sup_id}")
        elif resp.status_code == 422 or "already_registered" in resp.text.lower() or "already" in resp.text.lower():
            # Already registered — fetch user via admin API
            print(f"  user already exists, fetching via admin API")
            resp = await client.post(
                f"{LOCAL_API}/auth/v1/token?grant_type=password",
                headers={"apikey": LOCAL_ANON, "Content-Type": "application/json"},
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            )
            resp.raise_for_status()
            body = resp.json()
            sup_id = body["user"]["id"]
            print(f"  signin ok · supabase user_id = {sup_id}")
        else:
            print(f"  signup failed: {resp.status_code} {resp.text}", file=sys.stderr)
            sys.exit(1)

    # 2. Insert demo client + app user + membership
    conn = await asyncpg.connect(LOCAL_DB)
    try:
        await conn.execute(
            "INSERT INTO clients (slug, name) VALUES ($1, $2) ON CONFLICT (slug) DO NOTHING",
            DEMO_CLIENT_SLUG, DEMO_CLIENT_NAME,
        )
        user_id = await conn.fetchval(
            """
            INSERT INTO users (email, supabase_user_id) VALUES ($1, $2)
            ON CONFLICT (email) DO UPDATE SET supabase_user_id = EXCLUDED.supabase_user_id
            RETURNING id
            """,
            ADMIN_EMAIL, sup_id,
        )
        client_id = await conn.fetchval(
            "SELECT id FROM clients WHERE slug = $1", DEMO_CLIENT_SLUG
        )
        await conn.execute(
            """
            INSERT INTO user_client_memberships (user_id, client_id, role)
            VALUES ($1, $2, 'admin')
            ON CONFLICT (user_id, client_id) DO UPDATE SET role = 'admin'
            """,
            user_id, client_id,
        )
        print(f"  seeded · user_id={user_id} · client_id={client_id} · role=admin")
    finally:
        await conn.close()

    print(f"\nReady. Credentials:")
    print(f"  email:    {ADMIN_EMAIL}")
    print(f"  password: {ADMIN_PASSWORD}")
    print(f"  portal:   /portal/{DEMO_CLIENT_SLUG}")


if __name__ == "__main__":
    asyncio.run(main())
