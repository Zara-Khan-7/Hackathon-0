# Platinum Tier — Always-On Hybrid AI Employee

**Status:** Implemented | **Tests:** 66+ | **Skills:** 21 | **MCP Servers:** 5

## Architecture

```
        CLOUD VM (Oracle A1, 24/7)                LOCAL MACHINE (on-demand)
        ==========================                ==========================
Gmail/LI/FB/IG/X Watchers                        SyncWatcher (git pull every 60s)
         |                                              |
    Needs_Action/*.md                              Needs_Action/ <-- git pull
         |                                              |
  CloudOrchestrator                               LocalOrchestrator
  (SAFE + DRAFT tools only)                       (ALL tools, incl WhatsApp/Payment)
         |                                              |
  claim-by-move --> In_Progress/cloud-001/        claim-by-move --> In_Progress/local-001/
         |                                              |
  create_plan + draft_only                         Full execution via MCP
         |                                              |
  Pending_Approval/ --> git push                   Approval Watcher (terminal HITL)
                        |                               |
                   Private Git Repo <--> git pull   EXECUTE_*.md --> Done/
                                                        |
                                                   WhatsApp/Payment MCPs (local-only)
                                                        |
                                                   git push --> remote
```

## What's New in Platinum

| Feature | Description |
|---------|-------------|
| Hybrid Architecture | Cloud drafts, local executes |
| Domain Routing | 13 prefix types routed by role |
| Tool Policy | SAFE/DRAFT/DANGEROUS classification |
| Claim-by-Move | Atomic task ownership via os.rename |
| Git Vault Sync | Mock sync between cloud and local |
| WhatsApp MCP | 3 tools: list, read, send (LOCAL-ONLY) |
| Payment MCP | 5 tools: accounts, balance, txns, pay, status (LOCAL-ONLY) |
| Health Monitor | Heartbeat, disk, error rate checks |
| 5 New Skills | claim_task, sync_vault, route_to_local, whatsapp_reply, process_payment |

## Quick Start

```bash
# Setup
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Cloud orchestrator (dry-run)
python -m src.orchestrator.orchestrator --role cloud --dry-run --once

# Local orchestrator (dry-run)
python -m src.orchestrator.orchestrator --role local --dry-run --once

# Gold mode (backward-compatible)
python -m src.orchestrator.orchestrator --role gold --dry-run --once
```

## MCP Servers

| Server | Tools | Availability |
|--------|-------|-------------|
| Email | send_email, draft_email, list_drafts | Cloud + Local |
| Odoo | list_invoices, read_invoice, create_invoice_draft, post_invoice, list_partners, read_transactions | Cloud + Local |
| Social | post_facebook, post_instagram, post_twitter, get_social_summary, draft_social_post | Cloud + Local |
| WhatsApp | list_whatsapp_chats, read_whatsapp_chat, send_whatsapp | LOCAL-ONLY |
| Payment | list_accounts, get_balance, list_transactions, initiate_payment, payment_status | LOCAL-ONLY |

## Safety Model

- **Cloud Agent** can only call SAFE + DRAFT tools — never sends, posts, or pays
- **Local Agent** has full access — handles HITL approvals and dangerous actions
- **WhatsApp + Payment** servers only run on local machine
- **All external actions** require human approval
- **Mock mode** by default — no real actions without explicit configuration

## Project Structure

```
Platinum/
├── src/
│   ├── config/          # AgentConfig, DomainRouter, ToolPolicy
│   ├── claim/           # ClaimManager (claim-by-move)
│   ├── sync/            # GitVaultSync, ConflictResolver, SyncWatcher
│   ├── orchestrator/    # Gold + Cloud + Local orchestrators
│   ├── health/          # Heartbeat, HealthMonitor
│   ├── mcp_whatsapp/    # WhatsApp MCP server (LOCAL-ONLY)
│   ├── mcp_payment/     # Payment MCP server (LOCAL-ONLY)
│   ├── mcp_email/       # Email MCP server
│   ├── mcp_odoo/        # Odoo ERP MCP server
│   ├── mcp_social/      # Social media MCP server
│   ├── watchers/        # Gmail, LinkedIn, FB, IG, X, WhatsApp watchers
│   ├── approval/        # HITL approval pipeline
│   ├── scheduler/       # Recurring task scheduler
│   ├── audit/           # Weekly business auditor
│   └── utils/           # file_ops, logger, mcp_registry, frontmatter, retry
├── tests/               # 17 test files, 66+ tests
├── deploy/              # PM2, cloud/local setup scripts
├── .claude/skills/      # 21 Claude agent skills
└── config.yaml          # Central configuration
```

## Builds on Gold Tier

All 55 Gold tier tests continue to pass. Platinum adds ~11 new test files covering:
- Agent config, domain routing, tool policy
- Claim-by-move, git sync, conflict resolution
- Cloud + local orchestrators
- WhatsApp + Payment MCP servers
- Health monitoring
- End-to-end offline demo
