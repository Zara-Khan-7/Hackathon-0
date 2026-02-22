"""Fake data for testing all watchers without real APIs.

Covers: Gmail, LinkedIn, Facebook, Instagram, Twitter, and Odoo.
"""

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


# ---------------------------------------------------------------------------
# Facebook mock data (for watcher)
# ---------------------------------------------------------------------------

MOCK_FACEBOOK = [
    {
        "id": "mock_fb_001",
        "type": "notification",
        "title": "Sarah Chen commented on your post",
        "message": "Great results! We've seen similar improvements with AI automation.",
        "created_time": "2026-02-19T09:15:00+0000",
        "unread": True,
    },
    {
        "id": "mock_fb_002",
        "type": "message",
        "title": "Mark Johnson sent you a message",
        "message": "Hi, I'm interested in learning more about your enterprise plans. Can we schedule a demo?",
        "created_time": "2026-02-18T11:00:00+0000",
        "unread": True,
    },
    {
        "id": "mock_fb_003",
        "type": "notification",
        "title": "TechStart Inc. mentioned you in a post",
        "message": "Working with @YourCompany has been a game-changer for our team's productivity.",
        "created_time": "2026-02-18T17:30:00+0000",
        "unread": False,
    },
]


# ---------------------------------------------------------------------------
# Instagram mock data (for watcher)
# ---------------------------------------------------------------------------

MOCK_INSTAGRAM = [
    {
        "id": "mock_ig_001",
        "type": "dm",
        "from": "design_studio_co",
        "text": "Love your recent post about automation! Would you be open to a collab?",
        "timestamp": "2026-02-19T08:45:00+0000",
    },
    {
        "id": "mock_ig_002",
        "type": "dm",
        "from": "tech_reviewer_mike",
        "text": "Hey, would love to feature your product in our next review. DM me details?",
        "timestamp": "2026-02-18T14:20:00+0000",
    },
    {
        "id": "mock_ig_003",
        "type": "mention",
        "user": "startup_daily",
        "caption": "Top 10 AI tools transforming business in 2026 — @yourcompany makes the list!",
    },
]


# ---------------------------------------------------------------------------
# Twitter / X mock data (for watcher)
# ---------------------------------------------------------------------------

MOCK_TWITTER = [
    {
        "id": "mock_tw_001",
        "type": "mention",
        "text": "@yourcompany Your AI employee tool is exactly what our team needed. Reduced ticket processing by 60%!",
        "author_id": "user_1234",
        "author_name": "Alex Rivera",
        "created_at": "2026-02-19T10:30:00Z",
    },
    {
        "id": "mock_tw_002",
        "type": "mention",
        "text": "Anyone tried @yourcompany for workflow automation? Thinking about switching from our current setup.",
        "author_id": "user_5678",
        "author_name": "ProductHunt Daily",
        "created_at": "2026-02-18T22:15:00Z",
    },
    {
        "id": "mock_tw_003",
        "type": "dm",
        "text": "Hi there! We're a SaaS startup and would love to explore a partnership. Are you open to integrations?",
        "sender_id": "user_3456",
        "sender_name": "SaaSGrid",
        "created_at": "2026-02-19T07:00:00Z",
    },
]


# ---------------------------------------------------------------------------
# Odoo mock data (for watcher / auditor)
# ---------------------------------------------------------------------------

MOCK_ODOO_TRANSACTIONS = [
    {
        "id": "mock_odoo_001",
        "type": "invoice_received",
        "partner": "Acme Corporation",
        "amount": 5000.00,
        "description": "Q1 consulting invoice received",
        "date": "2026-02-15",
    },
    {
        "id": "mock_odoo_002",
        "type": "payment_received",
        "partner": "TechStart Inc.",
        "amount": 12500.00,
        "description": "Full payment received for project Alpha",
        "date": "2026-02-14",
    },
]
