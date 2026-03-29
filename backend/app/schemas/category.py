from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    slug: str
    is_active: bool = True
    display_order: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True