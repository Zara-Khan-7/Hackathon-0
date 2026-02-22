# Route to Local

Route a task that requires local-only capabilities.

## When to use
When a cloud agent encounters a task that needs dangerous tools (sending email, posting invoices, WhatsApp, payments).

## Steps
1. Create a draft/plan for the task
2. Route to Pending_Approval/ with requires_approval=true
3. Git push so local agent can pick it up
4. Local agent will handle HITL approval and execution

## Rules
- Cloud NEVER executes dangerous tools
- Cloud creates drafts only (draft_email, create_invoice_draft, draft_social_post)
- Tasks requiring local execution: WHATSAPP_, PAYMENT_, EXECUTE_, APPROVE_
- Tasks cloud drafts: EMAIL_, LINKEDIN_, FACEBOOK_, INSTAGRAM_, TWITTER_, ODOO_
