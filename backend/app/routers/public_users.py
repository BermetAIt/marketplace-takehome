from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.listing import Listing, ListingStatus
from app.models.user import User
from app.schemas.user import PublicUserResponse

router = APIRouter(prefix="/public/users", tags=["Public"])


@router.get("/{user_id}", response_model=PublicUserResponse)
def public_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    count = (
        db.query(func.count(Listing.id))
        .filter(
            Listing.owner_id == user_id,
            Listing.status == ListingStatus.approved,
        )
        .scalar()
    )
    return PublicUserResponse(
        id=user.id,
        full_name=user.full_name,
        profile_image_url=user.profile_image_url,
        city=user.city,
        verified_badge=bool(user.verified_badge),
        created_at=user.created_at,
        active_listings_count=int(count or 0),
    )
