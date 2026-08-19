import pytest
from fastapi.testclient import TestClient
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.services.notification_service import notification_manager


def test_password_security_and_hashing():
    raw_password = "SuperSecurePassword999!"
    hashed = get_password_hash(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_token_generation_and_decoding():
    token = create_access_token(subject="user-uuid-12345", role="admin")
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-uuid-12345"
    assert decoded["role"] == "admin"

    # Test invalid / tampered token
    invalid_token = token + "corrupted_tamper_signature"
    assert decode_access_token(invalid_token) is None


def test_notification_manager_methods(db_session, admin_user):
    notif = notification_manager.create_notification(
        db=db_session,
        user_id=admin_user.id,
        title="Admin Alert",
        message="System diagnostic test passed",
        notification_type="system_alert",
        severity="info",
    )
    assert notif.id is not None
    assert notif.user_id == admin_user.id
