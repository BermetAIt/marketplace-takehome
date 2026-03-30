import secrets
from datetime import timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_password_reset_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.db.database import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import AccountStatus, User
from app.core.deps import get_current_active_user
from app.schemas.user import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LogoutRequest,
    RefreshRequest,
    ResetPasswordRequest,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _utcnow():
    from datetime import datetime

    return datetime.now(timezone.utc)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=get_password_hash(user_data.password),
        phone=user_data.phone,
        preferred_language=user_data.preferred_language,
        account_status=AccountStatus.active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _issue_tokens(db: Session, user: User) -> Token:
    access = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    jti = secrets.token_urlsafe(32)
    exp = _utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=exp))
    db.commit()
    refresh = create_refresh_token(user.id, jti)
    return Token(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.account_status != AccountStatus.active:
        raise HTTPException(status_code=403, detail="Account is blocked or inactive")
    return _issue_tokens(db, user)


@router.post("/refresh", response_model=Token)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    payload = verify_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    jti = payload.get("jti")
    uid = payload.get("user_id")
    if not jti or not uid:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    row = (
        db.query(RefreshToken)
        .filter(RefreshToken.jti == jti, RefreshToken.user_id == uid)
        .first()
    )
    if not row or row.revoked_at is not None or row.expires_at < _utcnow():
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")
    user = db.query(User).filter(User.id == uid).first()
    if not user or user.account_status != AccountStatus.active:
        raise HTTPException(status_code=403, detail="User inactive")
    row.revoked_at = _utcnow()
    db.add(row)
    db.commit()
    return _issue_tokens(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: LogoutRequest, db: Session = Depends(get_db)):
    payload = verify_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None
    jti = payload.get("jti")
    uid = payload.get("user_id")
    if jti and uid:
        row = (
            db.query(RefreshToken)
            .filter(RefreshToken.jti == jti, RefreshToken.user_id == uid)
            .first()
        )
        if row and row.revoked_at is None:
            row.revoked_at = _utcnow()
            db.commit()
    return None


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        return {"detail": "If the email exists, reset instructions were sent."}
    token = generate_password_reset_token()
    user.password_reset_token = token
    user.password_reset_expires = _utcnow() + timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )
    db.commit()
    out = {"detail": "If the email exists, reset instructions were sent."}
    if settings.DEBUG:
        out["debug_reset_token"] = token
    return out


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    matched = (
        db.query(User)
        .filter(
            User.password_reset_token == body.token,
            User.password_reset_expires > _utcnow(),
        )
        .first()
    )
    if not matched:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    matched.password_hash = get_password_hash(body.new_password)
    matched.password_reset_token = None
    matched.password_reset_expires = None
    db.query(RefreshToken).filter(RefreshToken.user_id == matched.id).update(
        {"revoked_at": _utcnow()}
    )
    db.commit()
    return {"detail": "Password updated"}


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_active_user),
):
    if not verify_password(body.current_password, current.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current.password_hash = get_password_hash(body.new_password)
    db.query(RefreshToken).filter(RefreshToken.user_id == current.id).update(
        {"revoked_at": _utcnow()}
    )
    db.commit()
    return {"detail": "Password updated"}
