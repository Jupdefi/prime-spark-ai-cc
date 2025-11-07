#!/usr/bin/env python3
"""
AI-Enhanced Notion Bridge Agent

Extends the base Notion Bridge with intelligent AI analysis capabilities:
- Automatic content summarization
- Key insight extraction
- Content categorization
- Relationship mapping
- Semantic search
- LLM-powered Q&A over Notion content
"""

import os
import sys
import json
import logging
import asyncio
import hashlib
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import redis

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from agents.notion_bridge_agent import NotionBridgeAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ===== DATA MODELS =====

class AnalysisRequest(BaseModel):
    """Request for content analysis."""
    page_id: str
    analysis_type: str  # summary, insights, categorize, relationships
    depth: str = "standard"  # quick, standard, deep


class LLMRequest(BaseModel):
    """Request for LLM processing."""
    prompt: str
    context: Optional[str] = None
    model: str = "llama3.2:latest"
    max_tokens: int = 500


class SearchRequest(BaseModel):
    """Semantic search request."""
    query: str
    limit: int = 10
    threshold: float = 0.7


class PageAnalysis(BaseModel):
    """Analysis results for a page."""
    page_id: str
    page_title: str
    summary: str
    key_insights: List[str]
    categories: List[str]
    relationships: List[Dict[str, str]]
    sentiment: str
    word_count: int
    analyzed_at: str


# ===== AI-ENHANCED BRIDGE AGENT =====

