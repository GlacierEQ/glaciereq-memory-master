#!/usr/bin/env bash
set -euo pipefail

echo "💾 Neo4j Backup Script"
echo "===================="

# Configuration
BACKUP_DIR="./backups/neo4j"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="neo4j_backup_${TIMESTAMP}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "📁 Creating backup: $BACKUP_NAME"

# Check if Neo4j is running
if ! docker ps | grep neo4j >/dev/null; then
    echo "❌ Neo4j container not running"
    exit 1
fi

# Create backup using Neo4j admin
echo "💾 Executing Neo4j backup..."
docker exec $(docker ps -qf name=neo4j) neo4j-admin database backup \
    --backup-dir=/tmp/backup \
    --database=neo4j \
    --verbose

# Copy backup from container
echo "📤 Copying backup from container..."
docker cp $(docker ps -qf name=neo4j):/tmp/backup "$BACKUP_DIR/$BACKUP_NAME"

# Create backup metadata
cat > "$BACKUP_DIR/$BACKUP_NAME/metadata.json" << EOF
{
  "backup_name": "$BACKUP_NAME",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "database": "neo4j", 
  "backup_type": "full",
  "created_by": "backup-neo4j.sh"
}
EOF

# Compress backup
echo "🗜️ Compressing backup..."
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"
rm -rf "$BACKUP_DIR/$BACKUP_NAME"

# Cleanup old backups (keep last 7 days)
echo "🧽 Cleaning up old backups..."
find "$BACKUP_DIR" -name "neo4j_backup_*.tar.gz" -mtime +7 -delete

echo "✅ Backup complete: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo "📊 Backup size: $(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)"

# List available backups
echo "📁 Available backups:"
ls -lah "$BACKUP_DIR/"neo4j_backup_*.tar.gz 2>/dev/null || echo "  No previous backups found"

echo "✅ Neo4j backup complete"