# Silver Tier — Email & LinkedIn Automation with HITL Approval

**Status:** Implemented | **Tests:** 1 | **Skills:** 8 | **MCP Servers:** 1 | **Watchers:** 2

## What This Tier Does

Silver is the **automation layer** — it transforms Bronze's manual file-drop system into a real-time pipeline. Gmail and LinkedIn watchers automatically detect incoming messages, the orchestrator processes them through Claude AI skills, and a Human-in-the-Loop (HITL) approval system ensures no external action happens without human consent.

Think of it as **hiring your first AI assistant** — one that monitors your inbox, drafts replies, and asks you before sending anything.

## Architecture

```
    ┌─────────────────────────────────────────────────────────┐
    │                   EXTERNAL SOURCES                       │
    │              Gmail API    LinkedIn (Playwright)           │
    └──────────┬─────────────────────────────┬────────────────┘
               │                             │
               ▼                             ▼
    ┌──────────────────┐          ┌──────────────────┐
    │  gmail_watcher.py │          │linkedin_watcher.py│
    │  (polls every 60s)│          │ (scrapes via mock)│
    │  --mock / --once  │          │ --mock / --once   │
    └────────┬─────────┘          └────────┬─────────┘
             │  creates EMAIL_*.md          │  creates LINKEDIN_*.md
             └──────────┬──────────────────┘
                        ▼
             ┌──────────────────┐
             │  Needs_Action/   │  <-- Task files land here
             │  EMAIL_001.md    │      with YAML frontmatter
             │  LINKEDIN_002.md │
             └────────┬────────┘
                      │  Orchestrator picks up
                      ▼
             ┌──────────────────────────────────┐
             │         Orchestrator              │
             │  1. Reads task file               │
             │  2. Classifies by prefix          │
             │  3. Invokes Claude CLI skill      │
             │  4. Creates action plan           │
             │  5. Checks: needs approval?       │
             └────────┬───────────┬─────────────┘
                      │           │
              No approval    Needs approval
              needed          (emails, posts)
                      │           │
                      ▼           ▼
             ┌────────────┐  ┌───────────────────┐
             │   Done/    │  │ Pending_Approval/  │
             └────────────┘  │ APPROVE_EMAIL_001  │
                             └────────┬──────────┘
                                      │
                                      ▼
                             ┌──────────────────────┐
                             │  approval_watcher.py  │
                             │  Terminal-based HITL   │
                             │  [A]pprove [R]eject   │
                             │  [M]odify  [S]kip     │
                             └────────┬──────────────┘
                                      │
                          ┌───────────┼───────────┐
                          ▼           ▼           ▼
                    ┌──────────┐ ┌──────────┐ ┌──────────┐
                    │ Approved/│ │ Rejected/│ │ Modified │
                    └────┬─────┘ └──────────┘ └──────────┘
                         │
                         ▼  creates EXECUTE_*.md
                    ┌──────────────────┐
                    │  Needs_Action/   │
                    │  EXECUTE_EMAIL_001│
                    └────────┬────────┘
                             │
                             ▼
                    ┌──────────────────────┐
                    │  MCP Email Server    │
                    │  (JSON-RPC 2.0)      │
                    │  send_email (dry-run) │
                    └────────┬─────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     Done/        │ + Logs/ + Dashboard.md
                    └──────────────────┘
```

## How the Workflow Works (Step by Step)

### Step 1: Detection (Watchers)
The **Gmail Watcher** polls the Gmail API every 60 seconds (or uses mock data with `--mock`). When it finds a new email, it creates a task file:

```markdown
---
type: email
priority: high
status: new
requires_approval: true
from: alice@techcorp.com
subject: Enterprise pricing inquiry
---
Hi, we're interested in your enterprise license.
Could you send pricing for 50 seats?
```

The file is saved as `Needs_Action/EMAIL_20260223_143022_alice.md`.

