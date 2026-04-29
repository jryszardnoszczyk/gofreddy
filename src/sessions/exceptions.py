"""Session domain exceptions."""

from uuid import UUID


class SessionError(Exception):
    """Base exception for session operations."""


class SessionNotFound(SessionError):
    """Session not found or user doesn't own it."""

    def __init__(self, session_id: UUID) -> None:
        self.session_id = session_id
        super().__init__(f"Session {session_id} not found")


class SessionAlreadyCompleted(SessionError):
    """Session is already completed and cannot be modified."""

    def __init__(self, session_id: UUID) -> None:
        self.session_id = session_id
        super().__init__(f"Session {session_id} is already completed")


class IterationAlreadyExists(SessionError):
    """An iteration with the same (session_id, iteration_number) already exists."""

    def __init__(self, session_id: UUID, iteration_number: int) -> None:
        self.session_id = session_id
        self.iteration_number = iteration_number
        super().__init__(
            f"Iteration {iteration_number} already exists for session {session_id}"
        )
