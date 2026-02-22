# Skill: Complete Task

## Purpose
Execute (or simulate) a task from its plan, log the result, move source to `Done/`, and trigger dashboard update. Integrates with MCP email server for send actions.

## Trigger
Run after plan is created and reviewed (or auto-executed for low-risk tasks).

## Steps
1. Read `Company_Handbook.md` for current rules.
2. Read the `Plan_[name].md` file and parse its frontmatter.
3. **If Requires Approval = Yes:**
   - Write approval request to `Pending_Approval/APPROVE_[name].md` with full context.
   - Include the plan, original content, and proposed action.
   - STOP — do not execute.
4. **If Requires Approval = No:**
   - Execute based on task type:
     - **email (newsletter/low-priority):** Summarize, file, no reply needed.
     - **email (requires reply):** Use MCP email server to draft/send (dry-run default).
     - **linkedin/engagement:** Log metrics, suggest follow-up content ideas.
     - **execute (pre-approved):** Carry out the approved action via MCP tools.
     - **sales_post:** Trigger the `generate_sales_post` skill.
     - **schedule:** Trigger the `schedule_task` skill.
     - **odoo:** Use ai-employee-odoo MCP tools (sync_odoo_transactions, create_invoice_draft).
     - **facebook/instagram/twitter:** Use ai-employee-social MCP tools (draft_social_post, get_social_summary).
     - **social:** Use ai-employee-social MCP to summarize_social_activity.
     - **audit:** Run WeeklyAuditor from src.audit.auditor to generate CEO briefing.
     - **error:** Use ErrorHandler from src.errors.error_handler for recovery/escalation.
     - **general:** Simulate execution, document what would be done.
   - Mark all plan checkboxes as complete.
5. Write log entry to `Logs/[date]_[task_name].md`.
6. Move original task file from `Needs_Action/` → `Done/`.
7. Move `Plan_[name].md` from `Needs_Action/` → `Done/`.
8. Trigger `update_dashboard` skill.

## MCP Integration
Three MCP servers available for task execution:

**ai-employee-email** — Email operations:
- `draft_email` — Create a draft (always safe)
- `send_email` — Send an email (respects DRY_RUN)

**ai-employee-odoo** — Odoo ERP operations:
- `list_invoices`, `read_invoice` — Read invoice data
- `create_invoice_draft` — Create draft invoice (requires approval to post)
- `post_invoice` — Post invoice (requires prior approval)
- `list_partners` — Customer/vendor lookup
- `read_transactions` — Bank/cash transactions

**ai-employee-social** — Social media operations:
- `post_facebook`, `post_instagram`, `post_twitter` — Post content (requires approval)
- `get_social_summary` — Read engagement metrics
- `draft_social_post` — Save draft without posting

## Approved/ Flow
When processing EXECUTE_* files (from the approval pipeline):
1. Read the approved file from `Approved/` referenced in metadata.
2. Execute the approved action.
3. Move EXECUTE_* file to Done/.
4. Log the execution.

## Rules
- Move source file to `Done/` when finished.
- Log all actions in `Logs/`.
- Never take destructive actions without a plan.
- Dry-run mode: log what would be done instead of doing it.
