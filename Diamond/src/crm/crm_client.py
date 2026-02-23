"""CRM Client — mock integration with CRM systems (Salesforce/HubSpot).

Provides contact management, deal tracking, and activity logging.
All data is mock — no real CRM API calls.
"""

from __future__ import annotations

import copy
from typing import Any

from src.crm.mock_crm import MOCK_CONTACTS, MOCK_DEALS, MOCK_ACTIVITIES


class CRMClient:
    """Mock CRM client for Diamond tier.

    In production, this would connect to Salesforce, HubSpot, etc.
    """

    def __init__(self, mock: bool = True):
        self._mock = mock
        self._contacts = copy.deepcopy(MOCK_CONTACTS)
        self._deals = copy.deepcopy(MOCK_DEALS)
        self._activities = copy.deepcopy(MOCK_ACTIVITIES)

    def list_contacts(self, status: str | None = None,
                      tag: str | None = None) -> list[dict]:
        """List CRM contacts with optional filters."""
        results = self._contacts
        if status:
            results = [c for c in results if c["status"] == status]
        if tag:
            results = [c for c in results if tag in c.get("tags", [])]
        return results

    def get_contact(self, contact_id: str) -> dict | None:
        """Get a single contact by ID."""
        for c in self._contacts:
            if c["id"] == contact_id:
                return c
        return None

    def search_contacts(self, query: str) -> list[dict]:
        """Search contacts by name, email, or company."""
        query_lower = query.lower()
        return [
            c for c in self._contacts
            if query_lower in c["name"].lower()
            or query_lower in c["email"].lower()
            or query_lower in c["company"].lower()
        ]

    def create_contact(self, name: str, email: str, company: str,
                       tags: list[str] | None = None) -> dict:
        """Create a new contact."""
        contact = {
            "id": f"contact-{len(self._contacts) + 1:03d}",
            "name": name,
            "email": email,
            "company": company,
            "status": "active",
            "last_contact": None,
            "tags": tags or [],
        }
        self._contacts.append(contact)
        return contact

    def list_deals(self, stage: str | None = None,
                   contact_id: str | None = None) -> list[dict]:
        """List CRM deals with optional filters."""
        results = self._deals
        if stage:
            results = [d for d in results if d["stage"] == stage]
        if contact_id:
            results = [d for d in results if d["contact_id"] == contact_id]
        return results

    def get_deal(self, deal_id: str) -> dict | None:
        """Get a single deal by ID."""
        for d in self._deals:
            if d["id"] == deal_id:
                return d
        return None

    def get_pipeline_summary(self) -> dict:
        """Get deal pipeline summary."""
        stages: dict[str, list[dict]] = {}
        for deal in self._deals:
            stages.setdefault(deal["stage"], []).append(deal)

        summary = {}
        for stage, deals in stages.items():
            summary[stage] = {
                "count": len(deals),
                "total_value": sum(d["value"] for d in deals),
                "avg_probability": sum(d["probability"] for d in deals) / len(deals) if deals else 0,
            }
        return summary

    def list_activities(self, contact_id: str | None = None,
                        activity_type: str | None = None) -> list[dict]:
        """List CRM activities with optional filters."""
        results = self._activities
        if contact_id:
            results = [a for a in results if a["contact_id"] == contact_id]
        if activity_type:
            results = [a for a in results if a["type"] == activity_type]
        return results

    def log_activity(self, contact_id: str, activity_type: str,
                     subject: str) -> dict:
        """Log a new activity for a contact."""
        from datetime import date
        activity = {
            "id": f"activity-{len(self._activities) + 1:03d}",
            "contact_id": contact_id,
            "type": activity_type,
            "subject": subject,
            "date": date.today().isoformat(),
        }
        self._activities.append(activity)
        return activity

    def get_stats(self) -> dict:
        """Get CRM statistics."""
        pipeline = self.get_pipeline_summary()
        total_pipeline_value = sum(s["total_value"] for s in pipeline.values())
        return {
            "total_contacts": len(self._contacts),
            "active_contacts": len([c for c in self._contacts if c["status"] == "active"]),
            "total_deals": len(self._deals),
            "pipeline_value": total_pipeline_value,
            "total_activities": len(self._activities),
            "mock_mode": self._mock,
        }
