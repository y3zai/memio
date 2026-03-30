from importlib.metadata import PackageNotFoundError, version

from memio.client import Memio
from memio.exceptions import MemioError, NotFoundError, NotSupportedError, ProviderError
from memio.models import Document, Fact, GraphResult, Message, Triple
from memio.protocols import DocumentStore, FactStore, GraphStore, HistoryStore

try:
    __version__ = version("memio")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "Memio",
    "FactStore",
    "HistoryStore",
    "DocumentStore",
    "GraphStore",
    "Fact",
    "Message",
    "Document",
    "Triple",
    "GraphResult",
    "MemioError",
    "ProviderError",
    "NotSupportedError",
    "NotFoundError",
]
