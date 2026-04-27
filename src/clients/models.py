"""Client model for file-based per-client workspaces.

A `Client` describes a prospect or active agency client backed by a
filesystem workspace under `clients/<slug>/`. The fields here cover what
gofreddy's CLI flows and the audit pipeline actually consume — `slug`
addresses the workspace, `domain` is the prospect website used by audits,
and the optional `enrichments` / `fit_signals` dicts hold audit-derived
or ICP-scoring metadata.

This module is **not** a port of freddy's `src/clients/models.py`. Freddy's
model is an asyncpg-backed agency-multi-tenant dataclass (id/org_id/
competitor_brands/...). GoFreddy is a single-tenant file-based CLI; the
two schemas have different needs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Client(BaseModel):
    """An agency client (prospect or active)."""

    name: str
    slug: str
    domain: str
    enrichments: dict[str, Any] = Field(default_factory=dict)
    fit_signals: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
