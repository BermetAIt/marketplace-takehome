from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id", ondelete="SET NULL"), nullable=True, index=True)
    promotion_package_id = Column(
        Integer, ForeignKey("promotion_packages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(32), nullable=False, default="pending", index=True)
    payment_provider = Column(String(64), default="mock")
    provider_reference = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="payments")
    user_promotion = relationship("UserPromotion", back_populates="payment", uselist=False)
