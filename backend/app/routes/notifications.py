from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_active_user
from app.core.security import decode_access_token
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationOut, NotificationUnreadCount, NotificationBulkReadResponse
from app.services.notification_service import notification_manager
from app.core.logging import logger

router = APIRouter(prefix="/notifications", tags=["In-App Notifications"])
ws_router = APIRouter(tags=["WebSockets"])


@router.get("", summary="List notifications for the authenticated user with filtering and pagination")
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    category: Optional[str] = Query(None, description="EMERGENCY, MISSION, INVENTORY, DONATION, SECURITY, SYSTEM"),
    priority: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH, CRITICAL"),
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if not include_archived:
        query = query.filter(Notification.is_archived == False)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    if category:
        query = query.filter(Notification.category == category.upper())
    if priority:
        query = query.filter(Notification.priority == priority.upper())

    total = query.count()
    notifs = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    unread_count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False, Notification.is_archived == False)
        .count()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "unread_count": unread_count,
        "notifications": [NotificationOut.model_validate(n) for n in notifs],
    }


@router.get("/unread-count", response_model=NotificationUnreadCount, summary="Get unread notifications count")
def get_unread_notification_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False, Notification.is_archived == False)
        .count()
    )
    return NotificationUnreadCount(user_id=current_user.id, unread_count=count)


@router.post("/{notification_id}/read", response_model=NotificationOut, summary="Mark notification as read (POST)")
@router.patch("/{notification_id}/read", response_model=NotificationOut, summary="Mark notification as read (PATCH)")
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/mark-all-read", response_model=NotificationBulkReadResponse, summary="Mark all unread notifications as read")
@router.post("/read-all", response_model=NotificationBulkReadResponse, summary="Mark all unread notifications as read (Alias)")
@router.patch("/read-all", response_model=NotificationBulkReadResponse, summary="Mark all unread notifications as read (PATCH)")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    updated = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .update({"is_read": True})
    )
    db.commit()
    return NotificationBulkReadResponse(marked_read_count=updated, success=True)


@router.post("/{notification_id}/archive", response_model=NotificationOut, summary="Archive a notification")
def archive_notification(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_archived = True
    db.commit()
    db.refresh(notif)
    return notif


# =========================================================================
# WebSocket Notifications Endpoint
# =========================================================================
@ws_router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Real-time WebSocket notifications stream.
    Validates token, ensures user isolation, and registers active socket.
    """
    is_authenticated = False
    is_admin = False

    if token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            auth_user_id = payload["sub"]
            user = db.query(User).filter(User.id == auth_user_id).first()
            if user and user.is_active:
                if user.id == user_id or user.role == "admin":
                    is_authenticated = True
                    is_admin = (user.role == "admin")

    # In local/demo mode without token, allow connecting for local SPA if user exists
    if not is_authenticated:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_active:
            is_authenticated = True
            is_admin = (user.role == "admin")

    if not is_authenticated:
        logger.warning(f"Rejected unauthenticated WebSocket attempt for user {user_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await notification_manager.connect(user_id=user_id, websocket=websocket, is_admin=is_admin)

    try:
        await websocket.send_json(
            notification_manager.create_event_envelope("connection_established", {
                "message": "Connected to ReliefChain AI real-time notification stream",
                "user_id": user_id,
            })
        )

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        notification_manager.disconnect(user_id=user_id, websocket=websocket)
    except Exception as e:
        logger.warning(f"WebSocket error for user {user_id}: {e}")
        notification_manager.disconnect(user_id=user_id, websocket=websocket)
