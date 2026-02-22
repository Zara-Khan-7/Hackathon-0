# Claim Task

Claim a task from Needs_Action/ for exclusive processing.

## When to use
When a task file needs to be claimed by this agent to prevent double-processing.

## Steps
1. Read the task file from Needs_Action/
2. Move it to In_Progress/{agent_id}/ using ClaimManager
3. Log the claim action
4. If claim fails (file already taken), skip and move on

## Rules
- Only claim files that match your role's domain routing
- Cloud agents: skip WHATSAPP_, PAYMENT_, EXECUTE_, APPROVE_ prefixes
- Local agents: can claim any prefix
- If a claim fails, do NOT retry — another agent owns it
