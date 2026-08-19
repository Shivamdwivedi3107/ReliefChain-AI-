from typing import Generator, List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Validate JWT token and return the authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify that the authenticated user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user


ROLE_EQUIVALENCES = {
    "relief_organization": "ngo",
    "ngo": "ngo",
    "beneficiary": "citizen",
    "citizen": "citizen",
    "volunteer": "volunteer",
    "donor": "donor",
    "admin": "admin",
}


def require_roles(allowed_roles: List[str]) -> Callable[[User], User]:
    """Role-Based Access Control dependency factory supporting role aliases."""
    normalized_allowed = {ROLE_EQUIVALENCES.get(r.lower(), r.lower()) for r in allowed_roles}
    normalized_allowed.add("admin")

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_role = ROLE_EQUIVALENCES.get(current_user.role.lower(), current_user.role.lower())
        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Operation requires one of the following roles: {allowed_roles}",
            )
        return current_user

    return role_checker
