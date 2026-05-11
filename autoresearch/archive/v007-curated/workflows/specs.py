from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


RunScript = Callable[..., None]
RunSessionEvaluator = Callable[[str, Path, Path, Path, str], Optional[dict]]


@dataclass(frozen=True)
class WorkflowConfig:
    subdirs: list[str]
    default_timeout: int
    multiturn_timeout: int
    stall_limit: int
    default_client: str
    default_context: str
    fresh_max_turns: int | None = None
    multiturn_max_turns: int | None = None
    max_wall_time_seconds: int | None = None


@dataclass(frozen=True)
class FindingsPromotionConfig:
    title: str
    confirmed_threshold: int
    repeated_threshold: int


@dataclass(frozen=True)
class WorkflowSpec:
    name: str
    config: WorkflowConfig
    config_dir_name: str
    configure_env: Callable[[str], None]
    pre_summary_hooks: Callable[[Path, str, RunScript], None]
    snapshot_evaluations: Callable[[Path, RunSessionEvaluator], dict[str, object]]
    completion_guard: Callable[[dict[str, object]], tuple[str | None, str | None]]
    list_deliverables: Callable[[Path], list[str]]
    augment_quality_metrics: Callable[[list[dict], dict], None]
    count_findings: Callable[[str], int]
    findings_promotion: FindingsPromotionConfig
    # Optional post-session HTML+PDF render hook. When set, runtime/post_session.py
    # invokes it after summarize_session. Defaults None (lane skips auto-render).
    # Mirrors the v006 spec field; lanes that opt in pass a lambda calling
    # render_report.py via the harness's run_script convention.
    render_report: Callable[[Path, str, RunScript], None] | None = None
