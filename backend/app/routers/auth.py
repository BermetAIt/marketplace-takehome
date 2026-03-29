from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User, AccountStatus
from app.schemas.user import UserRegister, UserLogin, Token, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token
from datetime import timedelta
from app.core.config import settings

# === ВАЖНО: создаём router ===
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    
    # Проверка: существует ли email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Создание нового пользователя
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=get_password_hash(user_data.password),
        phone=user_data.phone,
        preferred_language=user_data.preferred_language,
        account_status=AccountStatus.active
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Вход пользователя"""
    
    # Поиск пользователя по email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверка статуса аккаунта
    if user.account_status != AccountStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked or inactive"
        )
    
    # Создание JWT токена
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}