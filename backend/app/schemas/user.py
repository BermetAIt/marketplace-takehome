# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class AccountStatusEnum(str, Enum):
    active = "active"
    blocked = "blocked"
    pending_verification = "pending_verification"
    deleted = "deleted"

# === Схемы для регистрации и входа ===
class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    preferred_language: str = "en"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# === Схемы токенов ===
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None

# === Схемы ответа ===
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    preferred_language: str
    account_status: AccountStatusEnum
    created_at: datetime
    
    class Config:
        from_attributes = True