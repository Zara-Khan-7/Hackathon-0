---
skill: post_approved_invoice
description: Post a draft invoice in Odoo after HITL approval
triggers:
  - EXECUTE_ODOO_invoice tasks (from approval pipeline)
requires_approval: false (already approved)
---

# Post Approved Invoice

## When to Use
Triggered when an EXECUTE_ODOO_invoice_* file appears in Needs_Action/ after human approval. Posts (confirms) the draft invoice in Odoo, making it official.

## Steps
1. Verify the file originated from Approved/ (check source_approval metadata)
2. Extract the Odoo invoice_id from the task content
3. Call `post_invoice` on **ai-employee-odoo** MCP with the invoice_id
4. Verify the response shows state="posted"
5. Log the confirmation with invoice name, amount, and partner
6. Move the task file to Done/
7. Update Dashboard.md with new invoice stats

## Important Rules
- **REQUIRES prior HITL approval** — never post without verified approval chain
- If the invoice_id is missing or invalid, create an ERROR_ task
- If Odoo MCP returns an error, do NOT retry automatically — route to Errors/
- Log the full invoice details for audit trail
- This is a financial action — treat with maximum care
