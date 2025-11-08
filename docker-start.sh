#!/bin/bash
# Quick start script for Docker environment

echo "================================================================================"
echo " GeoHackathon 2025 - Docker Environment Setup"
echo "================================================================================"

echo ""
echo "Step 1: Building Docker images..."
docker-compose build

echo ""
echo "Step 2: Starting services (Ollama + ChromaDB + App)..."
docker-compose up -d

echo ""
echo "Step 3: Waiting for services to be ready..."
sleep 10

echo ""
echo "Step 4: Checking service status..."
docker-compose ps

echo ""
echo "================================================================================"
echo " Docker Environment Ready!"
echo "================================================================================"

echo ""
echo "Services running:"
echo "  - App container:    geohackathon-rag"
echo "  - ChromaDB:         http://localhost:8000"
echo "  - Ollama:           http://localhost:11434"

echo ""
echo "Next steps:"
echo "  1. Enter the app container:"
echo "     docker-compose exec app /bin/bash"
echo ""
echo "  2. Inside container, test the components:"
echo "     python src/query_intent.py"
echo "     python src/toc_parser.py"
echo ""
echo "  3. View logs:"
echo "     docker-compose logs -f"
echo ""
echo "  4. Stop services:"
echo "     docker-compose down"

echo ""
echo "================================================================================"
