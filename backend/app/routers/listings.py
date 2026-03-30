from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_active_user, get_current_user_optional
from app.db.database import get_db
from app.models.category import Category
from app.models.listing import Listing, ListingStatus
from app.models.user import AccountStatus, User
from app.schemas.listing import (
    ListingCreate,
    ListingListResponse,
    ListingResponse,
    ListingSort,
    ListingUpdate,
)
from app.services.listing_rules import assert_owner_can_set_status

router = APIRouter(prefix="/listings", tags=["Listings"])


def _apply_sort(q, sort: ListingSort):
    if sort == ListingSort.newest:
        return q.order_by(desc(Listing.created_at))
    if sort == ListingSort.oldest:
        return q.order_by(asc(Listing.created_at))
    if sort == ListingSort.price_asc:
        return q.order_by(asc(Listing.price))
    if sort == ListingSort.price_desc:
        return q.order_by(desc(Listing.price))
    if sort == ListingSort.promoted_first:
        return q.order_by(desc(Listing.is_promoted), desc(Listing.created_at))
    if sort == ListingSort.most_viewed:
        return q.order_by(desc(Listing.view_count), desc(Listing.created_at))
    return q.order_by(desc(Listing.created_at))


def _listing_to_response(listing: Listing) -> ListingResponse:
    return ListingResponse.model_validate(listing)


@router.get("/", response_model=ListingListResponse)
def browse_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    sort: ListingSort = ListingSort.newest,
    db: Session = Depends(get_db),
):
    q = db.query(Listing).filter(Listing.status == ListingStatus.approved)
    if category_id:
        q = q.filter(Listing.category_id == category_id)
    if city:
        q = q.filter(Listing.city.ilike(f"%{city}%"))
    if min_price is not None:
        q = q.filter(Listing.price >= min_price)
    if max_price is not None:
        q = q.filter(Listing.price <= max_price)
    if search:
        term = f"%{search}%"
        q = q.filter(
            or_(Listing.title.ilike(term), Listing.description.ilike(term))
        )
    total = q.count()
    q = _apply_sort(q, sort)
    offset = (page - 1) * page_size
    items = q.offset(offset).limit(page_size).options(joinedload(Listing.images)).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


@router.get("/me", response_model=ListingListResponse)
def my_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: ListingSort = ListingSort.newest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    q = db.query(Listing).filter(Listing.owner_id == user.id)
    total = q.count()
    q = _apply_sort(q, sort)
    offset = (page - 1) * page_size
    items = q.offset(offset).limit(page_size).options(joinedload(Listing.images)).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


@router.get("/owner/{owner_id}", response_model=ListingListResponse)
def owner_public_listings(
    owner_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: ListingSort = ListingSort.newest,
    db: Session = Depends(get_db),
):
    q = db.query(Listing).filter(
        Listing.owner_id == owner_id,
        Listing.status == ListingStatus.approved,
    )
    total = q.count()
    q = _apply_sort(q, sort)
    offset = (page - 1) * page_size
    items = q.offset(offset).limit(page_size).options(joinedload(Listing.images)).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    viewer: Optional[User] = Depends(get_current_user_optional),
):
    listing = (
        db.query(Listing)
        .options(joinedload(Listing.images))
        .filter(Listing.id == listing_id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    is_owner = viewer and viewer.id == listing.owner_id
    if listing.status != ListingStatus.approved and not is_owner:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status == ListingStatus.approved or is_owner:
        listing.view_count = (listing.view_count or 0) + 1
        db.commit()
        db.refresh(listing)
    return listing


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
def create_listing(
    listing_data: ListingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    if user.account_status != AccountStatus.active:
        raise HTTPException(status_code=403, detail="Account restricted")
    cat = db.query(Category).filter(Category.id == listing_data.category_id).first()
    if not cat or not cat.is_active:
        raise HTTPException(status_code=400, detail="Invalid category")
    initial = ListingStatus(listing_data.initial_status.value)
    if initial not in (ListingStatus.draft, ListingStatus.pending_review):
        raise HTTPException(status_code=400, detail="Invalid initial status")
    payload = listing_data.model_dump(exclude={"initial_status"})
    new_listing = Listing(owner_id=user.id, **payload, status=initial)
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    return new_listing


@router.put("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    listing_data: ListingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    update_data = listing_data.model_dump(exclude_unset=True)
    new_status = update_data.pop("status", None)
    if "category_id" in update_data:
        cat = db.query(Category).filter(Category.id == update_data["category_id"]).first()
        if not cat or not cat.is_active:
            raise HTTPException(status_code=400, detail="Invalid category")
    for field, value in update_data.items():
        setattr(listing, field, value)
    if new_status:
        assert_owner_can_set_status(listing, ListingStatus(new_status.value), is_admin=False)
        listing.status = ListingStatus(new_status.value)
    elif any(
        k in update_data
        for k in ("title", "description", "price", "category_id", "attributes")
    ):
        if listing.status == ListingStatus.approved:
            listing.status = ListingStatus.pending_review
    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    listing.status = ListingStatus.archived
    db.commit()
    return None
