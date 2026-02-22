"""Tests for src.config.agent_config — AgentRole enum and AgentConfig class."""

import os
import pytest
from pathlib import Path

from src.config.agent_config import AgentRole, AgentConfig


class TestAgentRole:
    def test_cloud_value(self):
        assert AgentRole.CLOUD == "cloud"

    def test_local_value(self):
        assert AgentRole.LOCAL == "local"

    def test_gold_value(self):
        assert AgentRole.GOLD == "gold"

    def test_from_string(self):
        assert AgentRole("cloud") == AgentRole.CLOUD
        assert AgentRole("local") == AgentRole.LOCAL
        assert AgentRole("gold") == AgentRole.GOLD


class TestAgentConfig:
    def test_default_config(self):
        config = AgentConfig()
        assert config.agent_id is not None
        assert config.role in (AgentRole.CLOUD, AgentRole.LOCAL, AgentRole.GOLD)

    def test_env_override_agent_id(self, monkeypatch):
        monkeypatch.setenv("AGENT_ID", "test-agent-99")
        config = AgentConfig()
        assert config.agent_id == "test-agent-99"

    def test_env_override_role(self, monkeypatch):
        monkeypatch.setenv("AGENT_ROLE", "cloud")
        config = AgentConfig()
        assert config.role == AgentRole.CLOUD

    def test_is_cloud(self, monkeypatch):
        monkeypatch.setenv("AGENT_ROLE", "cloud")
        config = AgentConfig()
        assert config.is_cloud is True
        assert config.is_local is False

    def test_is_local(self, monkeypatch):
        monkeypatch.setenv("AGENT_ROLE", "local")
        config = AgentConfig()
        assert config.is_local is True
        assert config.is_cloud is False

    def test_is_gold(self, monkeypatch):
        monkeypatch.setenv("AGENT_ROLE", "gold")
        config = AgentConfig()
        assert config.is_gold is True

    def test_repr(self, monkeypatch):
        monkeypatch.setenv("AGENT_ID", "test-001")
        monkeypatch.setenv("AGENT_ROLE", "local")
        config = AgentConfig()
        r = repr(config)
        assert "test-001" in r
        assert "local" in r

    def test_config_from_yaml(self, tmp_path):
        yaml_content = "agent:\n  id: yaml-agent\n  role: cloud\n"
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_content)
        # Clear env vars to let yaml win
        os.environ.pop("AGENT_ID", None)
        os.environ.pop("AGENT_ROLE", None)
        config = AgentConfig(config_path=config_file)
        assert config.agent_id == "yaml-agent"
        assert config.role == AgentRole.CLOUD
