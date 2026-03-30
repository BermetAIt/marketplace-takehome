from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.db.database import get_db
from app.models.listing import Listing, ListingStatus
from app.models.listing_image import ListingImage
from app.models.user import User
from app.schemas.listing import ListingImageResponse, ListingResponse
from app.utils.files import ALLOWED_IMAGE, save_upload_file

router = APIRouter(prefix="/listings", tags=["Listing media"])


def _public_url(rel: str) -> str:
    base = settings.API_PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/uploads/{rel}"


@router.post(
    "/{listing_id}/images",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_listing_images(
    listing_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing or listing.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Listing not found")
    current = db.query(ListingImage).filter(ListingImage.listing_id == listing_id).count()
    if current + len(files) > settings.LISTING_MAX_IMAGES:
        raise HTTPException(status_code=400, detail="Too many images")
    max_order = (
        db.query(ListingImage.display_order)
        .filter(ListingImage.listing_id == listing_id)
        .order_by(ListingImage.display_order.desc())
        .first()
    )
    order_base = (max_order[0] if max_order else -1) + 1
    for i, file in enumerate(files):
        rel, _, _, _ = await save_upload_file(
            file,
            subdir=f"listings/{listing_id}",
            allowed_mime=ALLOWED_IMAGE,
            max_bytes=settings.MAX_UPLOAD_BYTES,
        )
        url = _public_url(rel)
        img = ListingImage(
            listing_id=listing_id,
            image_url=url,
            display_order=order_base + i,
            is_primary=(current == 0 and i == 0),
        )
        db.add(img)
    if listing.status == ListingStatus.approved:
        listing.status = ListingStatus.pending_review
    db.commit()
    listing = (
        db.query(Listing)
        .options(joinedload(Listing.images))
        .filter(Listing.id == listing_id)
        .first()
    )
    return listing


@router.delete("/{listing_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing_image(
    listing_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing or listing.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Listing not found")
    img = (
        db.query(ListingImage)
        .filter(ListingImage.id == image_id, ListingImage.listing_id == listing_id)
        .first()
    )
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    db.delete(img)
    db.commit()
    return None


@router.patch("/{listing_id}/images/{image_id}/primary", response_model=ListingImageResponse)
def set_primary_image(
    listing_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing or listing.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Listing not found")
    imgs = db.query(ListingImage).filter(ListingImage.listing_id == listing_id).all()
    target = next((x for x in imgs if x.id == image_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Image not found")
    for x in imgs:
        x.is_primary = x.id == image_id
    db.commit()
    db.refresh(target)
    return target
