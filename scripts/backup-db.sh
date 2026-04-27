#!/usr/bin/env bash
set -euo pipefail

DB_PATH="/home/steven/code/wedding-site/rsvps.db"
NAS_MOUNT="/mnt/nas-steven"
BACKUP_DIR="${NAS_MOUNT}/Backups/wedding_site_bk"
LOG_FILE="/home/steven/code/wedding-site/logs/backup-db.log"
RETENTION_DAYS=365

mkdir -p "$(dirname "$LOG_FILE")"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S%z')] $*" >> "$LOG_FILE"
}

if ! mountpoint -q "$NAS_MOUNT"; then
  log "ERROR: NAS not mounted at $NAS_MOUNT — aborting"
  exit 1
fi

if [[ ! -f "$DB_PATH" ]]; then
  log "ERROR: DB not found at $DB_PATH — aborting"
  exit 1
fi

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

LOCAL_BACKUP="${TMP_DIR}/rsvps_${TIMESTAMP}.db"
FINAL_FILE="${BACKUP_DIR}/rsvps_${TIMESTAMP}.db.gz"

log "Starting backup of $DB_PATH"
sqlite3 "$DB_PATH" ".backup '$LOCAL_BACKUP'"
gzip -f "$LOCAL_BACKUP"
cp "${LOCAL_BACKUP}.gz" "$FINAL_FILE"
SIZE="$(du -h "$FINAL_FILE" | cut -f1)"
log "Wrote $FINAL_FILE (${SIZE})"

PRUNED="$(find "$BACKUP_DIR" -maxdepth 1 -name 'rsvps_*.db.gz' -type f -mtime +${RETENTION_DAYS} -print -delete | wc -l)"
log "Pruned ${PRUNED} backup(s) older than ${RETENTION_DAYS} day(s)"
log "Done"
