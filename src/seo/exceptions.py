"""SEO audit exceptions."""


class SeoAuditError(Exception):
    """Non-recoverable SEO audit error."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class DataForSeoError(Exception):
    """DataForSEO provider error."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)
