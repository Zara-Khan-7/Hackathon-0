# Diamond Tier — Multi-Agent Swarm with Self-Improving Intelligence

**Status:** Implemented | **Tests:** 392 | **Skills:** 26 | **MCP Servers:** 5 | **Agents:** 4

## What This Tier Does

Diamond is the **intelligence layer** — it transforms Platinum's two-agent system into a **four-agent swarm** where specialized agents (Sales, Finance, Content, Security) collaborate via an in-memory message bus, learn from outcomes to improve over time, and are monitored by automated compliance checks. A REST API exposes the entire system's state, a CRM tracks contacts and deals, and an encrypted credential vault protects secrets.

Think of it as **building a full AI department** — with a sales rep, an accountant, a content creator, and a security officer, all coordinating through a shared communication channel and getting better at their jobs with every task.

## Architecture

```
                        ┌─────────────────────────────────────────┐
                        │          SwarmOrchestrator               │
                        │  1. Pick task from Needs_Action/         │
                        │  2. Find best agent via AgentRegistry    │
                        │  3. Security pre-scan (outgoing content) │
                        │  4. Delegate to specialized agent        │
                        │  5. Record outcome for learning          │
                        │  6. Route to Approval or Done/           │
                        │  7. Auto-optimize every 100 tasks        │
                        └──────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
           ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
           │AgentRegistry │   │  MessageBus  │   │OutcomeTracker│
           │ 4 agents     │   │  (A2A comms) │   │ (learning)   │
           │ score_task() │   │  priority Q  │   │ JSONL log    │
           │ best match   │   │  pub/sub     │   │ patterns     │
           └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
                  │                  │                   │
    ┌─────────────┼─────────────┐    │          ┌───────┼────────┐
    │             │             │    │          │                │
    ▼             ▼             ▼    │          ▼                ▼
┌────────┐  ┌─────────┐  ┌────────┐ │  ┌─────────────┐  ┌───────────┐
│ Sales  │  │Finance  │  │Content │ │  │   Prompt    │  │Performance│
│ Agent  │  │ Agent   │  │ Agent  │ │  │  Optimizer  │  │  Metrics  │
│        │  │         │  │        │ │  │             │  │           │
│EMAIL_  │  │ODOO_    │  │FACE.. │ │  │ Analyzes    │  │ Scores    │
│LINKED..│  │PAYMENT_ │  │INSTA..│ │  │ patterns    │  │ agents on │
│SALES.. │  │AUDIT_   │  │TWIT.. │ │  │ Generates   │  │ reliability│
│        │  │         │  │SOCIAL_│ │  │ recommen-   │  │ speed     │
│        │  │         │  │WHATS..│ │  │ dations     │  │ volume    │
└────┬───┘  └────┬────┘  └───┬───┘ │  └─────────────┘  └───────────┘
     │           │            │     │
     └───────────┼────────────┘     │
                 │                  │
     ┌───────────┼──────────┐      │
     │           │          │      │
     ▼           ▼          ▼      ▼
┌────────┐  ┌────────┐  ┌──────────────┐
│Security│  │  CRM   │  │  REST API    │
│ Agent  │  │ Client │  │  7 endpoints │
│        │  │        │  │              │
│Scans   │  │Contacts│  │/api/status   │
│ALL     │  │Deals   │  │/api/agents   │
│outgoing│  │Pipeline│  │/api/tasks    │
│content │  │Activity│  │/api/metrics  │
│for     │  │Log     │  │/api/crm      │
│secrets │  │        │  │/api/health   │
└────────┘  └────────┘  │/api/folders  │
     │                  └──────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│         Additional Services           │
│                                      │
│  ┌────────────┐  ┌────────────────┐  │
│  │ Credential │  │   Compliance   │  │
│  │   Vault    │  │   Reporter     │  │
│  │            │  │                │  │
│  │ Encrypted  │  │ Checks:        │  │
│  │ storage    │  │ - Approvals    │  │
│  │ for API    │  │ - Audit logs   │  │
│  │ keys,      │  │ - Error rates  │  │
│  │ tokens     │  │ - Completion   │  │
│  └────────────┘  └────────────────┘  │
│                                      │
│  ┌────────────────────────────────┐  │
│  │       Cloud Manager            │  │
│  │  Mock multi-cloud scaling      │  │
│  │  Launch/terminate instances    │  │
│  │  Auto-scale on queue depth     │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

## How the Workflow Works (Step by Step)

### Step 1: Task Arrives
A task file lands in `Needs_Action/` — either from a watcher (EMAIL_, FACEBOOK_, etc.), from a scheduler (SCHEDULE_, AUDIT_), or manually placed.

### Step 2: SwarmOrchestrator Picks Up
The SwarmOrchestrator extends Platinum's base orchestrator. When it finds a task:

```python
# 1. Find the best agent for this task
best_agent = self.registry.find_best_agent(task_prefix)
# Returns the agent with highest score for this task type

