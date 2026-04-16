"""Repository for deepfake analysis results."""

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

import asyncpg

from .models import (
    Confidence,
    DeepfakeAnalysisRecord,
    DetectionMethod,
    RiskLevel,
    Verdict,
)


class PostgresDeepfakeRepository:
    """Repository for deepfake analysis results."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_by_video_analysis_id(
        self,
        video_analysis_id: UUID,
        user_id: UUID,
    ) -> DeepfakeAnalysisRecord | None:
        """Get existing analysis for a video."""
        query = """
            SELECT * FROM deepfake_analysis
            WHERE video_analysis_id = $1
              AND user_id = $2
            ORDER BY analyzed_at DESC
            LIMIT 1
        """
        async with self._pool.acquire(timeout=10.0) as conn:
            row = await conn.fetchrow(query, video_analysis_id, user_id)
            if row:
                return self._row_to_record(row)
            return None

    async def create(
        self,
        video_analysis_id: UUID,
        user_id: UUID,
        lip_sync_score: float | None,
        lip_sync_anomaly_detected: bool | None,
        lip_sync_confidence: Confidence | None,
        lip_sync_error: str | None,
        reality_defender_score: float | None,
        reality_defender_verdict: Verdict | None,
        reality_defender_indicators: list[str],
        reality_defender_error: str | None,
        combined_score: float,
        is_deepfake: bool,
        risk_level: RiskLevel,
        detection_method: DetectionMethod,
        limitations: list[str],
        processing_time_ms: int,
        cost_cents: int,
    ) -> DeepfakeAnalysisRecord:
        """Create new deepfake analysis record."""
        record_id = uuid4()
        now = datetime.now(timezone.utc)

        query = """
            INSERT INTO deepfake_analysis (
                id, video_analysis_id, user_id,
                lip_sync_score, lip_sync_anomaly_detected,
                lip_sync_confidence, lip_sync_error,
                reality_defender_score, reality_defender_verdict,
                reality_defender_indicators, reality_defender_error,
                combined_score, is_deepfake, risk_level, detection_method,
                limitations, processing_time_ms, cost_cents, analyzed_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18, $19
            )
            ON CONFLICT (video_analysis_id, user_id) DO UPDATE SET
                lip_sync_score = EXCLUDED.lip_sync_score,
                lip_sync_anomaly_detected = EXCLUDED.lip_sync_anomaly_detected,
                lip_sync_confidence = EXCLUDED.lip_sync_confidence,
                lip_sync_error = EXCLUDED.lip_sync_error,
                reality_defender_score = EXCLUDED.reality_defender_score,
                reality_defender_verdict = EXCLUDED.reality_defender_verdict,
                reality_defender_indicators = EXCLUDED.reality_defender_indicators,
                reality_defender_error = EXCLUDED.reality_defender_error,
                combined_score = EXCLUDED.combined_score,
                is_deepfake = EXCLUDED.is_deepfake,
                risk_level = EXCLUDED.risk_level,
                detection_method = EXCLUDED.detection_method,
                limitations = EXCLUDED.limitations,
                processing_time_ms = EXCLUDED.processing_time_ms,
                cost_cents = EXCLUDED.cost_cents,
                analyzed_at = EXCLUDED.analyzed_at
            RETURNING *
        """
        async with self._pool.acquire(timeout=10.0) as conn:
            row = await conn.fetchrow(
                query,
                record_id,
                video_analysis_id,
                user_id,
                lip_sync_score,
                lip_sync_anomaly_detected,
                lip_sync_confidence.value if lip_sync_confidence else None,
                lip_sync_error,
                reality_defender_score,
                reality_defender_verdict.value if reality_defender_verdict else None,
                json.dumps(reality_defender_indicators),
                reality_defender_error,
                combined_score,
                is_deepfake,
                risk_level.value,
                detection_method.value,
                limitations,
                processing_time_ms,
                cost_cents,
                now,
            )
            return self._row_to_record(row)

    async def get_user_daily_cost(self, user_id: UUID) -> int:
        """Get user's deepfake detection spend today in cents."""
        query = """
            SELECT COALESCE(SUM(da.cost_cents), 0)
            FROM deepfake_analysis da
            WHERE da.user_id = $1
              AND da.analyzed_at >= CURRENT_DATE
        """
        async with self._pool.acquire(timeout=10.0) as conn:
            result = await conn.fetchval(query, user_id)
            return int(result)

    @staticmethod
    def _row_to_record(row: asyncpg.Record) -> DeepfakeAnalysisRecord:
        """Convert database row to record."""
        indicators = row["reality_defender_indicators"]
        if isinstance(indicators, str):
            try:
                indicators = json.loads(indicators)
            except Exception:
                indicators = []
        return DeepfakeAnalysisRecord(
            id=row["id"],
            video_analysis_id=row["video_analysis_id"],
            lip_sync_score=float(row["lip_sync_score"]) if row["lip_sync_score"] else None,
            lip_sync_anomaly_detected=row["lip_sync_anomaly_detected"],
            lip_sync_confidence=Confidence(row["lip_sync_confidence"])
            if row["lip_sync_confidence"]
            else None,
            lip_sync_error=row["lip_sync_error"],
            reality_defender_score=float(row["reality_defender_score"])
            if row["reality_defender_score"]
            else None,
            reality_defender_verdict=Verdict(row["reality_defender_verdict"])
            if row["reality_defender_verdict"]
            else None,
            reality_defender_indicators=indicators or [],
            reality_defender_error=row["reality_defender_error"],
            combined_score=float(row["combined_score"]),
            is_deepfake=row["is_deepfake"],
            risk_level=RiskLevel(row["risk_level"]),
            detection_method=DetectionMethod(row["detection_method"]),
            limitations=row["limitations"] or [],
            processing_time_ms=row["processing_time_ms"] or 0,
            cost_cents=row["cost_cents"] or 0,
            analyzed_at=row["analyzed_at"],
        )
