"""Common exceptions shared across modules."""


class PoolExhaustedError(Exception):
    """Raised when the database connection pool is exhausted."""

    def __init__(self, pool_size: int, timeout_seconds: float) -> None:
        self.pool_size = pool_size
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Connection pool exhausted (size={pool_size}) after {timeout_seconds}s"
        )