# 2. Security pre-scan
security_result = self.security_agent.scan_outgoing(task_content, task_type)
# Checks for passwords, tokens, API keys, bank details in content

# 3. Delegate to the specialized agent
result = best_agent.process_task(task_file)
# Agent reads the file, creates plan, executes within its domain

# 4. Record the outcome
self.outcome_tracker.record(task_id, agent_id, outcome, duration)
# Stored as JSONL for later analysis

# 5. Route result
if result.requires_approval:
    move_to("Pending_Approval/")
else:
    move_to("Done/")
```

### Step 3: Agent Selection (AgentRegistry)
Each agent declares its capabilities and scores tasks:

| Agent | Task Prefixes | Score Method |
|-------|--------------|-------------|
| **Sales Agent** | EMAIL_, LINKEDIN_, SALESPOST_ | 0.9 for email, 0.85 for LinkedIn, 0.8 for sales |
| **Finance Agent** | ODOO_, PAYMENT_, AUDIT_ | 0.9 for Odoo, 0.85 for payment, 0.8 for audit |
| **Content Agent** | FACEBOOK_, INSTAGRAM_, TWITTER_, SOCIAL_, WHATSAPP_ | 0.9 for social, 0.85 for WhatsApp |
| **Security Agent** | ERROR_, EXECUTE_, SCHEDULE_ | 0.9 for errors, 0.85 for execute |

The registry picks the agent with the highest score. If no agent matches, the task falls back to the base orchestrator.

### Step 4: Agent Processing
Each agent has domain-specific logic:

**Sales Agent** processes `EMAIL_001.md`:
1. Reads the email content and sender info
2. Checks CRM for existing contact/deal history
3. Drafts a professional reply with relevant pricing/info
4. Routes to Pending_Approval/ (external communication)

**Finance Agent** processes `ODOO_invoice.md`:
1. Reads invoice request details
2. Calls Odoo MCP `create_invoice_draft` (DRAFT — safe)
3. Routes to Pending_Approval/ for human to confirm posting

**Content Agent** processes `FACEBOOK_post.md`:
1. Reads the content brief
2. Formats for Facebook-specific requirements (character limits, hashtags)
3. Calls Social MCP `draft_social_post` (DRAFT — safe)
4. Routes to Pending_Approval/ (publishing requires approval)

**Security Agent** processes `ERROR_timeout.md`:
1. Reads the error details (what failed, stack trace, retry count)
2. Determines if retryable or needs escalation
3. Either creates a retry task or alerts the human

### Step 5: Security Scanning
The Security Agent scans ALL outgoing content before any external action:

```python
SENSITIVE_KEYWORDS = [
    "password", "credential", "secret", "token",
    "api_key", "bank", "transfer", "payment",
    "invoice", "wire"
]
```

If any keyword is detected:
- The task is flagged with `security_flagged: true`
- A security alert is broadcast to all agents via the A2A bus
- The task is routed to Pending_Approval/ for mandatory human review
- The human decides if the content is safe to send

### Step 6: A2A Communication
Agents communicate via the MockMessageBus (in-memory, simulates RabbitMQ/Redis):

**Message Types:**
| Type | Example |
|------|---------|
| `task_delegation` | Orchestrator → Sales Agent: "Handle EMAIL_001" |
| `task_result` | Sales Agent → Orchestrator: "Draft created, needs approval" |
| `info_request` | Sales Agent → Finance Agent: "What's the account balance?" |
| `info_response` | Finance Agent → Sales Agent: "Balance: $45,230" |
| `security_alert` | Security Agent → ALL: "Sensitive keyword detected in EMAIL_001" |
| `broadcast` | Orchestrator → ALL: "System entering maintenance mode" |

**Priority Queuing:** Messages are delivered in priority order:
- URGENT (0) > HIGH (1) > NORMAL (2) > LOW (3)

### Step 7: Self-Improving Loop
Every task outcome is recorded by the OutcomeTracker:

```json
{"task_id": "EMAIL_001", "agent_id": "sales-agent", "outcome": "success", "duration": 2.3, "timestamp": 1708732800}
```

Every 100 completed tasks, the PromptOptimizer analyzes patterns:
1. **Agent Reassignment** — If Finance Agent fails on email tasks >30% of the time, recommend reassigning to Sales Agent
2. **Failure Patterns** — If "timeout" appears in 3+ failures, recommend increasing timeout or adding retry
3. **Slow Agents** — If Content Agent averages >30s per task, recommend simplifying its prompts

The PerformanceMetrics module scores each agent:
- **Reliability** (50% weight) — success rate
- **Speed** (30% weight) — average task duration
- **Volume** (20% weight) — number of tasks handled
- **Composite** — weighted combination (0-100 scale)

### Step 8: Completion
Approved tasks execute via MCP tools. Results move to `Done/`, audit logs are written, the dashboard updates, and CRM contacts/deals are updated if relevant.

## Specialized Agents (4)

| Agent | Domain | Task Prefixes | Capabilities |
|-------|--------|---------------|-------------|
| **Sales Agent** | Email, LinkedIn, Sales | `EMAIL_`, `LINKEDIN_`, `SALESPOST_` | Professional email replies, LinkedIn outreach, sales content, CRM integration |
| **Finance Agent** | ERP, Payments, Audits | `ODOO_`, `PAYMENT_`, `AUDIT_` | Invoice creation, payment processing, financial auditing, transaction sync |
| **Content Agent** | Social Media, Messaging | `FACEBOOK_`, `INSTAGRAM_`, `TWITTER_`, `SOCIAL_`, `WHATSAPP_` | Platform-specific content, hashtags, engagement, WhatsApp replies |
| **Security Agent** | Validation, Errors | `ERROR_`, `EXECUTE_`, `SCHEDULE_` | Content scanning, error investigation, compliance validation, threat response |

## REST API (7 Endpoints)

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/status` | GET | System status | Tier, mode, uptime, agent count |
| `/api/agents` | GET | All 4 agents | Name, status, tasks done, success rate |
| `/api/tasks` | GET | Tasks by folder | `?folder=Needs_Action` returns task list |
| `/api/metrics` | GET | Performance metrics | Success rate, avg duration, patterns |
| `/api/crm` | GET | CRM summary | Contacts, deals, pipeline value |
| `/api/health` | GET | System health | All checks: heartbeat, disk, errors |
| `/api/folders` | GET | Folder counts | File count per folder |

