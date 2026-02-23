---
skill: handle_error
description: Detect failures in Errors/, attempt recovery, escalate if needed
triggers:
  - ERROR_ files in Needs_Action/ or Errors/
  - Daily scan error check
requires_approval: false (unless escalating)
---

# Handle Error

## When to Use
Triggered when ERROR_*.md files are found in Errors/ or when error tasks appear in Needs_Action/. Attempts automatic recovery for retryable errors and escalates persistent failures to the human operator.

## Steps
1. Read the ERROR_*.md file — parse frontmatter for:
   - `error_type`: What went wrong
   - `task_name`: Original task that failed
   - `retry_count` / `max_retries`: How many attempts remain
   - `can_retry`: Boolean — is automatic retry possible?
   - `original_file`: Path to the original task
2. **If retryable** (`can_retry=true`):
   - Re-create the original task file in Needs_Action/ with updated retry count
   - Update the ERROR_ file status to "retrying"
   - Log the retry attempt
3. **If NOT retryable** (`can_retry=false` or max retries exhausted):
   - Create APPROVE_ERROR_*.md in Pending_Approval/ requesting human intervention
   - Include full error details, traceback, and suggested actions
   - Mark ERROR_ file status as "escalated"
4. Update Dashboard.md error counts
5. Log all actions to Logs/

## Error Classification
| Error Type | Action |
|------------|--------|
| MCP timeout | Retry (transient) |
| Claude CLI error | Retry (transient) |
| File not found | Investigate (non-retryable) |
| API auth failure | Escalate to human |
| Odoo connection | Retry, then escalate |
| Unknown | Escalate to human |

## Important Rules
- Never silently discard errors — always log and track
- Maximum 3 retries before escalation (configurable)
- Escalation always goes through HITL approval
- Include enough context in escalation for the human to diagnose
- If the original task file is gone, note this in the escalation
