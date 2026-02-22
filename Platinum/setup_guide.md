# Setup Guide — AI Employee Silver Tier

## 1. Python Environment

```bash
cd AI-Employee-Project
python -m venv venv
source venv/bin/activate      # Linux/Mac
# or: venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## 2. Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

## 3. Google Cloud (Gmail API)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Gmail API**
4. Go to **Credentials** → Create **OAuth 2.0 Client ID**
   - Application type: Desktop App
   - Download the JSON file
5. Save as `credentials.json` in the project root
6. First run will open a browser for OAuth consent → saves `token.json`

### Required Gmail Scopes
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.send` (for Silver+ send capability)

## 4. LinkedIn (Optional — Browser Automation)

1. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```
2. Set `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` in `.env`
3. **Note:** LinkedIn automation may violate ToS. Use mock mode for testing:
   ```bash
   python -m src.watchers.linkedin_watcher --mock --once
   ```

## 5. MCP Email Server

The MCP email server uses Gmail SMTP by default:

1. Enable 2-Factor Auth on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate an app password for "Mail"
4. Set `SMTP_PASSWORD` in `.env` to this app password

## 6. Running (Mock Mode — Recommended for Testing)

### Start individual components:
```bash
# Mock Gmail watcher (single poll)
python -m src.watchers.gmail_watcher --mock --once

# Mock LinkedIn watcher (single poll)
python -m src.watchers.linkedin_watcher --mock --once

# Orchestrator (dry-run)
python -m src.orchestrator.orchestrator --dry-run

# Approval watcher (terminal HITL)
python -m src.approval.approval_watcher

# Scheduler
python -m src.scheduler.scheduler --dry-run
```

### Full integration test (3 terminals):
```bash
# Terminal 1: Orchestrator
python -m src.orchestrator.orchestrator --dry-run

# Terminal 2: Approval watcher
python -m src.approval.approval_watcher

# Terminal 3: Generate mock data
python -m src.watchers.gmail_watcher --mock --once
```

## 7. Running Tests

```bash
python -m pytest tests/ -v
```
