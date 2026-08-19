import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from fastapi import WebSocket
from sqlalchemy.orm import Session
from app.core.logging import logger, request_id_ctx_var
from app.models.notification import Notification
from app.models.user import User


class NotificationManager:
    """
    Advanced real-time WebSocket connection manager and event dispatcher.
    Supports topic subscriptions, standardized event envelopes, and persistent alerts.
    """

    def __init__(self):
        # Map user_id -> List of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Set of admin user_ids
        self.admin_user_ids: Set[str] = set()
        # Topic subscriptions: topic_name -> Set of WebSockets
        self.topic_subscribers: Dict[str, Set[WebSocket]] = {
            "operations": set(),
            "missions": set(),
            "inventory": set(),
            "notifications": set(),
        }

    @property
    def total_active_connections(self) -> int:
        return sum(len(conns) for conns in self.active_connections.values())

    async def connect(self, user_id: str, websocket: WebSocket, is_admin: bool = False, topics: Optional[List[str]] = None):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        if is_admin:
            self.admin_user_ids.add(user_id)

        # Register topic subscriptions
        assigned_topics = topics or ["operations", "missions", "notifications"]
        for topic in assigned_topics:
            if topic in self.topic_subscribers:
                self.topic_subscribers[topic].add(websocket)

        logger.info(f"WebSocket connected for user {user_id} (Admin: {is_admin}). Total sockets: {len(self.active_connections[user_id])}")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                self.admin_user_ids.discard(user_id)

        for topic_set in self.topic_subscribers.values():
            topic_set.discard(websocket)

        logger.info(f"WebSocket disconnected for user {user_id}")

    def create_event_envelope(self, event_name: str, data: Dict[str, Any], req_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate standardized WebSocket event payload."""
        return {
            "event": event_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": req_id or request_id_ctx_var.get(),
            "data": data,
        }

    async def send_personal_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            dead_sockets = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed sending to socket for user {user_id}: {e}")
                    dead_sockets.append(connection)
            for dead in dead_sockets:
                self.disconnect(user_id, dead)

    async def broadcast_event(self, event_name: str, data: Dict[str, Any], topic: Optional[str] = None):
        """Broadcasts standardized event envelope to all topic subscribers or all active connections."""
        payload = self.create_event_envelope(event_name, data)
        
        target_sockets = set()
        if topic and topic in self.topic_subscribers:
            target_sockets = set(self.topic_subscribers[topic])
        else:
            for conn_list in self.active_connections.values():
                target_sockets.update(conn_list)

        dead_sockets = []
        for socket in target_sockets:
            try:
                await socket.send_json(payload)
            except Exception:
                dead_sockets.append(socket)

        for dead in dead_sockets:
            for topic_set in self.topic_subscribers.values():
                topic_set.discard(dead)

    async def broadcast_to_admins(self, message: dict):
        for admin_id in list(self.admin_user_ids):
            await self.send_personal_message(admin_id, message)

    def create_notification(
        self,
        db: Session,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "system_alert",
        severity: str = "info",
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
    ) -> Notification:
        """Stores notification in DB and triggers background websocket broadcast if connected."""
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            severity=severity,
            reference_id=reference_id,
            reference_type=reference_type,
            is_read=False,
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)

        # Standardized event payload
        payload = self.create_event_envelope("notification_created", {
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "notification_type": notif.notification_type,
            "severity": notif.severity,
            "reference_id": notif.reference_id,
            "reference_type": notif.reference_type,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
        })

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.send_personal_message(user_id, payload))
        except Exception:
            pass

        return notif

    def broadcast_alert(
        self,
        db: Session,
        title: str,
        message: str,
        severity: str = "warning",
        target_role: Optional[str] = None,
    ):
        """Broadcasts a notification to all users matching a role or all active users."""
        query = db.query(User).filter(User.is_active == True)
        if target_role:
            query = query.filter(User.role == target_role)
        users = query.all()
        for u in users:
            self.create_notification(
                db=db,
                user_id=u.id,
                title=title,
                message=message,
                notification_type="system_alert",
                severity=severity,
            )


notification_manager = NotificationManager()
