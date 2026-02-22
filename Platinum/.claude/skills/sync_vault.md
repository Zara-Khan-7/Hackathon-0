# Sync Vault

Synchronize task folders with the remote git repository.

## When to use
After processing tasks, to push local changes to remote and pull new tasks.

## Steps
1. Git pull: fetch latest changes from remote
2. Resolve any conflicts using folder-based strategy:
   - Needs_Action: keep theirs (incoming)
   - In_Progress: keep ours (local)
   - Logs: union merge (both)
3. Git push: stage sync folders and push

## Rules
- Always pull before push
- Use mock git operations in development
- Never push secrets or .env files
- Commit messages: [{agent_id}] Auto-sync {timestamp}
