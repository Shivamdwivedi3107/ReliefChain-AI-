from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = None
try:
    candidate_engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args=connect_args,
        echo=False,
    )
    with candidate_engine.connect() as conn:
        pass
    engine = candidate_engine
    logger.info(f"Database connected: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
except Exception as e:
    logger.warning(f"Target DB unreachable ({e}). Initializing robust SQLite local fallback: sqlite:///./reliefchain.db")
    engine = create_engine("sqlite:///./reliefchain.db", connect_args={"check_same_thread": False}, echo=False)

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
