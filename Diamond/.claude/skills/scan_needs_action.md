# Skill: Scan Needs_Action

## Purpose
List all `.md` files in `Needs_Action/` folder, parse YAML frontmatter, classify by type and priority, and produce a sorted summary.

## Trigger
Run manually or as first step of task processing loop.

## Steps
1. Read `Company_Handbook.md` to confirm current rules.
2. List all `.md` files in `Needs_Action/` (ignore files starting with `Plan_`).
3. For each file:
   - Parse YAML frontmatter to extract: type, priority, from, subject, status, requires_approval
   - If no frontmatter, infer type from filename prefix (EMAIL_, LINKEDIN_, EXECUTE_, SALESPOST_, SCHEDULE_, ODOO_, FACEBOOK_, INSTAGRAM_, TWITTER_, SOCIAL_, AUDIT_, ERROR_)
   - Read body and produce 1-2 sentence summary
4. Sort results: high priority first, then medium, then low.
5. Output a numbered list grouped by type with priority tags.
6. Report total counts by type and priority.
7. If folder is empty, report "No pending tasks."

## Output Format
```
## Needs Action Summary (N items)

### High Priority
1. [EMAIL] EMAIL_mock_001.md — Invoice request from client@acme.com (financial)
2. [LINKEDIN] LINKEDIN_mock_002.md — DM from CTO about AI project (business_development)

### Medium Priority
3. [EXECUTE] EXECUTE_reply_client.md — Approved email reply, ready to send

### Low Priority
4. [EMAIL] EMAIL_mock_003.md — Weekly newsletter digest

## Counts
- Email: 2 | LinkedIn: 1 | Execute: 1 | Odoo: 0 | Facebook: 0 | Instagram: 0 | Twitter: 0 | Social: 0 | Audit: 0 | Error: 0
- High: 2 | Medium: 1 | Low: 1
- Requires Approval: 2
```

## Rules
- Read-only scan — never modify or delete files.
- Always parse YAML frontmatter first; fall back to filename prefix for type detection.
- Priority sort order: high > medium > low.
