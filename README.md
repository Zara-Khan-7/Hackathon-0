# AI Employee Project — From Task Queue to Multi-Agent Swarm

> A progressive, 5-tier autonomous AI assistant that manages emails, social media, invoicing, payments, WhatsApp, CRM, and compliance — with human-in-the-loop safety at every step.

**Total Tests:** 662 | **Total Skills:** 26 | **MCP Servers:** 5 | **Specialized Agents:** 4

---

## What Is This?

This project builds a **fully autonomous AI employee** in 5 progressive tiers — each one adding capabilities on top of the previous. Starting from a simple file-based task queue (Bronze), it evolves into a multi-agent swarm with self-improving intelligence (Diamond).

Every tier is self-contained, independently testable, and backward-compatible with all tiers below it.

```
Bronze ──► Silver ──► Gold ──► Platinum ──► Diamond
(queue)   (email)   (social)  (cloud)     (swarm)
 4 skills  8 skills  16 skills 21 skills   26 skills
 0 tests   1 test    55 tests  215 tests   392 tests
```

---

## Architecture Overview

```
                         ┌─────────────────────────────────┐
                         │      DIAMOND (Multi-Agent)       │
                         │  SwarmOrchestrator               │
                         │  4 Specialized Agents            │
                         │  A2A Message Bus                 │
                         │  Self-Improving Loop             │
                         │  Credential Vault + CRM + API   │
                    ┌────┴────────────────────────────┐     │
                    │    PLATINUM (Hybrid Cloud/Local) │     │
                    │  Cloud: SAFE+DRAFT tools only   │     │
                    │  Local: Full access + HITL      │     │
                    │  Claim-by-Move + Git Sync       │     │
                    │  WhatsApp + Payment MCPs        │     │
               ┌────┴───────────────────────────┐     │     │
               │    GOLD (Multi-Platform + ERP) │     │     │
               │  5 Social Watchers             │     │     │
               │  Odoo ERP Integration          │     │     │
               │  Ralph Wiggum (multi-step AI)  │     │     │
               │  Error Recovery + Auditing     │     │     │
          ┌────┴──────────────────────────┐     │     │     │
          │    SILVER (Email + LinkedIn)  │     │     │     │
          │  Gmail + LinkedIn Watchers    │     │     │     │
          │  Orchestrator Pipeline        │     │     │     │
          │  Email MCP Server             │     │     │     │
          │  HITL Approval System         │     │     │     │
     ┌────┴─────────────────────────┐     │     │     │     │
     │    BRONZE (Task Queue)       │     │     │     │     │
     │  File-based task system      │     │     │     │     │
     │  Needs_Action → Done flow    │     │     │     │     │
     │  Dashboard + Handbook        │     │     │     │     │
     └──────────────────────────────┘     │     │     │     │
                                          └─────┘     └─────┘
```

---

## Tier Comparison

| Feature | Bronze | Silver | Gold | Platinum | Diamond |
|---------|--------|--------|------|----------|---------|
| **Architecture** | File queue | Watchers + Orchestrator | Multi-platform + ERP | Hybrid Cloud/Local | Multi-agent swarm |
| **Test Files** | 0 | 1 | 6 | 17 | 29 |
| **Passing Tests** | — | — | 55 | 215 | 392 |
| **Skills** | 4 | 8 | 16 | 21 | 26 |
| **MCP Servers** | 0 | 1 | 3 | 5 | 5 |
| **Watchers** | 0 | 2 | 5 | 6 | 6 |
| **Orchestrator** | Manual | Single-loop | Ralph Wiggum | Cloud + Local | Swarm (4 agents) |
| **Approval** | None | HITL terminal | HITL + error recovery | HITL + claim safety | HITL + security scan |
| **Key Innovation** | Markdown tasks | Email automation | Multi-step AI loop | Cloud/local split | Self-improving agents |

---

## Quick Start

```bash
# Pick any tier (Diamond is the most complete)
cd Diamond

# Install dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/ -v

# Run the swarm orchestrator (dry-run, no real actions)
python -m src.orchestrator.orchestrator --role diamond --dry-run --once

# Or run backward-compatible modes
python -m src.orchestrator.orchestrator --role gold --dry-run --once
python -m src.orchestrator.orchestrator --role cloud --dry-run --once
python -m src.orchestrator.orchestrator --role local --dry-run --once
```

