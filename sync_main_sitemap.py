#!/usr/bin/env python3
"""Sync the main Prime Spark AI Command Center Sitemap"""

import os
from agents.notion_bridge_agent import NotionBridgeAgent

# Set the API key
# NOTION_API_KEY should be set in environment variables

# The main sitemap page ID
COMMAND_CENTER_PAGE_ID = "2a3c730e-c2c8-80ba-9506-d96546d66462"

agent = NotionBridgeAgent()

print("=" * 80)
print("📥 SYNCING PRIME SPARK AI COMMAND CENTER")
print("=" * 80)

# Get the full page content
print("\n📖 Fetching page content...")
blocks = agent.get_page_content(COMMAND_CENTER_PAGE_ID)

if blocks:
    print(f"✅ Retrieved {len(blocks)} content blocks")

    # Extract all text
    text_content = agent.extract_text_from_blocks(blocks)

    # Save to local file
    output_path = "/home/pironman5/prime-spark-ai/docs/notion_sync/PRIME_SPARK_COMMAND_CENTER.md"

    page = agent.get_page(COMMAND_CENTER_PAGE_ID)

    with open(output_path, 'w') as f:
        f.write("# PRIME SPARK AI – COMMAND CENTER SITEMAP\n\n")
        f.write(f"*Synced from Notion: {page.get('last_edited_time')}*\n\n")
        f.write(f"🔗 Source: https://notion.so/{COMMAND_CENTER_PAGE_ID.replace('-', '')}\n\n")
        f.write("=" * 80 + "\n\n")
        f.write(text_content)

    print(f"✅ Synced to: {output_path}")

    # Display preview
    print("\n" + "=" * 80)
    print("📄 CONTENT PREVIEW")
    print("=" * 80)
    print(text_content[:2000])
    if len(text_content) > 2000:
        print("\n... (truncated, see full content in file)")

    print("\n" + "=" * 80)
    print(f"📊 Total content size: {len(text_content)} characters")
    print("=" * 80)
else:
    print("❌ Failed to retrieve page content")
