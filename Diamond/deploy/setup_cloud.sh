#!/bin/bash
# Oracle Cloud VM provisioning script — Platinum Tier
# Run on Oracle Cloud A1 instance (ARM, 4 OCPU, 24GB RAM, Always Free)

set -e

echo "=== AI Employee — Cloud VM Setup ==="

# System updates
sudo apt update && sudo apt upgrade -y

# Python 3.11+
sudo apt install -y python3 python3-pip python3-venv git

# Node.js for PM2
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# Create app directory
sudo mkdir -p /opt/ai-employee
sudo chown $USER:$USER /opt/ai-employee

# Clone repo (placeholder — user fills in their private repo URL)
echo "NOTE: Clone your private repo to /opt/ai-employee"
echo "  git clone <your-private-repo-url> /opt/ai-employee"

# Python environment
cd /opt/ai-employee
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy cloud env
cp .env.cloud .env

# Set up PM2
pm2 start deploy/ecosystem.config.js
pm2 save
pm2 startup

echo "=== Setup complete ==="
echo "Check status: pm2 status"
echo "View logs: pm2 logs"
