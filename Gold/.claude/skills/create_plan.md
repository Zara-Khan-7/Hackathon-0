# Skill: Create Plan

## Purpose
Generate a `Plan_[original_name].md` for each task file in `Needs_Action/`. Plans are type-aware and include approval routing logic.

## Trigger
Run after "Scan Needs_Action" confirms pending items.

## Steps
1. Read `Company_Handbook.md` to load current rules.
2. For each `.md` file in `Needs_Action/` (ignore existing `Plan_*` files):
   a. Parse YAML frontmatter to get type, priority, requires_approval, subtype.
   b. Read body content to understand the task.
   c. Determine task type and select the appropriate plan template:
      - **email** → Draft reply, check attachments, determine send method
      - **linkedin/connection_request** → Evaluate profile, draft accept/decline response
      - **linkedin/message** → Draft reply, assess business opportunity
      - **linkedin/engagement** → Summarize metrics, suggest follow-up actions
      - **execute** → List concrete execution steps, verify approval exists
      - **sales_post** → Outline topic, key points, CTA, posting schedule
      - **schedule** → Define recurrence, target time, task to trigger
      - **odoo/invoice** → Review invoice details, verify partner in Odoo, create draft via Odoo MCP, route to approval
      - **odoo/transaction** → Sync transactions from Odoo, update Accounting/ records
      - **facebook/notification** → Assess notification, draft response if engagement needed
      - **instagram/dm** → Draft reply to DM, route to approval
      - **instagram/mention** → Acknowledge mention, draft engagement response
      - **twitter/mention** → Draft reply tweet, route to approval if engaging
      - **twitter/dm** → Draft response, route to approval
      - **social_post** → Generate platform-specific content (FB/IG/X), draft via social MCP, always route to approval
      - **audit** → Gather all system stats, generate CEO briefing, update dashboard
      - **error** → Assess error type, determine if retryable, attempt recovery or escalate to human
      - **general** → Generic checklist approach
   d. Check approval rules:
      - Money, invoices, payments → requires_approval = Yes
      - Sending messages to contacts → requires_approval = Yes
      - New business relationships → requires_approval = Yes
      - Publishing social media content → requires_approval = Yes
      - Posting invoices in Odoo → requires_approval = Yes
      - Internal/informational tasks → requires_approval = No
      - Audit/reporting tasks → requires_approval = No
      - Error recovery (retryable) → requires_approval = No
   e. Generate `Plan_[original_name].md` in `Needs_Action/` with frontmatter.

## Plan File Format
```
---
type: plan
source_file: [original filename]
task_type: [email|linkedin|execute|sales_post|schedule|odoo|facebook|instagram|twitter|social|audit|error]
priority: [high|medium|low]
requires_approval: [true|false]
created: [timestamp]
---

# Plan: [Task Title]

**Source:** Needs_Action/[filename]
**Type:** [task type] / [subtype]
**Priority:** [priority]
**Requires Approval:** [Yes/No]

## Steps
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Applicable Rules
- [Relevant handbook rules]

## Approval Routing
[If requires approval: "This task will be routed to Pending_Approval/ for human review."]
[If no approval: "This task can be executed directly."]
```

## Rules
- Never take destructive actions without a plan.
- Money/contacts/messaging → always create approval request in `Pending_Approval/`.
- One plan per task file. Skip files that already have a corresponding `Plan_` file.
