"""Tests for CRM client."""

import pytest
from src.crm.crm_client import CRMClient


@pytest.fixture
def crm():
    return CRMClient(mock=True)


class TestCRMClient:
    def test_list_contacts(self, crm):
        contacts = crm.list_contacts()
        assert len(contacts) == 3

    def test_list_contacts_by_status(self, crm):
        active = crm.list_contacts(status="active")
        assert len(active) == 2

    def test_list_contacts_by_tag(self, crm):
        enterprise = crm.list_contacts(tag="enterprise")
        assert len(enterprise) == 2

    def test_get_contact(self, crm):
        contact = crm.get_contact("contact-001")
        assert contact is not None
        assert contact["name"] == "Alice Johnson"

    def test_get_contact_not_found(self, crm):
        assert crm.get_contact("nonexistent") is None

    def test_search_contacts(self, crm):
        results = crm.search_contacts("Alice")
        assert len(results) == 1
        assert results[0]["name"] == "Alice Johnson"

    def test_search_by_company(self, crm):
        results = crm.search_contacts("TechCorp")
        assert len(results) == 1

    def test_create_contact(self, crm):
        contact = crm.create_contact("Test User", "test@example.com", "TestCo")
        assert contact["name"] == "Test User"
        assert len(crm.list_contacts()) == 4

    def test_list_deals(self, crm):
        deals = crm.list_deals()
        assert len(deals) == 3

    def test_list_deals_by_stage(self, crm):
        closed = crm.list_deals(stage="closed_won")
        assert len(closed) == 1

    def test_get_deal(self, crm):
        deal = crm.get_deal("deal-001")
        assert deal is not None
        assert deal["value"] == 50000

    def test_pipeline_summary(self, crm):
        summary = crm.get_pipeline_summary()
        assert "negotiation" in summary
        assert "closed_won" in summary

    def test_list_activities(self, crm):
        activities = crm.list_activities()
        assert len(activities) == 3

    def test_list_activities_by_contact(self, crm):
        activities = crm.list_activities(contact_id="contact-001")
        assert len(activities) == 2

    def test_log_activity(self, crm):
        activity = crm.log_activity("contact-001", "call", "Follow-up")
        assert activity["type"] == "call"
        assert len(crm.list_activities()) == 4

    def test_stats(self, crm):
        stats = crm.get_stats()
        assert stats["total_contacts"] == 3
        assert stats["total_deals"] == 3
        assert stats["mock_mode"] is True
