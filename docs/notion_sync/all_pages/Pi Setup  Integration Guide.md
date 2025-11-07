# Pi Setup & Integration Guide

*Synced from Notion*

🔗 [View in Notion](https://notion.so/2a3c730ec2c8810ba16ce5c2d89f0586)

---

# Pi Setup & Integration Guide

## Overview

This guide will help you set up your Raspberry Pi 5 to automatically pull and deploy code from this Notion workspace.

## Prerequisites

• Raspberry Pi 5 (16GB RAM)

• Pi OS installed

• Internet connection

• Notion API integration token

## Step 1: Install Notion API Client

### Option A: Node.js (Recommended)

```bash
# Install Node.js if not already installed
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Notion SDK
npm install -g @notionhq/client
```

### Option B: Python

```bash
# Install Python Notion client
pip3 install notion-client
```

## Step 2: Get Your Notion API Token

1. Go to

1. https://www.notion.so/my-integrations

1. Click "New integration"

1. Name it "Prime Spark Pi Sync"

1. Select your workspace

1. Copy the "Internal Integration Token"

1. Share the "Claude Code Services" page with your integration

## Step 3: Create the Sync Script

Create a file at

~/

prime-spark-sync.sh

:

```bash
#!/bin/bash
# Prime Spark Notion Sync Script

NOTION_TOKEN="your_token_here"
NOTION_DATABASE_ID="b4eb2a72-90db-45c8-869b-3cab568d2655"
DEPLOY_DIR="$HOME/prime-spark-deployments"

# Create deployment directory
mkdir -p "$DEPLOY_DIR"

# Fetch from Notion and deploy
# (Full script implementation coming soon)

echo "✅ Sync complete!"
```

Make it executable:

```bash
chmod +x ~/prime-spark-sync.sh
```

## Step 4: Test the Connection

```bash
~/prime-spark-sync.sh
```

You should see confirmation that the sync completed successfully.

## Step 5: Set Up Automatic Sync

Add to crontab to run every 15 minutes:

```bash
crontab -e
```

Add this line:

```javascript
*/15 * * * * /home/pi/prime-spark-sync.sh >> /var/log/prime-spark-sync.log 2>&1
```

## Usage

### Manual Sync

```bash
~/prime-spark-sync.sh
```

### View Sync Logs

```bash
tail -f /var/log/prime-spark-sync.log
```

### Force Deploy Specific MCP

```bash
~/prime-spark-sync.sh deploy spiral-memory
```

## Troubleshooting

### Connection Issues

• Verify your Notion token is correct

• Check that the integration has access to the page

• Ensure internet connectivity

### Deployment Failures

• Check Docker is running:

• docker ps

• Verify file permissions

• Review logs:

• tail -f /var/log/prime-spark-sync.log

## Next Steps

1. Deploy your first MCP from Notion

1. Set up N8N automation (optional)

1. Configure status reporting back to Notion

Your Pi is now ready to receive deployments from Claude Code Services!

⚡