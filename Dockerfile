# LAGIS - Dockerfile
# Local Autonomous Geopolitical Intelligence System

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama (for local LLM)
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/memory /app/logs /app/output/briefs /app/config /app/docs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_HOST=0.0.0.0:11434

# Expose Ollama port
EXPOSE 11434

# Default command runs the pipeline
CMD ["python", "main.py", "run"]
