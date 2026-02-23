# Process Payment

Handle a payment task (LOCAL-ONLY).

## When to use
When a PAYMENT_*.md task needs processing.

## Steps
1. Read the task file to understand the payment request
2. Use list_accounts and get_balance to verify source account
3. Use list_transactions for recent activity context
4. Create a payment plan with full details
5. Route to Pending_Approval/ — ALL payments require human approval
6. Once approved, use initiate_payment MCP tool
7. Track with payment_status tool

## Rules
- ALL payments ALWAYS require human approval — no exceptions
- This skill is LOCAL-ONLY (banking credentials never sync to cloud)
- Double-check recipient details before initiating
- Log all payment actions to Logs/ with full audit trail
- Never initiate duplicate payments