---

## How It Works

### The Core Loop

Every tier follows the same fundamental pattern:

```
1. DETECT    →  Watchers monitor Gmail, LinkedIn, Facebook, Instagram, X, WhatsApp
2. CREATE    →  Task files (*.md with YAML frontmatter) land in Needs_Action/
3. CLASSIFY  →  Orchestrator reads prefix (EMAIL_, PAYMENT_, etc.) to determine type
4. DELEGATE  →  Task routes to the right agent/skill based on type
5. PLAN      →  Agent creates an action plan
6. APPROVE   →  Dangerous actions go to Pending_Approval/ for human review
7. EXECUTE   →  Approved actions execute via MCP tools (mock by default)
8. COMPLETE  →  Results move to Done/, dashboard updates, audit log written
```

### Task File Format

All tasks are Markdown files with YAML frontmatter:

```yaml
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

### 15 Task Prefixes

| Prefix | Type | Handled By |
|--------|------|-----------|
| `EMAIL_` | Email reply | Sales Agent |
| `LINKEDIN_` | LinkedIn message | Sales Agent |
| `SALESPOST_` | Sales content | Sales Agent |
| `ODOO_` | ERP/invoicing | Finance Agent |
| `PAYMENT_` | Bank payment | Finance Agent |
| `AUDIT_` | Business audit | Finance Agent |
| `FACEBOOK_` | Facebook post | Content Agent |
| `INSTAGRAM_` | Instagram post | Content Agent |
| `TWITTER_` | Twitter/X post | Content Agent |
| `SOCIAL_` | Cross-platform | Content Agent |
| `WHATSAPP_` | WhatsApp message | Content Agent |
| `ERROR_` | Error recovery | Security Agent |
| `EXECUTE_` | Pre-approved action | Security Agent |
| `SCHEDULE_` | Recurring task | Any agent |
| `APPROVE_` | Approval request | Orchestrator |

---

## Project Structure

```
HACKATHON 0/
├── Bronze/                 # Tier 1: Basic task queue
│   ├── .claude/skills/     #   4 skills
│   ├── Needs_Action/       #   Input folder
│   ├── Done/               #   Completed tasks
│   ├── Dashboard.md        #   Status board
│   └── Company_Handbook.md #   Rules
│
├── Silver/                 # Tier 2: Email + LinkedIn
│   ├── src/
│   │   ├── watchers/       #   Gmail + LinkedIn watchers
│   │   ├── orchestrator/   #   Main processing loop
│   │   ├── approval/       #   HITL approval pipeline
│   │   ├── mcp_email/      #   Email MCP server
│   │   ├── scheduler/      #   Recurring tasks
│   │   └── utils/          #   File ops, logger, frontmatter
│   ├── tests/              #   1 test file
│   ├── .claude/skills/     #   8 skills
│   └── config.yaml         #   Configuration
│
├── Gold/                   # Tier 3: Multi-platform + ERP
│   ├── src/
│   │   ├── watchers/       #   + Facebook, Instagram, Twitter
│   │   ├── orchestrator/   #   + Ralph Wiggum multi-step loop
│   │   ├── audit/          #   Weekly business auditor
│   │   ├── errors/         #   Error handler + retry
│   │   ├── mcp_odoo/       #   Odoo ERP MCP server
│   │   ├── mcp_social/     #   Social media MCP + adapters
│   │   └── ...
│   ├── tests/              #   6 test files (55 tests)
│   ├── docker/             #   Odoo + PostgreSQL docker-compose
│   ├── .claude/skills/     #   16 skills
│   └── config.yaml
│
├── Platinum/               # Tier 4: Hybrid cloud/local
│   ├── src/
│   │   ├── config/         #   Agent roles, domain routing, tool policy
│   │   ├── claim/          #   Claim-by-move (atomic ownership)
│   │   ├── sync/           #   Git vault sync + conflict resolution
│   │   ├── health/         #   Heartbeat + health monitor
│   │   ├── mcp_whatsapp/   #   WhatsApp MCP (LOCAL-ONLY)
│   │   ├── mcp_payment/    #   Payment MCP (LOCAL-ONLY)
│   │   ├── orchestrator/   #   + Cloud + Local orchestrators
│   │   └── ...
│   ├── tests/              #   17 test files (215 tests)
│   ├── deploy/             #   PM2, cloud/local setup scripts
│   ├── .claude/skills/     #   21 skills
│   └── config.yaml
│
├── Diamond/                # Tier 5: Multi-agent swarm
│   ├── src/
│   │   ├── agents/         #   4 specialized agents + registry
│   │   ├── a2a/            #   Agent-to-agent message bus + router
│   │   ├── learning/       #   Outcome tracker, optimizer, metrics
│   │   ├── vault/          #   Encrypted credential vault
│   │   ├── compliance/     #   Compliance reporter
│   │   ├── crm/            #   CRM client (contacts, deals, pipeline)
│   │   ├── api/            #   REST API server (7 endpoints)
│   │   ├── scaling/        #   Cloud instance manager
│   │   ├── orchestrator/   #   + SwarmOrchestrator
│   │   └── ...
│   ├── tests/              #   29 test files (392 tests)
│   ├── .claude/skills/     #   26 skills
│   └── config.yaml
│
└── .gitignore
```

---

## MCP Servers (5 Total)

All servers use JSON-RPC 2.0 over stdio. Each tool is classified as SAFE, DRAFT, or DANGEROUS.

| # | Server | Tools | Safety | Available |
|---|--------|-------|--------|-----------|
| 1 | **Email** | `send_email`, `draft_email`, `list_drafts` | DANGEROUS / DRAFT / SAFE | All roles |
| 2 | **Odoo ERP** | `list_invoices`, `read_invoice`, `create_invoice_draft`, `post_invoice`, `list_partners`, `read_transactions` | Mixed | All roles |
| 3 | **Social** | `post_facebook`, `post_instagram`, `post_twitter`, `get_social_summary`, `draft_social_post` | DANGEROUS / SAFE / DRAFT | All roles |
| 4 | **WhatsApp** | `list_whatsapp_chats`, `read_whatsapp_chat`, `send_whatsapp` | SAFE / DANGEROUS | LOCAL-ONLY |
| 5 | **Payment** | `list_accounts`, `get_balance`, `list_transactions`, `initiate_payment`, `payment_status` | SAFE / DANGEROUS | LOCAL-ONLY |

---

## Safety Model

This project is designed with safety as a first-class concern:

1. **Human-in-the-Loop (HITL)** — All external actions (emails, posts, payments, messages) require human approval before execution
2. **Tool Policy** — Every MCP tool is classified as SAFE (read-only), DRAFT (creates drafts), or DANGEROUS (sends/posts/pays). Cloud agents can never call DANGEROUS tools
3. **Security Agent** — In Diamond tier, the Security Agent scans ALL outgoing content for sensitive keywords (passwords, tokens, API keys) before any action
4. **Credential Vault** — Secrets are stored separately, never in task files
5. **Compliance Reporter** — Automated checks verify that all dangerous actions went through approval
6. **DRY_RUN mode** — Default mode logs all actions without executing them
7. **MOCK mode** — All external APIs return fake data by default

---

## Diamond Tier Highlights

### Specialized Agents

| Agent | Domain | What It Does |
|-------|--------|-------------|
| **Sales Agent** | EMAIL_, LINKEDIN_, SALESPOST_ | Drafts professional replies, outreach, sales content |
| **Finance Agent** | ODOO_, PAYMENT_, AUDIT_ | Handles invoicing, payments, financial audits |
| **Content Agent** | FACEBOOK_, INSTAGRAM_, TWITTER_, SOCIAL_, WHATSAPP_ | Creates platform-specific content, manages messaging |
| **Security Agent** | ERROR_, EXECUTE_ | Validates all outgoing content, investigates errors |

### A2A Messaging

Agents communicate via an in-memory message bus (mock RabbitMQ/Redis):
- **Task delegation** — Orchestrator routes tasks to the best agent
- **Info requests** — Sales Agent can ask Finance Agent for account balance
- **Security alerts** — Security Agent broadcasts threats to all agents
- **Priority queuing** — URGENT > HIGH > NORMAL > LOW

### Self-Improving Loop

The system learns from every task:
- **OutcomeTracker** records success/failure/partial for every task
- **PromptOptimizer** analyzes patterns and generates recommendations (e.g., "Finance Agent fails on email tasks 30% of the time")
- **PerformanceMetrics** scores each agent on reliability, speed, and volume
- Optimization runs automatically every 100 completed tasks

### REST API (7 Endpoints)

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | System status, tier, mode |
| `GET /api/agents` | All 4 agents + their stats |
| `GET /api/tasks?folder=X` | Tasks in any folder |
| `GET /api/metrics` | Success rate, duration, patterns |
| `GET /api/crm` | CRM contacts, deals, pipeline |
| `GET /api/health` | System health check |
| `GET /api/folders` | File counts per folder |

---

## All 26 Skills

| # | Skill | Tier | Description |
|---|-------|------|-------------|
| 1 | `scan_needs_action` | Bronze | List and classify pending tasks |
| 2 | `create_plan` | Bronze | Generate type-aware action plans |
| 3 | `complete_task` | Bronze | Execute tasks with multi-MCP routing |
| 4 | `update_dashboard` | Bronze | Refresh Dashboard.md |
| 5 | `generate_sales_post` | Silver | Draft sales/promotional posts |
| 6 | `request_approval` | Silver | Create HITL approval requests |
| 7 | `execute_action` | Silver | Execute approved actions via MCP |
| 8 | `schedule_task` | Silver | Configure recurring tasks |
| 9 | `sync_odoo_transactions` | Gold | Read Odoo transactions |
| 10 | `create_invoice_draft` | Gold | Create draft invoice in Odoo |
| 11 | `post_approved_invoice` | Gold | Post approved invoice |
| 12 | `generate_social_post` | Gold | Create platform-specific content |
| 13 | `post_approved_social` | Gold | Post approved social content |
| 14 | `summarize_social_activity` | Gold | Fetch social metrics |
| 15 | `weekly_audit` | Gold | Full audit + CEO briefing |
| 16 | `handle_error` | Gold | Detect failures, retry or escalate |
| 17 | `claim_task` | Platinum | Claim task atomically (claim-by-move) |
| 18 | `sync_vault` | Platinum | Git sync between cloud and local |
| 19 | `route_to_local` | Platinum | Route dangerous tasks to local agent |
| 20 | `whatsapp_reply` | Platinum | Compose WhatsApp reply (LOCAL-ONLY) |
| 21 | `process_payment` | Platinum | Handle bank payments (LOCAL-ONLY) |
| 22 | `delegate_to_agent` | Diamond | Route task to best specialized agent |
| 23 | `optimize_prompts` | Diamond | Run self-improving optimization loop |
| 24 | `compliance_report` | Diamond | Generate compliance audit report |
| 25 | `crm_sync` | Diamond | Synchronize CRM contacts and deals |
| 26 | `crisis_response` | Diamond | Handle security alerts and emergencies |

---

## Running Tests

```bash
# All tiers can run tests independently
cd Gold     && python -m pytest tests/ -v    # 55 tests
cd Platinum && python -m pytest tests/ -v    # 215 tests
cd Diamond  && python -m pytest tests/ -v    # 392 tests
```

---

## Modes

| Variable | Default | Description |
|----------|---------|-------------|
| `DRY_RUN` | `true` | Log actions without executing |
| `MOCK_DATA` | `true` | Watchers use fake data |
| `ODOO_MOCK` | `true` | Odoo MCP returns mock data |
| `WHATSAPP_MOCK` | `true` | WhatsApp MCP returns mock data |
| `PAYMENT_MOCK` | `true` | Payment MCP returns mock data |

Set all to `false` in `.env` for live operation.

---

## Tech Stack

- **Language:** Python 3.10+
- **Task Format:** Markdown with YAML frontmatter
- **MCP Protocol:** JSON-RPC 2.0 over stdio
- **Testing:** pytest
- **APIs:** Gmail API, Playwright (LinkedIn), Odoo RPC, Tweepy, Instagrapi, Facebook SDK
- **Infrastructure:** PM2 (process manager), Oracle Cloud Free Tier, Git (vault sync)
- **Diamond extras:** Flask (API), cryptography (vault)

---

## License

This project was built for the Hackathon 0 competition.
