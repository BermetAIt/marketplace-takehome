import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.db.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notifications import NotificationListResponse, NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _to_out(n: Notification) -> NotificationOut:
    data: Optional[dict[str, Any]] = None
    if n.data_json:
        try:
            data = json.loads(n.data_json)
        except json.JSONDecodeError:
            data = None
    return NotificationOut(
        id=n.id,
        notification_type=n.notification_type,
        title=n.title,
        body=n.body,
        data=data,
        is_read=n.is_read,
        created_at=n.created_at,
    )


@router.get("/", response_model=NotificationListResponse)
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        q = q.filter(Notification.is_read.is_(False))
    total = q.count()
    unread_total = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.is_read.is_(False))
        .count()
    )
    rows = (
        q.order_by(desc(Notification.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [_to_out(x) for x in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
        "unread_total": unread_total,
    }


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    n = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user.id)
        .first()
    )
    if not n:
        raise HTTPException(status_code=404, detail="Not found")
    n.is_read = True
    db.commit()
    db.refresh(n)
    return _to_out(n)


@router.post("/read-all", status_code=204)
def mark_all_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read.is_(False)
    ).update({"is_read": True})
    db.commit()
    return None
