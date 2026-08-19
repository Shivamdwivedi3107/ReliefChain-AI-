import pytest
from fastapi.testclient import TestClient
from app.models.notification import Notification
from app.services.notification_service import notification_manager
from app.models.user import User


def test_list_and_manage_notifications(client: TestClient, citizen_token: str, admin_token: str, db_session):
    headers = {"Authorization": f"Bearer {citizen_token}"}

    # Get citizen user ID
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    user_id = me_res.json()["id"]

    # Verify initial notifications
    res = client.get("/api/v1/notifications", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "notifications" in data
    assert "unread_count" in data

    # Create a test notification directly for this user
    notif = notification_manager.create_notification(
        db=db_session,
        user_id=user_id,
        title="Emergency Test Alert",
        message="Flood alert in North Sector",
        notification_type="system_alert",
        severity="warning",
    )
    assert notif.id is not None
    assert notif.is_read is False

    # Check unread count endpoint
    unread_res = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread_res.status_code == 200
    assert unread_res.json()["unread_count"] >= 1

    # Mark as read
    patch_res = client.patch(f"/api/v1/notifications/{notif.id}/read", headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["is_read"] is True

    # Mark all read
    read_all_res = client.patch("/api/v1/notifications/read-all", headers=headers)
    assert read_all_res.status_code == 200
    assert read_all_res.json()["success"] is True
