"""Mock Message Bus — in-memory queue replacing RabbitMQ/Redis.

Provides pub/sub and point-to-point messaging between agents.
All messages are stored in memory (no external dependencies).
"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Callable

from src.a2a.message import A2AMessage, MessagePriority


class MockMessageBus:
    """In-memory message bus for agent-to-agent communication.

    In production, this would be backed by RabbitMQ or Redis Streams.
    The mock implementation provides the same API for testing and demos.
    """

    def __init__(self, max_queue_size: int = 1000):
        self._queues: dict[str, list[A2AMessage]] = defaultdict(list)
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._broadcast_subscribers: list[Callable] = []
        self._max_queue_size = max_queue_size
        self._total_published = 0
        self._total_consumed = 0
        self._lock = threading.Lock()

    def publish(self, message: A2AMessage) -> bool:
        """Publish a message to a recipient's queue.

        Returns True if published, False if queue full.
        """
        with self._lock:
            recipient = message.recipient_id

            if message.is_broadcast:
                self._handle_broadcast(message)
                self._total_published += 1
                return True

            queue = self._queues[recipient]
            if len(queue) >= self._max_queue_size:
                return False

            # Insert by priority (urgent first)
            priority_order = {
                MessagePriority.URGENT: 0,
                MessagePriority.HIGH: 1,
                MessagePriority.NORMAL: 2,
                MessagePriority.LOW: 3,
            }
            msg_priority = priority_order.get(message.priority, 2)

            # Find insertion point
            insert_idx = len(queue)
            for i, existing in enumerate(queue):
                existing_priority = priority_order.get(existing.priority, 2)
                if msg_priority < existing_priority:
                    insert_idx = i
                    break

            queue.insert(insert_idx, message)
            self._total_published += 1

            # Notify subscribers
            for callback in self._subscribers.get(recipient, []):
                try:
                    callback(message)
                except Exception:
                    pass

            return True

    def consume(self, agent_id: str, max_messages: int = 10) -> list[A2AMessage]:
        """Consume messages from an agent's queue.

        Returns up to max_messages, removing expired ones.
        """
        with self._lock:
            queue = self._queues.get(agent_id, [])

            # Remove expired messages
            queue[:] = [m for m in queue if not m.is_expired]

            # Take up to max_messages
            consumed = queue[:max_messages]
            self._queues[agent_id] = queue[max_messages:]
            self._total_consumed += len(consumed)

            return consumed

    def peek(self, agent_id: str) -> int:
        """Check how many messages are waiting for an agent."""
        with self._lock:
            queue = self._queues.get(agent_id, [])
            return len([m for m in queue if not m.is_expired])

    def subscribe(self, agent_id: str, callback: Callable[[A2AMessage], None]) -> None:
        """Subscribe to messages for a specific agent."""
        with self._lock:
            self._subscribers[agent_id].append(callback)

    def subscribe_broadcast(self, callback: Callable[[A2AMessage], None]) -> None:
        """Subscribe to all broadcast messages."""
        with self._lock:
            self._broadcast_subscribers.append(callback)

    def _handle_broadcast(self, message: A2AMessage) -> None:
        """Deliver a broadcast message to all queues and subscribers."""
        for agent_id in list(self._queues.keys()):
            if agent_id != message.sender_id:
                queue = self._queues[agent_id]
                if len(queue) < self._max_queue_size:
                    queue.append(message)

        for callback in self._broadcast_subscribers:
            try:
                callback(message)
            except Exception:
                pass

    def clear(self, agent_id: str | None = None) -> None:
        """Clear messages for a specific agent, or all if None."""
        with self._lock:
            if agent_id:
                self._queues.pop(agent_id, None)
            else:
                self._queues.clear()

    def get_stats(self) -> dict:
        """Get message bus statistics."""
        with self._lock:
            total_queued = sum(len(q) for q in self._queues.values())
            return {
                "backend": "memory",
                "total_queued": total_queued,
                "total_published": self._total_published,
                "total_consumed": self._total_consumed,
                "active_queues": len(self._queues),
                "max_queue_size": self._max_queue_size,
            }

    def __repr__(self) -> str:
        return f"MockMessageBus(queues={len(self._queues)}, published={self._total_published})"
