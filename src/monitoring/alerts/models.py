"""Alert domain models — rules and events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SpikeConfig(BaseModel):
    """Strict config for mention_spike rules. extra='forbid' prevents payload stuffing."""

    model_config = ConfigDict(extra="forbid")

    threshold_pct: int = Field(default=200, ge=50, le=1000)
    window_hours: Literal[1, 6, 24] = 1
    min_baseline_runs: int = Field(default=3, ge=1, le=10)


@dataclass(frozen=True, slots=True)
class AlertRule:
    id: UUID
    monitor_id: UUID
    user_id: UUID
    rule_type: str  # "mention_spike"
    config: dict[str, Any]
    webhook_url: str
    is_active: bool
    cooldown_minutes: int
    last_triggered_at: datetime | None
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class AlertEvent:
    id: UUID
    rule_id: UUID
    monitor_id: UUID
    triggered_at: datetime
    condition_summary: str
    payload: dict[str, Any]
    delivery_status: str  # "pending" | "delivered" | "failed"
    delivery_attempts: int
    last_delivery_at: datetime | None
    created_at: datetime
