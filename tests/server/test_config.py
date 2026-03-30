"""Tests for config loading, env var interpolation, and validation."""

import os

import pytest

from memio.server.config import ServerConfig, load_config


class TestConfigLoading:
    def test_defaults_without_config_file(self, tmp_path):
        """No config file → sensible defaults."""
        config = load_config(path=str(tmp_path / "nonexistent.yaml"))
        assert config.host == "127.0.0.1"
        assert config.port == 8080
        assert config.api_key is None
        assert config.stores == {}

    def test_loads_yaml(self, tmp_path):
        cfg_file = tmp_path / "test.yaml"
        cfg_file.write_text(
            "server:\n  host: 0.0.0.0\n  port: 9090\nstores:\n"
            "  facts:\n    provider: mem0\n    config:\n      api_key: my-key\n"
        )
        config = load_config(path=str(cfg_file))
        assert config.host == "0.0.0.0"
        assert config.port == 9090
        assert "facts" in config.stores
        assert config.stores["facts"].provider == "mem0"
        assert config.stores["facts"].config["api_key"] == "my-key"

    def test_env_var_interpolation(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "secret123")
        cfg_file = tmp_path / "test.yaml"
        cfg_file.write_text(
            "stores:\n  facts:\n    provider: mem0\n"
            "    config:\n      api_key: ${TEST_API_KEY}\n"
        )
        config = load_config(path=str(cfg_file))
        assert config.stores["facts"].config["api_key"] == "secret123"

    def test_unresolved_env_var_raises(self, tmp_path):
        cfg_file = tmp_path / "test.yaml"
        cfg_file.write_text(
            "stores:\n  facts:\n    provider: mem0\n"
            "    config:\n      api_key: ${NONEXISTENT_VAR_XYZ}\n"
        )
        with pytest.raises(RuntimeError, match="NONEXISTENT_VAR_XYZ"):
            load_config(path=str(cfg_file))

    def test_env_var_overrides(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MEMIO_HOST", "1.2.3.4")
        monkeypatch.setenv("MEMIO_PORT", "3000")
        monkeypatch.setenv("MEMIO_API_KEY", "env-key")
        cfg_file = tmp_path / "test.yaml"
        cfg_file.write_text("server:\n  host: 0.0.0.0\n  port: 8080\n")
        config = load_config(path=str(cfg_file))
        assert config.host == "1.2.3.4"
        assert config.port == 3000
        assert config.api_key == "env-key"
