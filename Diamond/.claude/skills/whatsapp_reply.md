# WhatsApp Reply

Compose and send a WhatsApp reply (LOCAL-ONLY).

## When to use
When a WHATSAPP_*.md task needs a response.

## Steps
1. Read the task file to understand the incoming message
2. Read the chat history using read_whatsapp_chat MCP tool
3. Draft a professional, concise reply
4. Route to Pending_Approval/ for human review
5. Once approved, use send_whatsapp MCP tool to send

## Rules
- NEVER send a WhatsApp message without human approval
- This skill is LOCAL-ONLY (WhatsApp session files never sync to cloud)
- Keep replies professional and concise
- Use the read_whatsapp_chat tool to understand context
- Log all message actions to Logs/
