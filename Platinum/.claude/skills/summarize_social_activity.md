---
skill: summarize_social_activity
description: Fetch social metrics from all platforms and update Dashboard.md
triggers:
  - SOCIAL_summary tasks
  - Weekly audit
  - Monday briefing
requires_approval: false
---

# Summarize Social Activity

## When to Use
Triggered by SOCIAL_summary tasks, as part of the weekly audit, or when updating Dashboard.md. Fetches recent engagement metrics from all platforms and writes a summary.

## Steps
1. Call `get_social_summary` on **ai-employee-social** MCP with `platform="all"`
2. For each platform, extract:
   - **Facebook**: post count, total likes, comments, shares, notifications
   - **Instagram**: post count, likes, DMs received, mentions
   - **Twitter/X**: tweet count, likes, retweets, mentions, DMs
3. Calculate cross-platform totals
4. Update the **Social Media** section of Dashboard.md with formatted tables
5. Log action

## Output Format (for Dashboard.md)
```markdown
## Social Media Performance

| Platform | Posts | Likes | Comments | DMs |
|----------|-------|-------|----------|-----|
| Facebook | X     | X     | X        | X   |
| Instagram| X     | X     | X        | X   |
| Twitter  | X     | X     | X        | X   |
| **Total**| **X** | **X** | **X**    |**X**|
```

## Important Rules
- This is a READ-ONLY operation — no approval needed
- If a platform's MCP call fails, show "N/A" instead of crashing
- Always include the timestamp of when stats were fetched
- Do not include any PII or message content in the summary — only metrics
