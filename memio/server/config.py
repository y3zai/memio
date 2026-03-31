"""Configuration loading — YAML + env var interpolation + provider factories."""

from __future__ import annotations

import importlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from memio.client import Memio

_ENV_VAR_RE = re.compile(r"\$\{(\w+)\}")


# ── Config dataclasses ───────────────────────────────────────────────


@dataclass
class StoreConfig:
    provider: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8080
    api_key: str | None = None
    stores: dict[str, StoreConfig] = field(default_factory=dict)


# ── YAML + env var loading ───────────────────────────────────────────


def _interpolate_env(value: Any) -> Any:
    """Replace ``${ENV_VAR}`` placeholders in strings. Fail-fast on missing."""
    if not isinstance(value, str):
        return value

    def _replace(match: re.Match) -> str:
        var = match.group(1)
        val = os.environ.get(var)
        if val is None:
            raise RuntimeError(
                f"Environment variable '{var}' is not set "
                f"(referenced in config as '${{{var}}}')"
            )
        return val

    return _ENV_VAR_RE.sub(_replace, value)


def _interpolate_dict(d: dict) -> dict:
    return {k: _interpolate_env(v) if isinstance(v, str) else
            (_interpolate_dict(v) if isinstance(v, dict) else v)
            for k, v in d.items()}


def load_config(path: str | None = None) -> ServerConfig:
    """Load server config from YAML file + env var overrides."""
    config_path = path or os.environ.get("MEMIO_CONFIG", "memio-server.yaml")

    raw: dict[str, Any] = {}
    if Path(config_path).exists():
        with open(config_path) as f:
            raw = yaml.safe_load(f) or {}

    server = raw.get("server", {})
    auth = raw.get("auth", {})
    stores_raw = raw.get("stores", {})

    # Parse store configs with env interpolation
    stores: dict[str, StoreConfig] = {}
    for store_type, store_def in stores_raw.items():
        if store_def and isinstance(store_def, dict):
            cfg = _interpolate_dict(store_def.get("config", {}))
            stores[store_type] = StoreConfig(
                provider=store_def["provider"],
                config=cfg,
            )

    # Build config with env var overrides
    api_key = os.environ.get("MEMIO_API_KEY") or _interpolate_env(
        auth.get("api_key")
    )
    host = os.environ.get("MEMIO_HOST") or _interpolate_env(
        server.get("host", "127.0.0.1")
    )
    port = os.environ.get("MEMIO_PORT") or _interpolate_env(
        server.get("port", 8080)
    )
    return ServerConfig(
        host=str(host),
        port=int(port),
        api_key=api_key if api_key else None,
        stores=stores,
    )


# ── Provider factories ───────────────────────────────────────────────

# Each factory takes a config dict and returns an adapter instance.

ProviderFactory = Callable[[dict[str, Any]], Any]

PROVIDER_FACTORIES: dict[str, dict[str, ProviderFactory]] = {}


def _register(provider: str, store_type: str, factory: ProviderFactory) -> None:
    PROVIDER_FACTORIES.setdefault(provider, {})[store_type] = factory


def _lazy_import(module_path: str, class_name: str) -> type:
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


# ── Mem0 ──


def _build_mem0_fact(cfg: dict) -> Any:
    cls = _lazy_import("memio.providers.mem0", "Mem0FactAdapter")
    # cfg is the inner config dict; pass non-api_key entries as provider config
    api_key = cfg.get("api_key")
    extra = {k: v for k, v in cfg.items() if k != "api_key"} or None
    return cls(api_key=api_key, config=extra)


def _build_mem0_graph(cfg: dict) -> Any:
    cls = _lazy_import("memio.providers.mem0", "Mem0GraphAdapter")
    api_key = cfg.get("api_key")
    extra = {k: v for k, v in cfg.items() if k != "api_key"} or None
    return cls(api_key=api_key, config=extra)


_register("mem0", "facts", _build_mem0_fact)
_register("mem0", "graph", _build_mem0_graph)


# ── Zep ──


def _build_zep_fact(cfg: dict) -> Any:
    cls = _lazy_import("memio.providers.zep", "ZepFactAdapter")
    return cls(api_key=cfg.get("api_key"))


