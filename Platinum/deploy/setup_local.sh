#!/bin/bash
# Local environment setup — Platinum Tier

set -e

echo "=== AI Employee — Local Setup ==="

# Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy local env template
if [ ! -f .env ]; then
    cp .env.local .env
    echo "Created .env from .env.local template"
    echo "Please fill in your secrets in .env"
fi

# Create required folders
mkdir -p In_Progress Needs_Action Pending_Approval Done Logs Errors

# Run tests
python -m pytest tests/ -v

echo "=== Local setup complete ==="
echo "Start local orchestrator: python -m src.orchestrator.orchestrator --role local --dry-run --once"
