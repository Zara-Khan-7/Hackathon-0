"""Tests for A2A message bus."""

import time
import pytest
from src.a2a.message import A2AMessage, MessageType, MessagePriority
from src.a2a.message_bus import MockMessageBus


def _make_msg(sender="agent-a", recipient="agent-b",
              msg_type=MessageType.TASK_DELEGATION,
              priority=MessagePriority.NORMAL, **kwargs):
    return A2AMessage(
        sender_id=sender,
        recipient_id=recipient,
        message_type=msg_type,
        payload=kwargs.get("payload", {"test": True}),
        priority=priority,
    )


class TestA2AMessage:
    def test_create_message(self):
        msg = _make_msg()
        assert msg.sender_id == "agent-a"
        assert msg.recipient_id == "agent-b"
        assert msg.message_type == MessageType.TASK_DELEGATION
        assert not msg.is_expired
        assert not msg.is_broadcast

    def test_broadcast_message(self):
        msg = _make_msg(recipient="all")
        assert msg.is_broadcast

    def test_expired_message(self):
        msg = _make_msg()
        msg.timestamp = time.time() - 7200  # 2 hours ago
        msg.ttl = 3600
        assert msg.is_expired

    def test_to_dict(self):
        msg = _make_msg()
        d = msg.to_dict()
        assert d["sender_id"] == "agent-a"
        assert d["message_type"] == "task_delegation"

    def test_from_dict(self):
        msg = _make_msg()
        d = msg.to_dict()
        msg2 = A2AMessage.from_dict(d)
        assert msg2.sender_id == msg.sender_id
        assert msg2.message_type == msg.message_type

    def test_repr(self):
        msg = _make_msg()
        assert "agent-a" in repr(msg)
        assert "agent-b" in repr(msg)


class TestMockMessageBus:
    def test_publish_and_consume(self):
        bus = MockMessageBus()
        msg = _make_msg()
        assert bus.publish(msg) is True
        messages = bus.consume("agent-b")
        assert len(messages) == 1
        assert messages[0].sender_id == "agent-a"

    def test_consume_empty_queue(self):
        bus = MockMessageBus()
        assert bus.consume("agent-x") == []

    def test_peek(self):
        bus = MockMessageBus()
        bus.publish(_make_msg())
        assert bus.peek("agent-b") == 1
        assert bus.peek("agent-a") == 0

    def test_max_queue_size(self):
        bus = MockMessageBus(max_queue_size=2)
        assert bus.publish(_make_msg()) is True
        assert bus.publish(_make_msg()) is True
        assert bus.publish(_make_msg()) is False  # Queue full

    def test_priority_ordering(self):
        bus = MockMessageBus()
        bus.publish(_make_msg(priority=MessagePriority.LOW))
        bus.publish(_make_msg(priority=MessagePriority.URGENT))
        bus.publish(_make_msg(priority=MessagePriority.NORMAL))

        messages = bus.consume("agent-b", max_messages=3)
        assert messages[0].priority == MessagePriority.URGENT
        assert messages[1].priority == MessagePriority.NORMAL
        assert messages[2].priority == MessagePriority.LOW

    def test_broadcast(self):
        bus = MockMessageBus()
        # Create queues by publishing a dummy first
        bus.publish(_make_msg(sender="x", recipient="agent-a"))
        bus.publish(_make_msg(sender="x", recipient="agent-c"))
        # Now broadcast
        broadcast = _make_msg(sender="agent-b", recipient="all")
        bus.publish(broadcast)

        # agent-a and agent-c should get the broadcast
        msgs_a = bus.consume("agent-a")
        assert any(m.is_broadcast for m in msgs_a)

    def test_expired_messages_removed_on_consume(self):
        bus = MockMessageBus()
        expired_msg = _make_msg()
        expired_msg.timestamp = time.time() - 7200
        expired_msg.ttl = 3600
        bus.publish(expired_msg)

        fresh_msg = _make_msg()
        bus.publish(fresh_msg)

        messages = bus.consume("agent-b")
        assert len(messages) == 1  # Only the fresh one

    def test_clear_specific_queue(self):
        bus = MockMessageBus()
        bus.publish(_make_msg())
        bus.clear("agent-b")
        assert bus.peek("agent-b") == 0

    def test_clear_all(self):
        bus = MockMessageBus()
        bus.publish(_make_msg())
        bus.clear()
        assert bus.peek("agent-b") == 0

    def test_subscribe_callback(self):
        bus = MockMessageBus()
        received = []
        bus.subscribe("agent-b", lambda m: received.append(m))
        bus.publish(_make_msg())
        assert len(received) == 1

    def test_stats(self):
        bus = MockMessageBus()
        bus.publish(_make_msg())
        stats = bus.get_stats()
        assert stats["total_published"] == 1
        assert stats["backend"] == "memory"
