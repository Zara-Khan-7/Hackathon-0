"""Mock WhatsApp data for testing and development."""

MOCK_CHATS = [
    {
        "chat_id": "wa_chat_001",
        "name": "Ahmed (CEO, Acme Corp)",
        "phone": "+971501234567",
        "last_message": "Can you send me the latest invoice?",
        "last_time": "2026-02-21 10:30:00",
        "unread": 1,
    },
    {
        "chat_id": "wa_chat_002",
        "name": "Sarah (Marketing Lead)",
        "phone": "+971509876543",
        "last_message": "The social media campaign is ready for review",
        "last_time": "2026-02-21 09:15:00",
        "unread": 0,
    },
    {
        "chat_id": "wa_chat_003",
        "name": "Supplier - Global Supplies",
        "phone": "+971504567890",
        "last_message": "Shipment will arrive on Thursday",
        "last_time": "2026-02-20 16:45:00",
        "unread": 2,
    },
]

MOCK_MESSAGES = {
    "wa_chat_001": [
        {"from": "Ahmed", "text": "Hi, how are you?", "time": "2026-02-21 10:00:00"},
        {"from": "me", "text": "Good morning! I'm doing well.", "time": "2026-02-21 10:05:00"},
        {"from": "Ahmed", "text": "Can you send me the latest invoice?", "time": "2026-02-21 10:30:00"},
    ],
    "wa_chat_002": [
        {"from": "Sarah", "text": "Hey, I've prepared the Q1 social campaign", "time": "2026-02-21 09:00:00"},
        {"from": "me", "text": "Great, I'll review it today", "time": "2026-02-21 09:10:00"},
        {"from": "Sarah", "text": "The social media campaign is ready for review", "time": "2026-02-21 09:15:00"},
    ],
    "wa_chat_003": [
        {"from": "Global Supplies", "text": "Order #4521 has been dispatched", "time": "2026-02-20 14:00:00"},
        {"from": "me", "text": "Thanks! When will it arrive?", "time": "2026-02-20 14:30:00"},
        {"from": "Global Supplies", "text": "Shipment will arrive on Thursday", "time": "2026-02-20 16:45:00"},
    ],
}

MOCK_SENT = []


def get_chats() -> list[dict]:
    return list(MOCK_CHATS)


def get_messages(chat_id: str) -> list[dict]:
    return MOCK_MESSAGES.get(chat_id, [])


def send_message(chat_id: str, text: str) -> dict:
    msg = {
        "chat_id": chat_id,
        "from": "me",
        "text": text,
        "time": "2026-02-21 12:00:00",
        "status": "sent_mock",
    }
    MOCK_SENT.append(msg)
    return msg
