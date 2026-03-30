from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.db.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.message_attachment import MessageAttachment
from app.models.user import User

router = APIRouter(prefix="/attachments", tags=["Attachments"])


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    att = db.query(MessageAttachment).filter(MessageAttachment.id == attachment_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Not found")
    msg = db.query(Message).filter(Message.id == att.message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Not found")
    conv = db.query(Conversation).filter(Conversation.id == msg.conversation_id).first()
    if not conv or user.id not in (conv.participant_a_id, conv.participant_b_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    path = settings.upload_path / att.file_path
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File missing")
    return FileResponse(
        path,
        filename=att.original_name,
        media_type=att.mime_type or "application/octet-stream",
    )
