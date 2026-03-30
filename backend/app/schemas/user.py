from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class AccountStatusEnum(str, Enum):
    active = "active"
    blocked = "blocked"
    pending_verification = "pending_verification"
    deleted = "deleted"


class UserRoleEnum(str, Enum):
    user = "user"
    admin = "admin"
    moderator = "moderator"
    support = "support"
    superadmin = "superadmin"


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = None
    preferred_language: str = "en"

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    preferred_language: Optional[str] = None
    company_name: Optional[str] = None
    seller_type: Optional[str] = None


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
    role: UserRoleEnum
    verified_badge: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PublicUserResponse(BaseModel):
    id: int
    full_name: str
    profile_image_url: Optional[str] = None
    city: Optional[str] = None
    verified_badge: bool
    created_at: datetime
    active_listings_count: int = 0

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    detail: str
