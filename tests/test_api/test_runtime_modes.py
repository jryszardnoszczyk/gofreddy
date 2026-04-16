"""Runtime mode resolution and task-client policy tests."""

from __future__ import annotations

import pytest

from src.api.dependencies import resolve_runtime_modes
from src.jobs.config import JobsConfig
from src.jobs.task_client import CloudTasksClient, MockTaskClient, create_task_client


def test_resolver_uses_non_production_defaults_when_modes_missing() -> None:
    modes = resolve_runtime_modes({"ENVIRONMENT": "development"})

    assert modes.environment == "development"
    assert modes.externals_mode == "real"
    assert modes.task_client_mode == "mock"


def test_resolver_rejects_invalid_externals_mode() -> None:
    with pytest.raises(RuntimeError, match="Invalid EXTERNALS_MODE"):
        resolve_runtime_modes({"ENVIRONMENT": "development", "EXTERNALS_MODE": "bad"})


def test_resolver_rejects_invalid_task_client_mode() -> None:
    with pytest.raises(RuntimeError, match="Invalid TASK_CLIENT_MODE"):
        resolve_runtime_modes({"ENVIRONMENT": "development", "TASK_CLIENT_MODE": "bad"})


def test_resolver_rejects_production_missing_externals_mode() -> None:
    with pytest.raises(RuntimeError, match="EXTERNALS_MODE"):
        resolve_runtime_modes({"ENVIRONMENT": "production", "TASK_CLIENT_MODE": "cloud", "CLOUD_TASKS_SA": "sa@example.com"})


def test_resolver_rejects_production_missing_task_client_mode() -> None:
    with pytest.raises(RuntimeError, match="TASK_CLIENT_MODE"):
        resolve_runtime_modes({"ENVIRONMENT": "production", "EXTERNALS_MODE": "real"})


def test_resolver_rejects_production_fake_externals() -> None:
    with pytest.raises(RuntimeError, match="EXTERNALS_MODE=real"):
        resolve_runtime_modes(
            {
                "ENVIRONMENT": "production",
                "EXTERNALS_MODE": "fake",
                "TASK_CLIENT_MODE": "cloud",
                "CLOUD_TASKS_SA": "sa@example.com",
            }
        )


def test_resolver_rejects_production_mock_task_client() -> None:
    with pytest.raises(RuntimeError, match="TASK_CLIENT_MODE=cloud"):
        resolve_runtime_modes(
            {
                "ENVIRONMENT": "production",
                "EXTERNALS_MODE": "real",
                "TASK_CLIENT_MODE": "mock",
            }
        )


def test_resolver_rejects_cloud_task_mode_without_service_account() -> None:
    with pytest.raises(RuntimeError, match="CLOUD_TASKS_SA"):
        resolve_runtime_modes(
            {
                "ENVIRONMENT": "development",
                "EXTERNALS_MODE": "real",
                "TASK_CLIENT_MODE": "cloud",
            }
        )


def test_resolver_normalizes_uppercase_production_modes() -> None:
    modes = resolve_runtime_modes(
        {
            "ENVIRONMENT": "PRODUCTION",
            "EXTERNALS_MODE": "REAL",
            "TASK_CLIENT_MODE": "CLOUD",
            "CLOUD_TASKS_SA": "sa@example.com",
        }
    )

    assert modes.environment == "production"
    assert modes.externals_mode == "real"
    assert modes.task_client_mode == "cloud"


def test_resolver_normalizes_mixed_case_non_production_modes() -> None:
    modes = resolve_runtime_modes(
        {
            "ENVIRONMENT": "DeVelopMent",
            "EXTERNALS_MODE": "FaKe",
            "TASK_CLIENT_MODE": "MoCk",
        }
    )

    assert modes.environment == "development"
    assert modes.externals_mode == "fake"
    assert modes.task_client_mode == "mock"


def test_task_client_factory_returns_mock_client() -> None:
    client = create_task_client("mock", JobsConfig())

    assert isinstance(client, MockTaskClient)


def test_task_client_factory_returns_cloud_client_when_config_present() -> None:
    config = JobsConfig(service_account="tasks@example.com")

    client = create_task_client("cloud", config)

    assert isinstance(client, CloudTasksClient)


def test_task_client_factory_rejects_cloud_client_without_service_account() -> None:
    config = JobsConfig(service_account="")

    with pytest.raises(RuntimeError, match="CLOUD_TASKS_SA"):
        create_task_client("cloud", config)
