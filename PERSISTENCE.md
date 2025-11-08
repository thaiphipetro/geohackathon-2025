# Data Persistence Guide

## Overview

All indexed data (embeddings, chunks, metadata) is **persistent** and stored in ChromaDB. You will NOT need to re-index after restarts.

---

## How It Works

### ChromaDB Architecture

```
Your Notebook/Scripts
       ↓
   localhost:8000
       ↓
ChromaDB Container (geohackathon-chromadb)
       ↓
Docker Volume (hackathon_chroma_data)  ← Persistent Storage
```

### What Gets Saved

1. **Vector Embeddings**: 768-dimensional vectors for each chunk
2. **Text Content**: Original chunk text (for retrieval)
3. **Metadata**:
   - `well_name`: Well identifier
   - `document_name`: PDF filename
   - `section_type`: Section classification (casing, depth, etc.)
   - `section_number`: TOC section number
   - `section_title`: Section title
   - `page`: Page number
   - `chunk_type`: 'text' or 'table'
   - `chunk_index`: Chunk position in document

### Persistence Guarantee

✅ **Data persists across:**
- Computer restarts
- Docker container stops/restarts
- System reboots
- ChromaDB container updates

❌ **Data is lost if:**
- Docker volume is deleted: `docker volume rm hackathon_chroma_data`
- Docker prune with volumes: `docker system prune --volumes`

---

## Checking Current Status

### Quick Check

```bash
python scripts/check_chromadb_status.py
```

**Output:**
```
Total chunks: 79
Wells indexed: Well 5
Documents indexed: NLOG_GS_PUB_App 07. Final-Well-Report_NLW-GT-03.pdf
Chunk types: text
```

### Manual Check via Docker

```bash
# Check if ChromaDB container is running
docker ps | grep chromadb

# Check volume exists
docker volume ls | grep chroma

# Inspect volume details
docker volume inspect hackathon_chroma_data
```

---

## Backup & Restore

### Creating a Backup

**Option 1: Using provided script (Git Bash)**
```bash
./scripts/backup_chromadb.sh
```

**Option 2: Manual backup (Windows Command Prompt)**
```bash
mkdir backups\chromadb
docker run --rm -v hackathon_chroma_data:/data:ro -v %cd%\backups\chromadb:/backup alpine tar czf /backup/chroma_backup.tar.gz -C /data .
```

**Backup Location:** `./backups/chromadb/chroma_backup_<timestamp>.tar.gz`

### Restoring from Backup

**Option 1: Using provided script (Git Bash)**
```bash
./scripts/restore_chromadb.sh ./backups/chromadb/chroma_backup_20250108_120000.tar.gz
```

**Option 2: Manual restore (Windows Command Prompt)**
```bash
# Stop ChromaDB
docker-compose stop chromadb

# Restore data
docker run --rm -v hackathon_chroma_data:/data -v %cd%\backups\chromadb:/backup alpine sh -c "rm -rf /data/* && tar xzf /backup/chroma_backup.tar.gz -C /data"

# Start ChromaDB
docker-compose up -d chromadb

# Verify
python scripts/check_chromadb_status.py
```

---

## Common Scenarios

### Scenario 1: Fresh System Setup

You want to set up the project on a new machine with existing backup:

```bash
# 1. Clone repo
git clone <repo_url>
cd Hackathon

# 2. Start ChromaDB
docker-compose up -d chromadb

# 3. Restore backup
./scripts/restore_chromadb.sh ./path/to/backup.tar.gz

# 4. Verify
python scripts/check_chromadb_status.py
```

**Result:** All indexed data is restored, no re-indexing needed ✅

### Scenario 2: After Reboot

You restarted your computer:

```bash
# 1. Start ChromaDB (if not auto-started)
docker-compose up -d chromadb

# 2. Verify data is still there
python scripts/check_chromadb_status.py
```

**Result:** Data is still there ✅

### Scenario 3: ChromaDB Container Update

You want to update ChromaDB to a newer version:

```bash
# 1. Backup first (just in case)
./scripts/backup_chromadb.sh

# 2. Stop and remove container
docker-compose down chromadb

# 3. Pull new image
docker pull chromadb/chroma:latest

# 4. Start with same volume
docker-compose up -d chromadb

# 5. Verify data is intact
python scripts/check_chromadb_status.py
```

**Result:** Data is migrated to new container ✅

### Scenario 4: Moving to Different Machine

You want to transfer your indexed data to another computer:

```bash
# On OLD machine:
./scripts/backup_chromadb.sh
# Copy ./backups/chromadb/chroma_backup_*.tar.gz to USB/cloud

# On NEW machine:
git clone <repo_url>
docker-compose up -d chromadb
./scripts/restore_chromadb.sh /path/to/chroma_backup.tar.gz
```

