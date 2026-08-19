# ReliefChain AI — Database Architecture & Operations

This guide covers PostgreSQL database configuration, connection pooling, high-throughput indexes, and Alembic database migration management.

---

## 1. Supported Relational Engines

| Engine | Target Environment | Connection Dialect | Connection Pooling |
|---|---|---|---|
| **PostgreSQL 16** | Production / Staging | `postgresql+psycopg2://` | Active (`pool_size=10`, `max_overflow=20`, `pool_recycle=1800s`) |
| **SQLite 3** | Local Dev / Automated Tests | `sqlite:///` | NullPool with Foreign Keys (`PRAGMA foreign_keys=ON`) |

---

## 2. Connection Pool Configuration

In `backend/app/database.py`, the engine utilizes production SQLAlchemy parameters:

```python
engine_kwargs = {
    "pool_size": 10,          # Base number of pooled persistent connections
    "max_overflow": 20,       # Maximum additional temporary burst connections
    "pool_recycle": 1800,     # Recycle stale connections after 30 minutes
    "pool_timeout": 30,       # Timeout when waiting for available connection
    "pool_pre_ping": True,    # Validate connection liveness before checking out
    "echo": False,            # Silence verbose query echoing in production
}
```

---

## 3. High-Throughput Indexes

ReliefChain AI models define targeted single and composite indexes on all frequently filtered and joined columns:

| Model / Table | Indexed Columns | Query Purpose |
|---|---|---|
| `relief_requests` | `id`, `citizen_id`, `status`, `priority`, `disaster_type`, `assigned_volunteer_id`, `created_at` | Rapid incident filtering, map bounding box queries, volunteer matching |
| `mission_status_histories`| `relief_request_id`, `new_status`, `changed_by_user_id`, `created_at` | Audit chronology and state transition tracing |
| `resource_inventories` | `organization_id`, `resource_id`, `(organization_id, resource_id)` (Unique) | Over-allocation prevention and stock lookup |
| `distributions` | `id`, `relief_request_id`, `resource_id`, `qr_token`, `status`, `created_at` | Single-use cryptographic QR validation |
| `blockchain_transactions` | `id`, `event_type`, `record_hash`, `tx_hash`, `status`, `created_at` | Merkle hash linking and whole-chain verification |
| `notifications` | `id`, `user_id`, `is_read`, `priority`, `category`, `created_at` | Real-time push alert delivery and inbox rendering |
| `audit_logs` | `id`, `user_id`, `action`, `entity_type`, `entity_id`, `created_at` | Security auditing and compliance queries |

---

## 4. Alembic Migration Workflow

Alembic manages schema evolution from an empty database to the latest state.

### Running Migrations Upwards (Upgrade)
```bash
cd backend
python -m alembic upgrade head
```

### Checking Current Revision
```bash
cd backend
python -m alembic current
```

### Creating a New Schema Revision
```bash
cd backend
python -m alembic revision --autogenerate -m "add_new_operational_field"
```

### Rolling Back One Revision (Downgrade)
```bash
cd backend
python -m alembic downgrade -1
```
