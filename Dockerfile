# AI-Horizon Local Models Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs data/backups data/costs data/reports data/uploads data/visualizations

# Set permissions
RUN chmod +x test_local_models.py

# Add health check script
RUN echo '#!/bin/bash\ncurl -f http://localhost:5000/api/database_stats || exit 1' > /app/healthcheck.sh \
    && chmod +x /app/healthcheck.sh

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/healthcheck.sh

# Environment variables
ENV PYTHONPATH=/app
ENV USE_LOCAL_MODELS=true
ENV PERPLEXICAL_URL=http://perplexical:3000
ENV OLLAMA_URL=http://ollama:11434

# Default command
CMD ["python", "status_server.py", "--host", "0.0.0.0", "--port", "5000"] 