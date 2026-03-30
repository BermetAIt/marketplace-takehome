from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import require_admin, require_moderator_or_admin
from app.db.database import get_db
from app.models.audit_log import AdminAuditLog
from app.models.conversation import Conversation
from app.models.listing import Listing as ListingModel, ListingStatus
from app.models.message import Message
from app.models.payment import Payment
from app.models.report import Report
from app.models.user import AccountStatus, User
from app.models.user_promotion import UserPromotion as UserPromo
from app.services.audit import write_audit_log
from app.services.notifications import notify_user

router = APIRouter(prefix="/admin", tags=["Admin"])


def _now():
    return datetime.now(timezone.utc)


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    def cnt(model, *filters):
        q = db.query(func.count(model.id))
        for f in filters:
            q = q.filter(f)
        return int(q.scalar() or 0)

    users_total = cnt(User)
    users_active = cnt(User, User.account_status == AccountStatus.active)
    users_blocked = cnt(User, User.account_status == AccountStatus.blocked)
    listings_total = cnt(ListingModel)
    listings_pending = cnt(ListingModel, ListingModel.status == ListingStatus.pending_review)
    listings_approved = cnt(ListingModel, ListingModel.status == ListingStatus.approved)
    listings_rejected = cnt(ListingModel, ListingModel.status == ListingStatus.rejected)
    conv_total = cnt(Conversation)
    msg_total = cnt(Message)
    reports_total = cnt(Report)
    pay_total = cnt(Payment)
    revenue = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == "successful"
    ).scalar()
    promos_active = cnt(UserPromo, UserPromo.status == "active")
    return {
        "users_total": users_total,
        "users_active": users_active,
        "users_blocked": users_blocked,
        "listings_total": listings_total,
        "listings_pending": listings_pending,
        "listings_approved": listings_approved,
        "listings_rejected": listings_rejected,
        "conversations_total": conv_total,
        "messages_total": msg_total,
        "reports_total": reports_total,
        "payments_total": pay_total,
        "revenue_promotions": float(revenue or 0),
        "active_promotions": promos_active,
    }


@router.get("/users")
def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    q = db.query(User)
    if search:
        term = f"%{search}%"
        q = q.filter((User.email.ilike(term)) | (User.full_name.ilike(term)))
    total = q.count()
    rows = q.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


@router.patch("/users/{user_id}/status")
def admin_set_user_status(
    user_id: int,
    request: Request,
    account_status: str = Query(..., alias="status"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        u.account_status = AccountStatus(account_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")
    write_audit_log(
        db,
        admin_user_id=admin.id,
        action="user_status_change",
        entity_type="user",
        entity_id=user_id,
        detail={"status": account_status},
        ip_address=request.client.host if request and request.client else None,
    )
    db.commit()
    return {"detail": "ok"}


@router.get("/listings")
def admin_list_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    listing_status: Optional[str] = Query(None, alias="status"),
    category_id: Optional[int] = None,
    city: Optional[str] = None,
    owner_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator_or_admin),
):
    q = db.query(ListingModel)
    if listing_status:
        q = q.filter(ListingModel.status == ListingStatus(listing_status))
    if category_id:
        q = q.filter(ListingModel.category_id == category_id)
    if city:
        q = q.filter(ListingModel.city.ilike(f"%{city}%"))
    if owner_id:
        q = q.filter(ListingModel.owner_id == owner_id)
    total = q.count()
    rows = q.order_by(ListingModel.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


@router.post("/listings/{listing_id}/moderate")
def moderate_listing(
    listing_id: int,
    request: Request,
    action: str = Query(..., pattern="^(approve|reject|archive)$"),
    note: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_moderator_or_admin),
):
    listing = db.query(ListingModel).filter(ListingModel.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Not found")
    owner = db.query(User).filter(User.id == listing.owner_id).first()
    if action == "approve":
        listing.status = ListingStatus.approved
        listing.moderation_note = note
        listing.published_at = _now()
        if owner:
            notify_user(
                db,
                user_id=owner.id,
                notif_type="listing_approved",
                title="Listing approved",
                body="Your listing is now public.",
                data={"listing_id": listing.id},
            )
    elif action == "reject":
        listing.status = ListingStatus.rejected
        listing.moderation_note = note
        if owner:
            notify_user(
                db,
                user_id=owner.id,
                notif_type="listing_rejected",
                title="Listing rejected",
                body=note or "Please review moderation feedback.",
                data={"listing_id": listing.id},
            )
    else:
        listing.status = ListingStatus.archived
        listing.moderation_note = note
    write_audit_log(
        db,
        admin_user_id=admin.id,
        action=f"listing_{action}",
        entity_type="listing",
        entity_id=listing_id,
        detail={"note": note},
        ip_address=request.client.host if request and request.client else None,
    )
    db.commit()
    return {"detail": "ok"}


@router.get("/reports")
def admin_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator_or_admin),
):
    q = db.query(Report)
    if status_filter:
        q = q.filter(Report.status == status_filter)
    total = q.count()
    rows = q.order_by(Report.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


@router.post("/reports/{report_id}/resolve")
def resolve_report(
    report_id: int,
    request: Request,
    resolution: str = Query(..., pattern="^(resolved|dismissed)$"),
    note: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_moderator_or_admin),
):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    r.status = resolution
    r.resolution_note = note
    r.reviewed_by_admin_id = admin.id
    r.reviewed_at = _now()
    notify_user(
        db,
        user_id=r.reporter_user_id,
        notif_type="report_status_changed",
        title=f"Report {resolution}",
        body=note,
        data={"report_id": r.id},
    )
    write_audit_log(
        db,
        admin_user_id=admin.id,
        action="report_resolve",
        entity_type="report",
        entity_id=report_id,
        detail={"resolution": resolution},
        ip_address=request.client.host if request and request.client else None,
    )
    db.commit()
    return {"detail": "ok"}


@router.get("/payments")
def admin_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(Payment)
    if status_filter:
        q = q.filter(Payment.status == status_filter)
    total = q.count()
    rows = q.order_by(Payment.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


@router.get("/conversations")
def admin_list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    listing_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator_or_admin),
):
    q = db.query(Conversation)
    if listing_id:
        q = q.filter(Conversation.listing_id == listing_id)
    total = q.count()
    rows = q.order_by(Conversation.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": rows, "total": total, "page": page, "page_size": page_size}


@router.get("/audit-logs")
def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(AdminAuditLog)
    total = q.count()
    rows = q.order_by(AdminAuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }
