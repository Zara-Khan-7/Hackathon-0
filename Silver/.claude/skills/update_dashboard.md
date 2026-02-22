# Skill: Update Dashboard

## Purpose
Rewrite `Dashboard.md` with current counts across all folders, approval stats, type breakdowns, and recent activity.

## Trigger
Run after task completion, approval decisions, or on-demand for status check.

## Steps
1. Count `.md` files in each folder (exclude `Plan_*` files from counts):
   - `Inbox/`
   - `Needs_Action/`
   - `Pending_Approval/`
   - `Approved/`
   - `Rejected/`
   - `Done/`
2. Count by type prefix in `Needs_Action/`:
   - EMAIL_*, LINKEDIN_*, EXECUTE_*, SALESPOST_*, SCHEDULE_*
3. Count by type in `Pending_Approval/`:
   - APPROVE_* files waiting for human review
4. Read most recent 3 log entries from `Logs/`.
5. Rewrite `Dashboard.md` with updated stats.

## Output Format
```markdown
# AI Employee Dashboard

## Status
- Last checked: [timestamp]
- Mode: [DRY_RUN / LIVE]
- Pending actions: [count]
- Awaiting approval: [count]

## Quick Stats
| Folder | Count |
|--------|-------|
| Inbox | [n] |
| Needs Action | [n] |
| Pending Approval | [n] |
| Approved | [n] |
| Rejected | [n] |
| Done | [n] |

## Task Breakdown (Needs_Action)
- Emails: [n]
- LinkedIn: [n]
- Execute: [n]
- Sales Posts: [n]
- Scheduled: [n]

## Approval Stats
- Pending: [n]
- Approved (total): [n]
- Rejected (total): [n]

## Recent Activity
- [latest 3 log entries with timestamps]
```

## Rules
- Dashboard must always reflect the true current state.
- Read-only on task folders — only write to `Dashboard.md`.
- Include approval pipeline stats (new for Silver tier).
- Show type breakdown for actionable items.
