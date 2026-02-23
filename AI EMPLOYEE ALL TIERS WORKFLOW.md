# AI Employee — All Tiers Workflow

## All 5 Tiers at a Glance

| | **Bronze** | **Silver** | **Gold** | **Platinum** | **Diamond** |
|---|---|---|---|---|---|
| **One-liner** | Digital inbox | Email assistant | Office manager | 24/7 cloud worker | AI department |
| **Tests** | 0 | 1 | 55 | 215 | 392 |
| **Skills** | 4 | 8 | 16 | 21 | 26 |
| **MCP Servers** | 0 | 1 (Email) | 3 (+Odoo, Social) | 5 (+WhatsApp, Payment) | 5 |
| **Watchers** | 0 | 2 (Gmail, LinkedIn) | 5 (+FB, IG, X) | 6 (+WhatsApp) | 6 |
| **Orchestrator** | Manual | Single loop | Ralph Wiggum loop | Cloud + Local | Swarm (4 agents) |
| **Approval** | None | Terminal HITL | HITL + error retry | HITL + claim safety | HITL + security scan |
| **Platforms** | None | Gmail, LinkedIn | +Facebook, Instagram, Twitter, Odoo | +WhatsApp, Banking | +CRM, REST API |
| **Architecture** | Files only | Python + watchdog | +Docker (Odoo) | +Oracle Cloud VM + Git sync | +Flask API, encryption |
| **Key Tech** | Markdown files | Gmail API, Playwright, JSON-RPC | Tweepy, Instagrapi, FB SDK, Odoo RPC | Git, PM2, os.rename | Flask, cryptography, threading |

---

## What Each Tier Actually Does (Plain English)

### Bronze — "A folder that acts like an inbox"

You drop a `.md` file into `Needs_Action/`. That's your task. The AI reads it, makes a plan, does the work, then moves the file to `Done/` and updates a dashboard. That's it. No automation, no watchers, no internet connections. Just files moving between folders. **4 skills** tell the AI how to scan, plan, execute, and update stats.

**How it works:** Human drops file → AI reads it → AI does the task → file moves to Done/

---

### Silver — "An assistant that watches your email"

Now the system **automatically** monitors Gmail and LinkedIn. When a new email arrives, a Python watcher creates a task file. An orchestrator (using `watchdog` library) picks it up, drafts a reply, and asks you to approve it in the terminal before sending. The email is sent through an **MCP server** (a small JSON-RPC service that wraps email sending). A scheduler creates recurring tasks like "daily inbox scan" and "weekly LinkedIn post."

**How it works:** Gmail/LinkedIn → Watcher creates task → Orchestrator drafts reply → You approve in terminal → MCP sends email → Done/

**Tech:** Gmail API, Playwright (for LinkedIn scraping), JSON-RPC 2.0 (MCP protocol), watchdog (file monitoring)

---

### Gold — "An office manager handling everything"

Silver only knew Gmail and LinkedIn. Gold adds **Facebook, Instagram, and Twitter/X** watchers (5 total). It also adds **Odoo ERP** for invoicing/accounting and a **Social Media MCP** for posting. Complex tasks (like creating invoices or running audits) use a **Ralph Wiggum loop** — the AI breaks the task into steps, executes each one, checks the result, and moves to the next (up to 5 iterations). If something fails, an **ErrorHandler** retries with exponential backoff (wait 1s, then 2s, then 4s). Every Sunday at 11 PM, a **weekly audit** runs and generates a CEO briefing.

**How it works:** 5 platforms watched → Orchestrator classifies by prefix (EMAIL_, FACEBOOK_, ODOO_, etc.) → Simple tasks go direct, complex tasks go through multi-step loop → Approval → 3 MCP servers execute → Error recovery if it fails → Weekly audit for the boss

**Tech:** Tweepy (Twitter), Instagrapi (Instagram), Facebook SDK, Odoo XML-RPC, Docker (Odoo + PostgreSQL), exponential backoff retry

---

### Platinum — "Your AI works while you sleep"

The AI splits into **two agents**:
- **Cloud Agent** (runs 24/7 on Oracle Cloud Free Tier) — monitors all platforms, creates drafts, but **can never send, post, or pay** (blocked by tool policy)
- **Local Agent** (runs on your machine) — has full access to everything, handles approvals and executes dangerous actions

They sync via **Git** — cloud pushes drafts, local pulls them, you approve, local executes and pushes results back. Tasks are claimed atomically using `os.rename()` (if two agents grab the same file, one fails instantly — no conflicts). Two new **LOCAL-ONLY** MCP servers handle WhatsApp messaging and bank payments — these credentials never leave your machine. A health monitor checks heartbeats, disk usage, and error rates.

**How it works:** Cloud agent watches 24/7 → Creates drafts (SAFE/DRAFT tools only) → Git push → Local pulls → You approve → Local executes with full MCP access (including WhatsApp/Payment) → Git push back → Cloud sees completion

**Tech:** Oracle Cloud Free Tier (ARM VM), Git (sync bridge), os.rename (atomic claim), PM2 (process manager), psutil (health monitoring)

---

### Diamond — "A full AI department"

Instead of 2 generic agents, Diamond has **4 specialized experts**:

| Agent | Handles | Good at |
|-------|---------|---------|
| **Sales Agent** | Emails, LinkedIn, sales posts | Professional communication, pricing, outreach |
| **Finance Agent** | Odoo invoices, payments, audits | Invoicing, bank transfers, financial reports |
| **Content Agent** | Facebook, Instagram, Twitter, WhatsApp | Platform-specific content, hashtags, messaging |
| **Security Agent** | Errors, approved actions | Scans ALL outgoing content for leaked passwords/tokens |

A **SwarmOrchestrator** finds the best agent for each task (agents score themselves — Sales Agent gives itself 0.9 for emails, Finance Agent gives 0.9 for invoices). Agents talk to each other via an **A2A message bus** (Sales can ask Finance "what's the client's balance?"). The system **learns from every task** — an OutcomeTracker records success/failure, a PromptOptimizer recommends improvements every 100 tasks ("Finance Agent fails on email tasks 30% of the time — reassign to Sales Agent"), and PerformanceMetrics scores each agent on reliability/speed/volume.

Extra services: **Credential Vault** (encrypted API key storage), **CRM** (contacts, deals, $182K pipeline), **REST API** (7 endpoints — check status, agents, tasks, metrics from any browser), **Compliance Reporter** (automated checks that all dangerous actions went through approval), **Cloud Manager** (mock auto-scaling).

**How it works:** Task arrives → SwarmOrchestrator asks AgentRegistry "who's best?" → Security Agent pre-scans content → Best agent processes task → Outcome recorded for learning → Every 100 tasks, system self-optimizes → CRM/API/Compliance updated

**Tech:** Flask (REST API), cryptography/Fernet (vault encryption), threading.Lock (message bus concurrency), JSONL (outcome logging), base64 (mock encryption)

---

## The Core Pattern (Same in Every Tier)

```
DETECT  →  CREATE  →  CLASSIFY  →  PLAN  →  APPROVE  →  EXECUTE  →  DONE
  │           │          │           │          │           │          │
watcher    .md file    prefix     AI plan    human       MCP tool   move to
monitors   created    routing    generated   reviews     called     Done/
```

Every tier follows this exact loop — they just add more watchers, more MCP tools, more intelligence, and more safety at each level.
