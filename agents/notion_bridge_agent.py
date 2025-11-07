#!/usr/bin/env python3
"""
Prime Spark Notion Bridge Agent

This agent creates a bidirectional bridge between Claude Code (local) and Notion workspace,
enabling seamless access to project documentation, updates, and collaboration between
the user, Claude web, and Claude Code local instances.

Features:
- Read Notion pages and databases
- Update Notion content
- Sync project information
- Search across Notion workspace
- Create new pages and update existing ones
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("Warning: notion-client not installed. Run: pip install notion-client")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pironman5/prime-spark-ai/logs/notion_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NotionBridgeAgent:
    """
    Bridge agent for connecting Claude Code with Notion workspace.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Notion Bridge Agent.

        Args:
            api_key: Notion API integration token (or set NOTION_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('NOTION_API_KEY')

        if not self.api_key:
            logger.warning("No Notion API key provided. Set NOTION_API_KEY environment variable.")
            self.client = None
        elif not NOTION_AVAILABLE:
            logger.error("notion-client library not installed")
            self.client = None
        else:
            try:
                self.client = Client(auth=self.api_key)
                logger.info("Notion Bridge Agent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Notion client: {e}")
                self.client = None

        # Cache for frequently accessed pages
        self.cache = {}
        self.cache_dir = Path("/home/pironman5/prime-spark-ai/cache/notion")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def is_connected(self) -> bool:
        """Check if the agent is connected to Notion."""
        return self.client is not None

    def search_workspace(self, query: str, filter_type: Optional[str] = None) -> List[Dict]:
        """
        Search across the Notion workspace.

        Args:
            query: Search query string
            filter_type: Filter by 'page' or 'database'

        Returns:
            List of matching pages/databases
        """
        if not self.is_connected():
            logger.error("Not connected to Notion")
            return []

        try:
            search_params = {"query": query}
            if filter_type:
                search_params["filter"] = {"property": "object", "value": filter_type}

            results = self.client.search(**search_params)
            logger.info(f"Found {len(results.get('results', []))} results for query: {query}")
            return results.get('results', [])

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_page(self, page_id: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Retrieve a Notion page by ID.

        Args:
            page_id: Notion page ID
            use_cache: Use cached version if available

        Returns:
            Page object or None
        """
        if not self.is_connected():
            logger.error("Not connected to Notion")
            return None

        # Check cache
        if use_cache and page_id in self.cache:
            logger.info(f"Using cached page: {page_id}")
            return self.cache[page_id]

        try:
            page = self.client.pages.retrieve(page_id=page_id)
            self.cache[page_id] = page

            # Save to disk cache
            cache_file = self.cache_dir / f"{page_id}.json"
            with open(cache_file, 'w') as f:
                json.dump(page, f, indent=2)

            logger.info(f"Retrieved page: {page_id}")
            return page

        except Exception as e:
            logger.error(f"Failed to retrieve page {page_id}: {e}")
            return None

    def get_page_content(self, page_id: str) -> Optional[List[Dict]]:
        """
        Get the content blocks of a Notion page.

        Args:
            page_id: Notion page ID

        Returns:
            List of content blocks
        """
        if not self.is_connected():
            logger.error("Not connected to Notion")
            return None

        try:
            blocks = self.client.blocks.children.list(block_id=page_id)
            logger.info(f"Retrieved {len(blocks.get('results', []))} blocks from page {page_id}")
            return blocks.get('results', [])

        except Exception as e:
            logger.error(f"Failed to retrieve page content: {e}")
            return None

    def extract_text_from_blocks(self, blocks: List[Dict]) -> str:
        """
        Extract plain text from Notion blocks.

        Args:
            blocks: List of Notion block objects

        Returns:
            Extracted text content
        """
        text_content = []

        for block in blocks:
            block_type = block.get('type')

            if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3',
                            'bulleted_list_item', 'numbered_list_item', 'quote', 'callout']:
                rich_text = block.get(block_type, {}).get('rich_text', [])
                for text_obj in rich_text:
                    text_content.append(text_obj.get('plain_text', ''))

            elif block_type == 'code':
                rich_text = block.get('code', {}).get('rich_text', [])
                code_text = ''.join([t.get('plain_text', '') for t in rich_text])
                text_content.append(f"```\n{code_text}\n```")

        return '\n'.join(text_content)

    def update_page_title(self, page_id: str, new_title: str) -> bool:
        """
        Update the title of a Notion page.

        Args:
            page_id: Notion page ID
            new_title: New title text

        Returns:
            True if successful
        """
        if not self.is_connected():
            logger.error("Not connected to Notion")
            return False

        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "title": {
                        "title": [{"text": {"content": new_title}}]
                    }
                }
            )
            logger.info(f"Updated page title: {new_title}")
            return True

        except Exception as e:
            logger.error(f"Failed to update page title: {e}")
            return False

    def append_to_page(self, page_id: str, content: str) -> bool:
        """
        Append content to a Notion page.

        Args:
            page_id: Notion page ID
            content: Text content to append

        Returns:
            True if successful
        """
        if not self.is_connected():
            logger.error("Not connected to Notion")
            return False

        try:
            # Split content into paragraphs
            paragraphs = content.split('\n\n')

            blocks = []
            for para in paragraphs:
                if para.strip():
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": para.strip()}}]
                        }
                    })

            self.client.blocks.children.append(block_id=page_id, children=blocks)
            logger.info(f"Appended {len(blocks)} blocks to page {page_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to append to page: {e}")
            return False

    def create_page(self, parent_id: str, title: str, content: Optional[str] = None) -> Optional[str]:
        """
        Create a new Notion page.

        Args:
            parent_id: Parent page or database ID
            title: Page title
            content: Optional initial content

        Returns:
            New page ID or None
        """
        if not self.is_connected():
            logger.error("Not connected to Notion")
            return None

        try:
            properties = {
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            }

            page_data = {
                "parent": {"page_id": parent_id},
                "properties": properties
            }

            # Add initial content if provided
            if content:
                paragraphs = content.split('\n\n')
                children = []
                for para in paragraphs:
                    if para.strip():
                        children.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": para.strip()}}]
                            }
                        })
                page_data["children"] = children

            new_page = self.client.pages.create(**page_data)
            page_id = new_page.get('id')
            logger.info(f"Created new page: {title} (ID: {page_id})")
            return page_id

        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            return None

    def get_prime_spark_pages(self) -> List[Dict]:
        """
        Search for all Prime Spark AI related pages.

        Returns:
            List of Prime Spark pages
        """
        return self.search_workspace("Prime Spark", filter_type="page")

    def sync_to_local(self, page_id: str, output_path: Optional[str] = None) -> bool:
        """
        Sync a Notion page to local markdown file.

        Args:
            page_id: Notion page ID
            output_path: Optional custom output path

        Returns:
            True if successful
        """
        if not self.is_connected():
            logger.error("Not connected to Notion")
            return False

        try:
            page = self.get_page(page_id)
            if not page:
                return False

            blocks = self.get_page_content(page_id)
            if not blocks:
                return False

            content = self.extract_text_from_blocks(blocks)

            # Determine output path
            if not output_path:
                page_title = page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'untitled')
                safe_title = "".join(c for c in page_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                output_path = f"/home/pironman5/prime-spark-ai/docs/notion_sync/{safe_title}.md"

            # Create directory if needed
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(output_path, 'w') as f:
                f.write(f"# {page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'Untitled')}\n\n")
                f.write(f"*Synced from Notion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                f.write(content)

            logger.info(f"Synced page to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to sync page to local: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get bridge agent status.

        Returns:
            Status dictionary
        """
        return {
            "connected": self.is_connected(),
            "notion_available": NOTION_AVAILABLE,
            "api_key_set": bool(self.api_key),
            "cache_size": len(self.cache),
            "cache_dir": str(self.cache_dir),
            "timestamp": datetime.now().isoformat()
        }


def main():
    """CLI interface for the Notion Bridge Agent."""
    import sys

    agent = NotionBridgeAgent()

    if not agent.is_connected():
        print("❌ Not connected to Notion. Please set NOTION_API_KEY environment variable.")
        print("\nTo get your API key:")
        print("1. Go to https://www.notion.so/my-integrations")
        print("2. Create a new integration")
        print("3. Copy the Internal Integration Token")
        print("4. Set environment variable: export NOTION_API_KEY='your-token-here'")
        print("5. Share your Notion pages with the integration")
        return 1

    print("✅ Notion Bridge Agent connected successfully!")
    print("\nSearching for Prime Spark AI pages...")

    pages = agent.get_prime_spark_pages()

    if pages:
        print(f"\n📄 Found {len(pages)} Prime Spark AI pages:")
        for i, page in enumerate(pages[:10], 1):
            title = page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'Untitled')
            print(f"  {i}. {title}")
            print(f"     ID: {page.get('id')}")
    else:
        print("No Prime Spark AI pages found. Make sure pages are shared with your integration.")

    print("\n" + "="*60)
    status = agent.get_status()
    print("Status:", json.dumps(status, indent=2))

    return 0


if __name__ == "__main__":
    exit(main())
