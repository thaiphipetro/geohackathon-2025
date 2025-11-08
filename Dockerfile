# GeoHackathon 2025 - Well Report RAG System
# Base image: Python 3.10 slim (CPU-only, no GPU required)

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies including OpenGL for Docling
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker cache optimization)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY src/ ./src/
COPY notebooks/ ./notebooks/
COPY outputs/ ./outputs/
COPY scripts/ ./scripts/

# Create directories for data and models
RUN mkdir -p /app/data \
    /app/outputs/rag \
    /app/chroma_db \
    /app/models

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command: Python shell
CMD ["python"]
