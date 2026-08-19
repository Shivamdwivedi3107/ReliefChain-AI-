from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.core.logging import logger


class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """
        Creates a structured, non-sensitive audit log entry.
        Never stores passwords, tokens, or private keys.
        """
        # Sanitize details to guarantee no secrets are leaked
        sanitized_details = {}
        if details:
            for k, v in details.items():
                if any(secret_kw in k.lower() for secret_kw in ["password", "token", "secret", "private_key", "auth"]):
                    sanitized_details[k] = "[REDACTED]"
                else:
                    sanitized_details[k] = v

        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=sanitized_details if sanitized_details else None,
            ip_address=ip_address,
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        logger.info(f"AUDIT: [{action}] on [{entity_type}:{entity_id}] by user [{user_id}]")
        return audit_entry


audit_service = AuditService()
