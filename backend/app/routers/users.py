from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.db.database import get_db
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserProfileUpdate, UserResponse
from app.utils.files import ALLOWED_IMAGE, save_upload_file

router = APIRouter(prefix="/users", tags=["Users"])


def _public_avatar_url(rel: str) -> str:
    base = settings.API_PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/uploads/{rel}"


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_active_user)):
    return user


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UserProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    rel, _, _, _ = await save_upload_file(
        file,
        subdir=f"avatars/{user.id}",
        allowed_mime=ALLOWED_IMAGE,
        max_bytes=settings.MAX_UPLOAD_BYTES,
    )
    user.profile_image_url = _public_avatar_url(rel)
    db.commit()
    db.refresh(user)
    return user
