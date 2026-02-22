"""Scheduler — manages recurring tasks using the `schedule` library.

Gold Tier schedules:
- Daily scan: 9:00 AM — scan Needs_Action/ and process items
- Weekly LinkedIn post: Friday 4:00 PM — generate sales post draft
- Monday CEO briefing: Monday 8:00 AM — compile weekly summary (references audit)
- Sunday weekly audit: Sunday 11:00 PM — run full business audit

All schedules respect DRY_RUN mode and create task files rather than
executing actions directly.
"""

import argparse
import os
import signal
import time
from datetime import datetime

import schedule
from dotenv import load_dotenv

from src.utils.file_ops import (
    create_task_file,
    get_folder,
    list_md_files,
    count_by_prefix,
)
from src.utils.logger import log_action, log_error, audit_log

load_dotenv()

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


class AIScheduler:
    """Manages recurring tasks for the AI Employee."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run or DRY_RUN
        self._running = True

        signal.signal(signal.SIGINT, self._handle_stop)
        signal.signal(signal.SIGTERM, self._handle_stop)

    def _handle_stop(self, signum, frame):
        log_action("Scheduler", "Shutting down...")
        self._running = False

    def daily_scan(self) -> None:
        """Daily morning scan — create a scan task for the orchestrator."""
        log_action("Scheduler", "Triggering daily scan", "scheduler")

        metadata = {
            "type": "schedule",
            "schedule_type": "daily_scan",
            "priority": "medium",
            "status": "pending",
            "requires_approval": False,
            "triggered_by": "scheduler",
        }

        body = (
            "# Scheduled: Daily Scan\n\n"
            f"**Triggered:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"**Schedule:** Daily at {os.getenv('DAILY_SCAN_TIME', '09:00')}\n\n"
            "## Actions\n\n"
            "1. Scan all folders for status\n"
            "2. Process any items in Needs_Action/\n"
            "3. Check for stale items in Pending_Approval/\n"
            "4. Check Errors/ for retryable tasks\n"
            "5. Update Dashboard.md\n"
        )

        date_str = datetime.now().strftime("%Y%m%d")
        filepath = create_task_file("Needs_Action", "SCHEDULE", f"daily_scan_{date_str}", metadata, body)
        log_action("Daily scan task created", filepath.name, "scheduler")
        audit_log("schedule_trigger", actor="scheduler", params={"job": "daily_scan"})

    def weekly_linkedin_post(self) -> None:
        """Weekly LinkedIn post — create a sales post task."""
        log_action("Scheduler", "Triggering weekly LinkedIn post", "scheduler")

        metadata = {
            "type": "schedule",
            "schedule_type": "weekly_post",
            "priority": "medium",
            "status": "pending",
            "requires_approval": False,
            "triggered_by": "scheduler",
        }

        body = (
            "# Scheduled: Weekly LinkedIn Post\n\n"
            f"**Triggered:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"**Schedule:** {os.getenv('WEEKLY_POST_DAY', 'friday').capitalize()} "
            f"at {os.getenv('WEEKLY_POST_TIME', '16:00')}\n\n"
            "## Actions\n\n"
            "1. Review recent completed tasks for content ideas\n"
            "2. Check LinkedIn engagement metrics\n"
            "3. Generate a thought-leadership post using generate_sales_post skill\n"
            "4. Route to Pending_Approval/ for human review\n"
        )

        date_str = datetime.now().strftime("%Y%m%d")
        filepath = create_task_file("Needs_Action", "SALESPOST", f"weekly_{date_str}", metadata, body)
        log_action("Weekly post task created", filepath.name, "scheduler")
        audit_log("schedule_trigger", actor="scheduler", params={"job": "weekly_post"})

    def monday_briefing(self) -> None:
        """Monday CEO briefing — compile weekly summary and reference latest audit."""
        log_action("Scheduler", "Triggering Monday briefing", "scheduler")

        # Gather stats
        done_count = len(list_md_files("Done"))
        pending_count = len(list_md_files("Needs_Action"))
        approval_count = len(list_md_files("Pending_Approval"))
        approved_count = len(list_md_files("Approved"))
        rejected_count = len(list_md_files("Rejected"))
        error_count = len(list_md_files("Errors"))
        done_by_type = count_by_prefix("Done")

        # Check for latest briefing from Sunday audit
        briefing_files = sorted(get_folder("Briefings").glob("*.md"), reverse=True)
        latest_briefing = briefing_files[0].name if briefing_files else "No audit briefing found"

        metadata = {
            "type": "schedule",
            "schedule_type": "monday_briefing",
            "priority": "high",
            "status": "pending",
            "requires_approval": False,
            "triggered_by": "scheduler",
        }

        body = (
            "# Scheduled: Monday CEO Briefing\n\n"
            f"**Triggered:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"**Schedule:** Monday at {os.getenv('MONDAY_BRIEFING_TIME', '08:00')}\n"
            f"**Latest Audit:** {latest_briefing}\n\n"
            "## Weekly Summary\n\n"
            f"- Tasks completed: {done_count}\n"
            f"- Currently pending: {pending_count}\n"
            f"- Awaiting approval: {approval_count}\n"
            f"- Approved this period: {approved_count}\n"
            f"- Rejected this period: {rejected_count}\n"
            f"- Errors/failures: {error_count}\n\n"
            "## Task Breakdown\n\n"
        )

        for prefix, count in sorted(done_by_type.items()):
            body += f"- {prefix}: {count}\n"

        body += (
            "\n## Actions\n\n"
            "1. Review the latest audit briefing in Briefings/\n"
            "2. Compile detailed weekly report\n"
            "3. Highlight key decisions made\n"
            "4. Review social media performance across all platforms\n"
            "5. Check Odoo revenue and outstanding invoices\n"
            "6. List upcoming tasks and deadlines\n"
            "7. Provide recommendations for the week ahead\n"
            "8. Update Dashboard.md with weekly stats\n"
        )

        date_str = datetime.now().strftime("%Y%m%d")
        filepath = create_task_file("Needs_Action", "SCHEDULE", f"monday_briefing_{date_str}", metadata, body)
        log_action("Monday briefing task created", filepath.name, "scheduler")
        audit_log("schedule_trigger", actor="scheduler", params={"job": "monday_briefing"})

    def sunday_audit(self) -> None:
        """Sunday weekly audit — run the full business/accounting audit."""
        log_action("Scheduler", "Triggering Sunday audit", "scheduler")

        metadata = {
            "type": "audit",
            "schedule_type": "weekly_audit",
            "priority": "high",
            "status": "pending",
            "requires_approval": False,
            "triggered_by": "scheduler",
        }

        body = (
            "# Scheduled: Weekly Business Audit\n\n"
            f"**Triggered:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"**Schedule:** Sunday at {os.getenv('SUNDAY_AUDIT_TIME', '23:00')}\n\n"
            "## Audit Steps\n\n"
            "1. Gather task completion statistics from Done/\n"
            "2. Gather revenue and invoice data from Odoo\n"
            "3. Gather social media engagement metrics\n"
            "4. Detect bottlenecks (tasks stuck > 48h, failed retries)\n"
            "5. Generate comprehensive CEO briefing in Briefings/\n"
            "6. Update Dashboard.md with audit results\n"
        )

        date_str = datetime.now().strftime("%Y%m%d")
        filepath = create_task_file("Needs_Action", "AUDIT", f"weekly_{date_str}", metadata, body)
        log_action("Sunday audit task created", filepath.name, "scheduler")
        audit_log("schedule_trigger", actor="scheduler", params={"job": "weekly_audit"})

    def setup_schedules(self) -> None:
        """Configure all recurring schedules."""
        daily_time = os.getenv("DAILY_SCAN_TIME", "09:00")
        post_day = os.getenv("WEEKLY_POST_DAY", "friday").lower()
        post_time = os.getenv("WEEKLY_POST_TIME", "16:00")
        briefing_time = os.getenv("MONDAY_BRIEFING_TIME", "08:00")
        audit_time = os.getenv("SUNDAY_AUDIT_TIME", "23:00")

        schedule.every().day.at(daily_time).do(self.daily_scan)
        log_action("Schedule set", f"Daily scan at {daily_time}", "scheduler")

        getattr(schedule.every(), post_day).at(post_time).do(self.weekly_linkedin_post)
        log_action("Schedule set", f"Weekly post on {post_day} at {post_time}", "scheduler")

        schedule.every().monday.at(briefing_time).do(self.monday_briefing)
        log_action("Schedule set", f"Monday briefing at {briefing_time}", "scheduler")

        schedule.every().sunday.at(audit_time).do(self.sunday_audit)
        log_action("Schedule set", f"Sunday audit at {audit_time}", "scheduler")

    def run(self, once: bool = False) -> None:
        """Main scheduler loop."""
        mode = "dry-run" if self.dry_run else "live"
        log_action("Scheduler", f"Starting ({mode} mode)", "scheduler")

        self.setup_schedules()

        if once:
            log_action("Scheduler", "Running all jobs once...", "scheduler")
            schedule.run_all()
            log_action("Scheduler", "Single run complete.", "scheduler")
            return

        log_action("Scheduler", "Entering main loop. Press Ctrl+C to stop.", "scheduler")
        while self._running:
            schedule.run_pending()
            time.sleep(60)

        log_action("Scheduler", "Stopped.", "scheduler")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Scheduler — Gold Tier")
    parser.add_argument("--dry-run", action="store_true", help="Don't execute real actions")
    parser.add_argument("--once", action="store_true", help="Run all jobs once and exit")
    parser.add_argument(
        "--trigger",
        choices=["daily_scan", "weekly_post", "monday_briefing", "weekly_audit"],
        help="Trigger a specific job immediately",
    )
    args = parser.parse_args()

    sched = AIScheduler(dry_run=args.dry_run)

    if args.trigger:
        job = {
            "daily_scan": sched.daily_scan,
            "weekly_post": sched.weekly_linkedin_post,
            "monday_briefing": sched.monday_briefing,
            "weekly_audit": sched.sunday_audit,
        }[args.trigger]
        job()
    else:
        sched.run(once=args.once)


if __name__ == "__main__":
    main()
