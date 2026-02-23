# Platinum Tier — Always-On Hybrid Cloud/Local AI Employee

**Status:** Implemented | **Tests:** 215 | **Skills:** 21 | **MCP Servers:** 5 | **Watchers:** 6

## What This Tier Does

Platinum is the **infrastructure layer** — it splits the AI employee into two coordinated agents: a **Cloud Agent** running 24/7 on Oracle Cloud Free Tier that monitors and drafts, and a **Local Agent** on your machine that executes dangerous actions with full human oversight. Tasks are synchronized via Git, ownership is managed with atomic claim-by-move, and two new MCP servers handle WhatsApp messaging and bank payments.

Think of it as **giving your AI employee a 24/7 office** — the cloud agent works nights and weekends creating drafts, while you review and approve from your desk when you're ready.

## Architecture

```
    ┌────────────────────────────────────────────────────────────────────┐
    │                     CLOUD VM (Oracle A1, 24/7)                     │
    │                                                                    │
    │  Gmail   LinkedIn  Facebook  Instagram  Twitter/X                  │
    │    │        │         │          │          │                       │
    │    ▼        ▼         ▼          ▼          ▼                       │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │              5 Watchers (--mock)              │                  │
    │  └──────────────────┬───────────────────────────┘                  │
    │                     ▼                                              │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │            Needs_Action/*.md                  │                  │
    │  └──────────────────┬───────────────────────────┘                  │
    │                     ▼                                              │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │          CloudOrchestrator                    │                  │
    │  │  1. Claim task (os.rename → In_Progress/)    │                  │
    │  │  2. Read + classify by prefix                │                  │
    │  │  3. Create plan (SAFE tools only)            │                  │
    │  │  4. Draft response (DRAFT tools only)        │                  │
    │  │  5. Force requires_approval = true           │                  │
    │  │  6. Move to Pending_Approval/                │                  │
    │  │  *** NEVER calls DANGEROUS tools ***         │                  │
    │  └──────────────────┬───────────────────────────┘                  │
    │                     ▼                                              │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │  Pending_Approval/APPROVE_EMAIL_001.md       │                  │
    │  └──────────────────┬───────────────────────────┘                  │
    │                     ▼                                              │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │  git add + commit + push                     │ ◄── Auto-sync   │
    │  └──────────────────┬───────────────────────────┘     after each   │
    │                     │                                  poll cycle   │
    └─────────────────────┼──────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Private Git Repo    │  <-- Sync bridge
              │   (GitHub/GitLab)     │
              └───────────┬───────────┘
                          │
    ┌─────────────────────┼──────────────────────────────────────────────┐
    │                     ▼            LOCAL MACHINE (on-demand)          │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │  SyncWatcher (git pull every 60 seconds)     │                  │
    │  └──────────────────┬───────────────────────────┘                  │
    │                     ▼                                              │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │          Pending_Approval/                    │                  │
    │  │          APPROVE_EMAIL_001.md                 │                  │
    │  └──────────────────┬───────────────────────────┘                  │
    │                     ▼                                              │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │       Approval Watcher (Terminal HITL)        │                  │
    │  │       [A]pprove  [R]eject  [M]odify          │                  │
    │  └──────────────────┬───────────────────────────┘                  │
    │                     ▼                                              │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │          LocalOrchestrator                    │                  │
    │  │  - Full MCP tool access (ALL tools)          │                  │
    │  │  - Executes EXECUTE_*, WHATSAPP_*, PAYMENT_* │                  │
    │  │  - Calls DANGEROUS tools (send, post, pay)   │                  │
    │  └──────────────────┬───────────────────────────┘                  │
    │                     ▼                                              │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │            5 MCP Servers                      │                  │
    │  │  Email | Odoo | Social | WhatsApp | Payment  │                  │
    │  │                        (LOCAL-ONLY) (LOCAL-ONLY)               │
    │  └──────────────────┬───────────────────────────┘                  │
    │                     ▼                                              │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │  Done/ + Logs/ + Dashboard.md                │                  │
    │  │  git add + commit + push                     │ ◄── Auto-sync   │
    │  └──────────────────────────────────────────────┘                  │
    │                                                                    │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │  WhatsApp Watcher (LOCAL-ONLY)               │                  │
    │  │  Monitors WhatsApp messages                  │                  │
    │  │  Creates WHATSAPP_*.md in Needs_Action/      │                  │
    │  └──────────────────────────────────────────────┘                  │
    │                                                                    │
    │  ┌──────────────────────────────────────────────┐                  │
    │  │  Health Monitor                               │                  │
    │  │  Checks heartbeats, disk, error rates        │                  │
    │  │  Creates ERROR_HEALTH_*.md on critical issues│                  │
    │  └──────────────────────────────────────────────┘                  │
    └────────────────────────────────────────────────────────────────────┘
```

