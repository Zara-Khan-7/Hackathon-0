"""Weekly business/accounting audit generator.

Gathers statistics from all system components and produces a comprehensive
Monday briefing for the CEO.

Usage:
    python -m src.audit.auditor --mock
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from src.utils.file_ops import get_project_root, get_folder, list_md_files, count_by_prefix
from src.utils.logger import log_action, audit_log
from src.utils import frontmatter

load_dotenv()


class WeeklyAuditor:
    """Gathers stats from all components and generates a CEO briefing."""

    def __init__(self, mock: bool = False):
        self.mock = mock
        self.project_root = get_project_root()
        self.now = datetime.now()
        self.week_start = self.now - timedelta(days=7)

    def gather_task_stats(self) -> dict:
        """Count tasks in Done/ by type and calculate completion stats."""
        done_files = list_md_files("Done")
        done_by_type = count_by_prefix("Done")

        # Count tasks completed in the last 7 days
        recent = 0
        for f in done_files:
            meta, _ = frontmatter.read_file(f)
            created = meta.get("created", "")
            if isinstance(created, str) and created >= self.week_start.strftime("%Y-%m-%d"):
                recent += 1

        # Pending tasks
        pending_count = len(list_md_files("Needs_Action"))
        approval_count = len(list_md_files("Pending_Approval"))

        return {
            "total_done": len(done_files),
            "done_this_week": recent,
            "done_by_type": done_by_type,
            "pending_tasks": pending_count,
            "pending_approvals": approval_count,
        }

    def gather_odoo_stats(self) -> dict:
        """Gather revenue and invoice stats from Odoo MCP."""
        try:
            from src.mcp_odoo.odoo_client import OdooClient
            client = OdooClient()
            invoices = client.list_invoices()
            if isinstance(invoices, dict) and "error" in invoices:
                invoices = []
        except Exception:
            invoices = []

        if not invoices and self.mock:
            from src.mcp_odoo.odoo_server import MOCK_INVOICES
            invoices = MOCK_INVOICES

        total_revenue = sum(inv.get("amount_total", 0) for inv in invoices
                           if inv.get("move_type") == "out_invoice" and inv.get("payment_state") == "paid")
        outstanding = sum(inv.get("amount_residual", 0) for inv in invoices
                         if inv.get("move_type") == "out_invoice" and inv.get("state") == "posted"
                         and inv.get("payment_state") != "paid")
        draft_invoices = sum(1 for inv in invoices if inv.get("state") == "draft")
        overdue = sum(1 for inv in invoices
                      if inv.get("invoice_date_due", "") < self.now.strftime("%Y-%m-%d")
                      and inv.get("payment_state") != "paid"
                      and inv.get("state") == "posted")

        return {
            "total_revenue_collected": total_revenue,
            "outstanding_amount": outstanding,
            "draft_invoices": draft_invoices,
            "overdue_invoices": overdue,
            "total_invoices": len(invoices),
        }

    def gather_social_stats(self) -> dict:
        """Gather engagement metrics from social MCP."""
        try:
            from src.mcp_social.social_client import SocialClient
            client = SocialClient()
            summary = client.get_social_summary(platform="all", limit=5)
            if isinstance(summary, dict) and "error" in summary:
                summary = {}
        except Exception:
            summary = {}

        if not summary and self.mock:
            from src.mcp_social.mock_social import (
                MOCK_FACEBOOK_FEED, MOCK_INSTAGRAM_FEED, MOCK_TWITTER_FEED,
                MOCK_FACEBOOK_NOTIFICATIONS, MOCK_INSTAGRAM_DMS,
                MOCK_TWITTER_MENTIONS, MOCK_TWITTER_DMS,
            )
            fb_likes = sum(p.get("likes", 0) for p in MOCK_FACEBOOK_FEED)
            ig_likes = sum(p.get("likes", 0) for p in MOCK_INSTAGRAM_FEED)
            tw_likes = sum(p.get("likes", 0) for p in MOCK_TWITTER_FEED)

            return {
                "facebook": {"posts": len(MOCK_FACEBOOK_FEED), "total_likes": fb_likes, "notifications": len(MOCK_FACEBOOK_NOTIFICATIONS)},
                "instagram": {"posts": len(MOCK_INSTAGRAM_FEED), "total_likes": ig_likes, "dms": len(MOCK_INSTAGRAM_DMS)},
                "twitter": {"posts": len(MOCK_TWITTER_FEED), "total_likes": tw_likes, "mentions": len(MOCK_TWITTER_MENTIONS), "dms": len(MOCK_TWITTER_DMS)},
            }

        return summary

    def detect_bottlenecks(self) -> list[dict]:
        """Find tasks stuck > 48h or with failed retries."""
        bottlenecks = []
        cutoff = (self.now - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")

        # Check Needs_Action for old tasks
        for f in list_md_files("Needs_Action"):
            meta, _ = frontmatter.read_file(f)
            created = meta.get("created", "")
            if isinstance(created, str) and created < cutoff:
                bottlenecks.append({
                    "file": f.name,
                    "issue": "Stuck in Needs_Action > 48 hours",
                    "created": created,
                    "priority": meta.get("priority", "medium"),
                })

        # Check Pending_Approval for old items
        for f in list_md_files("Pending_Approval"):
            meta, _ = frontmatter.read_file(f)
            created = meta.get("created", "")
            if isinstance(created, str) and created < cutoff:
                bottlenecks.append({
                    "file": f.name,
                    "issue": "Awaiting approval > 48 hours",
                    "created": created,
                    "priority": "high",
                })

        # Check Errors for failed tasks
        for f in list_md_files("Errors"):
            meta, _ = frontmatter.read_file(f)
            if meta.get("status") == "failed":
                bottlenecks.append({
                    "file": f.name,
                    "issue": f"Failed after {meta.get('max_retries', '?')} retries",
                    "created": meta.get("created", "?"),
                    "priority": "high",
                })

        return bottlenecks

    def generate_briefing(self) -> Path:
        """Generate the full Monday briefing markdown file."""
        task_stats = self.gather_task_stats()
        odoo_stats = self.gather_odoo_stats()
        social_stats = self.gather_social_stats()
        bottlenecks = self.detect_bottlenecks()

        date_str = self.now.strftime("%Y-%m-%d")
        week_range = f"{self.week_start.strftime('%b %d')} — {self.now.strftime('%b %d, %Y')}"

        # Build briefing markdown
        metadata = {
            "type": "briefing",
            "priority": "high",
            "status": "generated",
            "created": self.now.strftime("%Y-%m-%d %H:%M:%S"),
            "week": week_range,
        }

        body = f"# Monday CEO Briefing\n\n"
        body += f"**Week:** {week_range}\n"
        body += f"**Generated:** {self.now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        body += "---\n\n"

        # Executive Summary
        body += "## Executive Summary\n\n"
        body += f"- **{task_stats['done_this_week']}** tasks completed this week "
        body += f"({task_stats['total_done']} total all-time)\n"
        body += f"- **{task_stats['pending_tasks']}** tasks pending, "
        body += f"**{task_stats['pending_approvals']}** awaiting approval\n"
        body += f"- **${odoo_stats['total_revenue_collected']:,.2f}** revenue collected, "
        body += f"**${odoo_stats['outstanding_amount']:,.2f}** outstanding\n"
        if bottlenecks:
            body += f"- **{len(bottlenecks)} bottleneck(s)** detected — see details below\n"
        else:
            body += "- No bottlenecks detected\n"
        body += "\n"

        # Revenue & Accounting
        body += "## Revenue & Accounting\n\n"
        body += "| Metric | Value |\n|--------|-------|\n"
        body += f"| Revenue Collected | ${odoo_stats['total_revenue_collected']:,.2f} |\n"
        body += f"| Outstanding | ${odoo_stats['outstanding_amount']:,.2f} |\n"
        body += f"| Draft Invoices | {odoo_stats['draft_invoices']} |\n"
        body += f"| Overdue Invoices | {odoo_stats['overdue_invoices']} |\n"
        body += f"| Total Invoices | {odoo_stats['total_invoices']} |\n\n"

        # Completed Tasks
        body += "## Completed Tasks\n\n"
        body += "| Type | Count |\n|------|-------|\n"
        for prefix, count in sorted(task_stats['done_by_type'].items()):
            body += f"| {prefix} | {count} |\n"
        body += "\n"

        # Social Media Performance
        body += "## Social Media Performance\n\n"
        if isinstance(social_stats, dict):
            for platform, stats in social_stats.items():
                if isinstance(stats, dict):
                    body += f"### {platform.title()}\n\n"
                    for key, val in stats.items():
                        body += f"- **{key.replace('_', ' ').title()}:** {val}\n"
                    body += "\n"

        # Bottlenecks & Alerts
        body += "## Bottlenecks & Alerts\n\n"
        if bottlenecks:
            body += "| File | Issue | Priority | Created |\n|------|-------|----------|---------|\n"
            for b in bottlenecks:
                body += f"| {b['file']} | {b['issue']} | {b['priority']} | {b['created']} |\n"
        else:
            body += "No bottlenecks or alerts.\n"
        body += "\n"

        # Proactive Suggestions
        body += "## Proactive Suggestions\n\n"
        if odoo_stats['overdue_invoices'] > 0:
            body += "- [ ] **Follow up on overdue invoices** — send payment reminders (requires approval)\n"
        if odoo_stats['draft_invoices'] > 0:
            body += "- [ ] **Review draft invoices** — post or discard pending drafts\n"
        if task_stats['pending_approvals'] > 0:
            body += f"- [ ] **Clear approval queue** — {task_stats['pending_approvals']} items awaiting review\n"
        if not bottlenecks and odoo_stats['overdue_invoices'] == 0:
            body += "- All systems running smoothly. Consider setting new business development goals.\n"
        body += "\n"

        # Save to Briefings/
        briefings_dir = get_folder("Briefings")
        briefing_path = briefings_dir / f"{date_str}_Monday_Briefing.md"
        frontmatter.write_file(briefing_path, metadata, body)

        log_action("Audit", f"Briefing generated: {briefing_path.name}", "auditor")
        audit_log("briefing_generated", actor="auditor",
                  params={"file": briefing_path.name, "tasks_done": task_stats['done_this_week']})

        return briefing_path


def main():
    parser = argparse.ArgumentParser(description="Weekly business auditor")
    parser.add_argument("--mock", action="store_true", help="Use mock data")
    args = parser.parse_args()

    auditor = WeeklyAuditor(mock=args.mock)
    path = auditor.generate_briefing()
    print(f"Briefing generated: {path}")


if __name__ == "__main__":
    main()
