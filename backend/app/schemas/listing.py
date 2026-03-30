from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ListingStatusEnum(str, Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    archived = "archived"
    sold = "sold"

# === Базовая схема ===
class ListingBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    price: float = Field(..., gt=0)
    currency: str = "USD"
    city: Optional[str] = None
    category_id: int

# === Для создания ===
class ListingCreate(ListingBase):
    pass

# === Для обновления ===
class ListingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = None
    city: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[ListingStatusEnum] = None

# === Изображение ===
class ListingImageBase(BaseModel):
    image_url: str
    display_order: int = 0
    is_primary: bool = False

class ListingImageCreate(ListingImageBase):
    pass

class ListingImageResponse(ListingImageBase):
    id: int
    listing_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# === Полный ответ ===
class ListingResponse(ListingBase):
    id: int
    owner_id: int
    status: ListingStatusEnum
    is_promoted: bool
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    images: List[ListingImageResponse] = []
    
    class Config:
        from_attributes = True

# === Для списков с пагинацией ===
class ListingListResponse(BaseModel):
    items: List[ListingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int