**Result:** Data transferred successfully ✅

---

## Troubleshooting

### Issue: "No collections found"

**Symptoms:**
- `check_chromadb_status.py` shows 0 collections
- No data appears after indexing

**Solutions:**
```bash
# 1. Check if ChromaDB is running
docker ps | grep chromadb

# 2. If not running, start it
docker-compose up -d chromadb

# 3. Check logs
docker logs geohackathon-chromadb

# 4. If logs show errors, restart
docker-compose restart chromadb
```

### Issue: "Connection refused"

**Symptoms:**
- Cannot connect to localhost:8000
- Scripts fail with connection error

**Solutions:**
```bash
# 1. Verify ChromaDB container is running
docker ps | grep chromadb

# 2. Check port is exposed
docker port geohackathon-chromadb

# 3. Restart container
docker-compose restart chromadb

# 4. Check Windows firewall (if on Windows)
```

### Issue: "Out of disk space"

**Symptoms:**
- Indexing fails
- ChromaDB errors

**Solutions:**
```bash
# 1. Check Docker disk usage
docker system df

# 2. Check volume size
docker system df -v | grep chroma

# 3. Clean up old containers/images (NOT volumes!)
docker system prune  # WITHOUT --volumes flag!

# 4. Free up disk space on host system
```

### Issue: "Data disappeared after restart"

**Symptoms:**
- Data was there before restart
- Now showing 0 chunks

**Possible Causes & Solutions:**

**Cause 1: Volume was accidentally deleted**
```bash
# Check if volume exists
docker volume ls | grep chroma

# If missing, restore from backup
./scripts/restore_chromadb.sh ./backups/chromadb/latest_backup.tar.gz
```

**Cause 2: Connected to different ChromaDB instance**
```bash
# Check connection in notebook/script
# Should be: localhost:8000

# Verify correct container is running
docker ps | grep chromadb
```

**Cause 3: Volume mount changed**
```bash
# Check docker-compose.yml
# Line 34 should be: - chroma_data:/chroma/chroma

# Restart with correct mount
docker-compose down
docker-compose up -d chromadb
```

---

## Best Practices

### 1. Regular Backups

**Recommended Schedule:**
- Before major changes: `./scripts/backup_chromadb.sh`
- After indexing new wells: `./scripts/backup_chromadb.sh`
- Weekly: `./scripts/backup_chromadb.sh`

**Backup Retention:**
- Keep last 3-5 backups
- Delete old backups manually from `./backups/chromadb/`

### 2. Verify After Indexing

Always check status after indexing:
```bash
python scripts/check_chromadb_status.py
```

### 3. Document What's Indexed

Keep a log of what you've indexed:
```bash
# Example: index_log.txt
2025-01-08: Well 5 - NLOG_GS_PUB_App 07. Final-Well-Report_NLW-GT-03.pdf (79 chunks)
2025-01-08: Well 5 v1.0 - NLOG_GS_PUB_EOWR_SodM_NLW-GT-03-S1 v1.0_Redacted.pdf (45 chunks)
```

### 4. Avoid Volume Deletion

**NEVER run these commands:**
```bash
docker volume rm hackathon_chroma_data  # Deletes ALL indexed data!
docker system prune --volumes           # Deletes ALL unused volumes!
```

**Safe cleanup:**
```bash
docker system prune  # WITHOUT --volumes flag
```

---

## Storage Location

### Docker Volume Path

**Linux/Mac:**
```
/var/lib/docker/volumes/hackathon_chroma_data/_data
```

**Windows (WSL2):**
```
\\wsl$\docker-desktop-data\data\docker\volumes\hackathon_chroma_data\_data
```

**Windows (Docker Desktop):**
```
%LOCALAPPDATA%\Docker\wsl\data\ext4.vhdx (inside virtual disk)
```

**Note:** Direct access to volume data is NOT recommended. Always use backup/restore scripts.

---

## Summary

✅ **Your indexed data IS persistent**
- Stored in Docker volume `hackathon_chroma_data`
- Survives restarts, reboots, container updates
- Can be backed up and restored anytime

✅ **You do NOT need to re-index**
- Data is automatically loaded when you restart
- ChromaDB maintains all embeddings and metadata

✅ **Check status anytime**
```bash
python scripts/check_chromadb_status.py
```

✅ **Backup regularly**
```bash
./scripts/backup_chromadb.sh
```

✅ **Safe to restart Docker/computer**
- ChromaDB container will restart automatically (if configured)
- Data persists in volume
