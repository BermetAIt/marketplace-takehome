import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification


def notify_user(
    db: Session,
    *,
    user_id: int,
    notif_type: str,
    title: str,
    body: Optional[str] = None,
    data: Optional[dict[str, Any]] = None,
) -> Notification:
    n = Notification(
        user_id=user_id,
        notification_type=notif_type,
        title=title,
        body=body,
        data_json=json.dumps(data) if data else None,
        is_read=False,
    )
    db.add(n)
    return n
