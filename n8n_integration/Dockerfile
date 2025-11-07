# Prime Spark N8N Integration Hub - Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY n8n_hub.py .

# Create non-root user
RUN useradd -m -u 1000 n8n && chown -R n8n:n8n /app
USER n8n

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8004/health').raise_for_status()"

# Run application
CMD ["uvicorn", "n8n_hub:app", "--host", "0.0.0.0", "--port", "8004"]
