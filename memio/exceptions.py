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


class NotSupportedError(ProviderError):
    """Raised when a provider does not support a specific operation.

    Attributes:
        provider: Name of the provider (e.g. "mem0", "zep").
        operation: Name of the unsupported operation (e.g. "delete").
    """

    def __init__(self, provider: str, operation: str):
        super().__init__(provider, operation, NotImplementedError(
            f"{provider} does not support {operation}"
        ))
