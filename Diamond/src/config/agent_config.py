"""Agent configuration — identity, role, and settings.

Loads from config.yaml + environment variables (env vars take precedence).
"""

import os
from enum import Enum
from pathlib import Path

import yaml


class AgentRole(str, Enum):
    CLOUD = "cloud"
    LOCAL = "local"
    GOLD = "gold"      # backward-compatible single-machine mode
    DIAMOND = "diamond" # multi-agent swarm mode


class AgentConfig:
    """Agent identity and role configuration."""

    def __init__(self, config_path: str | Path | None = None):
        self._config = self._load_config(config_path)
        agent_section = self._config.get("agent", {})

        self.agent_id: str = os.getenv("AGENT_ID", agent_section.get("id", "local-001"))
        role_str = os.getenv("AGENT_ROLE", agent_section.get("role", "local"))
        self.role: AgentRole = AgentRole(role_str)
        self.heartbeat_interval: int = int(
            os.getenv("HEARTBEAT_INTERVAL", agent_section.get("heartbeat_interval", 30))
        )

        sync_section = self._config.get("sync", {})
        self.sync_enabled: bool = os.getenv(
            "GIT_SYNC_ENABLED", str(sync_section.get("enabled", False))
        ).lower() in ("true", "1", "yes")
        self.sync_interval: int = int(
            os.getenv("GIT_SYNC_INTERVAL", sync_section.get("interval", 60))
        )

    @staticmethod
    def _load_config(config_path: str | Path | None = None) -> dict:
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
        config_path = Path(config_path)
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    @property
    def is_cloud(self) -> bool:
        return self.role == AgentRole.CLOUD

    @property
    def is_local(self) -> bool:
        return self.role == AgentRole.LOCAL

    @property
    def is_gold(self) -> bool:
        return self.role == AgentRole.GOLD

    @property
    def is_diamond(self) -> bool:
        return self.role == AgentRole.DIAMOND

    def get(self, section: str, key: str, default=None):
        """Get a config value from a section."""
        return self._config.get(section, {}).get(key, default)

    def __repr__(self) -> str:
        return f"AgentConfig(id={self.agent_id!r}, role={self.role.value!r})"
