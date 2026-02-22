"""Mock data for all three social media platforms.

Used when *_MOCK=true or when real API connections fail.
"""

# ---------------------------------------------------------------------------
# Facebook mock data
# ---------------------------------------------------------------------------

MOCK_FACEBOOK_FEED = [
    {
        "id": "fb_post_001",
        "message": "Excited to announce our new AI-powered workflow automation! Helping businesses save 20+ hours per week.",
        "created_time": "2026-02-18T14:30:00+0000",
        "likes": 47,
        "comments": 12,
        "shares": 8,
    },
    {
        "id": "fb_post_002",
        "message": "Join us at the TechForward Conference next month. We'll be demonstrating our latest innovations.",
        "created_time": "2026-02-15T10:00:00+0000",
        "likes": 32,
        "comments": 5,
        "shares": 15,
    },
    {
        "id": "fb_post_003",
        "message": "Customer spotlight: How Acme Corp reduced manual data entry by 80% with our solution.",
        "created_time": "2026-02-12T16:45:00+0000",
        "likes": 89,
        "comments": 23,
        "shares": 31,
    },
]

MOCK_FACEBOOK_NOTIFICATIONS = [
    {
        "id": "fb_notif_001",
        "title": "Sarah Chen commented on your post",
        "message": "Great results! We've seen similar improvements.",
        "created_time": "2026-02-19T09:15:00+0000",
        "unread": True,
    },
    {
        "id": "fb_notif_002",
        "title": "TechStart Inc. mentioned you in a post",
        "message": "Working with @YourCompany has been a game-changer for our team.",
        "created_time": "2026-02-18T17:30:00+0000",
        "unread": True,
    },
    {
        "id": "fb_notif_003",
        "title": "Mark Johnson sent you a message",
        "message": "Hi, I'm interested in learning more about your enterprise plans.",
        "created_time": "2026-02-18T11:00:00+0000",
        "unread": False,
    },
]

# ---------------------------------------------------------------------------
# Instagram mock data
# ---------------------------------------------------------------------------

MOCK_INSTAGRAM_DMS = [
    {
        "id": "ig_dm_001",
        "from": "design_studio_co",
        "text": "Love your recent post about automation! Would you be open to a collab?",
        "timestamp": "2026-02-19T08:45:00+0000",
    },
    {
        "id": "ig_dm_002",
        "from": "tech_reviewer_mike",
        "text": "Hey, would love to feature your product in our next review. DM me details?",
        "timestamp": "2026-02-18T14:20:00+0000",
    },
]

MOCK_INSTAGRAM_MENTIONS = [
    {
        "id": "ig_mention_001",
        "user": "startup_daily",
        "caption": "Top 10 AI tools transforming business in 2026 — @yourcompany makes the list!",
    },
    {
        "id": "ig_mention_002",
        "user": "entrepreneur_jane",
        "caption": "Just implemented @yourcompany's solution. Results are incredible.",
    },
]

MOCK_INSTAGRAM_FEED = [
    {
        "id": "ig_post_001",
        "caption": "Behind the scenes of our product team building the next generation of AI tools.",
        "likes": 156,
        "comments": 18,
        "timestamp": "2026-02-17T12:00:00+0000",
    },
    {
        "id": "ig_post_002",
        "caption": "From manual processes to full automation — the journey of our clients.",
        "likes": 203,
        "comments": 34,
        "timestamp": "2026-02-14T15:30:00+0000",
    },
]

# ---------------------------------------------------------------------------
# Twitter / X mock data
# ---------------------------------------------------------------------------

MOCK_TWITTER_MENTIONS = [
    {
        "id": "tw_mention_001",
        "text": "@yourcompany Your AI employee tool is exactly what our team needed. Reduced ticket processing by 60%!",
        "author_id": "user_1234",
        "author_name": "Alex Rivera",
        "created_at": "2026-02-19T10:30:00Z",
    },
    {
        "id": "tw_mention_002",
        "text": "Anyone tried @yourcompany for workflow automation? Thinking about switching from our current setup.",
        "author_id": "user_5678",
        "author_name": "ProductHunt Daily",
        "created_at": "2026-02-18T22:15:00Z",
    },
    {
        "id": "tw_mention_003",
        "text": "@yourcompany When is the Odoo integration going live? Our accounting team is eager!",
        "author_id": "user_9012",
        "author_name": "CFO Corner",
        "created_at": "2026-02-18T16:00:00Z",
    },
]

MOCK_TWITTER_DMS = [
    {
        "id": "tw_dm_001",
        "text": "Hi there! We're a SaaS startup and would love to explore a partnership. Are you open to integrations?",
        "sender_id": "user_3456",
        "sender_name": "SaaSGrid",
        "created_at": "2026-02-19T07:00:00Z",
    },
    {
        "id": "tw_dm_002",
        "text": "Loved your thread on AI employees. Would you be interested in a podcast interview?",
        "sender_id": "user_7890",
        "sender_name": "TechTalk Pod",
        "created_at": "2026-02-17T19:45:00Z",
    },
]

MOCK_TWITTER_FEED = [
    {
        "id": "tw_post_001",
        "text": "The future of work isn't replacing humans — it's augmenting them. Our AI Employee handles the routine so your team can focus on what matters.",
        "likes": 234,
        "retweets": 67,
        "replies": 28,
        "created_at": "2026-02-18T13:00:00Z",
    },
    {
        "id": "tw_post_002",
        "text": "New feature alert: Odoo ERP integration is now in beta. Invoice management, transaction sync, and automated reconciliation.",
        "likes": 189,
        "retweets": 45,
        "replies": 15,
        "created_at": "2026-02-16T11:00:00Z",
    },
]
