# AI-Enhanced Notion Bridge - Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ai_bridge_agent.py .
COPY __init__.py .

# Copy parent notion bridge agent
COPY ../notion_bridge_agent.py ./agents/

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/', timeout=5)"

# Run the agent
CMD ["python", "ai_bridge_agent.py"]
