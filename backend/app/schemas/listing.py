from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ListingStatusEnum(str, Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    archived = "archived"
    inactive = "inactive"
    sold = "sold"


class ListingSort(str, Enum):
    newest = "newest"
    oldest = "oldest"
    price_asc = "price_asc"
    price_desc = "price_desc"
    promoted_first = "promoted_first"
    most_viewed = "most_viewed"


class ListingBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    price: float = Field(..., ge=0)
    currency: str = "USD"
    city: Optional[str] = None
    category_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    condition: Optional[str] = None
    contact_preference: Optional[str] = None
    is_negotiable: bool = False
    attributes: Optional[dict[str, Any]] = None


class ListingCreate(ListingBase):
    initial_status: Optional[ListingStatusEnum] = ListingStatusEnum.pending_review


class ListingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    city: Optional[str] = None
    category_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    condition: Optional[str] = None
    contact_preference: Optional[str] = None
    is_negotiable: Optional[bool] = None
    attributes: Optional[dict[str, Any]] = None
    status: Optional[ListingStatusEnum] = None


class ListingImageBase(BaseModel):
    image_url: str
    display_order: int = 0
    is_primary: bool = False


class ListingImageResponse(ListingImageBase):
    id: int
    listing_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ListingResponse(ListingBase):
    id: int
    owner_id: int
    status: ListingStatusEnum
    moderation_note: Optional[str] = None
    is_promoted: bool
    is_featured: bool
    view_count: int
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    images: List[ListingImageResponse] = []

    class Config:
        from_attributes = True


class ListingListResponse(BaseModel):
    items: List[ListingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
