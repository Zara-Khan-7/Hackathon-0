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
     - **general:** Simulate execution, document what would be done.
   - Mark all plan checkboxes as complete.
5. Write log entry to `Logs/[date]_[task_name].md`.
6. Move original task file from `Needs_Action/` → `Done/`.
7. Move `Plan_[name].md` from `Needs_Action/` → `Done/`.
8. Trigger `update_dashboard` skill.

## MCP Integration
For email sending, use the MCP email server tools:
- `draft_email` — Create a draft (always safe, dry-run compatible)
- `send_email` — Send an email (respects DRY_RUN flag)

Call via: `echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"send_email","arguments":{...}},"id":1}' | python -m src.mcp_email.email_server`

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
