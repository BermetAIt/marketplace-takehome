from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    target_type: str = Field(..., pattern="^(listing|user|message)$")
    target_id: int
    reason_code: str = Field(..., min_length=2, max_length=64)
    reason_text: Optional[str] = None


class ReportOut(BaseModel):
    id: int
    target_type: str
    target_id: int
    reason_code: str
    reason_text: Optional[str] = None
    status: str
    resolution_note: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
