#!/bin/bash

# Backup ChromaDB data to local filesystem

BACKUP_DIR="./backups/chromadb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="chroma_backup_${TIMESTAMP}.tar.gz"

echo "========================================"
echo "BACKING UP CHROMADB DATA"
echo "========================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Creating backup: $BACKUP_FILE"

# Backup using Docker
docker run --rm \
  -v hackathon_chroma_data:/data:ro \
  -v "$(pwd)/$BACKUP_DIR":/backup \
  alpine \
  tar czf "/backup/$BACKUP_FILE" -C /data .

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    echo ""
    echo "[OK] Backup created successfully!"
    echo "   File: $BACKUP_DIR/$BACKUP_FILE"
    echo "   Size: $BACKUP_SIZE"
    echo ""
    echo "To restore:"
    echo "   ./scripts/restore_chromadb.sh $BACKUP_DIR/$BACKUP_FILE"
else
    echo ""
    echo "[ERROR] Backup failed!"
    exit 1
fi

echo "========================================"
