# Skill: Create Plan for Task

## Purpose
For each `.md` file in `Needs_Action/`, generate a `Plan_[original_name].md` with actionable next steps.

## Trigger
Run after "Scan Needs_Action" confirms pending items.

## Steps
1. Read `Company_Handbook.md` to load current rules.
2. For each `.md` file in `Needs_Action/`:
   - Read its contents.
   - Determine task type (email, invoice, research, etc.).
   - Check if the task involves money, contacts, or messaging → if yes, flag for `Pending_Approval/`.
   - Generate a plan file `Plan_[original_name].md` in `Needs_Action/`.
3. Each plan file contains:
   - Reference to the source file.
   - Checklist of concrete next steps.
   - Any handbook rules that apply.
   - Approval flag if needed.

## Output Format
```markdown
# Plan: [Task Title]
**Source:** Needs_Action/[filename]
**Created:** [timestamp]
**Requires Approval:** Yes/No

## Steps
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Applicable Rules
- [relevant handbook rules]
```

## Rules (from Company_Handbook)
- Never take destructive actions without a plan.
- Money/contacts/messaging tasks → create approval request in Pending_Approval/.