## CRM Integration

The CRM tracks contacts and deals throughout the sales pipeline:

| Feature | Description |
|---------|-------------|
| **Contacts** | Name, email, company, status (lead/active/inactive) |
| **Deals** | Contact, value, stage (lead/proposal/negotiation/closed_won/closed_lost) |
| **Pipeline** | Total value by stage, win rate, deal count |
| **Activities** | Log interactions (email sent, meeting, call, note) |

Mock data includes 3 contacts, 3 deals ($182K pipeline), and 3 activities.

## Compliance Reporter

Automated compliance checks run on demand and verify:

| Check | What It Verifies |
|-------|-----------------|
| **Approval Pipeline** | All dangerous actions went through Pending_Approval/ |
| **Audit Log** | Logs/audit.jsonl exists and has recent entries |
| **Error Handling** | Error rate is below threshold (20%) |
| **Completion Rates** | Tasks are being completed (not stuck indefinitely) |

Results: `COMPLIANT`, `NON_COMPLIANT`, or `NEEDS_REVIEW`. Reports saved to `Briefings/`.

## Credential Vault

Encrypted storage for API keys, tokens, and secrets:

| Operation | Description |
|-----------|-------------|
| `store(key, value)` | Encrypt and store a credential |
| `retrieve(key)` | Decrypt and return a credential |
| `delete(key)` | Remove a credential |
| `list_keys()` | List all stored credential names |
| `has(key)` | Check if a credential exists |

