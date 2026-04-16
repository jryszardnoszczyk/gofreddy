"""Comment sync worker — fetches comments from Xpoz and upserts to DB."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ...common.cost_recorder import cost_recorder as _cost_recorder, extract_gemini_usage
from ..models import DataSource
from .models import CommentSyncResult
from .repository import PostgresCommentRepository

if TYPE_CHECKING:
    from google.genai import Client as GenaiClient

logger = logging.getLogger(__name__)

MAX_POSTS_PER_SYNC = 50

_CLASSIFY_SYSTEM = """You are a comment classifier. For each comment, determine:
1. sentiment: positive, negative, neutral, or mixed
2. sentiment_score: float from -1.0 (very negative) to 1.0 (very positive)
3. is_spam: true if the comment is spam, self-promotion, or bot-generated

Respond with JSON array: [{"id": "<comment_id>", "sentiment": "<label>", "sentiment_score": <float>, "is_spam": <bool>}]
"""

_VALID_SENTIMENTS = {"positive", "negative", "neutral", "mixed"}


class CommentSyncWorker:
    def __init__(
        self,
        xpoz_adapter,
        repository: PostgresCommentRepository,
        genai_client: GenaiClient | None = None,
        contact_service=None,
    ):
        self._xpoz = xpoz_adapter
        self._repository = repository
        self._genai = genai_client
        self._contact_service = contact_service

    async def sync_connection_comments(
        self, org_id: UUID, connection_id: UUID, platform: str, post_ids: list[str],
    ) -> CommentSyncResult:
        synced = 0
        skipped = 0
        errors = 0

        for post_id in post_ids[:MAX_POSTS_PER_SYNC]:
            try:
                comments = await self._xpoz.get_post_comments(
                    post_id, platform=DataSource(platform),
                )
                if not comments:
                    skipped += 1
                    continue

                tuples = []
                seen_authors: set[str] = set()
                for c in comments:
                    tuples.append((
                        platform,
                        post_id,
                        c.comment_id,
                        getattr(c, "author_username", None),
                        getattr(c, "author_name", None) if hasattr(c, "author_name") else None,
                        None,  # avatar_url
                        c.content,
                        c.published_at,
                        c.metadata.get("parent_comment_id") if c.metadata else None,
                        c.like_count,
                    ))
                    if c.author_username and c.author_username not in seen_authors:
                        seen_authors.add(c.author_username)
                        if self._contact_service:
                            try:
                                await self._contact_service.record_interaction(
                                    org_id, platform, c.author_username,
                                    display_name=getattr(c, "author_name", None) if hasattr(c, "author_name") else None,
                                )
                            except Exception:
                                logger.warning("contact_record_failed author=%s", c.author_username)

                count = await self._repository.upsert_comments(org_id, connection_id, tuples)
                synced += count
            except Exception:
                logger.exception("sync_post_comments_failed post_id=%s", post_id)
                errors += 1

        return CommentSyncResult(synced=synced, skipped=skipped, errors=errors)

    # ── Classification ──

    async def classify_comments(self, limit: int = 200) -> int:
        """Classify unclassified comments via Gemini Flash-Lite batch call.

        Returns the number of comments successfully classified.
        On Gemini failure: logs warning, leaves defaults, non-fatal.
        """
        if self._genai is None:
            logger.warning("classify_comments: no genai client configured")
            return 0

        comments = await self._repository.get_unclassified(limit)
        if not comments:
            return 0

        # Filter out empty/null bodies
        classifiable = [c for c in comments if c.body and c.body.strip()]
        if not classifiable:
            return 0

        try:
            results = await self._classify_batch(classifiable)
        except Exception:
            logger.warning("classify_comments_gemini_failed", exc_info=True)
            return 0

        classified = 0
        for comment_id, classification in results.items():
            try:
                await self._repository.update_classification(
                    comment_id,
                    sentiment_label=classification.get("sentiment"),
                    sentiment_score=classification.get("sentiment_score"),
                    is_spam=classification.get("is_spam", False),
                )
                classified += 1
            except Exception:
                logger.warning("classify_update_failed comment_id=%s", comment_id)

        return classified

    async def _classify_batch(
        self, comments: list[Any],
    ) -> dict[UUID, dict[str, Any]]:
        """Single Gemini call to classify a batch of comments."""
        from google.genai import types as genai_types

        from ...common.model_router import get_model_for_task

        model = get_model_for_task("comment_classification")

        inputs = [
            {"id": str(c.id), "text": (c.body or "")[:500]}
            for c in comments
        ]

        config = genai_types.GenerateContentConfig(
            system_instruction=_CLASSIFY_SYSTEM,
            response_mime_type="application/json",
            temperature=0.1,
        )

        response = await asyncio.wait_for(
            self._genai.aio.models.generate_content(
                model=model,
                contents=json.dumps(inputs, ensure_ascii=False),
                config=config,
            ),
            timeout=30,
        )

        t_in, t_out, cost = extract_gemini_usage(response, model)
        await _cost_recorder.record(
            "gemini", "comment_classify",
            tokens_in=t_in, tokens_out=t_out, cost_usd=cost, model=model,
        )

        if response.candidates and response.candidates[0].finish_reason not in (
            None, "STOP",
        ):
            logger.warning(
                "Gemini comment classification terminated: %s",
                response.candidates[0].finish_reason,
            )
            return {}

        if not response.text:
            return {}

        return self._parse_classification(response.text, comments)

    def _parse_classification(
        self, text: str, comments: list[Any],
    ) -> dict[UUID, dict[str, Any]]:
        """Parse Gemini JSON response into comment_id -> classification mapping."""
        valid_ids = {str(c.id) for c in comments}
        results: dict[UUID, dict[str, Any]] = {}

        try:
            items: list[dict[str, Any]] = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse comment classification JSON response")
            return {}

        if not isinstance(items, list):
            return {}

        for item in items:
            if not isinstance(item, dict):
                continue
            cid = item.get("id", "")
            sentiment = item.get("sentiment", "")
            if cid not in valid_ids or sentiment not in _VALID_SENTIMENTS:
                continue
            try:
                score = float(item.get("sentiment_score", 0.0))
                score = max(-1.0, min(1.0, score))
            except (TypeError, ValueError):
                score = 0.0
            results[UUID(cid)] = {
                "sentiment": sentiment,
                "sentiment_score": score,
                "is_spam": bool(item.get("is_spam", False)),
            }

        return results
