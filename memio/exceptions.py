class MemioError(Exception):
    """Base exception for all memio errors."""
    pass


class ProviderError(MemioError):
    """Wraps provider SDK exceptions."""

    def __init__(self, provider: str, operation: str, cause: Exception):
        self.provider = provider
        self.operation = operation
        self.cause = cause
        super().__init__(f"[{provider}] {operation} failed: {cause}")