## How the Workflow Works (Step by Step)

### Step 1: Cloud Detection (24/7)
The Cloud VM runs all 5 original watchers continuously. When a new email arrives at 3 AM, the Gmail watcher creates `EMAIL_20260223_alice.md` in `Needs_Action/`. No human needs to be awake.

### Step 2: Cloud Claim (Claim-by-Move)
The CloudOrchestrator **claims** the task atomically:
```
os.rename("Needs_Action/EMAIL_001.md", "In_Progress/cloud-001/EMAIL_001.md")
```
This is atomic on most filesystems — only one agent can claim a task. If two agents race for the same file, one gets `FileNotFoundError` and moves on. Stale claims (>1 hour) are automatically moved back to `Needs_Action/`.

### Step 3: Cloud Draft (SAFE + DRAFT Tools Only)
The CloudOrchestrator processes the task but is **restricted by Tool Policy**:

| Tool Classification | Cloud Can Use? | Local Can Use? |
|---------------------|---------------|----------------|
| **SAFE** (read-only) | YES | YES |
| **DRAFT** (creates drafts) | YES | YES |
| **DANGEROUS** (sends/posts/pays) | **NO** | YES |

So the cloud agent:
1. Reads the task, creates a plan
2. Calls `draft_email` (DRAFT) — NOT `send_email` (DANGEROUS)
3. Forces `requires_approval: true` in the frontmatter
4. Moves the draft to `Pending_Approval/APPROVE_EMAIL_001.md`

### Step 4: Git Sync (Cloud → Local)
After each poll cycle, the cloud agent:
```bash
git add Pending_Approval/ Done/ Logs/
git commit -m "[cloud-001] Auto-sync 2026-02-23T03:15:00"
git push
```

Meanwhile, the local machine runs a **SyncWatcher** that pulls every 60 seconds:
```bash
git stash && git pull --rebase && git stash pop
```

Conflict resolution is deterministic:
- `Needs_Action/` — keep incoming (theirs) — new tasks take priority
- `In_Progress/` — keep local (ours) — don't interrupt active work
- `Logs/` — union (both) — never lose audit entries

### Step 5: Human Review (Local HITL)
When the local machine pulls the new `APPROVE_EMAIL_001.md`, the approval watcher presents it for review. The human approves, and an `EXECUTE_EMAIL_001.md` is created.

### Step 6: Local Execution (Full MCP Access)
The LocalOrchestrator picks up the `EXECUTE_*` file and has access to ALL 5 MCP servers, including the two LOCAL-ONLY servers:

**WhatsApp MCP** (LOCAL-ONLY):
- `list_whatsapp_chats` — List active conversations (SAFE)
- `read_whatsapp_chat` — Read chat messages (SAFE)
- `send_whatsapp` — Send a WhatsApp message (DANGEROUS)

**Payment MCP** (LOCAL-ONLY):
- `list_accounts` — List bank accounts (SAFE)
- `get_balance` — Check account balance (SAFE)
- `list_transactions` — List recent transactions (SAFE)
- `initiate_payment` — Make a bank transfer (DANGEROUS)
- `payment_status` — Check payment status (SAFE)

These servers **never run on the cloud** — banking credentials and WhatsApp sessions stay on the local machine.

### Step 7: Completion + Sync Back
The local agent moves completed tasks to `Done/`, updates logs, and pushes to Git. The cloud sees the completion on its next pull.

### Step 8: Health Monitoring
The HealthMonitor runs periodically and checks:
- **Heartbeat** — Each agent writes a `.heartbeat_{agent_id}.json` file. If a heartbeat is >5 minutes old, the agent may be dead
- **Disk usage** — Warns if the task folder is getting too large
- **Error rate** — If >20% of recent tasks failed, creates an alert
- Critical issues create `ERROR_HEALTH_*.md` for human attention

