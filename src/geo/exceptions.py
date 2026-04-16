"""GEO audit exceptions."""


class GeoAuditError(Exception):
    """Non-recoverable audit pipeline error."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class ProviderUnavailableError(Exception):
    """External provider (Cloro, Gemini) is unavailable."""

    def __init__(self, provider: str, message: str = ""):
        self.provider = provider
        super().__init__(f"{provider} unavailable: {message}" if message else f"{provider} unavailable")
