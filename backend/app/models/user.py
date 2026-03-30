from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.models.enums import UserRole
import enum


class AccountStatus(str, enum.Enum):
    active = "active"
    blocked = "blocked"
    pending_verification = "pending_verification"
    deleted = "deleted"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True, index=True)
    profile_image_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    city = Column(String(100), nullable=True, index=True)
    preferred_language = Column(String(10), default="en")
    account_status = Column(Enum(AccountStatus), default=AccountStatus.active, index=True)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False, index=True)
    verified_badge = Column(Boolean, default=False)
    company_name = Column(String(255), nullable=True)
    seller_type = Column(String(64), nullable=True)
    response_rate = Column(Numeric(5, 2), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String(128), nullable=True, index=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    wallet_balance = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    listings = relationship("Listing", back_populates="owner")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    payments = relationship("Payment", back_populates="user")
    user_promotions = relationship("UserPromotion", back_populates="user")
    wallet_transactions = relationship(
        "WalletTransaction", back_populates="user", cascade="all, delete-orphan"
    )
