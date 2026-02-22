"""Scheduler — manages recurring tasks using the `schedule` library.

Default schedules:
- Daily scan: 9:00 AM — scan Needs_Action/ and process items
- Weekly LinkedIn post: Friday 4:00 PM — generate sales post draft
- Monday CEO briefing: Monday 8:00 AM — compile weekly summary

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
)
from src.utils.logger import log_action, log_error

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
            "4. Update Dashboard.md\n"
        )

        date_str = datetime.now().strftime("%Y%m%d")
        filepath = create_task_file("Needs_Action", "SCHEDULE", f"daily_scan_{date_str}", metadata, body)
        log_action("Daily scan task created", filepath.name, "scheduler")

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

    def monday_briefing(self) -> None:
        """Monday CEO briefing — compile weekly summary."""
        log_action("Scheduler", "Triggering Monday briefing", "scheduler")

        # Gather stats
        done_count = len(list_md_files("Done"))
        pending_count = len(list_md_files("Needs_Action"))
        approval_count = len(list_md_files("Pending_Approval"))
        approved_count = len(list_md_files("Approved"))
        rejected_count = len(list_md_files("Rejected"))

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
            f"**Schedule:** Monday at {os.getenv('MONDAY_BRIEFING_TIME', '08:00')}\n\n"
            "## Weekly Summary\n\n"
            f"- Tasks completed: {done_count}\n"
            f"- Currently pending: {pending_count}\n"
            f"- Awaiting approval: {approval_count}\n"
            f"- Approved this period: {approved_count}\n"
            f"- Rejected this period: {rejected_count}\n\n"
            "## Actions\n\n"
            "1. Compile detailed weekly report\n"
            "2. Highlight key decisions made\n"
            "3. List upcoming tasks and deadlines\n"
            "4. Provide recommendations for the week ahead\n"
            "5. Update Dashboard.md with weekly stats\n"
        )

        date_str = datetime.now().strftime("%Y%m%d")
        filepath = create_task_file("Needs_Action", "SCHEDULE", f"monday_briefing_{date_str}", metadata, body)
        log_action("Monday briefing task created", filepath.name, "scheduler")

    def setup_schedules(self) -> None:
        """Configure all recurring schedules."""
        daily_time = os.getenv("DAILY_SCAN_TIME", "09:00")
        post_day = os.getenv("WEEKLY_POST_DAY", "friday").lower()
        post_time = os.getenv("WEEKLY_POST_TIME", "16:00")
        briefing_time = os.getenv("MONDAY_BRIEFING_TIME", "08:00")

        # Daily scan
        schedule.every().day.at(daily_time).do(self.daily_scan)
        log_action("Schedule set", f"Daily scan at {daily_time}", "scheduler")

        # Weekly LinkedIn post
        getattr(schedule.every(), post_day).at(post_time).do(self.weekly_linkedin_post)
        log_action("Schedule set", f"Weekly post on {post_day} at {post_time}", "scheduler")

        # Monday briefing
        schedule.every().monday.at(briefing_time).do(self.monday_briefing)
        log_action("Schedule set", f"Monday briefing at {briefing_time}", "scheduler")

    def run(self, once: bool = False) -> None:
        """Main scheduler loop."""
        mode = "dry-run" if self.dry_run else "live"
        log_action("Scheduler", f"Starting ({mode} mode)", "scheduler")

        self.setup_schedules()

        if once:
            # Run all pending jobs immediately for testing
            log_action("Scheduler", "Running all jobs once...", "scheduler")
            schedule.run_all()
            log_action("Scheduler", "Single run complete.", "scheduler")
            return

        log_action("Scheduler", "Entering main loop. Press Ctrl+C to stop.", "scheduler")
        while self._running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

        log_action("Scheduler", "Stopped.", "scheduler")


def main():
    parser = argparse.ArgumentParser(description="AI Employee Scheduler")
    parser.add_argument("--dry-run", action="store_true", help="Don't execute real actions")
    parser.add_argument("--once", action="store_true", help="Run all jobs once and exit")
    parser.add_argument(
        "--trigger",
        choices=["daily_scan", "weekly_post", "monday_briefing"],
        help="Trigger a specific job immediately",
    )
    args = parser.parse_args()

    sched = AIScheduler(dry_run=args.dry_run)

    if args.trigger:
        job = {
            "daily_scan": sched.daily_scan,
            "weekly_post": sched.weekly_linkedin_post,
            "monday_briefing": sched.monday_briefing,
        }[args.trigger]
        job()
    else:
        sched.run(once=args.once)


if __name__ == "__main__":
    main()
