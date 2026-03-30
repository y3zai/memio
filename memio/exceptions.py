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
        hint: Optional guidance on what to do instead (e.g. "use delete_all").
    """

    def __init__(self, provider: str, operation: str, hint: str = ""):
        self.hint = hint

        message = f"[{provider}] {operation} is not supported"
        if hint:
            message += f": {hint}"

        cause = NotImplementedError(message)
        super().__init__(provider, operation, cause)
        Exception.__init__(self, message)
