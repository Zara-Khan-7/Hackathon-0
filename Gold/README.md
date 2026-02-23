# Gold Tier — Multi-Platform Social + ERP Integration

**Status:** Implemented | **Tests:** 55 | **Skills:** 16 | **MCP Servers:** 3 | **Watchers:** 5

## What This Tier Does

Gold is the **multi-platform layer** — it extends Silver's email/LinkedIn automation to cover Facebook, Instagram, and Twitter/X, adds Odoo ERP integration for invoicing and accounting, introduces a **Ralph Wiggum multi-step AI loop** for complex tasks, implements error recovery with retry logic, and runs automated weekly business audits that produce CEO briefings.

Think of it as **promoting your AI assistant to office manager** — one that handles all communication channels, manages invoicing, audits the business weekly, and recovers from failures automatically.

## Architecture

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                      EXTERNAL SOURCES                            │
    │   Gmail    LinkedIn    Facebook    Instagram    Twitter/X         │
    └───┬──────────┬──────────┬──────────┬──────────┬─────────────────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │ Gmail  │ │LinkedIn│ │Facebook│ │ Insta  │ │Twitter │
    │Watcher │ │Watcher │ │Watcher │ │Watcher │ │Watcher │
    └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
    ┌──────────────────────────────────────────────────┐
    │              Needs_Action/                        │
    │  EMAIL_*.md  LINKEDIN_*.md  FACEBOOK_*.md         │
    │  INSTAGRAM_*.md  TWITTER_*.md  ODOO_*.md          │
    │  AUDIT_*.md  SALESPOST_*.md  ERROR_*.md           │
    └─────────────────────┬────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────┐
    │                  Orchestrator                        │
    │                                                     │
    │  Simple tasks ──────────────► Direct processing     │
    │                                                     │
    │  Complex tasks (ODOO_, AUDIT_)                      │
    │       │                                             │
    │       ▼                                             │
    │  ┌─────────────────────────────┐                    │
    │  │  Ralph Wiggum Loop          │                    │
    │  │  Step 1: Plan               │                    │
    │  │  Step 2: Execute step       │                    │
    │  │  Step 3: Check result       │                    │
    │  │  Step 4: Next step or done  │                    │
    │  │  (max 5 iterations)         │                    │
    │  └─────────────────────────────┘                    │
    └──────────────┬──────────────────┬───────────────────┘
                   │                  │
           Needs approval?     No approval needed
                   │                  │
                   ▼                  ▼
    ┌──────────────────┐       ┌──────────┐
    │ Pending_Approval/│       │  Done/   │
    │ APPROVE_*.md     │       └──────────┘
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │          HITL Approval Pipeline           │
    │  [A]pprove  [R]eject  [M]odify  [S]kip   │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │              MCP Servers (3)              │
    │                                          │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
    │  │  Email   │ │  Odoo    │ │  Social  │ │
    │  │  Server  │ │  Server  │ │  Server  │ │
    │  │ send     │ │ invoice  │ │ post_fb  │ │
    │  │ draft    │ │ partners │ │ post_ig  │ │
    │  │ list     │ │ txns     │ │ post_tw  │ │
    │  └──────────┘ └──────────┘ └──────────┘ │
    └──────────────────┬───────────────────────┘
                       │
                       ▼
    ┌─────────────────────────────────────┐
    │  Done/ + Logs/ + Dashboard.md       │
    │  Accounting/ + Briefings/ + Errors/ │
    └─────────────────────────────────────┘
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
    ┌────────────┐ ┌────────┐ ┌──────────────┐
    │Weekly Audit│ │ Error  │ │  Scheduler   │
    │(Sun 11 PM) │ │Handler │ │(daily/weekly)│
    │CEO Briefing│ │+ Retry │ │              │
    └────────────┘ └────────┘ └──────────────┘
