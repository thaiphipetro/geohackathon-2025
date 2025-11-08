#!/bin/bash

# Restore ChromaDB data from backup

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo ""
    echo "Example: $0 ./backups/chromadb/chroma_backup_20250108_120000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "[ERROR] Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "========================================"
echo "RESTORING CHROMADB DATA"
echo "========================================"
echo "Backup file: $BACKUP_FILE"
echo ""
echo "WARNING: This will replace all current ChromaDB data!"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Stop ChromaDB container
echo ""
echo "Stopping ChromaDB container..."
docker-compose stop chromadb

# Restore data
echo "Restoring data..."
docker run --rm \
  -v hackathon_chroma_data:/data \
  -v "$(pwd)/$(dirname "$BACKUP_FILE")":/backup \
  alpine \
  sh -c "rm -rf /data/* && tar xzf /backup/$(basename "$BACKUP_FILE") -C /data"

if [ $? -eq 0 ]; then
    echo ""
    echo "[OK] Restore completed successfully!"
    echo ""
    echo "Starting ChromaDB container..."
    docker-compose up -d chromadb

    echo ""
    echo "[OK] ChromaDB restarted with restored data"
    echo "Run 'python scripts/check_chromadb_status.py' to verify"
else
    echo ""
    echo "[ERROR] Restore failed!"
    docker-compose up -d chromadb
    exit 1
fi

echo "========================================"
