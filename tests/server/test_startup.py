"""Tests for app startup failures and bad provider configuration."""

import pytest

from memio.server.config import ServerConfig, StoreConfig, build_memio_from_config


class TestStartupFailures:
    def test_unknown_provider_raises(self):
        config = ServerConfig(
            stores={"facts": StoreConfig(provider="nonexistent", config={})}
        )
        with pytest.raises(ValueError, match="Unknown provider"):
            build_memio_from_config(config)

    def test_unsupported_store_type_raises(self):
        config = ServerConfig(
            stores={"history": StoreConfig(provider="mem0", config={})}
        )
        with pytest.raises(ValueError, match="does not support store type"):
            build_memio_from_config(config)

    def test_letta_missing_agent_id_raises(self):
        config = ServerConfig(
            stores={"facts": StoreConfig(provider="letta", config={})}
        )
        with pytest.raises(ValueError, match="agent_id"):
            build_memio_from_config(config)

    def test_empty_config_raises(self):
        config = ServerConfig(stores={})
        with pytest.raises(ValueError, match="No stores configured"):
            build_memio_from_config(config)