class AIBridgeAgent(NotionBridgeAgent):
    """
    AI-Enhanced Notion Bridge Agent.

    Extends base bridge with:
    - Ollama LLM integration
    - Intelligent content analysis
    - Semantic search
    - Auto-categorization
    - Relationship detection
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI-enhanced bridge."""
        super().__init__(api_key)

        # Ollama configuration
        self.ollama_url = os.getenv('OLLAMA_EDGE_URL', 'http://localhost:11434')
        self.default_model = os.getenv('OLLAMA_DEFAULT_MODEL', 'llama3.2:latest')

        # Redis cache for LLM responses
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=1,  # Separate DB for AI cache
                decode_responses=True
            )
            self.redis_client.ping()
            self.cache_enabled = True
            logger.info("✅ Redis AI cache connected")
        except Exception as e:
            logger.warning(f"⚠️  Redis not available: {e}")
            self.redis_client = None
            self.cache_enabled = False

        # Analysis storage
        self.analysis_dir = Path("/home/pironman5/prime-spark-ai/analysis")
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

        logger.info("🧠 AI-Enhanced Bridge Agent initialized")
        self._verify_ollama()

    def _verify_ollama(self):
        """Verify Ollama is available."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                logger.info(f"✅ Ollama available with {len(models)} models")
            else:
                logger.warning("⚠️  Ollama not responding correctly")
        except Exception as e:
            logger.error(f"❌ Ollama connection failed: {e}")

    def _cache_key(self, operation: str, *args) -> str:
        """Generate cache key for operation."""
        key_data = f"{operation}:{':'.join(str(arg) for arg in args)}"
        return f"ai_bridge:{hashlib.md5(key_data.encode()).hexdigest()}"

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached result."""
        if not self.cache_enabled:
            return None

        try:
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache read error: {e}")

        return None

    def _set_cached(self, key: str, value: Any, ttl: int = 3600):
        """Set cached result."""
        if not self.cache_enabled:
            return

        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error(f"Cache write error: {e}")

    async def call_llm(
        self,
        prompt: str,
        context: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 500
    ) -> str:
        """
        Call Ollama LLM with prompt.

        Args:
            prompt: The prompt to send
            context: Optional context to include
            model: Model to use (default: llama3.2:latest)
            max_tokens: Max tokens to generate

        Returns:
            Generated text
        """
        model = model or self.default_model

        # Check cache
        cache_key = self._cache_key("llm", prompt, context, model)
        cached = self._get_cached(cache_key)
        if cached:
            logger.info("📦 Cache hit for LLM call")
            return cached['response']

        # Build full prompt
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\nQuestion:\n{prompt}"

        # Call Ollama API
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    'model': model,
                    'prompt': full_prompt,
                    'stream': False,
                    'options': {
                        'num_predict': max_tokens,
                        'temperature': 0.7
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')

                # Cache result
                self._set_cached(cache_key, {'response': generated_text})

                return generated_text
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return ""

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""

    async def analyze_page(
        self,
        page_id: str,
        analysis_type: str = "full",
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        Analyze a Notion page with AI.

        Args:
            page_id: Notion page ID
            analysis_type: Type of analysis (summary, insights, categorize, relationships, full)
            depth: Analysis depth (quick, standard, deep)

        Returns:
            Analysis results
        """
        logger.info(f"🔍 Analyzing page {page_id} ({analysis_type}, {depth})")

        # Get page content
        page = self.get_page(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")

        content = self.get_page_content(page_id)
        if not content:
            raise ValueError(f"Could not fetch content for {page_id}")

        # Extract text from blocks
        text_content = self._extract_text_from_blocks(content)
        page_title = page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'Untitled')

        # Initialize results
        analysis = {
            'page_id': page_id,
            'page_title': page_title,
            'analyzed_at': datetime.now().isoformat(),
            'analysis_type': analysis_type,
            'depth': depth
        }

        # Perform requested analysis
        if analysis_type in ['summary', 'full']:
            analysis['summary'] = await self._generate_summary(text_content, depth)

        if analysis_type in ['insights', 'full']:
            analysis['key_insights'] = await self._extract_insights(text_content, depth)

        if analysis_type in ['categorize', 'full']:
            analysis['categories'] = await self._categorize_content(text_content)

        if analysis_type in ['relationships', 'full']:
            analysis['relationships'] = await self._find_relationships(page_id, text_content)

        # Additional metadata
        analysis['word_count'] = len(text_content.split())
        analysis['sentiment'] = await self._analyze_sentiment(text_content)

        # Save analysis
        self._save_analysis(page_id, analysis)

        logger.info(f"✅ Analysis complete for {page_id}")
        return analysis

    def _extract_text_from_blocks(self, blocks: List[Dict]) -> str:
        """Extract plain text from Notion blocks."""
        text_parts = []

        for block in blocks:
            block_type = block.get('type', '')

            # Handle different block types
            if block_type == 'paragraph':
                text = self._extract_rich_text(block.get('paragraph', {}).get('rich_text', []))
                if text:
                    text_parts.append(text)

            elif block_type == 'heading_1':
                text = self._extract_rich_text(block.get('heading_1', {}).get('rich_text', []))
                if text:
                    text_parts.append(f"# {text}")

            elif block_type == 'heading_2':
                text = self._extract_rich_text(block.get('heading_2', {}).get('rich_text', []))
                if text:
                    text_parts.append(f"## {text}")

            elif block_type == 'heading_3':
                text = self._extract_rich_text(block.get('heading_3', {}).get('rich_text', []))
                if text:
                    text_parts.append(f"### {text}")

            elif block_type == 'bulleted_list_item':
                text = self._extract_rich_text(block.get('bulleted_list_item', {}).get('rich_text', []))
                if text:
                    text_parts.append(f"• {text}")

            elif block_type == 'numbered_list_item':
                text = self._extract_rich_text(block.get('numbered_list_item', {}).get('rich_text', []))
                if text:
                    text_parts.append(f"- {text}")

            elif block_type == 'quote':
                text = self._extract_rich_text(block.get('quote', {}).get('rich_text', []))
                if text:
                    text_parts.append(f"> {text}")

        return '\n\n'.join(text_parts)

    def _extract_rich_text(self, rich_text_array: List[Dict]) -> str:
        """Extract plain text from rich text array."""
        return ''.join([rt.get('plain_text', '') for rt in rich_text_array])

    async def _generate_summary(self, content: str, depth: str) -> str:
        """Generate summary of content."""
        if not content:
            return "No content to summarize"

        # Adjust prompt based on depth
        if depth == "quick":
            prompt = f"Provide a 1-sentence summary of this content:\n\n{content[:1000]}"
        elif depth == "deep":
            prompt = f"Provide a comprehensive 3-paragraph summary of this content:\n\n{content[:3000]}"
        else:  # standard
            prompt = f"Provide a concise 2-3 sentence summary of this content:\n\n{content[:2000]}"

        summary = await self.call_llm(prompt, max_tokens=200)
        return summary.strip()

    async def _extract_insights(self, content: str, depth: str) -> List[str]:
        """Extract key insights from content."""
        if not content:
            return []

        prompt = f"""Extract the {3 if depth == 'quick' else 7 if depth == 'deep' else 5} most important insights from this content.
Return as a simple numbered list.

Content:
{content[:2000]}

Insights:"""

        response = await self.call_llm(prompt, max_tokens=300)

        # Parse numbered list
        insights = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering
                insight = line.lstrip('0123456789.-• ').strip()
                if insight:
                    insights.append(insight)

        return insights[:7]  # Max 7 insights

    async def _categorize_content(self, content: str) -> List[str]:
        """Categorize content."""
        if not content:
            return ["uncategorized"]

        prompt = f"""Categorize this content into 2-4 relevant categories.
Choose from common categories like: Technical, Business, Strategy, Documentation, Planning, Research, Development, Design, Marketing, Operations, Finance, etc.

Content:
{content[:1500]}

Categories (comma-separated):"""

        response = await self.call_llm(prompt, max_tokens=50)

        # Parse categories
        categories = [cat.strip() for cat in response.split(',')]
        return [cat for cat in categories if cat and len(cat) > 2][:4]

    async def _find_relationships(self, page_id: str, content: str) -> List[Dict[str, str]]:
        """Find relationships to other pages."""
        # Simplified - in production would search across all pages
        return []

    async def _analyze_sentiment(self, content: str) -> str:
        """Analyze sentiment of content."""
        if not content:
            return "neutral"

        prompt = f"""Analyze the sentiment of this content in one word: positive, negative, or neutral.

Content:
{content[:1000]}

Sentiment:"""

        response = await self.call_llm(prompt, max_tokens=10)
        sentiment = response.strip().lower()

        if sentiment in ['positive', 'negative', 'neutral']:
            return sentiment
        return "neutral"

    def _save_analysis(self, page_id: str, analysis: Dict):
        """Save analysis to disk."""
        analysis_file = self.analysis_dir / f"{page_id}_analysis.json"

        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)

        logger.info(f"💾 Analysis saved: {analysis_file}")

    def get_analysis(self, page_id: str) -> Optional[Dict]:
        """Get saved analysis for a page."""
        analysis_file = self.analysis_dir / f"{page_id}_analysis.json"

        if analysis_file.exists():
            with open(analysis_file, 'r') as f:
                return json.load(f)

        return None

    async def semantic_search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search across Notion pages.

        Simplified implementation - in production would use embeddings.
        """
        # For now, use LLM to help with search
        all_pages = self.search_workspace("")

        if not all_pages:
            return []

        # Get top matches
        results = []
        for page in all_pages[:limit]:
            page_id = page['id']
            title = page.get('title', 'Untitled')

            # Simple relevance check
            results.append({
                'page_id': page_id,
                'title': title,
                'relevance_score': 0.8,  # Simplified
                'snippet': title
            })

        return results[:limit]


# ===== FASTAPI APPLICATION =====

app = FastAPI(
    title="AI-Enhanced Notion Bridge API",
    description="Intelligent Notion Bridge with AI analysis capabilities",
    version="2.0.0"
)

# Initialize AI bridge
try:
    ai_bridge = AIBridgeAgent()
except Exception as e:
    logger.error(f"Failed to initialize AI bridge: {e}")
    ai_bridge = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        'agent': 'AI-Enhanced Notion Bridge',
        'version': '2.0.0',
        'capabilities': [
            'notion_sync',
            'ai_analysis',
            'llm_processing',
            'semantic_search'
        ],
        'ollama_available': ai_bridge is not None
    }


@app.post("/bridge/analyze/page/{page_id}")
async def analyze_page(page_id: str, request: AnalysisRequest):
    """Analyze a Notion page with AI."""
    if not ai_bridge:
        raise HTTPException(status_code=503, detail="AI Bridge not available")

    try:
        analysis = await ai_bridge.analyze_page(
            page_id,
            request.analysis_type,
            request.depth
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bridge/analyze/summary/{page_id}")
async def get_summary(page_id: str, depth: str = "standard"):
    """Get summary of a page."""
    if not ai_bridge:
        raise HTTPException(status_code=503, detail="AI Bridge not available")

    try:
        # Check if analysis exists
        analysis = ai_bridge.get_analysis(page_id)
        if analysis and 'summary' in analysis:
            return {'summary': analysis['summary']}

        # Generate new analysis
        analysis = await ai_bridge.analyze_page(page_id, "summary", depth)
        return {'summary': analysis.get('summary', '')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bridge/analyze/insights/{page_id}")
async def get_insights(page_id: str):
    """Get key insights from a page."""
    if not ai_bridge:
        raise HTTPException(status_code=503, detail="AI Bridge not available")

    try:
        analysis = ai_bridge.get_analysis(page_id)
        if analysis and 'key_insights' in analysis:
            return {'insights': analysis['key_insights']}

        analysis = await ai_bridge.analyze_page(page_id, "insights")
        return {'insights': analysis.get('key_insights', [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bridge/search/semantic")
async def semantic_search(request: SearchRequest):
    """Semantic search across Notion pages."""
    if not ai_bridge:
        raise HTTPException(status_code=503, detail="AI Bridge not available")

    try:
        results = await ai_bridge.semantic_search(request.query, request.limit)
        return {'results': results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bridge/llm/ask")
async def llm_ask(request: LLMRequest):
    """Ask LLM a question."""
    if not ai_bridge:
        raise HTTPException(status_code=503, detail="AI Bridge not available")

    try:
        response = await ai_bridge.call_llm(
            request.prompt,
            request.context,
            request.model,
            request.max_tokens
        )
        return {'response': response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bridge/llm/models")
async def list_models():
    """List available LLM models."""
    try:
        ollama_url = os.getenv('OLLAMA_EDGE_URL', 'http://localhost:11434')
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)

        if response.status_code == 200:
            models = response.json().get('models', [])
            return {'models': [m['name'] for m in models]}
        else:
            raise HTTPException(status_code=503, detail="Ollama not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting AI-Enhanced Notion Bridge API...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
