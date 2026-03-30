from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    attribute_schema = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    display_order = Column(Integer, default=0, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    listings = relationship("Listing", back_populates="category")
    translations = relationship(
        "CategoryTranslation", back_populates="category", cascade="all, delete-orphan"
    )
    parent = relationship("Category", remote_side=[id], backref="children")