Mock mode uses base64 encoding. Production mode uses Fernet symmetric encryption from the `cryptography` library. All access is logged for audit.

## Directory Structure

```
Diamond/
├── src/
│   ├── agents/                    # NEW in Diamond
│   │   ├── base_agent.py          # BaseSpecializedAgent, AgentStatus, AgentCapability
│   │   ├── sales_agent.py         # Sales Agent (EMAIL_, LINKEDIN_, SALESPOST_)
│   │   ├── finance_agent.py       # Finance Agent (ODOO_, PAYMENT_, AUDIT_)
│   │   ├── content_agent.py       # Content Agent (FACEBOOK_..WHATSAPP_)
│   │   ├── security_agent.py      # Security Agent (ERROR_, EXECUTE_) + scan_outgoing()
│   │   └── agent_registry.py      # AgentRegistry: register, find_best_agent, stats
│   ├── a2a/                       # NEW in Diamond
│   │   ├── message.py             # A2AMessage, MessageType, MessagePriority
│   │   ├── message_bus.py         # MockMessageBus: publish, consume, subscribe
│   │   └── router.py              # MessageRouter: delegate, request_info, broadcast
│   ├── learning/                  # NEW in Diamond
│   │   ├── outcome_tracker.py     # OutcomeTracker: record, success_rate, patterns
│   │   ├── prompt_optimizer.py    # PromptOptimizer: analyze, recommend changes
│   │   └── performance_metrics.py # PerformanceMetrics: score agents, rank, health
│   ├── vault/                     # NEW in Diamond
│   │   └── credential_vault.py    # CredentialVault: store, retrieve, delete (encrypted)
│   ├── compliance/                # NEW in Diamond
│   │   └── compliance_reporter.py # ComplianceReporter: run checks, generate reports
│   ├── crm/                       # NEW in Diamond
│   │   ├── mock_crm.py            # Mock contacts, deals, activities
│   │   └── crm_client.py          # CRMClient: contacts, deals, pipeline, activities
│   ├── api/                       # NEW in Diamond
│   │   └── api_server.py          # APIServer: 7 endpoints (Flask/mock)
│   ├── scaling/                   # NEW in Diamond
│   │   └── cloud_manager.py       # CloudManager: launch, terminate, scale instances
│   ├── orchestrator/
│   │   ├── orchestrator.py        # Base (Gold) + --role diamond
│   │   ├── cloud_orchestrator.py  # Cloud (Platinum)
│   │   ├── local_orchestrator.py  # Local (Platinum)
│   │   └── swarm_orchestrator.py  # SwarmOrchestrator (Diamond)
│   ├── config/                    # From Platinum
│   ├── claim/                     # From Platinum
│   ├── sync/                      # From Platinum
│   ├── health/                    # From Platinum
│   ├── mcp_email/                 # From Silver (3 tools)
│   ├── mcp_odoo/                  # From Gold (6 tools)
│   ├── mcp_social/                # From Gold (5 tools)
│   ├── mcp_whatsapp/              # From Platinum (3 tools, LOCAL-ONLY)
│   ├── mcp_payment/               # From Platinum (5 tools, LOCAL-ONLY)
│   ├── watchers/                  # 6 watchers (from all tiers)
│   ├── approval/                  # HITL pipeline (from Silver)
│   ├── scheduler/                 # Recurring tasks (from Silver)
│   ├── audit/                     # Weekly auditor (from Gold)
│   ├── errors/                    # Error handler (from Gold)
│   └── utils/                     # Shared utilities
├── tests/                         # 29 test files, 392 tests
│   ├── test_specialized_agents.py # 40 tests: all 4 agents
│   ├── test_message_bus.py        # 12 tests: A2A messaging
│   ├── test_a2a_router.py         # 12 tests: message routing
│   ├── test_outcome_tracker.py    # 16 tests: outcome tracking + optimization
│   ├── test_performance_metrics.py# 9 tests: agent scoring
│   ├── test_credential_vault.py   # 12 tests: vault operations
│   ├── test_compliance_reporter.py# 8 tests: compliance checks
│   ├── test_crm_client.py         # 16 tests: CRM operations
│   ├── test_api_server.py         # 11 tests: REST API
│   ├── test_cloud_manager.py      # 13 tests: cloud scaling
│   ├── test_swarm_orchestrator.py # 12 tests: swarm pipeline
│   ├── test_e2e_diamond_demo.py   # 12 tests: full integration
│   └── ... (Platinum + Gold tests preserved)
├── .claude/skills/                # 26 agent skills
├── deploy/                        # PM2, cloud/local setup scripts
├── Dashboard.md                   # Full swarm dashboard
├── Company_Handbook.md            # Complete rules (Diamond)
├── config.yaml                    # Central configuration
└── requirements.txt               # + cryptography, flask
```

