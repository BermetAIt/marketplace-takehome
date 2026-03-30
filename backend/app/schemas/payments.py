from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class PaymentInitiate(BaseModel):
    listing_id: int
    promotion_package_id: int
    target_city: Optional[str] = None
    target_category_id: Optional[int] = None


class PaymentOut(BaseModel):
    id: int
    user_id: int
    listing_id: Optional[int] = None
    promotion_package_id: Optional[int] = None
    amount: Decimal
    currency: str
    status: str
    payment_provider: str
    provider_reference: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    items: list[PaymentOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class PromotionPackageOut(BaseModel):
    id: int
    code: str
    title_en: str
    title_ru: Optional[str] = None
    description: Optional[str] = None
    promotion_type: str
    base_price: Decimal
    currency: str
    duration_days: int
    is_active: bool

    class Config:
        from_attributes = True


class UserPromotionOut(BaseModel):
    id: int
    listing_id: int
    promotion_package_id: int
    promotion_type: str
    target_city: Optional[str] = None
    target_category_id: Optional[int] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    status: str
    purchased_price: Optional[Decimal] = None

    class Config:
        from_attributes = True


class WalletTopUpMock(BaseModel):
    amount: Decimal = Field(..., gt=0)