## Domain Routing Rules

| Task Prefix | Cloud Action | Local Action | Why Split? |
|-------------|-------------|-------------|------------|
| `EMAIL_` | Draft reply | Send email | SMTP credentials local-only |
| `LINKEDIN_` | Draft post | Post content | Session cookies local-only |
| `FACEBOOK_` | Draft post | Post content | API key local-only |
| `INSTAGRAM_` | Draft | Post content | Session local-only |
| `TWITTER_` | Draft tweet | Post tweet | API key local-only |
| `WHATSAPP_` | **Skip** | Full access | Session files never sync |
| `PAYMENT_` | **Skip** | Full access | Banking creds never sync |
| `SCHEDULE_` | Full | Full | Either can schedule |
| `ODOO_` | Draft invoice | Post invoice | Posting is dangerous |
| `AUDIT_` | Full | Full | Read-only, either can do |
| `ERROR_` | Handle/retry | Handle/retry | Either can handle |
| `APPROVE_` | **Skip** | HITL terminal | Requires human |
| `EXECUTE_` | **Skip** | Execute action | Only local executes |

## Directory Structure

```
Platinum/
├── src/
│   ├── config/                    # NEW in Platinum
│   │   ├── agent_config.py        # AgentRole enum, AgentConfig class
│   │   ├── domain_router.py       # Routing table: prefix → cloud/local action
│   │   └── tool_policy.py         # SAFE/DRAFT/DANGEROUS classification
│   ├── claim/                     # NEW in Platinum
│   │   └── claim_manager.py       # Atomic claim-by-move + stale cleanup
│   ├── sync/                      # NEW in Platinum
│   │   ├── git_sync.py            # GitVaultSync: pull, push, sync_cycle
│   │   ├── conflict_resolver.py   # Deterministic merge conflict rules
│   │   └── sync_watcher.py        # Background daemon (pull every 60s)
│   ├── health/                    # NEW in Platinum
│   │   ├── heartbeat.py           # Write heartbeat JSON files
│   │   └── health_monitor.py      # Check heartbeats, disk, error rate
│   ├── orchestrator/
│   │   ├── orchestrator.py        # Base orchestrator (Gold) + --role flag
│   │   ├── cloud_orchestrator.py  # CloudOrchestrator (SAFE+DRAFT only)
│   │   └── local_orchestrator.py  # LocalOrchestrator (ALL tools)
│   ├── mcp_whatsapp/              # NEW in Platinum (LOCAL-ONLY)
│   │   ├── whatsapp_server.py     # JSON-RPC MCP: 3 tools
│   │   ├── whatsapp_client.py     # Subprocess wrapper
│   │   └── mock_whatsapp.py       # Mock chats/messages
│   ├── mcp_payment/               # NEW in Platinum (LOCAL-ONLY)
│   │   ├── payment_server.py      # JSON-RPC MCP: 5 tools
│   │   ├── payment_client.py      # Subprocess wrapper
│   │   └── mock_payment.py        # Mock accounts/transactions
│   ├── watchers/
│   │   ├── gmail_watcher.py       # Gmail (from Silver)
│   │   ├── linkedin_watcher.py    # LinkedIn (from Silver)
│   │   ├── facebook_watcher.py    # Facebook (from Gold)
│   │   ├── instagram_watcher.py   # Instagram (from Gold)
│   │   ├── twitter_watcher.py     # Twitter/X (from Gold)
│   │   └── whatsapp_watcher.py    # WhatsApp (NEW, LOCAL-ONLY)
│   ├── mcp_email/                 # Email MCP (from Silver)
│   ├── mcp_odoo/                  # Odoo MCP (from Gold)
│   ├── mcp_social/                # Social MCP (from Gold)
│   ├── approval/                  # HITL approval (from Silver)
│   ├── scheduler/                 # Recurring tasks (from Silver)
│   ├── audit/                     # Weekly auditor (from Gold)
│   ├── errors/                    # Error handler (from Gold)
│   └── utils/
│       ├── file_ops.py            # + get_in_progress_folder()
│       ├── logger.py              # + agent_id in audit logs
│       ├── mcp_registry.py        # + whatsapp/payment, + policy filter
│       ├── frontmatter.py
│       └── retry.py
├── tests/                         # 17 test files, 215 tests
│   ├── test_agent_config.py
│   ├── test_domain_router.py
│   ├── test_tool_policy.py
│   ├── test_claim_manager.py
│   ├── test_git_sync.py
│   ├── test_cloud_orchestrator.py
│   ├── test_local_orchestrator.py
│   ├── test_whatsapp_server.py
│   ├── test_payment_server.py
│   ├── test_health_monitor.py
│   ├── test_e2e_offline_demo.py
│   └── ... (Gold tests preserved)
├── deploy/
│   ├── ecosystem.config.js        # PM2 process manager config
│   ├── setup_cloud.sh             # Oracle Cloud VM provisioning
│   ├── setup_local.sh             # Local environment setup
│   └── deploy_cloud.sh            # Git clone + PM2 start
├── In_Progress/                   # Claimed tasks (by agent_id)
├── .claude/skills/                # 21 agent skills
├── Dashboard.md                   # + cloud/local agent health sections
├── Company_Handbook.md            # + Platinum hybrid rules
├── config.yaml                    # + agent section (id, role, sync)
└── requirements.txt               # + gitpython, psutil
```

