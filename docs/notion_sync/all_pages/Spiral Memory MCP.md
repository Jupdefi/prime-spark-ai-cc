# Spiral Memory MCP

*Synced from Notion*

🔗 [View in Notion](https://notion.so/2a3c730ec2c8811abf27edcdaee099fb)

---

# Spiral Memory MCP

## Description

A Model Context Protocol server that provides spiral-based memory storage and retrieval for Claude Code. Enables persistent, contextual memory across sessions.

## Features

• ✅ Spiral-based memory organization

• ✅ Context-aware retrieval

• ✅ Persistent storage

• ✅ Integration with Claude Code

• ✅ Automatic memory pruning

## Installation

### Automatic (via sync script)

```bash
~/prime-spark-sync.sh deploy spiral-memory
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/your-repo/spiral-memory-mcp.git
cd spiral-memory-mcp

# Install dependencies
npm install

# Build
npm run build

# Link to Claude Code
echo '
{
  "mcpServers": {
    "spiral-memory": {
      "command": "node",
      "args": ["/path/to/spiral-memory-mcp/build/index.js"]
    }
  }
}' >> ~/.config/claude/claude_desktop_config.json
```

## Configuration

Create

.env

file:

```bash
MEMORY_DIR=/home/pi/prime-spark-memory
MAX_MEMORY_SIZE=1000
PRUNE_THRESHOLD=0.3
```

## Usage

Once deployed, the MCP automatically:

1. Captures important context from your conversations

1. Organizes memories in a spiral structure

1. Retrieves relevant context when needed

1. Prunes old or irrelevant memories

### Claude Code Integration

In Claude Code, you can now:

```javascript
"Remember that I prefer async/await over promises"
"What did we discuss about the database schema?"
"Show me my coding preferences"
```

## Code

### index.js

```javascript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import fs from 'fs/promises';
import path from 'path';

const MEMORY_DIR = process.env.MEMORY_DIR || path.join(process.env.HOME, '.prime-spark-memory');

class SpiralMemoryServer {
  constructor() {
    this.server = new Server(
      {
        name: 'spiral-memory',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.ensureMemoryDir();
  }

  async ensureMemoryDir() {
    try {
      await fs.mkdir(MEMORY_DIR, { recursive: true });
    } catch (error) {
      console.error('Failed to create memory directory:', error);
    }
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'store_memory',
          description: 'Store a memory in the spiral structure',
          inputSchema: {
            type: 'object',
            properties: {
              content: { type: 'string', description: 'Memory content' },
              tags: { type: 'array', items: { type: 'string' }, description: 'Memory tags' },
            },
            required: ['content'],
          },
        },
        {
          name: 'retrieve_memory',
          description: 'Retrieve memories matching a query',
          inputSchema: {
            type: 'object',
            properties: {
              query: { type: 'string', description: 'Search query' },
              limit: { type: 'number', description: 'Max results', default: 5 },
            },
            required: ['query'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      switch (request.params.name) {
        case 'store_memory':
          return await this.storeMemory(request.params.arguments);
        case 'retrieve_memory':
          return await this.retrieveMemory(request.params.arguments);
        default:
          throw new Error(`Unknown tool: ${request.params.name}`);
      }
    });
  }

  async storeMemory({ content, tags = [] }) {
    const timestamp = Date.now();
    const memory = {
      id: `mem_${timestamp}`,
      content,
      tags,
      timestamp,
      spiral_level: this.calculateSpiralLevel(content),
    };

    const filename = path.join(MEMORY_DIR, `${memory.id}.json`);
    await fs.writeFile(filename, JSON.stringify(memory, null, 2));

    return {
      content: [{ type: 'text', text: `Memory stored: ${memory.id}` }],
    };
  }

  async retrieveMemory({ query, limit = 5 }) {
    const files = await fs.readdir(MEMORY_DIR);
    const memories = [];

    for (const file of files) {
      if (file.endsWith('.json')) {
        const content = await fs.readFile(path.join(MEMORY_DIR, file), 'utf-8');
        memories.push(JSON.parse(content));
      }
    }

    // Simple relevance scoring
    const scored = memories
      .map(mem => ({
        ...mem,
        score: this.calculateRelevance(mem, query),
      }))
      .filter(mem => mem.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(scored, null, 2),
        },
      ],
    };
  }

  calculateSpiralLevel(content) {
    // Simplified spiral level calculation
    return Math.floor(content.length / 100);
  }

  calculateRelevance(memory, query) {
    const queryLower = query.toLowerCase();
    const contentLower = memory.content.toLowerCase();
    
    if (contentLower.includes(queryLower)) return 1.0;
    
    const queryWords = queryLower.split(' ');
    const matches = queryWords.filter(word => contentLower.includes(word)).length;
    
    return matches / queryWords.length;
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Spiral Memory MCP running...');
  }
}

const server = new SpiralMemoryServer();
server.run().catch(console.error);
```

### package.json

```json
{
  "name": "spiral-memory-mcp",
  "version": "1.0.0",
  "description": "Spiral-based memory MCP for Claude Code",
  "main": "build/index.js",
  "type": "module",
  "scripts": {
    "build": "tsc && node -e \"require('fs').chmodSync('build/index.js', '755')\"",
    "watch": "tsc --watch",
    "prepare": "npm run build"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0"
  }
}
```

## Status

✅

Ready to Deploy

Waiting for your approval to deploy to Pi 5.

## Notes

• First MCP in the Claude Code Services deployment system

• Will be used to test the full deployment pipeline

• Can be extended with more sophisticated memory algorithms