def _build_zep_history(cfg: dict) -> Any:
    cls = _lazy_import("memio.providers.zep", "ZepHistoryAdapter")
    return cls(api_key=cfg.get("api_key"))


def _build_zep_graph(cfg: dict) -> Any:
    cls = _lazy_import("memio.providers.zep", "ZepGraphAdapter")
    return cls(api_key=cfg.get("api_key"))


_register("zep", "facts", _build_zep_fact)
_register("zep", "history", _build_zep_history)
_register("zep", "graph", _build_zep_graph)


# ── Chroma ──


def _build_chroma_document(cfg: dict) -> Any:
    import chromadb

    persist_dir = cfg.get("persist_directory")
    if persist_dir:
        client = chromadb.PersistentClient(path=persist_dir)
    else:
        client = chromadb.EphemeralClient()

    cls = _lazy_import("memio.providers.chroma", "ChromaDocumentAdapter")
    return cls(client=client, collection_name=cfg["collection_name"])


_register("chroma", "documents", _build_chroma_document)


# ── Letta ──


def _build_letta_adapter(cfg: dict, class_name: str) -> Any:
    if "agent_id" not in cfg:
        raise ValueError("Letta provider requires 'agent_id' in config")
    cls = _lazy_import("memio.providers.letta", class_name)
    return cls(
        agent_id=cfg["agent_id"],
        api_key=cfg.get("api_key"),
        base_url=cfg.get("base_url"),
    )


def _build_letta_fact(cfg: dict) -> Any:
    return _build_letta_adapter(cfg, "LettaFactAdapter")


def _build_letta_history(cfg: dict) -> Any:
    return _build_letta_adapter(cfg, "LettaHistoryAdapter")


def _build_letta_document(cfg: dict) -> Any:
    return _build_letta_adapter(cfg, "LettaDocumentAdapter")


_register("letta", "facts", _build_letta_fact)
_register("letta", "history", _build_letta_history)
_register("letta", "documents", _build_letta_document)


# ── Qdrant ──


def _build_qdrant_document(cfg: dict) -> Any:
    from qdrant_client import AsyncQdrantClient

    client = AsyncQdrantClient(
        url=cfg.get("url"),
        api_key=cfg.get("api_key"),
        location=cfg.get("location", ":memory:"),
    )
    cls = _lazy_import("memio.providers.qdrant", "QdrantDocumentAdapter")
    return cls(client=client, collection_name=cfg["collection_name"])


_register("qdrant", "documents", _build_qdrant_document)


# ── Supermemory ──


def _build_supermemory_fact(cfg: dict) -> Any:
    cls = _lazy_import("memio.providers.supermemory", "SupermemoryFactAdapter")
    return cls(api_key=cfg.get("api_key"))


def _build_supermemory_document(cfg: dict) -> Any:
    cls = _lazy_import("memio.providers.supermemory", "SupermemoryDocumentAdapter")
    return cls(api_key=cfg.get("api_key"), container_tag=cfg.get("container_tag"))


_register("supermemory", "facts", _build_supermemory_fact)
_register("supermemory", "documents", _build_supermemory_document)


# ── Build Memio from config ──────────────────────────────────────────


def build_memio_from_config(config: ServerConfig) -> Memio:
    """Instantiate a Memio client from a ServerConfig."""
    if not config.stores:
        raise ValueError(
            "No stores configured. Add at least one store to your "
            "memio-server.yaml (or set MEMIO_CONFIG to point to your config file)."
        )

    adapters: dict[str, Any] = {}

    for store_type, store_cfg in config.stores.items():
        provider = store_cfg.provider
        factories = PROVIDER_FACTORIES.get(provider)
        if factories is None:
            raise ValueError(f"Unknown provider: {provider!r}")
        factory = factories.get(store_type)
        if factory is None:
            raise ValueError(
                f"Provider {provider!r} does not support store type {store_type!r}"
            )
        adapters[store_type] = factory(store_cfg.config)

    return Memio(
        facts=adapters.get("facts"),
        history=adapters.get("history"),
        documents=adapters.get("documents"),
        graph=adapters.get("graph"),
    )
