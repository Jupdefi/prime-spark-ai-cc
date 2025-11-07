#!/usr/bin/env python3
"""Explore Prime Spark AI Notion workspace structure"""

import os
import sys
from agents.notion_bridge_agent import NotionBridgeAgent

# Notion API key should be set in environment
# Set NOTION_API_KEY environment variable before running

def explore_workspace():
    agent = NotionBridgeAgent()

    if not agent.is_connected():
        print("❌ Failed to connect to Notion")
        return

    print("=" * 80)
    print("🔍 EXPLORING PRIME SPARK AI NOTION WORKSPACE")
    print("=" * 80)

    # Search for all pages (empty query returns everything accessible)
    print("\n📚 Searching for all accessible pages...\n")
    all_results = agent.client.search(filter={"property": "object", "value": "page"})

    pages = all_results.get('results', [])

    if not pages:
        print("⚠️  No pages found. Make sure pages are shared with the integration.")
        return

    print(f"✅ Found {len(pages)} accessible pages:\n")
    print("-" * 80)

    for i, page in enumerate(pages, 1):
        page_id = page.get('id')

        # Get title from properties
        props = page.get('properties', {})
        title = "Untitled"

        # Try different title property names
        for key in ['title', 'Title', 'Name', 'name']:
            if key in props:
                title_data = props[key]
                if title_data.get('type') == 'title' and title_data.get('title'):
                    title = title_data['title'][0].get('plain_text', 'Untitled')
                    break

        # If still untitled, try to get from page object
        if title == "Untitled" and 'title' in page:
            page_title = page['title']
            if isinstance(page_title, list) and len(page_title) > 0:
                title = page_title[0].get('plain_text', 'Untitled')

        created = page.get('created_time', 'N/A')
        edited = page.get('last_edited_time', 'N/A')
        url = f"https://notion.so/{page_id.replace('-', '')}"

        print(f"{i}. {title}")
        print(f"   📅 Created: {created}")
        print(f"   ✏️  Edited: {edited}")
        print(f"   🔗 URL: {url}")
        print(f"   🆔 ID: {page_id}")

        # Try to get a preview of content
        try:
            blocks = agent.get_page_content(page_id)
            if blocks:
                print(f"   📝 Content blocks: {len(blocks)}")

                # Extract first paragraph
                for block in blocks[:3]:
                    block_type = block.get('type')
                    if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3']:
                        rich_text = block.get(block_type, {}).get('rich_text', [])
                        if rich_text:
                            text = rich_text[0].get('plain_text', '').strip()
                            if text and text != "Untitled":
                                preview = text[:100] + "..." if len(text) > 100 else text
                                print(f"   💬 Preview: {preview}")
                                break
                    elif block_type == 'child_page':
                        child_title = block.get('child_page', {}).get('title', 'Untitled')
                        print(f"   📂 Contains child page: {child_title}")
        except Exception as e:
            print(f"   ⚠️  Could not read content: {e}")

        print("-" * 80)

    # Summary
    print(f"\n✅ Total accessible pages: {len(pages)}")
    print("\n💡 Tip: To sync any page locally, use:")
    print("   agent.sync_to_local('<page-id>', '<output-path>')")
    print("\n📖 All pages are now accessible via the bridge agent!")

if __name__ == "__main__":
    explore_workspace()
