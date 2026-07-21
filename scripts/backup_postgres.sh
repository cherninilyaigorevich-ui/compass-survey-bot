#!/bin/bash

set -e

cd /opt/compass-survey-bot

BACKUP_DIR="/opt/backup/postgres"
DATE=$(date +"%Y-%m-%d_%H-%M")

FILE="$BACKUP_DIR/compass_$DATE.sql.gz"


echo "Starting PostgreSQL backup..."


docker compose exec -T postgres \
pg_dump \
-U compass \
-d compass \
| gzip > "$FILE"


echo "Backup created:"
echo "$FILE"

echo "Removing old backups..."

find "$BACKUP_DIR" \
-name "compass_*.sql.gz" \
-mtime +7 \
-delete


echo "Cleanup completed"
