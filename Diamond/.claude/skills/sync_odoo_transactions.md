---
skill: sync_odoo_transactions
description: Read recent transactions from Odoo MCP and write summary to Accounting/
triggers:
  - ODOO_ files in Needs_Action/
  - Weekly audit schedule
requires_approval: false
---

# Sync Odoo Transactions

## When to Use
Triggered by ODOO_sync or ODOO_transactions tasks, or as part of the weekly audit. Reads recent bank/cash transactions from the Odoo ERP via the ai-employee-odoo MCP server and writes a formatted summary to Accounting/Current_Month.md.

## Steps
1. Call `read_transactions` tool on the **ai-employee-odoo** MCP server with `days=30`
2. Call `list_invoices` tool to get current invoice status
3. Format results as a markdown table with columns: Date, Description, Partner, Amount, Journal
4. Calculate totals: revenue in, expenses out, net
5. Create or update `Accounting/Current_Month.md` with YAML frontmatter:
   - type: accounting
   - created: current timestamp
   - period: current month
6. Log action to Logs/

## Output Format
```markdown
# Accounting Summary — [Month Year]

## Transactions (Last 30 Days)
| Date | Description | Partner | Amount | Journal |
|------|-------------|---------|--------|---------|
| ...  | ...         | ...     | $X.XX  | Bank    |

## Totals
- Revenue In: $X,XXX.XX
- Expenses Out: $X,XXX.XX
- Net: $X,XXX.XX

## Outstanding Invoices
| Invoice | Partner | Amount Due | Due Date | Status |
|---------|---------|------------|----------|--------|
```

## Important Rules
- This is a READ-ONLY operation — no approval needed
- Never modify Odoo data in this skill
- If Odoo MCP is unreachable, log the error and skip gracefully
- Always include the generation timestamp
