from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.db.database import get_db
from app.models.enums import UserRole
from app.models.user import AccountStatus, User

security = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    payload = verify_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None
    uid = payload.get("user_id")
    if not uid:
        return None
    user = db.query(User).filter(User.id == uid).first()
    if not user or user.account_status == AccountStatus.deleted:
        return None
    return user


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    uid = payload.get("user_id")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.account_status == AccountStatus.deleted:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deleted")
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if user.account_status != AccountStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )
    return user


def require_admin(user: User = Depends(get_current_active_user)) -> User:
    if user.role not in (UserRole.admin, UserRole.superadmin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


def require_moderator_or_admin(user: User = Depends(get_current_active_user)) -> User:
    if user.role not in (UserRole.admin, UserRole.superadmin, UserRole.moderator):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return user
