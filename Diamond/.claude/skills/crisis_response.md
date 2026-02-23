# Crisis Response

Handle security alerts and system emergencies via the Security Agent.

## When to use
When the Security Agent detects a threat, credential leak, or policy violation.

## Steps
1. Security Agent scans outgoing content for sensitive keywords
2. If threat detected, broadcast SECURITY_ALERT via A2A message bus
3. All agents receive the alert and pause non-critical operations
4. Create ERROR_SECURITY_*.md in Errors/ with details
5. Flag affected tasks for manual review
6. Generate compliance report documenting the incident
7. Log full audit trail

## Alert Types
- credential_leak: Sensitive data (passwords, tokens, API keys) in outgoing content
- policy_violation: Action attempted without required approval
- error_accumulation: >10 unresolved errors detected
- system_degradation: Agent heartbeat stale or high failure rate

## Rules
- ALL security alerts require human review
- Affected tasks are blocked until cleared
- Full audit trail is mandatory
- Never suppress or ignore security alerts
