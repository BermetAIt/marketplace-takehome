from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    listing_id: int
    recipient_user_id: int


class MessageAttachmentOut(BaseModel):
    id: int
    file_name: str
    original_name: str
    mime_type: str
    file_size: int
    download_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    text_body: Optional[str] = None
    is_read: bool
    sent_at: datetime
    attachments: List[MessageAttachmentOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    listing_id: int
    other_user_id: int
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    unread_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    items: List[ConversationOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageListResponse(BaseModel):
    items: List[MessageOut]
    total: int
    page: int
    page_size: int
    total_pages: int
