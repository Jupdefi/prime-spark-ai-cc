#!/usr/bin/env python3
"""
Recursively sync all Prime Spark AI pages from Notion
"""

import os
import json
from pathlib import Path
from agents.notion_bridge_agent import NotionBridgeAgent

# Set the API key
# NOTION_API_KEY should be set in environment variables

agent = NotionBridgeAgent()

print("=" * 80)
print("🔄 RECURSIVE PRIME SPARK AI DOCUMENTATION SYNC")
print("=" * 80)

# Search for all Prime Spark pages
print("\n🔍 Discovering all Prime Spark AI pages...")
all_pages = agent.client.search(filter={"property": "object", "value": "page"})

pages = all_pages.get('results', [])
print(f"✅ Found {len(pages)} total pages\n")

# Create output directory
sync_dir = Path("/home/pironman5/prime-spark-ai/docs/notion_sync/all_pages")
sync_dir.mkdir(parents=True, exist_ok=True)

# Create index file
index_content = "# Prime Spark AI - Notion Documentation Index\n\n"
index_content += f"*Generated: {agent.get_status()['timestamp']}*\n\n"
index_content += f"Total pages synced: {len(pages)}\n\n"
index_content += "---\n\n"

synced_count = 0

for i, page in enumerate(pages, 1):
    page_id = page.get('id')

    # Try to get title
    props = page.get('properties', {})
    title = f"Untitled_{i}"

    for key in ['title', 'Title', 'Name', 'name']:
        if key in props:
            title_data = props[key]
            if title_data.get('type') == 'title' and title_data.get('title'):
                title = title_data['title'][0].get('plain_text', title)
                break

    # Clean title for filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    if not safe_title:
        safe_title = f"page_{i}"

    print(f"{i}/{len(pages)} 📄 {title}")

    try:
        # Get page content
        blocks = agent.get_page_content(page_id)

        if blocks:
            # Extract all text
            text_parts = []

            for block in blocks:
                block_type = block.get('type')

                # Handle regular text blocks
                if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3',
                                'bulleted_list_item', 'numbered_list_item', 'quote', 'callout']:
                    rich_text = block.get(block_type, {}).get('rich_text', [])
                    for text_obj in rich_text:
                        text = text_obj.get('plain_text', '').strip()
                        if text:
                            # Add heading markers
                            if block_type == 'heading_1':
                                text_parts.append(f"# {text}")
                            elif block_type == 'heading_2':
                                text_parts.append(f"## {text}")
                            elif block_type == 'heading_3':
                                text_parts.append(f"### {text}")
                            elif block_type == 'bulleted_list_item':
                                text_parts.append(f"• {text}")
                            elif block_type == 'numbered_list_item':
                                text_parts.append(f"1. {text}")
                            elif block_type == 'quote':
                                text_parts.append(f"> {text}")
                            else:
                                text_parts.append(text)

                # Handle code blocks
                elif block_type == 'code':
                    rich_text = block.get('code', {}).get('rich_text', [])
                    code_text = ''.join([t.get('plain_text', '') for t in rich_text])
                    language = block.get('code', {}).get('language', '')
                    text_parts.append(f"```{language}\n{code_text}\n```")

                # Handle child pages (links to sub-pages)
                elif block_type == 'child_page':
                    child_title = block.get('child_page', {}).get('title', 'Untitled')
                    child_id = block.get('id')
                    text_parts.append(f"\n🔗 **Child Page:** [{child_title}](https://notion.so/{child_id.replace('-', '')})")

                # Handle link to page blocks
                elif block_type == 'link_to_page':
                    page_ref = block.get('link_to_page', {})
                    if 'page_id' in page_ref:
                        linked_page_id = page_ref['page_id']
                        text_parts.append(f"\n🔗 **Linked Page:** [View](https://notion.so/{linked_page_id.replace('-', '')})")

            content = "\n\n".join(text_parts)

            # Save to file
            output_file = sync_dir / f"{safe_title}.md"

            with open(output_file, 'w') as f:
                f.write(f"# {title}\n\n")
                f.write(f"*Synced from Notion*\n\n")
                f.write(f"🔗 [View in Notion](https://notion.so/{page_id.replace('-', '')})\n\n")
                f.write("---\n\n")
                f.write(content if content.strip() else "*No content*")

            # Add to index
            index_content += f"## {title}\n\n"
            index_content += f"- File: `{output_file.name}`\n"
            index_content += f"- Notion URL: https://notion.so/{page_id.replace('-', '')}\n"
            index_content += f"- Content length: {len(content)} characters\n"
            index_content += f"- Blocks: {len(blocks)}\n\n"

            synced_count += 1
            print(f"   ✅ Synced → {output_file.name}")

    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        index_content += f"## {title}\n\n"
        index_content += f"- ⚠️ Failed to sync: {str(e)}\n\n"

# Save index
index_file = sync_dir / "INDEX.md"
with open(index_file, 'w') as f:
    f.write(index_content)

print("\n" + "=" * 80)
print(f"✅ SYNC COMPLETE!")
print("=" * 80)
print(f"📊 Synced: {synced_count}/{len(pages)} pages")
print(f"📁 Output directory: {sync_dir}")
print(f"📖 Index file: {index_file}")
print("\nView the index:")
print(f"   cat {index_file}")
