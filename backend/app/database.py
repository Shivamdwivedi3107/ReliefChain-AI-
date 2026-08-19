from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

connect_args = {}
engine_kwargs = {"pool_pre_ping": True, "echo": False}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine_kwargs["connect_args"] = connect_args
else:
    # PostgreSQL production pool configuration
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 1800  # Recycle connections every 30 minutes
    engine_kwargs["pool_timeout"] = 30    # 30s timeout for obtaining pooled connection

engine = None
try:
    candidate_engine = create_engine(
        settings.DATABASE_URL,
        **engine_kwargs
    )
    with candidate_engine.connect() as conn:
        pass
    engine = candidate_engine
    logger.info(f"Database connected: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
except Exception as e:
    if settings.ENVIRONMENT == "production":
        logger.error(f"CRITICAL: Failed to connect to production database ({e}).")
        raise
    else:
        logger.warning(f"Target DB unreachable ({e}). Initializing robust SQLite local fallback: sqlite:///./reliefchain.db")
        engine = create_engine("sqlite:///./reliefchain.db", connect_args={"check_same_thread": False}, echo=False)

# Enable foreign keys for SQLite
if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing request-scoped database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Utility to test database connectivity."""
    try:
        with engine.connect() as conn:
            return True
    except Exception as err:
        logger.error(f"Database health check failed: {err}")
        return False
