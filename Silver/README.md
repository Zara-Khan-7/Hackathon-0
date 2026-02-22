# AI Employee Project

An AI-powered personal assistant that monitors Gmail and LinkedIn, processes tasks through an approval pipeline, and executes actions via MCP tools. Local-first, dry-run by default.

## Architecture

```
Gmail/LinkedIn → Watchers (--mock) → Needs_Action/*.md
                                          ↓
                                    Orchestrator (watchdog)
                                          ↓
                                    Claude CLI Skills
                                          ↓
                                  Needs Approval? ──Yes──→ Pending_Approval/
                                       │                        ↓
                                       No              approval_watcher.py
                                       │                   (terminal HITL)
                                       ↓                        ↓
                                  Execute Action         Approved/ or Rejected/
                                  (MCP email/post)              ↓
                                       │               EXECUTE_*.md → Needs_Action/
                                       ↓                        ↓
                                    Done/ + Logs/ + Dashboard.md
```

## Directory Structure

| Folder | Purpose |
|--------|---------|
| `Inbox/` | Raw incoming items for triage |
| `Needs_Action/` | Watchers create `.md` task files here |
| `Pending_Approval/` | Items awaiting human review |
| `Approved/` | Approved actions (archive) |
| `Rejected/` | Rejected actions (archive) |
| `Done/` | Completed tasks |
| `Logs/` | Action logs for audit |
| `src/` | Python source code |
| `.claude/skills/` | Agent skill definitions (8 skills) |

## Key Files

- **Dashboard.md** — Live overview of all queues and stats
- **Company_Handbook.md** — Workflow rules and guidelines
- **config.yaml** — Watcher/scheduler settings
- **setup_guide.md** — Credential setup instructions

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings (defaults to dry-run + mock)

# 3. Test with mock data
python -m src.watchers.gmail_watcher --mock --once
python -m src.watchers.linkedin_watcher --mock --once

# 4. Run orchestrator (dry-run)
python -m src.orchestrator.orchestrator --dry-run --once

# 5. Run approval watcher
python -m src.approval.approval_watcher --once

# 6. Run scheduler
python -m src.scheduler.scheduler --once
```

## Components

### Watchers (`src/watchers/`)
- **gmail_watcher.py** — Polls Gmail API, creates EMAIL_*.md tasks
- **linkedin_watcher.py** — Playwright-based LinkedIn monitor, creates LINKEDIN_*.md tasks
- Both support `--mock` (fake data) and `--dry-run` (no file creation) flags

### Orchestrator (`src/orchestrator/`)
- Watches `Needs_Action/` for new .md files
- Classifies by type and priority
- Invokes Claude CLI skills (`claude -p`) for planning and execution
- Routes approval-required tasks to `Pending_Approval/`

### Approval Pipeline (`src/approval/`)
- Terminal-based HITL (Human-in-the-Loop) review
- Approve → creates EXECUTE_*.md in Needs_Action/
- Reject → moves to Rejected/
- Modify → edit content, then re-prompt

### MCP Email Server (`src/mcp_email/`)
- JSON-RPC 2.0 over stdio (MCP protocol)
- Tools: `send_email`, `draft_email`, `list_drafts`
- Dry-run by default (logs to Logs/ instead of sending)

### LinkedIn Poster (`src/linkedin_poster/`)
- Post template system (thought leadership, case study, tips, news)
- All posts require approval before publishing
- Simulated publishing in dry-run mode

### Scheduler (`src/scheduler/`)
- Daily scan (9 AM), weekly LinkedIn post (Friday 4 PM), Monday briefing (8 AM)
- Creates task files in Needs_Action/ for orchestrator pickup

## Agent Skills (8)

| Skill | Purpose |
|-------|---------|
| `scan_needs_action` | List and classify pending tasks |
| `create_plan` | Generate type-aware action plans |
| `complete_task` | Execute tasks with MCP integration |
| `update_dashboard` | Refresh Dashboard.md stats |
| `generate_sales_post` | Draft LinkedIn posts |
| `request_approval` | Create HITL approval requests |
| `execute_action` | Execute approved actions |
| `schedule_task` | Configure recurring tasks |

## Testing

```bash
# Run unit tests
python -m pytest tests/ -v

# Test MCP server
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python -m src.mcp_email.email_server

# Full integration (3 terminals)
python -m src.orchestrator.orchestrator --dry-run          # Terminal 1
python -m src.approval.approval_watcher                    # Terminal 2
python -m src.watchers.gmail_watcher --mock --once         # Terminal 3
```

## Modes

| Mode | Description |
|------|-------------|
| `DRY_RUN=true` | Log all external actions instead of executing (default) |
| `MOCK_DATA=true` | Use fake data for watchers instead of real APIs (default) |
| `DRY_RUN=false` | Execute real actions (send emails, post to LinkedIn) |
| `MOCK_DATA=false` | Use real Gmail/LinkedIn APIs (requires credentials) |
