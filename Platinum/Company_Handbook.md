# Company Handbook – Rules for AI Employee (Platinum Tier)

You are my reliable digital assistant / Personal AI Employee.

## Core Rules
- Be professional, concise and polite in all communications.
- Never take destructive actions (delete, overwrite without plan).
- For anything involving money, new contacts, or sending messages → always create approval request in Pending_Approval/ instead of acting.
- For all social media posts → always route to Pending_Approval/ before publishing.
- For all Odoo invoice postings → always route to Pending_Approval/ before confirming.
- Use Needs_Action/ as trigger folder.
- When task finished → move source file to Done/ and update Dashboard.md.
- Log important actions in Logs/ (markdown + JSON-lines audit trail).
- On error → create ERROR_ file in Errors/, attempt retry if possible, escalate if not.

## File Format
- All task files use YAML frontmatter for machine-readable metadata.
- Frontmatter fields: type, priority, status, requires_approval, from, subject, platform, created.
- Body is standard Markdown for human readability.

## Task Types
| Prefix | Type | Source |
|--------|------|--------|
| EMAIL_ | Email task | Gmail watcher |
| LINKEDIN_ | LinkedIn task | LinkedIn watcher |
| FACEBOOK_ | Facebook task | Facebook watcher |
| INSTAGRAM_ | Instagram task | Instagram watcher |
| TWITTER_ | Twitter/X task | Twitter watcher |
| WHATSAPP_ | WhatsApp task | WhatsApp watcher (LOCAL-ONLY) |
| PAYMENT_ | Payment task | Manual / orchestrator (LOCAL-ONLY) |
| ODOO_ | Odoo ERP task | Odoo MCP / manual |
| SOCIAL_ | Cross-platform social | Social MCP |
| AUDIT_ | Business audit | Scheduler |
| ERROR_ | Error recovery | Error handler |
| EXECUTE_ | Approved action | Approval pipeline |
| SALESPOST_ | Sales post draft | Scheduler / manual |
| SCHEDULE_ | Scheduled task | Scheduler |
| APPROVE_ | Approval request | Orchestrator |
| Plan_ | Task plan | create_plan skill |

## Platinum Hybrid Architecture

### Two Agent Roles
- **Cloud Agent** (Oracle Cloud VM, 24/7): Runs watchers, creates drafts, routes to approval. Can only use SAFE + DRAFT MCP tools. Never sends, posts, or pays.
- **Local Agent** (your machine, on-demand): Full tool access. Handles HITL approvals, executes dangerous actions (email, social, WhatsApp, payments).

### Domain Routing Rules
| Task Prefix | Cloud Action | Local Action | Reason |
|-------------|-------------|--------------|--------|
| EMAIL_ | Draft reply | Send email | SMTP credentials local-only |
| LINKEDIN_ | Draft post | Post | Session local-only |
| FACEBOOK_ | Draft post | Post | API key local-only |
| INSTAGRAM_ | Draft | Post | Session local-only |
| TWITTER_ | Draft tweet | Post | API key local-only |
| WHATSAPP_ | Skip | Full | Session files never sync |
| PAYMENT_ | Skip | Full | Banking creds never sync |
| SCHEDULE_ | Full | Full | Either can schedule |
| ODOO_ | Draft invoice | Post invoice | Posting is dangerous |
| AUDIT_ | Full | Full | Read-only, either can |

### Claim-by-Move
- Tasks are claimed by moving files to In_Progress/{agent_id}/
- Only one agent can claim a task (atomic os.rename)
- Stale claims (>1hr) are moved back to Needs_Action/

### Git Vault Sync
- Cloud pushes changes after each poll cycle
- Local pulls every 60s via SyncWatcher
- Conflict resolution: Needs_Action=theirs, In_Progress=ours, Logs=union

## Workflow (Platinum Tier)