## The 21 Skills

Skills 1-16 are inherited from Gold. Platinum adds 5 new skills:

| # | Skill | What It Does |
|---|-------|-------------|
| 17 | `claim_task` | Atomically claim a task via os.rename to In_Progress/{agent_id}/ |
| 18 | `sync_vault` | Run git pull/push cycle to sync between cloud and local |
| 19 | `route_to_local` | Move a task to Pending_Approval/ for local execution |
| 20 | `whatsapp_reply` | Draft and send WhatsApp messages (LOCAL-ONLY) |
| 21 | `process_payment` | Initiate bank payments via Payment MCP (LOCAL-ONLY) |

## What Platinum Adds Over Gold

| Feature | Gold | Platinum |
|---------|------|----------|
| Architecture | Single machine | Cloud + Local hybrid |
| Availability | When you run it | Cloud agent runs 24/7 |
| Watchers | 5 | 6 (+WhatsApp, LOCAL-ONLY) |
| MCP Servers | 3 | 5 (+WhatsApp, +Payment) |
| Task Ownership | None | Claim-by-move (atomic) |
| Sync | None | Git vault sync + conflict resolution |
| Health | None | Heartbeat + disk + error rate monitor |
| Secrets | In config | Isolated (local-only, never synced) |
| Skills | 16 | 21 (+5 new) |
| Tests | 55 | 215 |

## What the Next Tier (Diamond) Adds

Diamond builds on Platinum by adding:
- **4 specialized agents** — Sales, Finance, Content, Security (domain experts)
- **A2A message bus** — Agents communicate via in-memory message bus
- **Self-improving loop** — OutcomeTracker + PromptOptimizer + PerformanceMetrics
- **Credential vault** — Encrypted storage for API keys and secrets
- **CRM integration** — Contact management, deal pipeline, activity logging
- **REST API** — 7 endpoints for status, agents, tasks, metrics, CRM, health
- **Compliance reporter** — Automated compliance checks + markdown reports
- **Cloud scaling** — Mock multi-cloud instance management
- **5 more skills** (26 total)
- **392 passing tests**

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests (215 tests)
python -m pytest tests/ -v

# Cloud orchestrator (dry-run)
python -m src.orchestrator.orchestrator --role cloud --dry-run --once

# Local orchestrator (dry-run)
python -m src.orchestrator.orchestrator --role local --dry-run --once

# Gold mode (backward-compatible)
python -m src.orchestrator.orchestrator --role gold --dry-run --once
```

## Modes

| Variable | Default | Description |
|----------|---------|-------------|
| `DRY_RUN` | `true` | Log all external actions instead of executing |
| `MOCK_DATA` | `true` | Watchers use fake data |
| `ODOO_MOCK` | `true` | Odoo MCP returns mock data |
| `WHATSAPP_MOCK` | `true` | WhatsApp MCP returns mock data |
| `PAYMENT_MOCK` | `true` | Payment MCP returns mock data |

Set all to `false` in `.env` for live operation.
