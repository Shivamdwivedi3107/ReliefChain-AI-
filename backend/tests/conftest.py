import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.organization import Organization
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings

# Disable rate limiting for unit tests to prevent test client throttling
settings.RATE_LIMIT_ENABLED = False
settings.ENVIRONMENT = "testing"

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def db_session_scope():
    """Create fresh tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_user(db_session):
    user = User(
        email="admin_fixture@reliefchain.ai",
        full_name="Admin Fixture",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="admin",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(client):
    client.post("/api/v1/auth/register", json={
        "email": "admin_test@reliefchain.ai",
        "full_name": "Admin Tester",
        "password": "SecurePassword123!",
        "role": "admin",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "admin_test@reliefchain.ai",
        "password": "SecurePassword123!",
    })
    return res.json()["access_token"]


@pytest.fixture
def citizen_token(client):
    client.post("/api/v1/auth/register", json={
        "email": "citizen_test@reliefchain.ai",
        "full_name": "Citizen Tester",
        "password": "SecurePassword123!",
        "role": "citizen",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "citizen_test@reliefchain.ai",
        "password": "SecurePassword123!",
    })
    return res.json()["access_token"]


@pytest.fixture
def volunteer_token(client):
    client.post("/api/v1/auth/register", json={
        "email": "volunteer_test@reliefchain.ai",
        "full_name": "Volunteer Tester",
        "password": "SecurePassword123!",
        "role": "volunteer",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "volunteer_test@reliefchain.ai",
        "password": "SecurePassword123!",
    })
    return res.json()["access_token"]


@pytest.fixture
def ngo_token(client):
    client.post("/api/v1/auth/register", json={
        "email": "ngo_test@reliefchain.ai",
        "full_name": "NGO Tester",
        "password": "SecurePassword123!",
        "role": "ngo",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "ngo_test@reliefchain.ai",
        "password": "SecurePassword123!",
    })
    return res.json()["access_token"]


@pytest.fixture
def relief_request_data():
    return {
        "disaster_type": "flood",
        "location_name": "Riverside Sector 4",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "affected_people": 15,
        "required_resources": ["water", "food", "medical_kit"],
        "urgency_description": "Trapped families on roof need urgent clean water and first aid.",
    }