```

## How the Workflow Works (Step by Step)

### Step 1: Multi-Platform Detection (5 Watchers)
Five watchers run in parallel, each monitoring a different platform:

| Watcher | What It Monitors | Task File Created |
|---------|-----------------|-------------------|
| Gmail | Inbox emails via Gmail API | `EMAIL_20260223_sender.md` |
| LinkedIn | Messages/invitations via Playwright | `LINKEDIN_20260223_user.md` |
| Facebook | Page notifications/DMs via Graph API | `FACEBOOK_20260223_post.md` |
| Instagram | DMs/mentions via Instagrapi | `INSTAGRAM_20260223_user.md` |
| Twitter/X | Mentions/DMs via Tweepy | `TWITTER_20260223_mention.md` |

Each creates a Markdown file with YAML frontmatter in `Needs_Action/`.

### Step 2: Classification (Orchestrator)
The orchestrator reads the filename prefix to determine task type and routing:

| Prefix | Type | Routing |
|--------|------|---------|
| `EMAIL_` | Email reply | Email MCP |
| `LINKEDIN_` | LinkedIn response | LinkedIn poster |
| `FACEBOOK_` | Facebook content | Social MCP |
| `INSTAGRAM_` | Instagram content | Social MCP |
| `TWITTER_` | Twitter/X content | Social MCP |
| `ODOO_` | ERP/invoicing | Odoo MCP (Ralph Wiggum) |
| `AUDIT_` | Business audit | Audit system (Ralph Wiggum) |
| `SALESPOST_` | Sales content | LinkedIn poster |
| `EXECUTE_` | Approved action | Direct MCP call |
| `ERROR_` | Error recovery | Error handler |
| `SCHEDULE_` | Recurring task | Scheduler |

### Step 3: Processing (Simple vs. Complex)

**Simple tasks** (EMAIL_, LINKEDIN_, social posts) go through direct processing:
1. Create plan via `create_plan` skill
2. Execute via `complete_task` skill
3. Route to approval or Done/

**Complex tasks** (ODOO_, AUDIT_) use the **Ralph Wiggum multi-step loop**:
1. AI creates an initial plan with numbered steps
2. Executes Step 1, checks result
3. If Step 1 succeeded, executes Step 2, etc.
4. Up to 5 iterations before forcing completion
5. Each step can invoke MCP tools (create invoice, read transactions, etc.)

### Step 4: Approval (Same HITL as Silver)
Any task that involves external actions goes to `Pending_Approval/`:
- Sending emails → requires approval
- Posting on social media → requires approval
- Posting invoices in Odoo → requires approval
- Creating invoice drafts → does NOT require approval

### Step 5: Execution via 3 MCP Servers
Approved actions execute through the appropriate MCP server:

**Email MCP** (`src/mcp_email/`):
- `send_email` — Send email via SMTP (DANGEROUS)
- `draft_email` — Save email draft (DRAFT)
- `list_drafts` — List saved drafts (SAFE)

**Odoo MCP** (`src/mcp_odoo/`):
- `list_invoices` — List all invoices (SAFE)
- `read_invoice` — Read invoice details (SAFE)
- `create_invoice_draft` — Create draft invoice (DRAFT)
- `post_invoice` — Confirm and post invoice (DANGEROUS)
- `list_partners` — List business partners (SAFE)
- `read_transactions` — Read accounting transactions (SAFE)

**Social MCP** (`src/mcp_social/`):
- `post_facebook` — Post to Facebook page (DANGEROUS)
- `post_instagram` — Post to Instagram (DANGEROUS)
- `post_twitter` — Post to Twitter/X (DANGEROUS)
- `get_social_summary` — Get engagement metrics (SAFE)
- `draft_social_post` — Create social media draft (DRAFT)

### Step 6: Error Recovery
When a task fails, the ErrorHandler:
1. Creates an `ERROR_*.md` file in `Errors/`
2. Checks if the error is retryable (network timeout, API rate limit)
3. Retries with exponential backoff (1s, 2s, 4s — max 3 retries)
4. If all retries fail, escalates to human via `Pending_Approval/`

### Step 7: Weekly Audit
Every Sunday at 11 PM, the scheduler triggers a full business audit:
1. Gathers stats from Odoo (revenue, invoices, overdue)
2. Gathers social media metrics (posts, engagement, DMs)
3. Counts task pipeline stats (done, pending, errors)
4. Generates a CEO briefing in `Briefings/Monday_Briefing.md`

## Directory Structure

```
Gold/
├── src/
│   ├── watchers/
│   │   ├── gmail_watcher.py       # Gmail API polling
│   │   ├── linkedin_watcher.py    # LinkedIn scraping
│   │   ├── facebook_watcher.py    # Facebook Graph API
│   │   ├── instagram_watcher.py   # Instagram via Instagrapi
│   │   └── twitter_watcher.py     # Twitter/X via Tweepy
│   ├── orchestrator/
│   │   └── orchestrator.py        # Main loop + Ralph Wiggum
│   ├── approval/
│   │   └── approval_watcher.py    # Terminal HITL approval
│   ├── mcp_email/
│   │   ├── email_server.py        # Email MCP (3 tools)
│   │   └── email_client.py        # Subprocess wrapper
│   ├── mcp_odoo/
│   │   ├── odoo_server.py         # Odoo MCP (6 tools)
│   │   ├── odoo_client.py         # Subprocess wrapper
│   │   └── mock_odoo.py           # Mock invoices/partners/txns
│   ├── mcp_social/
│   │   ├── social_server.py       # Social MCP (5 tools)
│   │   ├── social_client.py       # Subprocess wrapper
│   │   ├── mock_social.py         # Mock posts/metrics
│   │   └── adapters/
│   │       ├── facebook_adapter.py
│   │       ├── instagram_adapter.py
│   │       └── twitter_adapter.py
│   ├── audit/
│   │   └── auditor.py             # Weekly business audit
│   ├── errors/
│   │   └── error_handler.py       # Error recovery + retry
│   ├── scheduler/
│   │   └── scheduler.py           # Recurring task scheduler
│   └── utils/
│       ├── file_ops.py            # File operations
│       ├── logger.py              # Audit logging (MD + JSONL)
│       ├── frontmatter.py         # YAML frontmatter parser
│       ├── mcp_registry.py        # MCP server registry
│       └── retry.py               # Retry decorator with backoff
├── tests/
│   ├── test_pipeline.py           # Silver pipeline tests
│   ├── test_odoo_server.py        # Odoo MCP tests
│   ├── test_social_server.py      # Social MCP tests
│   ├── test_orchestrator.py       # Orchestrator routing tests
│   ├── test_error_handler.py      # Error recovery tests
│   └── test_auditor.py            # Audit system tests
├── docker/
│   └── docker-compose.yml         # Odoo 17 + PostgreSQL
├── .claude/skills/                # 16 agent skills
├── Inbox/                         # Raw incoming items
├── Needs_Action/                  # Active task queue
├── Pending_Approval/              # Awaiting human review
├── Approved/                      # Approved actions archive
├── Rejected/                      # Rejected actions archive
├── Done/                          # Completed tasks
├── Logs/                          # Audit trail (MD + JSONL)
├── Accounting/                    # Odoo transaction summaries
├── Briefings/                     # Weekly CEO briefings
├── Errors/                        # Failed tasks for retry
├── Dashboard.md                   # Live status board
├── Company_Handbook.md            # Workflow rules
├── config.yaml                    # Configuration
└── requirements.txt               # Dependencies
```

## The 16 Skills

| # | Skill | What It Does |
|---|-------|-------------|
| 1 | `scan_needs_action` | List and classify all pending tasks with type/priority |
| 2 | `create_plan` | Generate type-aware action plans (with Odoo/social/audit templates) |
| 3 | `complete_task` | Execute tasks with multi-MCP routing (email/odoo/social) |
| 4 | `update_dashboard` | Refresh Dashboard.md with accounting/social/audit/error stats |
| 5 | `generate_sales_post` | Draft multi-platform sales and promotional posts |
| 6 | `request_approval` | Create HITL approval requests in Pending_Approval/ |
| 7 | `execute_action` | Execute approved actions via the correct MCP server |
| 8 | `schedule_task` | Configure recurring tasks (daily/weekly/monthly) |
| 9 | `sync_odoo_transactions` | Read Odoo transactions and save to Accounting/ |
| 10 | `create_invoice_draft` | Create a draft invoice in Odoo ERP |
| 11 | `post_approved_invoice` | Post an approved invoice (confirms it in Odoo) |
| 12 | `generate_social_post` | Create platform-specific content (FB/IG/X formatting) |
| 13 | `post_approved_social` | Post approved content to Facebook/Instagram/Twitter |
| 14 | `summarize_social_activity` | Fetch engagement metrics and update Dashboard.md |
| 15 | `weekly_audit` | Run full business audit and generate CEO briefing |
| 16 | `handle_error` | Detect failures, attempt retry with backoff, or escalate |

## What Gold Adds Over Silver

| Feature | Silver | Gold |
|---------|--------|------|
| Watchers | 2 (Gmail, LinkedIn) | 5 (+Facebook, Instagram, Twitter) |
| MCP Servers | 1 (Email) | 3 (+Odoo ERP, Social Media) |
| Task Types | 5 prefixes | 13 prefixes |
| Processing | Linear | Ralph Wiggum multi-step loop |
| Error Handling | None | ErrorHandler + retry with backoff |
| Auditing | None | Weekly business audit + CEO briefing |
| ERP | None | Full Odoo integration (invoicing, partners, transactions) |
| Social Posting | LinkedIn only | Facebook + Instagram + Twitter/X |
| Skills | 8 | 16 (+8 new) |
| Tests | 1 | 55 |

## What the Next Tier (Platinum) Adds

Platinum builds on Gold by adding:
- **Hybrid cloud/local architecture** — Cloud VM runs 24/7 (drafts only), local machine executes
- **2 more MCP servers** — WhatsApp + Payment (LOCAL-ONLY)
- **Claim-by-move** — Atomic task ownership via `os.rename()`
- **Git vault sync** — Cloud pushes, local pulls, conflict resolution
- **Health monitoring** — Heartbeat, disk usage, error rate checks
- **5 more skills** (21 total)
- **215 passing tests**

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test all watchers with mock data
python -m src.watchers.gmail_watcher --mock --once
python -m src.watchers.linkedin_watcher --mock --once
python -m src.watchers.facebook_watcher --mock --once
python -m src.watchers.instagram_watcher --mock --once
python -m src.watchers.twitter_watcher --mock --once

# Run orchestrator (dry-run)
python -m src.orchestrator.orchestrator --dry-run --once

# Run approval watcher
python -m src.approval.approval_watcher --once

# Run weekly audit (mock)
python -m src.audit.auditor --mock

# Run all tests (55 tests)
python -m pytest tests/ -v
```

## Modes

| Variable | Default | Description |
|----------|---------|-------------|
| `DRY_RUN` | `true` | Log all external actions instead of executing |
| `MOCK_DATA` | `true` | Watchers use fake data instead of real APIs |
| `ODOO_MOCK` | `true` | Odoo MCP returns mock data (no Docker needed) |

Set all to `false` in `.env` for live operation.
