"""Fake email and LinkedIn data for testing watchers without real APIs."""

MOCK_EMAILS = [
    {
        "id": "mock_email_001",
        "from": "client@acmecorp.com",
        "subject": "Q1 Invoice Request",
        "date": "2026-02-17",
        "snippet": "Hi, could you please send over the Q1 invoice? We need it for our records by end of week.",
        "body": (
            "Hi,\n\n"
            "Could you please send over the Q1 invoice for the consulting work completed "
            "in January-March? We need it for our quarterly reconciliation by Friday.\n\n"
            "The PO number is PO-2026-0142.\n\n"
            "Thanks,\nSarah Chen\nAccounts Payable, Acme Corp"
        ),
        "labels": ["INBOX", "UNREAD"],
    },
    {
        "id": "mock_email_002",
        "from": "newsletter@techdigest.io",
        "subject": "This Week in AI: February 2026",
        "date": "2026-02-17",
        "snippet": "Top stories: Claude 4 benchmarks, open-source agent frameworks, and more.",
        "body": (
            "This Week in AI\n\n"
            "1. Claude 4 sets new benchmarks in reasoning tasks\n"
            "2. Open-source agent frameworks gaining enterprise adoption\n"
            "3. EU AI Act enforcement begins Q2 2026\n\n"
            "Read more at techdigest.io/ai-weekly"
        ),
        "labels": ["INBOX", "UNREAD", "CATEGORY_UPDATES"],
    },
    {
        "id": "mock_email_003",
        "from": "recruiter@toptalent.com",
        "subject": "Partnership Opportunity — AI Consulting",
        "date": "2026-02-16",
        "snippet": "We'd love to discuss a potential partnership for AI consulting services.",
        "body": (
            "Hello,\n\n"
            "I'm reaching out from TopTalent Consulting. We've been following your work "
            "in AI automation and would love to explore a partnership opportunity.\n\n"
            "Would you be available for a 30-minute call next week?\n\n"
            "Best regards,\nMike Johnson\nBD Manager, TopTalent Consulting\n"
            "Phone: +1-555-0123"
        ),
        "labels": ["INBOX", "UNREAD"],
    },
]

MOCK_LINKEDIN_ITEMS = [
    {
        "id": "mock_li_001",
        "type": "connection_request",
        "from_name": "Jessica Lee",
        "from_title": "VP of Engineering at CloudScale",
        "message": "Hi! I saw your recent post on AI agents. Would love to connect and discuss potential synergies.",
        "date": "2026-02-17",
    },
    {
        "id": "mock_li_002",
        "type": "message",
        "from_name": "David Park",
        "from_title": "CTO at StartupXYZ",
        "message": (
            "Hey, we're looking for someone to help us build an AI-powered customer support system. "
            "Your profile caught my eye. Would you be interested in a quick chat?"
        ),
        "date": "2026-02-17",
    },
    {
        "id": "mock_li_003",
        "type": "engagement",
        "post_title": "5 Ways AI Agents Will Transform Small Business in 2026",
        "likes": 147,
        "comments": 23,
        "shares": 8,
        "top_comment": "Great insights! We implemented something similar and saw 40% efficiency gains.",
        "date": "2026-02-16",
    },
]
