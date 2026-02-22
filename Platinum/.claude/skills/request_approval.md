# Skill: Request Approval

## Purpose
Create a structured approval request in `Pending_Approval/` for actions that require human review before execution.

## Trigger
- Invoked by orchestrator when a task has `requires_approval: true`.
- Invoked by other skills (complete_task, generate_sales_post) when they detect sensitive actions.

## When Approval Is Required
Per Company Handbook rules:
- Anything involving **money** (invoices, payments, billing)
- Anything involving **new contacts** (connection requests, partnerships)
- Anything involving **sending messages** (emails, LinkedIn messages, posts)
- Any **external-facing action** (publishing, API calls to third parties)

## Steps
1. Gather all context about the proposed action:
   - Original task file and its metadata
   - Plan file (if exists)
   - Proposed action details (draft email, post content, etc.)
2. Create `APPROVE_[task_name].md` in `Pending_Approval/` with:
   - YAML frontmatter with full metadata
   - Clear description of what will happen if approved
   - The exact content that will be sent/published
   - Risk assessment
3. Log the approval request creation.

## Approval File Format
```markdown
---
type: approval
original_task: [source filename]
task_type: [email|linkedin|sales_post|etc]
priority: [high|medium|low]
from: [sender if applicable]
subject: [subject if applicable]
status: pending_approval
created: [timestamp]
---

# Approval Request: [Title]

**Task:** [source filename]
**Type:** [task type]
**Priority:** [priority]
**Risk:** [low|medium|high]

## What Will Happen
[Clear description of the proposed action]

## Proposed Content
[Draft email / post / message that will be sent]

## Action Required
Choose one:
- **APPROVE** — Execute this action
- **REJECT** — Cancel this action
- **MODIFY** — Edit the content and re-submit
```

## Rules
- Every approval request must include the exact content that will be acted upon.
- Never execute a sensitive action without an approval file first.
- Include enough context for the reviewer to make an informed decision.
