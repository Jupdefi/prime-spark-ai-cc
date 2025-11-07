#!/bin/bash
# Quick test script for Notion Bridge Agent

cd /home/pironman5/prime-spark-ai
source venv/bin/activate
# NOTION_API_KEY should be set in environment variables before running

echo "Testing Notion Bridge Agent..."
python3 agents/notion_bridge_agent.py
