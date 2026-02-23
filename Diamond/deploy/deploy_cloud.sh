#!/bin/bash
# Deploy/update cloud instance — Platinum Tier

set -e

cd /opt/ai-employee

# Pull latest code
git pull origin main

# Update dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Restart PM2 processes
pm2 restart all

echo "=== Deploy complete ==="
pm2 status
