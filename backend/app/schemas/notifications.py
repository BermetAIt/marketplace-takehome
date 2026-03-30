from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    notification_type: str
    title: str
    body: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: list[NotificationOut]
    total: int
    page: int
    page_size: int
    total_pages: int
    unread_total: int
