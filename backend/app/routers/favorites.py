from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_active_user
from app.db.database import get_db
from app.models.favorite import Favorite
from app.models.listing import Listing
from app.models.user import User
from app.schemas.listing import ListingListResponse

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("/", response_model=ListingListResponse)
def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    q = (
        db.query(Listing)
        .join(Favorite, Favorite.listing_id == Listing.id)
        .filter(Favorite.user_id == user.id)
    )
    total = q.count()
    offset = (page - 1) * page_size
    items = (
        q.order_by(Favorite.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .options(joinedload(Listing.images))
        .all()
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


@router.post("/{listing_id}", status_code=status.HTTP_201_CREATED)
def add_favorite(
    listing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    exists = (
        db.query(Favorite)
        .filter(Favorite.user_id == user.id, Favorite.listing_id == listing_id)
        .first()
    )
    if exists:
        return {"detail": "Already in favorites"}
    db.add(Favorite(user_id=user.id, listing_id=listing_id))
    db.commit()
    return {"detail": "Added"}


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    listing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    fav = (
        db.query(Favorite)
        .filter(Favorite.user_id == user.id, Favorite.listing_id == listing_id)
        .first()
    )
    if fav:
        db.delete(fav)
        db.commit()
    return None
