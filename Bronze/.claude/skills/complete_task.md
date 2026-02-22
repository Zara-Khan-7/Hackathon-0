# Skill: Complete Task & Cleanup

## Purpose
Execute (or simulate) a task from its plan, log the result, move the source to `Done/`, and clean up.

## Trigger
Run after a plan has been created and reviewed.

## Steps
1. Read `Company_Handbook.md` to confirm rules.
2. Read the `Plan_[name].md` file for the task.
3. If **Requires Approval = Yes** → write approval request to `Pending_Approval/` and STOP. Do not proceed.
4. If **Requires Approval = No** → simulate execution:
   - For Bronze tier: write a summary of what *would* be done (no real external actions).
   - Mark all plan checkboxes as complete.
5. Write a log entry to `Logs/[timestamp]_[task_name].md` with:
   - What was done.
   - Outcome (simulated for Bronze).
   - Timestamp.
6. Move the original task file from `Needs_Action/` → `Done/`.
7. Move (or delete) the `Plan_[name].md` from `Needs_Action/` → `Done/`.
8. Trigger "Update Dashboard" skill.

## Rules (from Company_Handbook)
- When task finished → move source file to Done/ and update Dashboard.md.
- Log important actions in Logs/.
- Never take destructive actions without a plan.
