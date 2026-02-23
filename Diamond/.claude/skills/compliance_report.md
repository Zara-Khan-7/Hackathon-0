# Compliance Report

Generate a compliance audit report covering all agent activities.

## When to use
Weekly (or on-demand) to verify system compliance with business rules.

## Steps
1. Check approval pipeline integrity (all EXECUTE_ files have APPROVE_ records)
2. Verify audit log completeness and recency
3. Check error accumulation (flag if >10 unresolved errors)
4. Check task completion rates from OutcomeTracker
5. Generate markdown compliance report
6. Save report to Briefings/ folder
7. If violations found, create ERROR_COMPLIANCE_*.md in Errors/

## Checks
- All dangerous actions went through human approval
- Audit trail is complete and recent (within 24h)
- Errors are being handled, not accumulating
- Task success rate is above 50% threshold
- No credential leaks in outgoing content