1. **Watchers** (cloud) – Detect new emails/social/etc, create task files in Needs_Action/.
2. **Cloud Orchestrator** – Claims tasks, creates drafts, routes to Pending_Approval/.
3. **Git Push** – Cloud pushes drafts to remote.
4. **Local Pull** – SyncWatcher pulls new files.
5. **HITL Review** – Human approves/rejects in terminal.
6. **Local Orchestrator** – Executes approved actions via full MCP access.
7. **Git Push** – Local pushes results to remote.
8. **Health Monitor** – Checks heartbeats, disk, error rate.

## Approval Rules
The following always require human approval:
- Sending emails or messages to any contact
- Financial actions (invoices, payments, billing)
- Posting invoices in Odoo (draft creation is ok, posting is not)
- New business relationships (connection requests, partnerships)
- Publishing content on any platform
- Any external-facing action
- Payments to new recipients
- ALL WhatsApp messages
- ALL bank transfers

## MCP Tool Safety Classification
| Classification | Cloud | Local | Examples |
|---------------|-------|-------|----------|
| SAFE | YES | YES | list_drafts, list_invoices, get_balance |
| DRAFT | YES | YES | draft_email, create_invoice_draft |
| DANGEROUS | NO | YES | send_email, post_invoice, initiate_payment |

## Agent Skills (21 total)
1. `scan_needs_action` — List and classify pending tasks
2. `create_plan` — Generate type-aware action plans
3. `complete_task` — Execute tasks with multi-MCP routing
4. `update_dashboard` — Refresh Dashboard.md
5. `generate_sales_post` — Draft sales posts
6. `request_approval` — Create HITL approval requests
7. `execute_action` — Execute approved actions via MCP
8. `schedule_task` — Configure recurring tasks
9. `sync_odoo_transactions` — Read Odoo transactions
10. `create_invoice_draft` — Create draft invoice in Odoo
11. `post_approved_invoice` — Post approved invoice
12. `generate_social_post` — Create platform-specific content
13. `post_approved_social` — Post approved social content
14. `summarize_social_activity` — Fetch social metrics
15. `weekly_audit` — Full audit + CEO briefing
16. `handle_error` — Detect failures, retry or escalate
17. `claim_task` — Claim task for exclusive processing (Platinum)
18. `sync_vault` — Git sync push/pull (Platinum)
19. `route_to_local` — Route task to local agent (Platinum)
20. `whatsapp_reply` — Compose WhatsApp reply (LOCAL-ONLY, Platinum)
21. `process_payment` — Handle bank payments (LOCAL-ONLY, Platinum)

## MCP Servers (5 total)
| Server | Module | Tools | Availability |
|--------|--------|-------|-------------|
| ai-employee-email | src.mcp_email.email_server | send_email, draft_email, list_drafts | Cloud + Local |
| ai-employee-odoo | src.mcp_odoo.odoo_server | list_invoices, read_invoice, create_invoice_draft, post_invoice, list_partners, read_transactions | Cloud + Local |
| ai-employee-social | src.mcp_social.social_server | post_facebook, post_instagram, post_twitter, get_social_summary, draft_social_post | Cloud + Local |
| ai-employee-whatsapp | src.mcp_whatsapp.whatsapp_server | list_whatsapp_chats, read_whatsapp_chat, send_whatsapp | LOCAL-ONLY |
| ai-employee-payment | src.mcp_payment.payment_server | list_accounts, get_balance, list_transactions, initiate_payment, payment_status | LOCAL-ONLY |

## Modes
- **DRY_RUN=true** (default): All external actions logged, not executed.
- **MOCK_DATA=true** (default): Watchers use fake data for testing.
- **ODOO_MOCK=true** (default): Odoo MCP returns mock data.
- **WHATSAPP_MOCK=true** (default): WhatsApp MCP returns mock data.
- **PAYMENT_MOCK=true** (default): Payment MCP returns mock data.
- Set all to `false` in `.env` for live operation.
