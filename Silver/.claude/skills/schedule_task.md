# Skill: Schedule Task

## Purpose
Configure and manage recurring tasks: daily inbox scans, weekly LinkedIn posts, Monday CEO briefings.

## Trigger
- Invoked by orchestrator when processing SCHEDULE_* files.
- Invoked manually to set up new scheduled tasks.

## Available Schedules

### Daily Scan (9:00 AM)
- Run `scan_needs_action` skill
- Process any overnight items
- Generate morning summary

### Weekly LinkedIn Post (Friday 4:00 PM)
- Trigger `generate_sales_post` skill
- Route draft through approval pipeline
- Optimized for Friday afternoon engagement

### Monday CEO Briefing (8:00 AM)
- Compile weekly summary:
  - Tasks completed last week
  - Pending approvals
  - Key metrics (emails processed, LinkedIn engagement)
  - Upcoming scheduled items
- Create briefing in `Needs_Action/` for review

## Steps
1. Read the SCHEDULE_* task file for configuration:
   - Schedule type (daily_scan, weekly_post, monday_briefing, custom)
   - Time and recurrence settings
   - Any specific parameters
2. Validate the schedule configuration.
3. Register with the scheduler module (`src/scheduler/scheduler.py`).
4. Confirm registration by updating the task file.
5. Log the schedule setup.

## Schedule File Format
```markdown
---
type: schedule
schedule_type: [daily_scan|weekly_post|monday_briefing|custom]
time: "09:00"
day: "monday"
recurrence: [daily|weekly|monthly]
enabled: true
status: active
created: [timestamp]
---

# Scheduled Task: [Name]

**Type:** [schedule type]
**Time:** [HH:MM]
**Day:** [day of week, if weekly]
**Recurrence:** [daily|weekly|monthly]

## Task Details
[What this schedule triggers]

## History
- [Last 3 executions with timestamps]
```

## Rules
- All schedules respect the system timezone.
- Schedules can be paused by setting `enabled: false` in frontmatter.
- Every scheduled execution is logged.
- The scheduler process must be running for schedules to fire (`python -m src.scheduler.scheduler`).
