import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AdminAuditLog


def write_audit_log(
    db: Session,
    *,
    admin_user_id: int,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    detail: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> None:
    row = AdminAuditLog(
        admin_user_id=admin_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail_json=json.dumps(detail) if detail else None,
        ip_address=ip_address,
    )
    db.add(row)
