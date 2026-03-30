from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class PromotionPackage(Base):
    __tablename__ = "promotion_packages"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    title_en = Column(String(255), nullable=False)
    title_ru = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    promotion_type = Column(String(64), nullable=False, index=True)
    base_price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    duration_days = Column(Integer, default=7)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user_promotions = relationship("UserPromotion", back_populates="package")
