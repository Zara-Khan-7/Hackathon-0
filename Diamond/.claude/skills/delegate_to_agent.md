# Delegate to Agent

Route a task to the best specialized agent in the Diamond swarm.

## When to use
When the SwarmOrchestrator needs to assign a task to a specialized agent (Sales, Finance, Content, or Security).

## Steps
1. Read the task file from Needs_Action/
2. Classify the task type by prefix (EMAIL_, PAYMENT_, FACEBOOK_, etc.)
3. Query the AgentRegistry for the best-fit agent
4. Send an A2A delegation message via the MessageRouter
5. Agent processes the task and returns a result
6. Record the outcome in OutcomeTracker
7. Route to Pending_Approval/ if needed, otherwise move to Done/

## Rules
- Sales Agent handles: EMAIL_, LINKEDIN_, SALESPOST_
- Finance Agent handles: ODOO_, PAYMENT_, AUDIT_
- Content Agent handles: FACEBOOK_, INSTAGRAM_, TWITTER_, SOCIAL_, WHATSAPP_
- Security Agent handles: ERROR_, EXECUTE_ (validation)
- If no agent matches, fall back to base orchestrator pipeline
- Security Agent always scans outgoing content before external actions
