# Skill: Update Dashboard

## Purpose
Rewrite `Dashboard.md` with current counts across all folders, approval stats, type breakdowns, accounting/social/audit stats, error tracking, and recent activity.

## Trigger
Run after task completion, approval decisions, audit generation, or on-demand for status check.

## Steps
1. Count `.md` files in each folder (exclude `Plan_*` files from counts):
   - `Inbox/`
   - `Needs_Action/`
   - `Pending_Approval/`
   - `Approved/`
   - `Rejected/`
   - `Done/`
   - `Accounting/`
   - `Briefings/`
   - `Errors/`
2. Count by type prefix in `Needs_Action/`:
   - EMAIL_*, LINKEDIN_*, EXECUTE_*, SALESPOST_*, SCHEDULE_*, ODOO_*, FACEBOOK_*, INSTAGRAM_*, TWITTER_*, SOCIAL_*, AUDIT_*, ERROR_*
3. Count by type in `Pending_Approval/`:
   - APPROVE_* files waiting for human review
4. Gather Accounting summary (if available from Odoo MCP):
   - Revenue collected, outstanding amount, draft invoices, overdue invoices
5. Gather Social Media summary (if available from Social MCP):
   - Per-platform engagement stats (likes, comments, DMs)
6. Check Audit status:
   - Last audit date (latest file in Briefings/)
   - Bottleneck count from latest audit
7. Check Error status:
   - Active errors in Errors/
   - Retryable vs. escalated counts
8. Read most recent 3 log entries from `Logs/`.
9. Rewrite `Dashboard.md` with all updated stats.

## Output Format
```markdown
# AI Employee Dashboard — Gold Tier

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
| Accounting | [n] |
| Briefings | [n] |
| Errors | [n] |

## Task Breakdown (Needs_Action)
- Emails: [n] | LinkedIn: [n] | Execute: [n]
- Sales Posts: [n] | Scheduled: [n] | Odoo: [n]
- Facebook: [n] | Instagram: [n] | Twitter: [n]
- Social: [n] | Audit: [n] | Error: [n]

## Accounting (Odoo)
| Metric | Value |
|--------|-------|
| Revenue Collected | $X,XXX |
| Outstanding | $X,XXX |
| Draft Invoices | [n] |
| Overdue Invoices | [n] |

## Social Media
| Platform | Posts | Likes | DMs |
|----------|-------|-------|-----|
| Facebook | [n] | [n] | [n] |
| Instagram | [n] | [n] | [n] |
| Twitter | [n] | [n] | [n] |

## Audit Status
- Last audit: [date]
- Latest briefing: [filename]
- Bottlenecks: [count]

## Error Tracking
- Active errors: [n]
- Retryable: [n]
- Escalated: [n]

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
- If Odoo or Social MCP data is unavailable, show "N/A" — don't fail.
- Include all Gold tier sections (accounting, social, audit, errors).
