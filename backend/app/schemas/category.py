from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    slug: str
    is_active: bool = True
    display_order: int = 0
    parent_id: Optional[int] = None
    attribute_schema: Optional[dict[str, Any]] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
