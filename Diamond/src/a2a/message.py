"""A2A Message — data model for agent-to-agent communication.

Messages are the core unit of inter-agent communication in the Diamond swarm.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageType(str, Enum):
    TASK_DELEGATION = "task_delegation"     # Delegate a task to another agent
    TASK_RESULT = "task_result"             # Return result of a delegated task
    INFO_REQUEST = "info_request"           # Request information from another agent
    INFO_RESPONSE = "info_response"         # Respond to an info request
    SECURITY_ALERT = "security_alert"       # Security agent broadcasts an alert
    STATUS_UPDATE = "status_update"         # Agent status change notification
    BROADCAST = "broadcast"                 # Message to all agents


@dataclass
class A2AMessage:
    """A message passed between agents in the Diamond swarm."""

    sender_id: str
    recipient_id: str                       # "all" for broadcast
    message_type: MessageType
    payload: dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    correlation_id: str | None = None       # Links request/response pairs
    ttl: int = 3600                         # Seconds before message expires

    @property
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl

    @property
    def is_broadcast(self) -> bool:
        return self.recipient_id == "all"

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: dict) -> A2AMessage:
        return cls(
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            message_type=MessageType(data["message_type"]),
            payload=data["payload"],
            priority=MessagePriority(data.get("priority", "normal")),
            message_id=data.get("message_id", str(uuid.uuid4())[:8]),
            timestamp=data.get("timestamp", time.time()),
            correlation_id=data.get("correlation_id"),
            ttl=data.get("ttl", 3600),
        )

    def __repr__(self) -> str:
        return (
            f"A2AMessage(id={self.message_id!r}, "
            f"{self.sender_id}→{self.recipient_id}, "
            f"type={self.message_type.value})"
        )
