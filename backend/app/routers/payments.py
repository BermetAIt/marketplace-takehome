from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.db.database import get_db
from app.models.listing import Listing, ListingStatus
from app.models.payment import Payment
from app.models.promotion_package import PromotionPackage
from app.models.user import User
from app.models.user_promotion import UserPromotion
from app.schemas.payments import PaymentInitiate, PaymentListResponse, PaymentOut, WalletTopUpMock
from app.services.notifications import notify_user
from app.models.wallet_transaction import WalletTransaction

router = APIRouter(prefix="/payments", tags=["Payments"])


def _now():
    return datetime.now(timezone.utc)


@router.post("/initiate", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def initiate_payment(
    body: PaymentInitiate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    listing = db.query(Listing).filter(Listing.id == body.listing_id).first()
    if not listing or listing.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != ListingStatus.approved:
        raise HTTPException(status_code=400, detail="Only approved listings can be promoted")
    pkg = (
        db.query(PromotionPackage)
        .filter(PromotionPackage.id == body.promotion_package_id, PromotionPackage.is_active.is_(True))
        .first()
    )
    if not pkg:
        raise HTTPException(status_code=400, detail="Invalid promotion package")
    amount = Decimal(str(pkg.base_price))
    pay = Payment(
        user_id=user.id,
        listing_id=listing.id,
        promotion_package_id=pkg.id,
        amount=amount,
        currency=pkg.currency,
        status="pending",
        payment_provider="mock",
        provider_reference=None,
    )
    db.add(pay)
    db.flush()
    up = UserPromotion(
        user_id=user.id,
        listing_id=listing.id,
        promotion_package_id=pkg.id,
        payment_id=pay.id,
        promotion_type=pkg.promotion_type,
        target_city=body.target_city,
        target_category_id=body.target_category_id,
        status="pending_payment",
        purchased_price=amount,
    )
    db.add(up)
    db.commit()
    db.refresh(pay)
    return pay


@router.post("/{payment_id}/mock-confirm", response_model=PaymentOut)
def mock_confirm(
    payment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    pay = db.query(Payment).filter(Payment.id == payment_id).first()
    if not pay or pay.user_id != user.id:
        raise HTTPException(status_code=404, detail="Payment not found")
    if pay.status != "pending":
        raise HTTPException(status_code=400, detail="Payment not pending")
    pay.status = "successful"
    pay.paid_at = _now()
    pay.provider_reference = f"mock_{payment_id}_{int(_now().timestamp())}"
    up = db.query(UserPromotion).filter(UserPromotion.payment_id == pay.id).first()
    if up:
        pkg = db.query(PromotionPackage).filter(PromotionPackage.id == up.promotion_package_id).first()
        dur = timedelta(days=pkg.duration_days if pkg else 7)
        up.status = "active"
        up.starts_at = _now()
        up.ends_at = _now() + dur
        listing = db.query(Listing).filter(Listing.id == up.listing_id).first()
        if listing:
            listing.is_promoted = True
            if pkg and pkg.promotion_type == "featured":
                listing.is_featured = True
    notify_user(
        db,
        user_id=user.id,
        notif_type="payment_successful",
        title="Payment successful",
        body="Your promotion is active.",
        data={"payment_id": pay.id},
    )
    if up:
        notify_user(
            db,
            user_id=user.id,
            notif_type="promotion_activated",
            title="Promotion activated",
            body="Your listing promotion is now active.",
            data={"user_promotion_id": up.id, "listing_id": up.listing_id},
        )
    db.commit()
    db.refresh(pay)
    return pay


@router.get("/me", response_model=PaymentListResponse)
def my_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    q = db.query(Payment).filter(Payment.user_id == user.id)
    total = q.count()
    rows = (
        q.order_by(Payment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


@router.post("/wallet/mock-topup", status_code=status.HTTP_200_OK)
def wallet_mock_topup(
    body: WalletTopUpMock,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    amt = body.amount
    bal = user.wallet_balance or Decimal("0")
    new_bal = bal + amt
    user.wallet_balance = new_bal
    db.add(
        WalletTransaction(
            user_id=user.id,
            amount=amt,
            currency="USD",
            balance_after=new_bal,
            reference_type="mock_topup",
            note="Mock wallet top-up",
        )
    )
    db.commit()
    return {"balance": str(new_bal)}
