# Docker Setup Guide

## Quick Start

### 1. Build and Start Services

```bash
# Build and start all services (app + ChromaDB + Ollama)
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 2. Access the Application

```bash
# Enter the app container
docker-compose exec app /bin/bash

# Inside container, run Python scripts
python scripts/quick_explore.py
python src/rag_system.py
```

### 3. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

---

## Services

### 1. App Service (geohackathon-rag)
- **Purpose:** Main application container
- **Port:** None (CLI-based)
- **Volumes:**
  - `./src` → `/app/src` (source code, live-reload)
  - `./outputs` → `/app/outputs` (results)
  - `./Training data-shared with participants` → `/app/data` (read-only)
  - `chroma_data` → `/app/chroma_db` (persistent vector DB)

### 2. ChromaDB Service (geohackathon-chromadb)
- **Purpose:** Vector database for embeddings
- **Port:** 8000
- **Access:** http://localhost:8000
- **Persistence:** `chroma_data` volume

### 3. Ollama Service (geohackathon-ollama)
- **Purpose:** LLM server (Llama 3.2 3B)
- **Port:** 11434
- **Access:** http://localhost:11434
- **Persistence:** `ollama_models` volume
- **Auto-pulls:** Llama 3.2 3B on first startup

---

## Development Workflow

### Code Changes
Source code in `./src` is mounted as a volume, so changes are reflected immediately:

```bash
# Edit on host
vim src/rag_system.py

# Run in container (no rebuild needed)
docker-compose exec app python src/rag_system.py
```

### Add Dependencies

```bash
# Edit requirements.txt on host
echo "new-package==1.0.0" >> requirements.txt

# Rebuild app container
docker-compose build app
docker-compose up -d app
```

### Test RAG System

```bash
# Enter container
docker-compose exec app /bin/bash

# Inside container
cd /app
python -c "
from src.rag_system import RAGSystem
rag = RAGSystem()
print(rag.query('What is the well depth?'))
"
```

---

## Troubleshooting

### Ollama Model Not Downloaded

```bash
# Check Ollama logs
docker-compose logs ollama

# Manually pull model
docker-compose exec ollama ollama pull llama3.2:3b

# Verify model
docker-compose exec ollama ollama list
```

### ChromaDB Connection Issues

```bash
# Check ChromaDB is running
docker-compose ps chromadb

# Test connection
curl http://localhost:8000/api/v1/heartbeat

# Restart ChromaDB
docker-compose restart chromadb
```

### Volume Permissions

```bash
# If permission errors, fix ownership
docker-compose exec app chown -R $(id -u):$(id -g) /app/outputs
```

### Clean Reset

```bash
# Stop everything
docker-compose down

# Remove all data (WARNING: deletes ChromaDB + Ollama models)
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

---

## Performance Notes

### CPU-Only Execution
- All services run on CPU (no GPU required)
- Ollama configured for CPU inference
- Nomic embeddings use CPU

### Resource Requirements
- **RAM:** ~4GB minimum
  - App: ~1GB
  - ChromaDB: ~512MB
  - Ollama: ~2GB (Llama 3.2 3B)
- **Disk:** ~5GB
  - Base images: ~2GB
  - Ollama models: ~2GB
  - ChromaDB data: ~500MB (depends on corpus)

---

## Production Deployment

### Build for Production

```bash
# Build optimized image
docker build -t geohackathon-rag:latest .

# Run without docker-compose
docker run -it --rm \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/Training\ data-shared\ with\ participants:/app/data:ro \
  --network rag-network \
  geohackathon-rag:latest \
  python src/rag_system.py
```

### Environment Variables

```bash
# Override Ollama host
docker-compose up -d -e OLLAMA_HOST=http://custom-ollama:11434
```

---

## File Structure

```
.
├── Dockerfile                 # Main app container
├── docker-compose.yml         # Service orchestration
├── .dockerignore             # Exclude files from build
├── requirements.txt          # Python dependencies
├── src/                      # Source code (mounted)
│   ├── query_intent.py
│   ├── toc_parser.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── vector_store.py
│   └── rag_system.py
├── outputs/                  # Results (mounted)
│   ├── exploration/
│   └── rag/
└── Training data.../         # Well reports (mounted, read-only)
```

---

## Next Steps

After Docker setup is complete:

1. **Verify services:**
   ```bash
   docker-compose ps
   # All services should show "Up"
   ```

2. **Enter app container:**
   ```bash
   docker-compose exec app /bin/bash
   ```

3. **Run implementation:**
   ```bash
   python src/query_intent.py      # Test query mapping
   python src/toc_parser.py         # Test TOC lookup
   python src/rag_system.py         # Full RAG pipeline
   ```

4. **Monitor logs:**
   ```bash
   docker-compose logs -f app
   ```
