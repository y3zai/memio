class MemioError(Exception):
    """Base exception for all memio errors."""
    pass


class ProviderError(MemioError):
    """Wraps provider SDK exceptions with context.

    Attributes:
        provider: Name of the provider (e.g. "mem0", "zep", "chroma").
        operation: Name of the operation that failed (e.g. "add", "search").
        cause: The original exception from the provider SDK.
    """

    def __init__(self, provider: str, operation: str, cause: Exception):
        self.provider = provider
        self.operation = operation
        self.cause = cause
        super().__init__(f"[{provider}] {operation} failed: {cause}")
