# Bronze Tier — File-Based Task Queue System

**Status:** Implemented | **Tests:** 0 | **Skills:** 4 | **MCP Servers:** 0

## What This Tier Does

Bronze is the **foundation layer** — a simple, file-based task queue where Markdown files represent tasks. There is no automation, no watchers, and no MCP servers. A human (or the next tier) drops task files into `Needs_Action/`, and the AI agent processes them using 4 basic skills.

Think of it as a **digital inbox** with a structured workflow.

## How It Works

```
                   ┌──────────────┐
                   │   Human /    │
                   │  Upper Tier  │
                   └──────┬───────┘
                          │ drops .md file
                          ▼
               ┌──────────────────┐
               │  Needs_Action/   │  ◄── Task files land here
               │  EMAIL_xxx.md    │
               │  TASK_yyy.md     │
               └──────────┬──────┘
                          │ Agent picks up
                          ▼
               ┌──────────────────┐
               │  AI Agent reads  │
               │  + creates plan  │
               │  + executes task │
               └──────────┬──────┘
                          │ moves to
                          ▼
               ┌──────────────────┐
               │     Done/        │  ◄── Completed tasks stored here
               └──────────────────┘
                          │
                          ▼
               ┌──────────────────┐
               │  Dashboard.md    │  ◄── Updated with stats
               └──────────────────┘
```

## Directory Structure

```
Bronze/
├── .claude/
│   └── skills/
│       ├── scan_needs_action.md    # Skill 1: List pending tasks
│       ├── create_plan.md          # Skill 2: Create action plan
│       ├── complete_task.md        # Skill 3: Execute a task
│       └── update_dashboard.md     # Skill 4: Refresh Dashboard
├── Inbox/                          # Raw incoming items (triage)
├── Needs_Action/                   # Active task queue
├── Pending_Approval/               # Tasks awaiting human review
├── Done/                           # Completed tasks
├── Logs/                           # Action logs
├── Dashboard.md                    # Live status board
├── Company_Handbook.md             # Workflow rules
└── README.md                       # This file
```

## Task File Format

Tasks are plain Markdown files. No YAML frontmatter required at this tier (Silver adds that).

```markdown
# Task: Reply to client email

Client John Smith asked about pricing for our Premium plan.
Draft a professional reply with the current pricing sheet attached.
```

## The 4 Skills

| # | Skill | What It Does |
|---|-------|-------------|
| 1 | `scan_needs_action` | Scans `Needs_Action/` and lists all pending tasks with their filenames and content preview |
| 2 | `create_plan` | Reads a task file and generates a step-by-step action plan |
| 3 | `complete_task` | Executes the plan — writes a response, creates output files, and moves the task to `Done/` |
| 4 | `update_dashboard` | Counts files in each folder and refreshes `Dashboard.md` with current stats |

## Key Rules (from Company_Handbook.md)

- Be professional, concise, and polite
- Never take destructive actions without a plan
- Anything involving money or sending messages → needs approval
- When finished → move to `Done/` and update `Dashboard.md`
- On error → log in `Logs/`

## What Bronze Does NOT Have

- No watchers (no automatic email/social monitoring)
- No orchestrator (no automated polling loop)
- No MCP servers (no external tool integration)
- No tests (testing starts in Silver)
- No YAML frontmatter (structured metadata starts in Silver)
- No approval pipeline (HITL approval starts in Silver)

## What the Next Tier (Silver) Adds

Silver builds on Bronze by adding:
- Gmail and LinkedIn **watchers** that automatically create task files
- An **orchestrator** that polls `Needs_Action/` every 10 seconds
- An **Email MCP server** for sending/drafting emails
- A **HITL approval pipeline** with terminal-based review
- A **scheduler** for recurring tasks
- YAML frontmatter for machine-readable task metadata
- 4 additional skills (8 total)
