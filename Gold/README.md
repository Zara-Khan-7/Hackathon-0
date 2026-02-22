# AI Employee Project — Gold Tier

An autonomous AI-powered employee that monitors Gmail, LinkedIn, Facebook, Instagram, and X/Twitter, manages Odoo ERP invoicing, processes tasks through an approval pipeline, runs weekly business audits, and executes actions via 3 MCP servers. Local-first, dry-run by default.

## Architecture

```
Gmail/LinkedIn/Facebook/Instagram/X
         |
    Watchers (--mock)
         |
  Needs_Action/*.md
         |
  Orchestrator (+ Ralph Wiggum for complex tasks)
         |
  Claude CLI Skills --> Plans
         |
  Needs Approval? --Yes--> Pending_Approval/ --> HITL --> Approved/Rejected
       |                                                    |
       No                                          EXECUTE_*.md --> Needs_Action/
       |                                                    |
  Execute via MCP <-----------------------------------------+
  (email / odoo / social)
       |
  Done/ + Logs/ + Dashboard.md
       |
  Weekly Audit (Sunday 11PM) --> Briefings/Monday_Briefing.md
       |
  Errors/ (failed tasks) --> retry queue --> ErrorHandler
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
| `Logs/` | Action logs (markdown + JSON-lines audit trail) |
| `Accounting/` | Odoo transaction summaries |
| `Briefings/` | Weekly CEO briefings |
| `Errors/` | Failed tasks queued for retry |
| `docker/` | Odoo 17 + PostgreSQL Docker config |
| `src/` | Python source code |
| `.claude/skills/` | Agent skill definitions (16 skills) |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings (defaults to dry-run + mock)

# 3. Test with mock data (all watchers)
python -m src.watchers.gmail_watcher --mock --once
python -m src.watchers.linkedin_watcher --mock --once
python -m src.watchers.facebook_watcher --mock --once
python -m src.watchers.instagram_watcher --mock --once
python -m src.watchers.twitter_watcher --mock --once

# 4. Run orchestrator (dry-run)
python -m src.orchestrator.orchestrator --dry-run --once

# 5. Run approval watcher
python -m src.approval.approval_watcher --once

# 6. Run scheduler
python -m src.scheduler.scheduler --once

# 7. Run weekly audit (mock)
python -m src.audit.auditor --mock

# 8. Run all tests
python -m pytest tests/ -v
```

## Odoo ERP Setup (Optional)

```bash
# Requires Docker Desktop installed and running
cd docker
docker-compose up -d
# Odoo web UI at http://localhost:8069 (admin/admin)
# Set ODOO_MOCK=false in .env to use real Odoo
```

## Components

### Watchers (`src/watchers/`) — 5 total
- **gmail_watcher.py** — Polls Gmail API, creates EMAIL_*.md tasks
- **linkedin_watcher.py** — Playwright-based LinkedIn monitor, creates LINKEDIN_*.md
- **facebook_watcher.py** — Facebook page notifications/messages, creates FACEBOOK_*.md
- **instagram_watcher.py** — Instagram DMs/mentions, creates INSTAGRAM_*.md
- **twitter_watcher.py** — X/Twitter mentions/DMs, creates TWITTER_*.md
- All support `--mock`, `--dry-run`, and `--once` flags

### Orchestrator (`src/orchestrator/`)
- Watches `Needs_Action/` for new .md files
- Classifies by type and priority (13 prefix types)
- Invokes Claude CLI skills (`claude -p`) for planning and execution
- Routes approval-required tasks to `Pending_Approval/`
- **Ralph Wiggum loop** for complex multi-step tasks (ODOO_, AUDIT_)
- Error recovery with retry decorator + ErrorHandler

### Approval Pipeline (`src/approval/`)
- Terminal-based HITL (Human-in-the-Loop) review
- Approve / Reject / Modify / Skip
- Creates EXECUTE_*.md for approved actions

### MCP Servers — 3 total

| Server | Module | Tools |
|--------|--------|-------|
| **ai-employee-email** | `src.mcp_email.email_server` | send_email, draft_email, list_drafts |
| **ai-employee-odoo** | `src.mcp_odoo.odoo_server` | list_invoices, read_invoice, create_invoice_draft, post_invoice, list_partners, read_transactions |
| **ai-employee-social** | `src.mcp_social.social_server` | post_facebook, post_instagram, post_twitter, get_social_summary, draft_social_post |

### Audit System (`src/audit/`)
- Weekly business/accounting audit
- Gathers stats from Odoo, social media, and task pipeline
- Generates CEO briefing in Briefings/

### Error Recovery (`src/errors/`)
- ErrorHandler: catches exceptions, creates ERROR_*.md
- Retry queue with exponential backoff (1s, 2s, 4s)
- Escalation to HITL for persistent failures

### Scheduler (`src/scheduler/`)
- Daily scan (9 AM), weekly post (Friday 4 PM), Monday briefing (8 AM), Sunday audit (11 PM)

## Agent Skills (16)

| # | Skill | Purpose |
|---|-------|---------|
| 1 | `scan_needs_action` | List and classify all pending tasks |
| 2 | `create_plan` | Generate type-aware plans (Odoo/social/audit templates) |
| 3 | `complete_task` | Execute with multi-MCP routing |
| 4 | `update_dashboard` | Refresh stats (accounting/social/audit/errors) |
| 5 | `generate_sales_post` | Draft multi-platform posts |
| 6 | `request_approval` | Create HITL approval requests |
| 7 | `execute_action` | Execute approved actions (email/Odoo/social) |
| 8 | `schedule_task` | Configure recurring tasks |
| 9 | `sync_odoo_transactions` | Read Odoo transactions → Accounting/ |
| 10 | `create_invoice_draft` | Create draft invoice → approval |
| 11 | `post_approved_invoice` | Post approved invoice in Odoo |
| 12 | `generate_social_post` | Create FB/IG/X content |
| 13 | `post_approved_social` | Post approved social content |
| 14 | `summarize_social_activity` | Fetch metrics → Dashboard.md |
| 15 | `weekly_audit` | Full audit → CEO briefing |
| 16 | `handle_error` | Detect failures, retry or escalate |

## Testing

```bash
# Unit tests
python -m pytest tests/ -v

# MCP server tests (pipe JSON-RPC)
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python -m src.mcp_email.email_server
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python -m src.mcp_odoo.odoo_server
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python -m src.mcp_social.social_server

# Full integration (4 terminals)
python -m src.orchestrator.orchestrator --dry-run          # Terminal 1
python -m src.approval.approval_watcher                    # Terminal 2
python -m src.watchers.gmail_watcher --mock --once         # Terminal 3
python -m src.watchers.facebook_watcher --mock --once      # Terminal 3
python -m src.scheduler.scheduler --trigger weekly_audit   # Terminal 4
```

## Modes

| Mode | Description |
|------|-------------|
| `DRY_RUN=true` | Log all external actions instead of executing (default) |
| `MOCK_DATA=true` | Use fake data for watchers (default) |
| `ODOO_MOCK=true` | Use mock Odoo data, no Docker needed (default) |
| `*_MOCK=true` | Use mock social data (default for FB/IG/X) |
| Set all to `false` | Full live operation with real APIs |
