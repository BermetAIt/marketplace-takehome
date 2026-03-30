from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class UserPromotion(Base):
    __tablename__ = "user_promotions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    promotion_package_id = Column(
        Integer, ForeignKey("promotion_packages.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True)
    promotion_type = Column(String(64), nullable=False)
    target_city = Column(String(100), nullable=True, index=True)
    target_category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=True, index=True)
    ends_at = Column(DateTime(timezone=True), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="pending_payment", index=True)
    purchased_price = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="user_promotions")
    listing = relationship("Listing", back_populates="user_promotions")
    package = relationship("PromotionPackage", back_populates="user_promotions")
    payment = relationship("Payment", back_populates="user_promotion")
