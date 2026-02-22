# AI Employee Project

An AI-powered employee agent that processes tasks through a structured queue system.

## Directory Structure

| Folder | Purpose |
|---|---|
| `Inbox/` | Raw incoming items for triage |
| `Needs_Action/` | Watchers write `.md` task files here |
| `Done/` | Completed tasks are moved here |
| `Logs/` | Action logs for audit |
| `.claude/skills/` | Agent skills and capabilities |

## Key Files

- **Dashboard.md** – Live overview of task queues and status
- **Company_Handbook.md** – Workflow rules and guidelines

## Getting Started

1. Drop a task file into `Needs_Action/`
2. The agent picks it up, processes it, and moves the result to `Done/`
3. Check `Dashboard.md` for current status