The **LinkedIn Watcher** does the same for LinkedIn messages/invitations, creating `LINKEDIN_*.md` files.

### Step 2: Processing (Orchestrator)
The orchestrator watches `Needs_Action/` using Python's `watchdog` library. When a new `.md` file appears:

1. **Reads** the YAML frontmatter to determine type and priority
2. **Classifies** the task by its filename prefix (`EMAIL_`, `LINKEDIN_`, `EXECUTE_`, `SALESPOST_`, `SCHEDULE_`)
3. **Invokes** the appropriate Claude CLI skill via `claude -p`
4. **Creates a plan** — a step-by-step action plan for how to handle the task
5. **Checks approval rules** — anything that sends external communications requires HITL

### Step 3: Approval (HITL Pipeline)
Tasks requiring approval are moved to `Pending_Approval/`. The `approval_watcher.py` presents each task in the terminal:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PENDING APPROVAL: APPROVE_EMAIL_001.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type: email | Priority: high
From: alice@techcorp.com
Subject: Enterprise pricing inquiry

Proposed Action:
  Draft reply with Premium plan pricing ($299/seat)

[A]pprove  [R]eject  [M]odify  [S]kip  >
```

- **Approve** — Creates `EXECUTE_EMAIL_001.md` in `Needs_Action/` for execution
- **Reject** — Moves to `Rejected/` with rejection reason
- **Modify** — Opens the content for editing, then re-prompts for approval
- **Skip** — Leaves in queue for later review

### Step 4: Execution (MCP Email Server)
When the orchestrator picks up an `EXECUTE_*` file, it calls the **Email MCP Server** via JSON-RPC 2.0:

```json
{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "send_email", "arguments": {"to": "alice@techcorp.com", "subject": "Re: Enterprise pricing inquiry", "body": "..."}}, "id": 1}
```

In `DRY_RUN=true` mode (default), the email is logged but not sent. The task file moves to `Done/`.

### Step 5: Completion
The task file moves to `Done/`, an audit log entry is written to `Logs/`, and `Dashboard.md` is updated with current stats.

## Directory Structure

```
Silver/
├── src/
│   ├── watchers/
│   │   ├── gmail_watcher.py       # Gmail API polling, creates EMAIL_*.md
│   │   └── linkedin_watcher.py    # LinkedIn scraping, creates LINKEDIN_*.md
│   ├── orchestrator/
│   │   └── orchestrator.py        # Main processing loop (watchdog-based)
│   ├── approval/
│   │   └── approval_watcher.py    # Terminal HITL: Approve/Reject/Modify/Skip
│   ├── mcp_email/
│   │   ├── email_server.py        # JSON-RPC 2.0 MCP server (3 tools)
│   │   └── email_client.py        # Subprocess wrapper for MCP calls
│   ├── scheduler/
│   │   └── scheduler.py           # Recurring tasks (daily scan, weekly post)
│   ├── linkedin_poster/
│   │   └── linkedin_poster.py     # Post templates (thought leadership, tips)
│   └── utils/
│       ├── file_ops.py            # File move, read, write helpers
│       ├── logger.py              # Markdown + JSON-lines audit logging
│       └── frontmatter.py         # YAML frontmatter parser
├── tests/
│   └── test_pipeline.py           # Pipeline integration test
├── .claude/skills/                # 8 agent skill definitions
│   ├── scan_needs_action.md       # List and classify pending tasks
│   ├── create_plan.md             # Generate action plans
│   ├── complete_task.md           # Execute tasks via MCP
│   ├── update_dashboard.md        # Refresh Dashboard.md
│   ├── generate_sales_post.md     # Draft LinkedIn/sales posts
│   ├── request_approval.md        # Create HITL approval requests
│   ├── execute_action.md          # Execute approved actions
│   └── schedule_task.md           # Configure recurring tasks
├── Inbox/                         # Raw incoming items
├── Needs_Action/                  # Active task queue
├── Pending_Approval/              # Awaiting human review
├── Approved/                      # Approved actions (archive)
├── Rejected/                      # Rejected actions (archive)
├── Done/                          # Completed tasks
├── Logs/                          # Action audit trail
├── Dashboard.md                   # Live status board
├── Company_Handbook.md            # Workflow rules
├── config.yaml                    # Watcher/scheduler settings
└── requirements.txt               # Python dependencies
```

## The 8 Skills

| # | Skill | What It Does |
|---|-------|-------------|
| 1 | `scan_needs_action` | Scans `Needs_Action/` and lists all pending tasks with type, priority, and preview |
| 2 | `create_plan` | Reads a task file and generates a step-by-step action plan based on task type |
| 3 | `complete_task` | Executes the plan — drafts replies, creates output files, routes to approval or Done/ |
| 4 | `update_dashboard` | Counts files in each folder and refreshes Dashboard.md with current stats |
| 5 | `generate_sales_post` | Drafts LinkedIn thought leadership, case study, or tips posts |
| 6 | `request_approval` | Creates an approval request in Pending_Approval/ with proposed action details |
| 7 | `execute_action` | Picks up EXECUTE_*.md files and calls the appropriate MCP tool |
| 8 | `schedule_task` | Configures recurring tasks (daily scan, weekly post, Monday briefing) |

## MCP Email Server

The Email MCP server implements the [Model Context Protocol](https://modelcontextprotocol.io/) using JSON-RPC 2.0 over stdio:

| Tool | Safety | Description |
|------|--------|-------------|
| `list_drafts` | SAFE | List all saved email drafts |
| `draft_email` | DRAFT | Create an email draft (no send) |
| `send_email` | DANGEROUS | Send an email (requires approval) |

## Scheduler

| Schedule | Time | What It Creates |
|----------|------|----------------|
| Daily inbox scan | 9:00 AM | `SCHEDULE_daily_scan.md` |
| Weekly LinkedIn post | Friday 4:00 PM | `SALESPOST_weekly.md` |
| Monday CEO briefing | Monday 8:00 AM | `SCHEDULE_monday_briefing.md` |

## What Silver Adds Over Bronze

| Feature | Bronze | Silver |
|---------|--------|--------|
| Task creation | Manual file drop | Automatic via watchers |
| Processing | Manual skill invocation | Automated orchestrator loop |
| Approval | None | Full HITL pipeline |
| Email | None | MCP server (send/draft/list) |
| Scheduling | None | Recurring task scheduler |
| Monitoring | None | Gmail + LinkedIn watchers |
| Skills | 4 | 8 (+4 new) |
| Tests | 0 | 1 |

## What the Next Tier (Gold) Adds

Gold builds on Silver by adding:
- **3 more watchers** — Facebook, Instagram, Twitter/X (5 total)
- **2 more MCP servers** — Odoo ERP + Social Media (3 total)
- **Ralph Wiggum loop** — Multi-step AI processing for complex tasks
- **Weekly business audit** — Automated CEO briefings
- **Error recovery** — Retry queue with exponential backoff
- **8 more skills** (16 total)
- **55 passing tests**

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test with mock data
python -m src.watchers.gmail_watcher --mock --once
python -m src.watchers.linkedin_watcher --mock --once

# Run orchestrator (dry-run)
python -m src.orchestrator.orchestrator --dry-run --once

# Run approval watcher
python -m src.approval.approval_watcher --once

# Run scheduler
python -m src.scheduler.scheduler --once

# Run tests
python -m pytest tests/ -v
```

## Modes

| Variable | Default | Description |
|----------|---------|-------------|
| `DRY_RUN` | `true` | Log all external actions instead of executing |
| `MOCK_DATA` | `true` | Watchers use fake data instead of real APIs |

Set both to `false` in `.env` for live operation (requires Gmail API credentials).
