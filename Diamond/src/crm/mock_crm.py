"""Mock CRM data — simulates a CRM system (Salesforce/HubSpot).

Provides contacts, deals, and activity data for the CRM client.
"""

MOCK_CONTACTS = [
    {
        "id": "contact-001",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "company": "TechCorp",
        "status": "active",
        "last_contact": "2026-02-20",
        "tags": ["prospect", "enterprise"],
    },
    {
        "id": "contact-002",
        "name": "Bob Smith",
        "email": "bob@example.com",
        "company": "StartupXYZ",
        "status": "active",
        "last_contact": "2026-02-18",
        "tags": ["customer", "smb"],
    },
    {
        "id": "contact-003",
        "name": "Carol Davis",
        "email": "carol@example.com",
        "company": "MegaInc",
        "status": "inactive",
        "last_contact": "2026-01-15",
        "tags": ["lead", "enterprise"],
    },
]

MOCK_DEALS = [
    {
        "id": "deal-001",
        "title": "TechCorp Annual License",
        "contact_id": "contact-001",
        "value": 50000,
        "currency": "USD",
        "stage": "negotiation",
        "probability": 75,
        "created": "2026-02-01",
    },
    {
        "id": "deal-002",
        "title": "StartupXYZ Onboarding",
        "contact_id": "contact-002",
        "value": 12000,
        "currency": "USD",
        "stage": "closed_won",
        "probability": 100,
        "created": "2026-01-20",
    },
    {
        "id": "deal-003",
        "title": "MegaInc Enterprise Pilot",
        "contact_id": "contact-003",
        "value": 120000,
        "currency": "USD",
        "stage": "proposal",
        "probability": 40,
        "created": "2026-02-10",
    },
]

MOCK_ACTIVITIES = [
    {
        "id": "activity-001",
        "contact_id": "contact-001",
        "type": "email_sent",
        "subject": "Follow-up on proposal",
        "date": "2026-02-20",
    },
    {
        "id": "activity-002",
        "contact_id": "contact-002",
        "type": "meeting",
        "subject": "Quarterly review",
        "date": "2026-02-18",
    },
    {
        "id": "activity-003",
        "contact_id": "contact-001",
        "type": "call",
        "subject": "Pricing discussion",
        "date": "2026-02-19",
    },
]
