from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
import enum


class ListingStatus(str, enum.Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    archived = "archived"
    inactive = "inactive"
    sold = "sold"


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False, index=True)
    currency = Column(String(3), default="USD")
    city = Column(String(100), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    condition = Column(String(64), nullable=True)
    contact_preference = Column(String(32), nullable=True)
    is_negotiable = Column(Boolean, default=False)
    attributes = Column(JSON, nullable=True)
    status = Column(Enum(ListingStatus), default=ListingStatus.pending_review, index=True)
    moderation_note = Column(Text, nullable=True)
    is_promoted = Column(Boolean, default=False, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    view_count = Column(Integer, default=0)
    published_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="listings")
    category = relationship("Category", back_populates="listings")
    images = relationship(
        "ListingImage", back_populates="listing", cascade="all, delete-orphan"
    )
    favorites = relationship("Favorite", back_populates="listing", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="listing")
    user_promotions = relationship("UserPromotion", back_populates="listing")
