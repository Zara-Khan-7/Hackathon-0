# CRM Sync

Synchronize CRM data (contacts, deals, activities) with the AI Employee.

## When to use
When the Sales Agent needs CRM context for email replies or outreach, or when generating reports that need pipeline data.

## Steps
1. Connect to CRM client (mock mode by default)
2. List active contacts and recent activities
3. Check deal pipeline for open opportunities
4. Provide context to Sales Agent for personalized communication
5. Log any new activities back to CRM
6. Update dashboard with pipeline summary

## Rules
- CRM is in mock mode by default (MOCK_DATA=true)
- Never modify CRM contacts without approval
- Use pipeline summary for audit reports
- Activity logging is automatic when tasks complete
