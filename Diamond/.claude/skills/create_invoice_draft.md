---
skill: create_invoice_draft
description: Create a draft invoice in Odoo from a task, then route to approval
triggers:
  - ODOO_invoice tasks in Needs_Action/
requires_approval: true
---

# Create Invoice Draft

## When to Use
Triggered when an ODOO_invoice_* task appears in Needs_Action/. Parses the task for partner and line item details, creates a draft invoice via the Odoo MCP server, and routes it to Pending_Approval/ for HITL review.

## Steps
1. Read the task file and extract:
   - Partner name/ID
   - Line items (description, quantity, unit price)
   - Invoice type (customer invoice = out_invoice, vendor bill = in_invoice)
2. Call `list_partners` on **ai-employee-odoo** MCP to verify the partner exists
3. Call `create_invoice_draft` on **ai-employee-odoo** MCP with partner_id and lines
4. Create an APPROVE_ODOO_invoice_*.md file in Pending_Approval/ containing:
   - Full invoice details (partner, lines, total)
   - The Odoo draft invoice ID
   - Clear instructions: "Approve to POST this invoice in Odoo"
5. Move original task to Done/
6. Log action and update dashboard

## Important Rules
- **NEVER post an invoice without HITL approval** — only create drafts
- Verify the partner exists before creating the draft
- Include the exact amount and line items in the approval request
- If partner not found, create an error task instead of guessing
- All financial actions require human review
