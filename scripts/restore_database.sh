#!/usr/bin/env bash
# ==============================================================================
# ReliefChain AI — Production Database Restore Script
# ==============================================================================
# Safe database restore utility with mandatory confirmation and SHA-256 verification.
# Never automatically overwrites production data.
# ==============================================================================

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path_to_backup_file>"
    echo "Example: $0 ./backups/reliefchain_sqlite_20260819_152650.db"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ Error: Backup file '${BACKUP_FILE}' does not exist."
    exit 1
fi

echo "=================================================================="
echo "⚠️ RELIEFCHAIN AI DATABASE RESTORE WARNING"
echo "Target Backup File: ${BACKUP_FILE}"
echo "=================================================================="

# Check SHA-256 Checksum if file exists
if [ -f "${BACKUP_FILE}.sha256" ]; then
    echo "🔍 Validating SHA-256 integrity checksum..."
    sha256sum -c "${BACKUP_FILE}.sha256" || { echo "❌ SHA-256 checksum mismatch! Aborting restore."; exit 1; }
    echo "✅ Integrity verified."
fi

read -p "🚨 Are you SURE you want to restore the database from ${BACKUP_FILE}? (yes/N): " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
    echo "Aborted restore operation."
    exit 0
fi

if [[ "${BACKUP_FILE}" == *.db ]]; then
    echo "📦 Restoring SQLite database..."
    cp "${BACKUP_FILE}" "./reliefchain.db"
    echo "✅ SQLite database restored successfully."
elif [[ "${BACKUP_FILE}" == *.sql.gz ]]; then
    echo "📦 Restoring PostgreSQL database..."
    gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER:-reliefchain}" -d "${POSTGRES_DB:-reliefchain}"
    echo "✅ PostgreSQL database restored successfully."
fi
