# ReliefChain AI — Backup, Restore & Disaster Recovery (DR)

This runbook outlines procedures for logical database backups, cryptographic checksum validation, automated retention, and disaster recovery.

---

## 1. Backup Strategy

ReliefChain AI incorporates an automated backup script (`backend/scripts/backup_db.py`) that performs:
- **Timestamped Logical Dumps**: Creates structured `.sql` (PostgreSQL) or `.db` (SQLite) snapshots.
- **SHA-256 Checksumming**: Computes and writes `.sha256` files alongside each archive.
- **Automated Retention Pruning**: Automatically prunes archives older than a configurable threshold (default: 7 days).

---

## 2. Running a Manual Backup

```bash
# Execute standard backup to backups/ directory
python backend/scripts/backup_db.py --output-dir backups --retention-days 7

# Example Output:
# [SUCCESS] Backup created at: /app/backups/reliefchain_postgres_20260819_205000.sql
# [CHECKSUM] SHA-256: 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945
```

---

## 3. Restoring from Backup

Before applying a database restore, `backend/scripts/restore_db.py` verifies the cryptographic SHA-256 checksum to prevent corrupted or tampered snapshots from entering the database.

```bash
# Restore from a verified backup archive
python backend/scripts/restore_db.py backups/reliefchain_postgres_20260819_205000.sql
```

---

## 4. Disaster Recovery (DR) Runbook

In the event of total server or container failure:

1. **Spin up fresh infrastructure**:
   ```bash
   docker compose -f docker-compose.prod.yml down -v
   docker compose -f docker-compose.prod.yml up -d db
   ```
2. **Apply latest verified backup snapshot**:
   ```bash
   docker exec -i reliefchain-db psql -U reliefchain -d reliefchain < backups/latest_verified_backup.sql
   ```
3. **Start backend and reverse proxy**:
   ```bash
   docker compose -f docker-compose.prod.yml up -d backend proxy
   ```
4. **Verify whole-chain ledger integrity**:
   ```bash
   curl -f http://localhost/api/v1/ledger/verify
   ```
