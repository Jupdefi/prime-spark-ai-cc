# Prime Spark Voice Command Hub - Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (audio, portaudio, espeak)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    alsa-utils \
    espeak \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Piper TTS (optional, if not using system install)
RUN mkdir -p /opt/piper/voices && \
    wget -q https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_aarch64.tar.gz -O /tmp/piper.tar.gz && \
    tar -xzf /tmp/piper.tar.gz -C /opt/piper && \
    rm /tmp/piper.tar.gz && \
    chmod +x /opt/piper/piper

# Download en_US voice for Piper
RUN cd /opt/piper/voices && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Add piper to PATH
ENV PATH="/opt/piper:${PATH}"

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY voice_hub.py .

# Create non-root user (but needs audio group)
RUN useradd -m -u 1000 -G audio voice && chown -R voice:voice /app
USER voice

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8005/health').raise_for_status()"

# Run application
CMD ["uvicorn", "voice_hub:app", "--host", "0.0.0.0", "--port", "8005"]
