import os
from typing import List, Union, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ReliefChain AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development, testing, staging, production
    DEBUG: bool = False if os.getenv("ENVIRONMENT", "").lower() == "production" else (os.getenv("DEBUG", "True").lower() in ("true", "1", "t"))
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "reliefchain-dev-super-secret-key-change-in-production-12345")
    JWT_SECRET_KEY: Optional[str] = os.getenv("JWT_SECRET_KEY", None)
    ALGORITHM: str = "HS256"
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24)))  # 1 day default

    # Allowed Hosts for TrustedHostMiddleware
    ALLOWED_HOSTS: Union[List[str], str] = os.getenv("ALLOWED_HOSTS", "*")

    # Deployment & Worker Process Tuning
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./reliefchain.db")
    TEST_DATABASE_URL: Optional[str] = os.getenv("TEST_DATABASE_URL", None)

    # PostgreSQL config items (optional fallback assembly)
    POSTGRES_SERVER: Optional[str] = os.getenv("POSTGRES_SERVER", None)
    POSTGRES_USER: Optional[str] = os.getenv("POSTGRES_USER", None)
    POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD", None)
    POSTGRES_DB: Optional[str] = os.getenv("POSTGRES_DB", None)
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() in ("true", "1", "t")
    RATE_LIMIT_LOGIN_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_LOGIN_PER_MINUTE", "15"))
    RATE_LIMIT_REGISTER_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_REGISTER_PER_MINUTE", "10"))
    RATE_LIMIT_QR_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_QR_PER_MINUTE", "60"))
    RATE_LIMIT_PUBLIC_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PUBLIC_PER_MINUTE", "120"))
    RATE_LIMIT_AUTH_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_AUTH_PER_MINUTE", "300"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "standard")  # standard or json

    # Blockchain
    BLOCKCHAIN_RPC_URL: str = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
    CONTRACT_ADDRESS: str = os.getenv("CONTRACT_ADDRESS", "")
    BLOCKCHAIN_PRIVATE_KEY: str = os.getenv("BLOCKCHAIN_PRIVATE_KEY", "")

    # AI Model
    AI_MODEL_PATH: str = os.getenv("AI_MODEL_PATH", "ai/model/priority_classifier.joblib")

    # Storage
    STORAGE_LOCAL_DIR: str = os.getenv("STORAGE_LOCAL_DIR", "uploads/evidence")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Optional[str]) -> str:
        if not v:
            return "sqlite:///./reliefchain.db"
        # Normalize postgres:// to postgresql+psycopg2:// or postgresql://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+psycopg2://", 1)
        elif v.startswith("postgresql://") and "+psycopg2" not in v:
            v = v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        env = (self.ENVIRONMENT or "development").lower()
        if env not in ("development", "testing", "staging", "production"):
            raise ValueError(f"Invalid ENVIRONMENT '{self.ENVIRONMENT}'. Must be development, testing, staging, or production.")

        if env == "production":
            # Production must reject DEBUG=True
            if self.DEBUG is True:
                raise ValueError("CRITICAL SECURITY ERROR: DEBUG must be False in production mode.")

            # Ensure insecure default key is not used in production
            insecure_keys = [
                "reliefchain-dev-super-secret-key-change-in-production-12345",
                "secret",
                "changeme",
                "default",
                "admin",
                "password",
            ]
            if self.SECRET_KEY in insecure_keys or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: In production mode, "
                    "SECRET_KEY must be a cryptographically strong random string of at least 32 characters."
                )
            # Ensure CORS does not use wildcards in production
            if "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError("CORS cannot allow wildcard '*' in production mode.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
