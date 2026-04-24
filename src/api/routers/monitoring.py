"""Monitoring router — Monitor CRUD + mention listing + FTS search."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ...monitoring.exceptions import (
    AlertRuleLimitError,
    AlertRuleNotFoundError,
    ClassificationCapExceededError,
    MonitorLimitExceededError,
    MonitorNotFoundError,
    MonitoringError,
    WebhookDeliveryError,
)
from ...monitoring.models import DataSource
from ...monitoring.service import MonitoringService
from ..dependencies import (
    get_current_user_id,
    get_monitoring_service,
    get_webhook_delivery,
)
from ..rate_limit import limiter
from ..schemas_monitoring import (
    AlertEventResponse,
    AlertRuleResponse,
    ChangelogEntryResponse,
    ChangelogListResponse,
    ClassifyIntentRequest,
    ClassifyIntentResponse,
    CreateAlertRuleRequest,
    CreateMonitorRequest,
    MentionResponse,
    MentionSearchResponse,
    MonitorResponse,
    MonitorSummaryResponse,
    SaveToWorkspaceRequest,
    SaveToWorkspaceResponse,
    SentimentBucketResponse,
    SentimentTimeSeriesResponse,
    ShareOfVoiceEntryResponse,
    ShareOfVoiceResponse,
    TrendsCorrelationBucketResponse,
    TrendsCorrelationResponse,
    WeeklyDigestCreate,
    WeeklyDigestResponse,
    UpdateAlertRuleRequest,
    UpdateMonitorRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitors", tags=["monitoring"])


# 1. POST /v1/monitors — Create monitor
@router.post("", response_model=MonitorResponse, status_code=201)
@limiter.limit("30/minute")
async def create_monitor(
    request: Request,
    body: CreateMonitorRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    # Parse keywords as comma-separated string into list
    keywords = [k.strip() for k in body.keywords.split(",") if k.strip()]
    if not keywords:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_keywords", "message": "At least one keyword required"},
        )

    competitor_brands = [b.strip()[:100] for b in body.competitor_brands if b.strip()]

    try:
        monitor = await service.create_monitor(
            user_id=user_id,
            name=body.name,
            keywords=keywords,
            sources=body.sources,
            boolean_query=body.boolean_query,
            competitor_brands=competitor_brands,
        )
    except MonitorLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "monitor_limit_exceeded", "message": "Monitor limit exceeded"},
        )
    except MonitoringError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_sources", "message": str(exc)},
        )
    return MonitorResponse.from_monitor(monitor)


# 2. GET /v1/monitors — List user's monitors (enriched summary)
@router.get("", response_model=list[MonitorSummaryResponse])
@limiter.limit("30/minute")
async def list_monitors(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    return await service.list_monitors_enriched(user_id)


# 3. GET /v1/monitors/{monitor_id} — Get monitor details with mention count
@router.get("/{monitor_id}", response_model=MonitorResponse)
@limiter.limit("30/minute")
async def get_monitor(
    request: Request,
    monitor_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    try:
        monitor, count = await service.get_monitor_with_stats(monitor_id, user_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    return MonitorResponse.from_monitor(monitor, mention_count=count)


# 4. PUT /v1/monitors/{monitor_id} — Update monitor
@router.put("/{monitor_id}", response_model=MonitorResponse)
@limiter.limit("30/minute")
async def update_monitor(
    request: Request,
    monitor_id: UUID,
    body: UpdateMonitorRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    fields = body.model_dump(exclude_unset=True)

    # Convert keywords string to list if provided
    if "keywords" in fields and fields["keywords"] is not None:
        fields["keywords"] = [k.strip() for k in fields["keywords"].split(",") if k.strip()]

    # Validate competitor_brands if provided
    if "competitor_brands" in fields and fields["competitor_brands"] is not None:
        brands = fields["competitor_brands"]
        if len(brands) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "too_many_competitors", "message": "Maximum 10 competitor brands"},
            )
        fields["competitor_brands"] = [b.strip()[:100] for b in brands if b.strip()]

    # Track user edits for V2 auto-refinement conflict resolution
    fields["last_user_edit_at"] = datetime.now(tz=timezone.utc)

    try:
        monitor = await service.update_monitor(monitor_id, user_id, **fields)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    # Only trigger a backfill when query-relevant fields changed.
    # Non-query fields (name, is_active) don't warrant an external API crawl.
    _BACKFILL_TRIGGERS = {"keywords", "boolean_query", "sources"}
    if body.model_fields_set & _BACKFILL_TRIGGERS:
        task_client = getattr(request.app.state, "monitor_task_client", None)
        if task_client:
            try:
                await task_client.enqueue_monitor_run(
                    monitor_id=monitor.id, delay_seconds=0
                )
            except Exception:
                logger.warning(
                    "Failed to enqueue backfill for monitor %s", monitor.id
                )

    return MonitorResponse.from_monitor(monitor)


# 5. DELETE /v1/monitors/{monitor_id} — Delete monitor
@router.delete("/{monitor_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_monitor(
    request: Request,
    monitor_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    deleted = await service.delete_monitor(monitor_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )


# 6. GET /v1/monitors/{monitor_id}/mentions — Unified mention query (FTS + filters + sort)
@router.get("/{monitor_id}/mentions")
@limiter.limit("30/minute")
async def list_mentions(
    request: Request,
    monitor_id: UUID,
    q: str | None = Query(None, max_length=512),
    source: DataSource | None = None,
    sentiment: str | None = Query(None, description="positive|negative|neutral|mixed"),
    intent: str | None = Query(None, description="complaint|question|recommendation|purchase_signal|general_discussion"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: str = Query("published_at", description="published_at|engagement|relevance"),
    sort_order: str = Query("desc", description="asc|desc"),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    from ...monitoring.models import IntentLabel, SentimentLabel

    try:
        await service.get_monitor(monitor_id, user_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )

    sentiment_label = None
    if sentiment:
        try:
            sentiment_label = SentimentLabel(sentiment)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "invalid_sentiment", "message": f"Invalid sentiment: {sentiment}"},
            )

    intent_label: IntentLabel | None = None
    if intent:
        try:
            intent_label = IntentLabel(intent)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_intent",
                    "message": f"Invalid intent: {intent}. Valid values: {[e.value for e in IntentLabel]}",
                },
            )

    mentions, total_count = await service.query_mentions(
        user_id, monitor_id,
        q=q, source=source, sentiment=sentiment_label, intent=intent_label,
        date_from=date_from, date_to=date_to,
        sort_by=sort_by, sort_order=sort_order,
        limit=limit, offset=offset,
    )
    return {
        "data": [MentionResponse.from_mention(m) for m in mentions],
        "total": total_count,
    }


# 7. POST /v1/monitors/{monitor_id}/run — Run monitor now
@router.post("/{monitor_id}/run", status_code=202)
@limiter.limit("6/minute")
async def run_monitor_now(
    request: Request,
    monitor_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    try:
        monitor = await service.get_monitor(monitor_id, user_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    try:
        await service.enqueue_run(monitor, trigger="manual")
    except MonitoringError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "cooldown_active", "message": str(exc)},
        )
    # Dispatch to Cloud Tasks (matches update_monitor pattern)
    task_client = getattr(request.app.state, "monitor_task_client", None)
    if task_client:
        try:
            await task_client.enqueue_monitor_run(
                monitor_id=monitor_id, delay_seconds=0
            )
        except Exception:
            logger.warning(
                "Failed to enqueue Cloud Tasks run for monitor %s", monitor_id
            )
    return {"status": "enqueued", "monitor_id": str(monitor_id)}


# 8. GET /v1/monitors/{monitor_id}/runs — Run history
@router.get("/{monitor_id}/runs")
@limiter.limit("30/minute")
async def get_monitor_runs(
    request: Request,
    monitor_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: MonitoringService = Depends(get_monitoring_service),
) -> dict:
    """Get run history for a monitor."""
    from dataclasses import asdict

    try:
        await service.get_monitor(monitor_id, user_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )

    runs = await service.get_runs(
        monitor_id=monitor_id,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return {"data": [asdict(r) for r in runs]}


# ── Alert endpoints (PR-068) ──


# 9. POST /v1/monitors/{monitor_id}/alerts — Create alert rule
@router.post("/{monitor_id}/alerts", response_model=AlertRuleResponse, status_code=201)
@limiter.limit("30/minute")
async def create_alert_rule(
    request: Request,
    monitor_id: UUID,
    body: CreateAlertRuleRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    from ...common.url_validation import resolve_and_validate

    # Validate webhook URL (SSRF check at creation time)
    try:
        await resolve_and_validate(body.webhook_url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_webhook_url", "message": str(exc)},
        )

    max_rules = 999  # billing-strip: no tier gate on alert rule count
    try:
        rule = await service.create_alert_rule(
            monitor_id=monitor_id,
            user_id=user_id,
            rule_type=body.rule_type,
            config=body.config.model_dump(),
            webhook_url=body.webhook_url,
            cooldown_minutes=body.cooldown_minutes,
            max_rules=max_rules,
        )
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    except AlertRuleLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "rule_limit_exceeded", "message": f"Maximum {max_rules} alert rules per monitor"},
        )
    return AlertRuleResponse.from_rule(rule)


# 10. GET /v1/monitors/{monitor_id}/alerts — List alert rules
@router.get("/{monitor_id}/alerts", response_model=list[AlertRuleResponse])
@limiter.limit("30/minute")
async def list_alert_rules(
    request: Request,
    monitor_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    try:
        await service.get_monitor(monitor_id, user_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    rules = await service.list_alert_rules(monitor_id, user_id)
    return [AlertRuleResponse.from_rule(r) for r in rules]


# 11. PUT /v1/monitors/{monitor_id}/alerts/{alert_id} — Update alert rule
@router.put("/{monitor_id}/alerts/{alert_id}", response_model=AlertRuleResponse)
@limiter.limit("30/minute")
async def update_alert_rule(
    request: Request,
    monitor_id: UUID,
    alert_id: UUID,
    body: UpdateAlertRuleRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    fields = body.model_dump(exclude_unset=True)

    # Re-validate webhook URL if changed
    if "webhook_url" in fields and fields["webhook_url"] is not None:
        from ...common.url_validation import resolve_and_validate

        try:
            await resolve_and_validate(fields["webhook_url"])
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "invalid_webhook_url", "message": str(exc)},
            )

    # Convert SpikeConfig to dict if present
    if "config" in fields and fields["config"] is not None:
        fields["config"] = fields["config"].model_dump()

    try:
        rule = await service.update_alert_rule(alert_id, user_id, **fields)
    except AlertRuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "rule_not_found", "message": "Alert rule not found"},
        )
    return AlertRuleResponse.from_rule(rule)


# 12. DELETE /v1/monitors/{monitor_id}/alerts/{alert_id} — Delete alert rule
@router.delete("/{monitor_id}/alerts/{alert_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_alert_rule(
    request: Request,
    monitor_id: UUID,
    alert_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    deleted = await service.delete_alert_rule(alert_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "rule_not_found", "message": "Alert rule not found"},
        )


# 13. GET /v1/monitors/{monitor_id}/alerts/history — List alert events
@router.get("/{monitor_id}/alerts/history", response_model=list[AlertEventResponse])
@limiter.limit("30/minute")
async def list_alert_events(
    request: Request,
    monitor_id: UUID,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    try:
        await service.get_monitor(monitor_id, user_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    events = await service.list_alert_events(monitor_id, user_id, limit, offset)
    return [AlertEventResponse.from_event(e) for e in events]


# 14. POST /v1/monitors/{monitor_id}/alerts/{alert_id}/test — Test webhook
@router.post("/{monitor_id}/alerts/{alert_id}/test")
@limiter.limit("5/minute")
async def test_alert_webhook(
    request: Request,
    monitor_id: UUID,
    alert_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    from ...monitoring.alerts.delivery import WebhookDelivery

    delivery = get_webhook_delivery(request)
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "alerting_disabled", "message": "Alerting is not enabled"},
        )
    try:
        rule = await service.get_alert_rule(alert_id, user_id)
    except AlertRuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "rule_not_found", "message": "Alert rule not found"},
        )
    try:
        success = await delivery.send_test(rule)
    except WebhookDeliveryError as exc:
        return {"success": False, "error": str(exc)}
    except Exception:
        logger.exception("Test webhook failed for rule %s", alert_id)
        return {"success": False, "error": "Webhook delivery failed"}
    return {"success": success}


# ── Intelligence Layer Endpoints (PR-071) ──


# 15. GET /v1/monitors/{monitor_id}/sentiment — Sentiment time-series
@router.get("/{monitor_id}/sentiment", response_model=SentimentTimeSeriesResponse)
@limiter.limit("30/minute")
async def get_sentiment(
    request: Request,
    monitor_id: UUID,
    window: Literal["1d", "7d", "14d", "30d", "90d"] = "7d",
    granularity: Literal["1h", "6h", "1d"] = "1d",
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    try:
        buckets = await service.sentiment_time_series(
            monitor_id, user_id, window=window, granularity=granularity,
        )
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    return SentimentTimeSeriesResponse(
        monitor_id=monitor_id,
        window=window,
        granularity=granularity,
        buckets=[
            SentimentBucketResponse(
                period_start=b.period_start,
                avg_sentiment=b.avg_sentiment,
                mention_count=b.mention_count,
                positive_count=b.positive_count,
                negative_count=b.negative_count,
                neutral_count=b.neutral_count,
                mixed_count=b.mixed_count,
            )
            for b in buckets
        ],
    )


# 16. POST /v1/monitors/{monitor_id}/classify-intent — On-demand intent classification
@router.post("/{monitor_id}/classify-intent", response_model=ClassifyIntentResponse)
@limiter.limit("30/minute")
async def classify_intent(
    request: Request,
    monitor_id: UUID,
    body: ClassifyIntentRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    try:
        count = await service.classify_intents(
            monitor_id, user_id, mention_ids=body.mention_ids,
        )
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    except ClassificationCapExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "classification_cap_exceeded",
                "message": "Daily classification limit reached (1000/monitor)",
            },
        )
    return ClassifyIntentResponse(classified_count=count)


# 18. GET /v1/monitors/{monitor_id}/share-of-voice — Share of Voice
@router.get("/{monitor_id}/share-of-voice", response_model=ShareOfVoiceResponse)
@limiter.limit("30/minute")
async def get_share_of_voice(
    request: Request,
    monitor_id: UUID,
    window: Literal["7d", "14d", "30d", "90d"] = "30d",
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    _WINDOW_DAYS = {"7d": 7, "14d": 14, "30d": 30, "90d": 90}
    window_days = _WINDOW_DAYS[window]
    try:
        entries = await service.get_share_of_voice(
            monitor_id, user_id, window_days=window_days,
        )
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    return ShareOfVoiceResponse(
        monitor_id=monitor_id,
        window_days=window_days,
        entries=[
            ShareOfVoiceEntryResponse(
                brand=e.brand,
                mention_count=e.mention_count,
                percentage=e.percentage,
                sentiment_avg=e.sentiment_avg,
            )
            for e in entries
        ],
    )


# 19. GET /v1/monitors/{monitor_id}/trends-correlation — Google Trends correlation
@router.get("/{monitor_id}/trends-correlation", response_model=TrendsCorrelationResponse)
@limiter.limit("30/minute")
async def get_trends_correlation(
    request: Request,
    monitor_id: UUID,
    window_days: int = Query(30, ge=1, le=90, description="Lookback window in days"),
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    _DAYS_TO_WINDOW = {7: "7d", 14: "14d", 30: "30d", 90: "90d"}
    window = _DAYS_TO_WINDOW.get(window_days, "30d")
    try:
        result = await service.get_trends_correlation(
            monitor_id, user_id, window=window,
        )
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    return TrendsCorrelationResponse(
        monitor_id=monitor_id,
        window_days=window_days,
        keyword=result.keyword,
        correlation_coefficient=result.correlation_coefficient,
        buckets=[
            TrendsCorrelationBucketResponse(
                period_start=b.period_start,
                mention_count=b.mention_count,
                google_trends_score=b.google_trends_score,
            )
            for b in result.buckets
        ],
    )


# 20. POST /v1/monitors/{monitor_id}/digests — Persist weekly digest
@router.post("/{monitor_id}/digests", response_model=WeeklyDigestResponse, status_code=201)
@limiter.limit("30/minute")
async def create_weekly_digest(
    request: Request,
    monitor_id: UUID,
    body: WeeklyDigestCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    from datetime import datetime, timezone
    from ...monitoring.models import WeeklyDigestRecord
    from uuid import uuid4

    try:
        monitor = await service.get_monitor(monitor_id, user_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )

    digest = WeeklyDigestRecord(
        id=uuid4(),
        monitor_id=monitor_id,
        client_id=monitor.client_id,
        week_ending=body.week_ending,
        stories=body.stories,
        executive_summary=body.executive_summary,
        action_items=body.action_items,
        dqs_score=None,
        iteration_count=body.iteration_count,
        avg_story_delta=body.avg_story_delta,
        generated_at=datetime.now(timezone.utc),
        digest_markdown=body.digest_markdown,
    )
    await service._repo.save_weekly_digest(digest)
    return WeeklyDigestResponse.from_digest(digest)


# I: GET /v1/monitors/{monitor_id}/digests — List recent digests
@router.get("/{monitor_id}/digests", response_model=list[WeeklyDigestResponse])
@limiter.limit("30/minute")
async def list_digests(
    request: Request,
    monitor_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
    limit: int = Query(10, ge=1, le=50),
):
    # IDOR check: verify user owns this monitor
    try:
        await service.get_monitor(monitor_id, user_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )

    digests = await service._repo.list_weekly_digests(monitor_id, limit=limit)
    return [WeeklyDigestResponse.from_digest(d) for d in digests]


# 21. POST /v1/monitors/{monitor_id}/mentions/save-to-workspace — Save to workspace
@router.post(
    "/{monitor_id}/mentions/save-to-workspace",
    response_model=SaveToWorkspaceResponse,
)
@limiter.limit("30/minute")
async def save_to_workspace(
    request: Request,
    monitor_id: UUID,
    body: SaveToWorkspaceRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    # Validate collection exists AND belongs to user (via conversation ownership)
    workspace_repo = getattr(request.app.state, "workspace_repository", None)
    if not workspace_repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "workspace_unavailable", "message": "Workspace service not configured"},
        )
    collection = await workspace_repo.get_collection(body.collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "collection_not_found", "message": "Collection not found"},
        )
    # Verify ownership: collection → conversation → user
    conversation_repo = getattr(request.app.state, "conversation_repository", None)
    if conversation_repo:
        conv = await conversation_repo.get_by_id(collection.conversation_id, user_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "collection_not_found", "message": "Collection not found"},
            )

    if body.mention_ids and len(body.mention_ids) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "too_many_mentions",
                "message": "Max 500 mentions per save. Use filters to narrow selection.",
            },
        )

    # Validate annotation lengths
    if body.annotations:
        for key, val in body.annotations.items():
            if len(val) > 500:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "annotation_too_long", "message": f"Annotation for {key} exceeds 500 chars"},
                )

    try:
        saved = await service.save_mentions_to_workspace(
            monitor_id, user_id,
            collection_id=body.collection_id,
            mention_ids=body.mention_ids,
            annotations=body.annotations,
        )
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    return SaveToWorkspaceResponse(
        saved_count=saved,
        collection_id=body.collection_id,
    )


# ── Changelog (V2 self-optimizing refinement) ──


@router.get("/{monitor_id}/changelog", response_model=ChangelogListResponse)
@limiter.limit("30/minute")
async def get_changelog(
    request: Request,
    monitor_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    """Get changelog entries for a monitor."""
    try:
        entries, total = await service.get_changelog(monitor_id, user_id, limit=limit, offset=offset)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "monitor_not_found", "message": "Monitor not found"},
        )
    return ChangelogListResponse(
        entries=[
            ChangelogEntryResponse(
                id=e.id,
                monitor_id=e.monitor_id,
                change_type=e.change_type,
                change_detail=e.change_detail,
                rationale=e.rationale,
                autonomy_level=e.autonomy_level,
                status=e.status,
                applied_by=e.applied_by,
                analysis_run_id=e.analysis_run_id,
                created_at=e.created_at,
            )
            for e in entries
        ],
        total=total,
    )


@router.post("/{monitor_id}/changelog/{entry_id}/approve", response_model=ChangelogEntryResponse)
@limiter.limit("30/minute")
async def approve_changelog_entry(
    request: Request,
    monitor_id: UUID,
    entry_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    """Approve a pending changelog entry and apply its change."""
    try:
        entry = await service.approve_changelog_entry(monitor_id, entry_id, user_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Monitor or changelog entry not found"},
        )
    return ChangelogEntryResponse(
        id=entry.id,
        monitor_id=entry.monitor_id,
        change_type=entry.change_type,
        change_detail=entry.change_detail,
        rationale=entry.rationale,
        autonomy_level=entry.autonomy_level,
        status=entry.status,
        applied_by=entry.applied_by,
        analysis_run_id=entry.analysis_run_id,
        created_at=entry.created_at,
    )


@router.post("/{monitor_id}/changelog/{entry_id}/reject", response_model=ChangelogEntryResponse)
@limiter.limit("30/minute")
async def reject_changelog_entry(
    request: Request,
    monitor_id: UUID,
    entry_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MonitoringService = Depends(get_monitoring_service),
):
    """Reject a pending changelog entry."""
    try:
        entry = await service.reject_changelog_entry(monitor_id, entry_id, user_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Monitor or changelog entry not found"},
        )
    return ChangelogEntryResponse(
        id=entry.id,
        monitor_id=entry.monitor_id,
        change_type=entry.change_type,
        change_detail=entry.change_detail,
        rationale=entry.rationale,
        autonomy_level=entry.autonomy_level,
        status=entry.status,
        applied_by=entry.applied_by,
        analysis_run_id=entry.analysis_run_id,
        created_at=entry.created_at,
    )
