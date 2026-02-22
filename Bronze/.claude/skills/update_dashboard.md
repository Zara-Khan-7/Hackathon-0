# Skill: Update Dashboard

## Purpose
Rewrite `Dashboard.md` with current counts and recent activity.

## Trigger
Run after any task is completed, or on-demand for a status check.

## Steps
1. Count `.md` files in `Inbox/` (exclude Plan_ files).
2. Count `.md` files in `Needs_Action/` (exclude Plan_ files).
3. Count `.md` files in `Done/`.
4. Read the most recent log entry from `Logs/` for last activity.
5. Rewrite `Dashboard.md` with updated stats.

## Output Format
```markdown
# AI Employee Dashboard

## Status
- Last checked: [timestamp]
- Pending actions: [count of Needs_Action items]
- Recent activity: [description from latest log]

## Quick Stats
- Inbox items: [count]
- Needs Action: [count]
- Done this week: [count]

## Recent Log
- [latest 3 log entries, one-line each]
```

## Rules (from Company_Handbook)
- Dashboard must always reflect the true state of the folders.
- Read-only on task folders — only Dashboard.md is modified.
