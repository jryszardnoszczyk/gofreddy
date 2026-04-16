"""Evaluation module exceptions."""


class EvaluationError(Exception):
    """Base exception for evaluation failures."""

    def __init__(self, message: str, *, domain: str | None = None) -> None:
        self.domain = domain
        super().__init__(message)


class StructuralFailure(EvaluationError):
    """Raised when structural gate validation fails."""

    def __init__(self, domain: str, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Structural gate failed for {domain}: {reason}", domain=domain)


class JudgeError(EvaluationError):
    """Raised when an LLM judge fails to produce a valid score."""

    def __init__(self, judge: str, criterion: str, reason: str) -> None:
        self.judge = judge
        self.criterion = criterion
        self.reason = reason
        super().__init__(f"Judge {judge} failed on {criterion}: {reason}")
