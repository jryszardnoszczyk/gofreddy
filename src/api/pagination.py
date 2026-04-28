"""Shared pagination constants for all v1 list endpoints.

Every sibling list endpoint (GET /v1/monitors, /v1/api-keys, /v1/sessions,
/v1/geo/audits, /v1/monitors/{id}/mentions, /runs, /digests, /alerts/history,
/changelog, /v1/sessions/{id}/iterations, /actions) declares its `limit` query
parameter against these two constants so a generic UI list component can rely
on a single (max, default) pair across the API surface.
"""

from __future__ import annotations

DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 200
