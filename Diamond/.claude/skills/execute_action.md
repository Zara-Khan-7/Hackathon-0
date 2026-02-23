# Skill: Execute Action

## Purpose
Execute a previously approved action. Only processes EXECUTE_* files that have gone through the HITL approval pipeline.

## Trigger
- Invoked by orchestrator when it finds EXECUTE_* files in `Needs_Action/`.
- These files are created by the approval_watcher after the user approves an action.

## Steps
1. Read `Company_Handbook.md` for current rules.
2. Read the EXECUTE_* file and parse its frontmatter.
3. Verify approval chain:
   - Check that `source_approval` references a valid approval file.
   - Check that the approved file exists in `Approved/`.
4. Determine action type from metadata and execute:
   - **Email reply:** Use MCP email server (`send_email` or `draft_email` tool).
   - **LinkedIn message:** Log the response (Playwright send in live mode).
   - **LinkedIn connection:** Accept/decline (Playwright in live mode).
   - **Sales post:** Publish to LinkedIn (simulated in dry-run).
   - **Odoo invoice:** Call `post_invoice` on ai-employee-odoo MCP to confirm the draft.
   - **Odoo transaction:** Call `create_invoice_draft` on ai-employee-odoo MCP.
   - **Facebook post:** Call `post_facebook` on ai-employee-social MCP.
   - **Instagram post:** Call `post_instagram` on ai-employee-social MCP.
   - **Twitter post:** Call `post_twitter` on ai-employee-social MCP.
   - **General:** Execute the described action steps.
5. In **dry-run mode** (default):
   - Log what would be done to `Logs/`.
   - Write a summary to the EXECUTE file.
   - Do NOT make any external API calls.
6. In **live mode**:
   - Make the actual API call / send the message.
   - Log the result including any response/confirmation.
7. Move EXECUTE_* file to `Done/`.
8. Write detailed log entry to `Logs/`.
9. Trigger `update_dashboard` skill.

## MCP Execution
Three MCP servers available for executing approved actions:

**ai-employee-email** — `send_email`, `draft_email`
**ai-employee-odoo** — `post_invoice`, `create_invoice_draft`, `list_partners`
**ai-employee-social** — `post_facebook`, `post_instagram`, `post_twitter`

All calls respect the DRY_RUN flag. In dry-run mode, actions are logged but not sent.

## Safety Checks
- NEVER execute an action without a valid approval reference.
- ALWAYS respect the DRY_RUN flag from .env.
- Log every execution attempt, successful or not.
- If the approved file is missing or corrupted, log an error and skip.

## Rules
- Only process files with the EXECUTE_ prefix.
- All executions are logged in `Logs/`.
- Dry-run is the default — set DRY_RUN=false in .env for live execution.
