from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.db.database import get_db
from app.models.conversation import Conversation
from app.models.listing import Listing, ListingStatus
from app.models.message import Message
from app.models.message_attachment import MessageAttachment
from app.models.user import AccountStatus, User
from app.schemas.messaging import (
    ConversationCreate,
    ConversationListResponse,
    ConversationOut,
    MessageAttachmentOut,
    MessageListResponse,
    MessageOut,
)
from app.services.notifications import notify_user
from app.utils.files import ALLOWED_MESSAGE, save_upload_file

router = APIRouter(prefix="/conversations", tags=["Messaging"])


def _now():
    return datetime.now(timezone.utc)


def _other_user_id(conv: Conversation, me: int) -> int:
    return conv.participant_b_id if conv.participant_a_id == me else conv.participant_a_id


def _base_url() -> str:
    return settings.API_PUBLIC_BASE_URL.rstrip("/")


def _attachment_url(att_id: int) -> str:
    return f"{_base_url()}/api/attachments/{att_id}/download"


def _conversation_out(db: Session, conv: Conversation, me: int) -> ConversationOut:
    other = _other_user_id(conv, me)
    last = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id, Message.deleted_at.is_(None))
        .order_by(desc(Message.sent_at))
        .first()
    )
    preview = None
    if last:
        preview = (last.text_body or "")[:200]
    unread = (
        db.query(Message)
        .filter(
            Message.conversation_id == conv.id,
            Message.sender_id != me,
            Message.is_read.is_(False),
        )
        .count()
    )
    return ConversationOut(
        id=conv.id,
        listing_id=conv.listing_id,
        other_user_id=other,
        last_message_at=conv.last_message_at,
        last_message_preview=preview,
        unread_count=unread,
        created_at=conv.created_at,
    )


def _message_to_out(msg: Message) -> MessageOut:
    atts = [
        MessageAttachmentOut(
            id=a.id,
            file_name=a.file_name,
            original_name=a.original_name,
            mime_type=a.mime_type,
            file_size=a.file_size,
            download_url=_attachment_url(a.id),
            created_at=a.created_at,
        )
        for a in (msg.attachments or [])
    ]
    return MessageOut(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        text_body=msg.text_body,
        is_read=msg.is_read,
        sent_at=msg.sent_at,
        attachments=atts,
    )


@router.post("/", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_or_get_conversation(
    body: ConversationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    if body.recipient_user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")
    other = db.query(User).filter(User.id == body.recipient_user_id).first()
    if not other or other.account_status != AccountStatus.active:
        raise HTTPException(status_code=400, detail="Invalid recipient")
    listing = db.query(Listing).filter(Listing.id == body.listing_id).first()
    if not listing or listing.status != ListingStatus.approved:
        raise HTTPException(status_code=400, detail="Listing not available for messaging")
    a, b = sorted([user.id, body.recipient_user_id])
    existing = (
        db.query(Conversation)
        .filter(
            Conversation.listing_id == body.listing_id,
            Conversation.participant_a_id == a,
            Conversation.participant_b_id == b,
        )
        .first()
    )
    if existing:
        return _conversation_out(db, existing, user.id)
    conv = Conversation(
        listing_id=body.listing_id,
        created_by_user_id=user.id,
        participant_a_id=a,
        participant_b_id=b,
        last_message_at=None,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return _conversation_out(db, conv, user.id)


@router.get("/", response_model=ConversationListResponse)
def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    q = db.query(Conversation).filter(
        or_(
            Conversation.participant_a_id == user.id,
            Conversation.participant_b_id == user.id,
        )
    )
    total = q.count()
    rows = (
        q.order_by(desc(Conversation.last_message_at), desc(Conversation.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [_conversation_out(db, c, user.id) for c in rows]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv or user.id not in (conv.participant_a_id, conv.participant_b_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    q = (
        db.query(Message)
        .options(joinedload(Message.attachments))
        .filter(Message.conversation_id == conversation_id, Message.deleted_at.is_(None))
    )
    total = q.count()
    rows = (
        q.order_by(asc(Message.sent_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    for m in rows:
        if m.sender_id != user.id and not m.is_read:
            m.is_read = True
    db.commit()
    return {
        "items": [_message_to_out(m) for m in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=201)
async def send_message(
    conversation_id: int,
    text: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv or user.id not in (conv.participant_a_id, conv.participant_b_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    file_list = files or []
    if not text and not file_list:
        raise HTTPException(status_code=400, detail="Message must have text or attachment")
    if len(file_list) > settings.MESSAGE_MAX_ATTACHMENTS:
        raise HTTPException(status_code=400, detail="Too many attachments")
    msg = Message(
        conversation_id=conversation_id,
        sender_id=user.id,
        text_body=text,
        is_read=False,
        sent_at=_now(),
    )
    db.add(msg)
    db.flush()
    for file in file_list:
        rel, orig, size, mime = await save_upload_file(
            file,
            subdir=f"messages/{conversation_id}",
            allowed_mime=ALLOWED_MESSAGE,
            max_bytes=settings.MAX_UPLOAD_BYTES,
        )
        att = MessageAttachment(
            message_id=msg.id,
            file_name=rel.split("/")[-1],
            original_name=orig,
            mime_type=mime,
            file_size=size,
            file_path=rel,
        )
        db.add(att)
    conv.last_message_at = _now()
    other = _other_user_id(conv, user.id)
    notify_user(
        db,
        user_id=other,
        notif_type="new_message",
        title="New message",
        body=(text[:200] if text else "Attachment"),
        data={"conversation_id": conversation_id, "listing_id": conv.listing_id},
    )
    db.commit()
    msg = (
        db.query(Message)
        .options(joinedload(Message.attachments))
        .filter(Message.id == msg.id)
        .first()
    )
    return _message_to_out(msg)
