---
skill: weekly_audit
description: Orchestrate the full weekly business audit and generate CEO briefing
triggers:
  - AUDIT_ tasks in Needs_Action/
  - Sunday 11 PM schedule
requires_approval: false
---

# Weekly Business Audit

## When to Use
Triggered by AUDIT_weekly_* tasks from the Sunday scheduler or manual invocation. Runs a comprehensive audit across all system components and generates a CEO briefing.

## Steps
1. **Gather task stats** from Done/ — count by type, completion rates, recent volume
2. **Gather Odoo stats** — call `list_invoices` and `read_transactions` on ai-employee-odoo MCP:
   - Total revenue collected
   - Outstanding amounts
   - Draft invoices pending
   - Overdue invoices
3. **Gather social stats** — call `get_social_summary` on ai-employee-social MCP:
   - Engagement metrics per platform
   - DM/message counts
4. **Detect bottlenecks**:
   - Tasks stuck in Needs_Action/ > 48 hours
   - Items in Pending_Approval/ > 48 hours
   - Failed tasks in Errors/ (exhausted retries)
5. **Generate briefing** — write to Briefings/YYYY-MM-DD_Monday_Briefing.md with sections:
   - Executive Summary (key numbers, alerts)
   - Revenue & Accounting (table from Odoo)
   - Completed Tasks (table by type)
   - Social Media Performance (table per platform)
   - Bottlenecks & Alerts (table of stuck/failed items)
   - Proactive Suggestions (actionable checklist with approval links)
6. Update Dashboard.md with latest audit timestamp
7. Move AUDIT_ task to Done/
8. Log audit completion

## Important Rules
- The audit itself does NOT require approval (it's read-only reporting)
- If any MCP server is unreachable, note it in the briefing and continue
- The briefing should be self-contained — a CEO should understand it without context
- Include clear numbers and trends, not vague statements
- Proactive suggestions should be actionable and indicate which ones need approval
