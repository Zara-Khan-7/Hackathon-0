"""Message Router — routes A2A messages between specialized agents.

Handles task delegation, result collection, and inter-agent coordination.
"""

from __future__ import annotations

from typing import Any

from src.a2a.message import A2AMessage, MessageType, MessagePriority
from src.a2a.message_bus import MockMessageBus
from src.agents.agent_registry import AgentRegistry
from src.agents.base_agent import BaseSpecializedAgent


class MessageRouter:
    """Routes messages between agents via the message bus.

    Provides high-level operations like delegate_task and broadcast_alert,
    built on top of the raw message bus.
    """

    def __init__(self, bus: MockMessageBus, registry: AgentRegistry):
        self._bus = bus
        self._registry = registry

    def delegate_task(self, sender_id: str, task: dict,
                      target_agent_id: str | None = None) -> A2AMessage | None:
        """Delegate a task to the best available agent (or a specific one).

        If target_agent_id is None, auto-selects the best agent.
        Returns the sent message, or None if no agent available.
        """
        if target_agent_id is None:
            agent = self._registry.find_best_agent(task)
            if agent is None:
                return None
            target_agent_id = agent.agent_id

        msg = A2AMessage(
            sender_id=sender_id,
            recipient_id=target_agent_id,
            message_type=MessageType.TASK_DELEGATION,
            payload={"task": task},
            priority=self._task_to_priority(task),
        )
        self._bus.publish(msg)
        return msg

    def send_result(self, agent_id: str, recipient_id: str,
                    result: dict, correlation_id: str | None = None) -> A2AMessage:
        """Send a task result back to the requester."""
        msg = A2AMessage(
            sender_id=agent_id,
            recipient_id=recipient_id,
            message_type=MessageType.TASK_RESULT,
            payload={"result": result},
            correlation_id=correlation_id,
        )
        self._bus.publish(msg)
        return msg

    def request_info(self, sender_id: str, target_id: str,
                     query: str, context: dict | None = None) -> A2AMessage:
        """Request information from another agent."""
        msg = A2AMessage(
            sender_id=sender_id,
            recipient_id=target_id,
            message_type=MessageType.INFO_REQUEST,
            payload={"query": query, "context": context or {}},
        )
        self._bus.publish(msg)
        return msg

    def respond_info(self, sender_id: str, recipient_id: str,
                     response: Any, correlation_id: str | None = None) -> A2AMessage:
        """Respond to an information request."""
        msg = A2AMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=MessageType.INFO_RESPONSE,
            payload={"response": response},
            correlation_id=correlation_id,
        )
        self._bus.publish(msg)
        return msg

    def broadcast_alert(self, sender_id: str, alert_type: str,
                        details: dict) -> A2AMessage:
        """Broadcast a security alert to all agents."""
        msg = A2AMessage(
            sender_id=sender_id,
            recipient_id="all",
            message_type=MessageType.SECURITY_ALERT,
            payload={"alert_type": alert_type, "details": details},
            priority=MessagePriority.URGENT,
        )
        self._bus.publish(msg)
        return msg

    def broadcast_status(self, sender_id: str, status: str,
                         details: dict | None = None) -> A2AMessage:
        """Broadcast agent status update to all agents."""
        msg = A2AMessage(
            sender_id=sender_id,
            recipient_id="all",
            message_type=MessageType.STATUS_UPDATE,
            payload={"status": status, "details": details or {}},
        )
        self._bus.publish(msg)
        return msg

    def get_messages(self, agent_id: str, max_messages: int = 10) -> list[A2AMessage]:
        """Get pending messages for an agent."""
        return self._bus.consume(agent_id, max_messages)

    def pending_count(self, agent_id: str) -> int:
        """Check how many messages are pending for an agent."""
        return self._bus.peek(agent_id)

    @staticmethod
    def _task_to_priority(task: dict) -> MessagePriority:
        """Convert task priority to message priority."""
        priority_map = {
            "high": MessagePriority.HIGH,
            "medium": MessagePriority.NORMAL,
            "low": MessagePriority.LOW,
        }
        return priority_map.get(task.get("priority", "medium"), MessagePriority.NORMAL)

    def get_stats(self) -> dict:
        """Get router + bus statistics."""
        return {
            "bus": self._bus.get_stats(),
            "registry": {
                "total_agents": self._registry.total_count,
                "idle": self._registry.idle_count,
                "busy": self._registry.busy_count,
            },
        }
