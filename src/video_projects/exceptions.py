"""Video project domain exceptions."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


class VideoProjectError(Exception):
    """Base video project error."""


@dataclass(slots=True)
class VideoProjectNotFoundError(VideoProjectError):
    project_id: UUID

    def __str__(self) -> str:
        return f"Video project {self.project_id} not found"


@dataclass(slots=True)
class VideoProjectSceneNotFoundError(VideoProjectError):
    scene_id: UUID

    def __str__(self) -> str:
        return f"Video project scene {self.scene_id} not found"


@dataclass(slots=True)
class VideoProjectRevisionConflictError(VideoProjectError):
    project_id: UUID
    expected_revision: int
    actual_revision: int

    def __str__(self) -> str:
        return (
            f"Video project {self.project_id} revision conflict: "
            f"expected {self.expected_revision}, actual {self.actual_revision}"
        )


class VideoProjectInvalidStateError(VideoProjectError):
    """Raised when a project mutation is invalid in the current state."""

