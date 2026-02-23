"""Agent Registry — manages all specialized agents in the Diamond swarm.

Provides agent lookup, task delegation, and load balancing.
"""

from __future__ import annotations

from typing import Any

from src.agents.base_agent import BaseSpecializedAgent, AgentStatus
from src.agents.sales_agent import SalesAgent
from src.agents.finance_agent import FinanceAgent
from src.agents.content_agent import ContentAgent
from src.agents.security_agent import SecurityAgent


# Default agent types available in Diamond tier
DEFAULT_AGENT_TYPES = {
    "sales": SalesAgent,
    "finance": FinanceAgent,
    "content": ContentAgent,
    "security": SecurityAgent,
}


class AgentRegistry:
    """Manages the pool of specialized agents."""

    def __init__(self):
        self._agents: dict[str, BaseSpecializedAgent] = {}

    def register(self, agent: BaseSpecializedAgent) -> None:
        """Register a specialized agent."""
        self._agents[agent.agent_id] = agent

    def unregister(self, agent_id: str) -> None:
        """Remove an agent from the registry."""
        self._agents.pop(agent_id, None)

    def get(self, agent_id: str) -> BaseSpecializedAgent | None:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    def get_by_type(self, agent_type: str) -> list[BaseSpecializedAgent]:
        """Get all agents of a specific type."""
        return [a for a in self._agents.values() if a.AGENT_TYPE == agent_type]

    def list_agents(self) -> list[dict[str, Any]]:
        """List all registered agents with their stats."""
        return [agent.get_stats() for agent in self._agents.values()]

    def find_best_agent(self, task: dict) -> BaseSpecializedAgent | None:
        """Find the best available agent for a task based on scoring.

        Returns the idle agent with the highest score, or None if no agent can handle it.
        """
        candidates = []
        for agent in self._agents.values():
            if agent.status != AgentStatus.IDLE:
                continue
            score = agent.score_task(task)
            if score > 0:
                candidates.append((score, agent))

        if not candidates:
            return None

        # Sort by score descending, return best match
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def find_agents_for_prefix(self, prefix: str) -> list[BaseSpecializedAgent]:
        """Find all agents that can handle a given task prefix."""
        return [a for a in self._agents.values() if a.can_handle(prefix)]

    @property
    def idle_count(self) -> int:
        return sum(1 for a in self._agents.values() if a.status == AgentStatus.IDLE)

    @property
    def busy_count(self) -> int:
        return sum(1 for a in self._agents.values() if a.status == AgentStatus.BUSY)

    @property
    def total_count(self) -> int:
        return len(self._agents)

    def get_swarm_stats(self) -> dict:
        """Get aggregate stats for the entire swarm."""
        total_completed = sum(a._tasks_completed for a in self._agents.values())
        total_failed = sum(a._tasks_failed for a in self._agents.values())
        return {
            "total_agents": self.total_count,
            "idle": self.idle_count,
            "busy": self.busy_count,
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
            "agents": self.list_agents(),
        }

    def __len__(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return f"AgentRegistry(agents={len(self._agents)}, idle={self.idle_count})"


def create_default_registry() -> AgentRegistry:
    """Create an AgentRegistry with all default Diamond agents."""
    registry = AgentRegistry()
    for agent_type, agent_class in DEFAULT_AGENT_TYPES.items():
        registry.register(agent_class())
    return registry
