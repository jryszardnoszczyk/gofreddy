from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.rate_limit import limiter
from src.api.routers.evaluation import router
from src.evaluation.models import DimensionResult, ScoringType


TEST_USER_ID = uuid4()


@pytest.fixture
def mock_evaluation_service():
    service = AsyncMock()
    service.critique_session.return_value = [
        DimensionResult(
            criterion_id="GEO-1",
            scoring_type=ScoringType.GRADIENT,
            raw_score=4,
            normalized_score=0.75,
            reasoning="Answer-first block is present and specific.",
            evidence=["The page opens with a direct answer."],
            model="judge-model",
        )
    ]
    return service


@pytest.fixture
def app(mock_evaluation_service):
    from src.api.dependencies import get_current_user_id

    test_app = FastAPI()
    test_app.state.limiter = limiter
    test_app.state.evaluation_service = mock_evaluation_service

    async def override_user_id():
        return TEST_USER_ID

    test_app.dependency_overrides[get_current_user_id] = override_user_id
    test_app.include_router(router, prefix="/v1")
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_critique_endpoint_returns_trusted_dimension_payload(client, mock_evaluation_service) -> None:
    response = client.post(
        "/v1/evaluation/critique",
        json={
            "criteria": [
                {
                    "criterion_id": "GEO-1",
                    "rubric_prompt": "Judge GEO-1",
                    "output_text": "A direct answer block.",
                    "source_text": "Original page data.",
                    "scoring_type": "gradient",
                }
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["criterion_id"] == "GEO-1"
    assert data["results"][0]["normalized_score"] == 0.75
    assert data["results"][0]["model"] == "judge-model"
    mock_evaluation_service.critique_session.assert_awaited_once()
