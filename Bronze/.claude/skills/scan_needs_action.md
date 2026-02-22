# Skill: Scan Needs_Action

## Purpose
List all `.md` files in `Needs_Action/` and provide a brief summary of each.

## Trigger
Run manually or as first step of the task processing loop.

## Steps
1. Read `Company_Handbook.md` to confirm current rules apply.
2. List all `.md` files in `Needs_Action/`.
3. For each file:
   - Read its contents.
   - Produce a 1–2 sentence summary.
4. Output a numbered list of tasks with summaries.
5. If the folder is empty, report "No pending tasks in Needs_Action/."

## Output Format
```
## Needs_Action Scan – [timestamp]
1. **[filename]** – [summary]
2. **[filename]** – [summary]
...
Total: X item(s) pending.
```

## Rules (from Company_Handbook)
- Read-only scan — never modify or delete source files in this step.
