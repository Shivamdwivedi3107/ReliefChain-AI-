#!/usr/bin/env bash
# ==============================================================================
# ReliefChain AI — Production Database Backup Script
# ==============================================================================
# Safe database backup script supporting PostgreSQL and SQLite environments.
# Never automatically overwrites existing production backups.
# ==============================================================================

set -euo pipefail

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "${BACKUP_DIR}"

echo "=================================================================="
echo "🛡️ ReliefChain AI Database Backup System"
echo "Timestamp: ${TIMESTAMP}"
echo "=================================================================="

if [ -n "${POSTGRES_DB:-}" ] && [ -n "${POSTGRES_USER:-}" ]; then
    BACKUP_FILE="${BACKUP_DIR}/reliefchain_postgres_${TIMESTAMP}.sql.gz"
    echo "📦 Backing up PostgreSQL database '${POSTGRES_DB}' to ${BACKUP_FILE}..."
    PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dump -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" | gzip > "${BACKUP_FILE}"
    echo "🔒 Generating SHA-256 integrity checksum..."
    sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
    echo "✅ Backup completed successfully: ${BACKUP_FILE}"
elif [ -f "./reliefchain.db" ]; then
    BACKUP_FILE="${BACKUP_DIR}/reliefchain_sqlite_${TIMESTAMP}.db"
    echo "📦 Backing up SQLite database './reliefchain.db' to ${BACKUP_FILE}..."
    cp "./reliefchain.db" "${BACKUP_FILE}"
    echo "🔒 Generating SHA-256 integrity checksum..."
    sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
    echo "✅ SQLite backup completed successfully: ${BACKUP_FILE}"
else
    echo "⚠️ Notice: Running python backup script fallback..."
    python3 backups/backup.py
fi
