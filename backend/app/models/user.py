from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
from sqlalchemy.sql import func
from app.db.database import Base
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
    phone = Column(String(20), nullable=True)
    profile_image_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    preferred_language = Column(String(10), default="en")
    account_status = Column(Enum(AccountStatus), default=AccountStatus.active)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())