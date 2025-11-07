#!/usr/bin/env python3
"""Test accessing the Prime Spark AI Site Map from Notion"""

import os
import sys
import json

# Set the API key
# NOTION_API_KEY should be set in environment variables

# Import the bridge agent
from agents.notion_bridge_agent import NotionBridgeAgent

# Page ID from the URL: https://www.notion.so/Prime-Spark-AI-Site-Map-1d5c730ec2c88023bc42d1056855f8c1
page_id = "1d5c730ec2c88023bc42d1056855f8c1"

print("=" * 70)
print("Testing Notion Bridge Agent with Prime Spark AI Site Map")
print("=" * 70)

# Initialize agent
agent = NotionBridgeAgent()

if not agent.is_connected():
    print("❌ Failed to connect to Notion")
    sys.exit(1)

print("✅ Connected to Notion\n")

# Test 1: Get the page
print("📄 Retrieving page...")
page = agent.get_page(page_id)

if page:
    print("✅ Page retrieved successfully!")
    print(f"   Title: {page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'N/A')}")
    print(f"   ID: {page.get('id')}")
    print(f"   Created: {page.get('created_time')}")
    print(f"   Last edited: {page.get('last_edited_time')}")
else:
    print("❌ Failed to retrieve page. Make sure you've shared it with the integration!")
    print("\nTo share the page:")
    print("1. Open the page in Notion")
    print("2. Click '...' (three dots) in the top right")
    print("3. Click 'Add connections'")
    print("4. Select 'Prime Spark Bridge Agent'")
    print("5. Click 'Confirm'")
    sys.exit(1)

# Test 2: Get page content
print("\n📝 Retrieving page content...")
blocks = agent.get_page_content(page_id)

if blocks:
    print(f"✅ Retrieved {len(blocks)} content blocks")

    # Extract text
    text_content = agent.extract_text_from_blocks(blocks)
    print(f"\n📖 Page Preview (first 500 chars):")
    print("-" * 70)
    print(text_content[:500] + "..." if len(text_content) > 500 else text_content)
    print("-" * 70)
else:
    print("⚠️  No content blocks found")

# Test 3: Sync to local file
print("\n💾 Syncing page to local markdown...")
sync_path = "/home/pironman5/prime-spark-ai/docs/notion_sync/Prime_Spark_AI_Site_Map.md"
if agent.sync_to_local(page_id, sync_path):
    print(f"✅ Page synced to: {sync_path}")
else:
    print("❌ Failed to sync page")

# Test 4: Search workspace
print("\n🔍 Searching workspace for 'Prime Spark'...")
results = agent.search_workspace("Prime Spark")
if results:
    print(f"✅ Found {len(results)} results:")
    for i, result in enumerate(results[:5], 1):
        result_type = result.get('object')
        if result_type == 'page':
            title = result.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'Untitled')
            print(f"   {i}. [{result_type}] {title}")
            print(f"      URL: https://notion.so/{result.get('id').replace('-', '')}")
else:
    print("⚠️  No search results found")

print("\n" + "=" * 70)
print("✅ Bridge Agent Test Complete!")
print("=" * 70)
print("\nNext steps:")
print("• Review synced content: cat ~/prime-spark-ai/docs/notion_sync/Prime_Spark_AI_Site_Map.md")
print("• Access more pages by sharing them with 'Prime Spark Bridge Agent'")
print("• Use the bridge agent in your own scripts!")
