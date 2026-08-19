import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    Base,
    User,
    Organization,
    Disaster,
    ReliefRequest,
    Resource,
    ResourceInventory,
    Donation,
    Distribution,
    BlockchainTransaction,
    QRVerification,
    PredictionHistory,
    Notification,
)

# In-memory SQLite engine for comprehensive model mapping and relationship testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_models_creation_and_relationships(db_session):
    # 1. Organization
    org = Organization(
        name="Global Hope Relief",
        registration_number="NGO-REG-98765",
        organization_type="NGO",
        contact_email="contact@globalhope.org",
        contact_phone="+1234567890",
        address="123 Aid Ave, Metropolis",
        verification_status="verified",
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    assert org.id is not None
    assert org.verification_status == "verified"

    # 2. Users (Admin, NGO Coordinator, Volunteer, Citizen)
    citizen = User(
        email="citizen@example.com",
        full_name="Jane Doe",
        hashed_password="hashed_secret_pw",
        role="citizen",
        phone_number="+1987654321",
    )
    volunteer = User(
        email="volunteer@example.com",
        full_name="John Field",
        hashed_password="hashed_secret_pw",
        role="volunteer",
        organization_id=org.id,
    )
    db_session.add_all([citizen, volunteer])
    db_session.commit()
    db_session.refresh(citizen)
    db_session.refresh(volunteer)
    assert volunteer.organization.name == "Global Hope Relief"

    # 3. Disaster
    disaster = Disaster(
        title="Hurricane Elena Cat-4",
        disaster_type="cyclone",
        severity="high",
        location_name="Coastal Bay Sector 7",
        latitude=24.1234,
        longitude=88.5678,
    )
    db_session.add(disaster)
    db_session.commit()
    db_session.refresh(disaster)
    assert disaster.id is not None

    # 4. Resource & Inventory
    resource = Resource(
        name="Emergency Medical Trauma Kit",
        category="medicine",
        unit="boxes",
    )
    db_session.add(resource)
    db_session.commit()
    db_session.refresh(resource)

    inventory = ResourceInventory(
        organization_id=org.id,
        resource_id=resource.id,
        total_quantity=500.0,
        available_quantity=450.0,
        reserved_quantity=50.0,
        warehouse_location="Metropolis Central Depot A",
    )
    db_session.add(inventory)
    db_session.commit()

    # 5. Relief Request
    req = ReliefRequest(
        citizen_id=citizen.id,
        disaster_id=disaster.id,
        disaster_type="cyclone",
        location_name="Coastal Bay Sector 7, Block B",
        latitude=24.1250,
        longitude=88.5690,
        affected_people=12,
        required_resources=[{"resource": "medicine", "qty": 2}],
        priority="high",
        status="assigned",
        assigned_organization_id=org.id,
        assigned_volunteer_id=volunteer.id,
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)
    assert req.citizen.email == "citizen@example.com"
    assert req.assigned_volunteer.full_name == "John Field"

    # 6. Donation
    donation = Donation(
        donor_id=citizen.id,
        donor_name="Jane Doe",
        donation_type="monetary",
        amount=250.0,
        currency="USD",
        organization_id=org.id,
        status="received",
        record_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    db_session.add(donation)
    db_session.commit()

    # 7. Distribution
    dist = Distribution(
        relief_request_id=req.id,
        resource_id=resource.id,
        organization_id=org.id,
        volunteer_id=volunteer.id,
        recipient_id=citizen.id,
        quantity=2.0,
        status="dispatched",
        qr_token="token-crypto-xyz-123",
        record_hash="d3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b856",
    )
    db_session.add(dist)
    db_session.commit()
    db_session.refresh(dist)
    assert dist.relief_request_id == req.id

    # 8. QR Verification
    qr_ver = QRVerification(
        distribution_id=dist.id,
        verification_token="token-crypto-xyz-123",
        status="valid",
    )
    db_session.add(qr_ver)

    # 9. Blockchain Transaction
    bc_tx = BlockchainTransaction(
        event_type="distribution",
        reference_id=dist.id,
        record_hash="d3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b856",
        tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        block_number=1024,
        status="confirmed",
    )
    db_session.add(bc_tx)

    # 10. AI Prediction History
    pred = PredictionHistory(
        request_id=req.id,
        disaster_type="cyclone",
        affected_people=12,
        location_risk_score=8.5,
        medical_needed=1,
        food_needed=1,
        water_needed=1,
        vulnerable_population=1,
        predicted_priority="high",
        confidence_score=0.92,
        contributing_factors={"people_count": 0.4, "medical_flag": 0.3},
    )
    db_session.add(pred)

    # 11. Notification
    notif = Notification(
        user_id=citizen.id,
        title="Relief Dispatch Confirmed",
        message="Volunteer John Field has been dispatched with medical supplies.",
        notification_type="assignment",
        reference_id=dist.id,
        reference_type="distribution",
    )
    db_session.add(notif)
    db_session.commit()

    # Final assertions
    assert len(citizen.notifications) == 1
    assert len(org.inventories) == 1
    assert len(org.members) == 1
    assert org.inventories[0].resource.name == "Emergency Medical Trauma Kit"