## All 26 Skills

| # | Skill | Tier | What It Does |
|---|-------|------|-------------|
| 1 | `scan_needs_action` | Bronze | List and classify all pending tasks |
| 2 | `create_plan` | Bronze | Generate type-aware action plans |
| 3 | `complete_task` | Bronze | Execute tasks with multi-MCP routing |
| 4 | `update_dashboard` | Bronze | Refresh Dashboard.md with all stats |
| 5 | `generate_sales_post` | Silver | Draft LinkedIn/sales posts |
| 6 | `request_approval` | Silver | Create HITL approval requests |
| 7 | `execute_action` | Silver | Execute approved actions via MCP |
| 8 | `schedule_task` | Silver | Configure recurring tasks |
| 9 | `sync_odoo_transactions` | Gold | Read Odoo transactions to Accounting/ |
| 10 | `create_invoice_draft` | Gold | Create draft invoice in Odoo ERP |
| 11 | `post_approved_invoice` | Gold | Post approved invoice (confirms in Odoo) |
| 12 | `generate_social_post` | Gold | Create platform-specific content |
| 13 | `post_approved_social` | Gold | Post approved social content |
| 14 | `summarize_social_activity` | Gold | Fetch engagement metrics |
| 15 | `weekly_audit` | Gold | Full audit + CEO briefing |
| 16 | `handle_error` | Gold | Detect failures, retry or escalate |
| 17 | `claim_task` | Platinum | Atomic claim-by-move to In_Progress/ |
| 18 | `sync_vault` | Platinum | Git pull/push between cloud and local |
| 19 | `route_to_local` | Platinum | Route dangerous tasks to local agent |
| 20 | `whatsapp_reply` | Platinum | Compose WhatsApp replies (LOCAL-ONLY) |
| 21 | `process_payment` | Platinum | Handle bank payments (LOCAL-ONLY) |
| 22 | `delegate_to_agent` | Diamond | Route task to best specialized agent |
| 23 | `optimize_prompts` | Diamond | Run self-improving optimization loop |
| 24 | `compliance_report` | Diamond | Generate compliance audit report |
| 25 | `crm_sync` | Diamond | Synchronize CRM contacts and deals |
| 26 | `crisis_response` | Diamond | Handle security alerts and emergencies |

## What Diamond Adds Over Platinum

| Feature | Platinum | Diamond |
|---------|----------|---------|
| Architecture | 2 agents (cloud/local) | 4 specialized agents + swarm |
| Agent Intelligence | Same logic for all tasks | Domain-expert agents score and claim tasks |
| Communication | Git sync only | A2A message bus (pub/sub, priority queues) |
| Learning | None | OutcomeTracker + PromptOptimizer + Metrics |
| Security | Tool policy only | Security Agent scans ALL outgoing content |
| Secrets | Isolated by machine | Encrypted credential vault |
| CRM | None | Full contact/deal/pipeline management |
| API | None | REST API with 7 endpoints |
| Compliance | None | Automated compliance checks + reports |
| Scaling | Fixed 2 agents | Dynamic cloud instance management |
| Skills | 21 | 26 (+5 new) |
| Tests | 215 | 392 (+177 new) |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests (392 tests)
python -m pytest tests/ -v

# Diamond swarm orchestrator (dry-run)
python -m src.orchestrator.orchestrator --role diamond --dry-run --once

# Cloud orchestrator (dry-run, backward-compatible)
python -m src.orchestrator.orchestrator --role cloud --dry-run --once

# Local orchestrator (dry-run, backward-compatible)
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

## Backward Compatibility

All lower-tier tests continue to pass:
- Gold: 55/55
- Platinum: 215/215
- Diamond: 392/392

Every `--role` mode is supported: `diamond`, `cloud`, `local`, `gold`.
