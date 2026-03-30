from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.promotion_package import PromotionPackage
from app.schemas.payments import PromotionPackageOut

router = APIRouter(prefix="/promotion-packages", tags=["Promotions"])


@router.get("/", response_model=list[PromotionPackageOut])
def list_packages(db: Session = Depends(get_db)):
    rows = (
        db.query(PromotionPackage)
        .filter(PromotionPackage.is_active.is_(True))
        .order_by(PromotionPackage.id)
        .all()
    )
    return rows
