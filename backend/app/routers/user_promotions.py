from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.models.user_promotion import UserPromotion
from app.schemas.payments import UserPromotionOut

router = APIRouter(prefix="/user-promotions", tags=["Promotions"])


@router.get("/me", response_model=list[UserPromotionOut])
def my_promotions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    rows = (
        db.query(UserPromotion)
        .filter(UserPromotion.user_id == user.id)
        .order_by(UserPromotion.id.desc())
        .all()
    )
    return rows
