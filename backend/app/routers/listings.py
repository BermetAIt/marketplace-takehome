from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.listing import Listing, ListingStatus
from app.models.user import User
from app.schemas.listing import (
    ListingCreate, ListingUpdate, ListingResponse, ListingListResponse
)
from app.core.security import verify_token

router = APIRouter(prefix="/listings", tags=["Listings"])

# === Получить все объявления (с пагинацией, фильтрами) ===
@router.get("/", response_model=ListingListResponse)
def get_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    status_filter: Optional[str] = Query(None, alias="status"),  # ← переименовал, чтобы не конфликтовало со статусом Python
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Базовый запрос — только одобренные объявления
    query = db.query(Listing).filter(Listing.status == ListingStatus.approved)
    
    # Фильтры
    if category_id:
        query = query.filter(Listing.category_id == category_id)
    if city:
        query = query.filter(Listing.city.ilike(f"%{city}%"))
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    if search:
        query = query.filter(
            (Listing.title.ilike(f"%{search}%")) | 
            (Listing.description.ilike(f"%{search}%"))
        )
    if status_filter:
        query = query.filter(Listing.status == status_filter)
    
    # Пагинация
    total = query.count()
    offset = (page - 1) * page_size
    listings = query.offset(offset).limit(page_size).all()
    
    return {
        "items": listings,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

# === Получить объявление по ID ===
@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Увеличиваем счётчик просмотров
    listing.view_count += 1
    db.commit()
    
    return listing

# === Создать объявление ===
@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
def create_listing(
    listing_data: ListingCreate,  # ← ИСПРАВЛЕНО: двоеточие + правильное имя
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    # Проверка токена
    payload = verify_token(authorization.replace("Bearer ", ""))
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Проверка категории
    from app.models.category import Category
    category = db.query(Category).filter(Category.id == listing_data.category_id).first()
    if not category or not category.is_active:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    # Создание объявления
    new_listing = Listing(
        owner_id=user_id,
        **listing_data.dict(),
        status=ListingStatus.pending_review
    )
    
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    
    return new_listing

# === Обновить объявление (только владелец) ===
@router.put("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    listing_data: ListingUpdate,  
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    # Проверка токена
    payload = verify_token(authorization.replace("Bearer ", ""))
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    
    # Найти объявление
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Проверка: только владелец может редактировать
    if listing.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this listing")
    
    # Обновление полей
    update_data = listing_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(listing, field, value)
    
    # Если изменили важные поля — вернуть на модерацию
    if any(k in update_data for k in ['title', 'description', 'price', 'category_id']):
        if listing.status == ListingStatus.approved:
            listing.status = ListingStatus.pending_review
    
    db.commit()
    db.refresh(listing)
    
    return listing

# === Удалить/Архивировать объявление (только владелец) ===
@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: int,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    # Проверка токена
    payload = verify_token(authorization.replace("Bearer ", ""))
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    
    # Найти объявление
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Проверка: только владелец может удалять
    if listing.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this listing")
    
    # Soft delete — меняем статус на archived
    listing.status = ListingStatus.archived
    db.commit()
    
    return None

# === Получить все объявления владельца ===
@router.get("/owner/{owner_id}", response_model=ListingListResponse)
def get_owner_listings(
    owner_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Listing).filter(
        Listing.owner_id == owner_id,
        Listing.status.in_([ListingStatus.approved, ListingStatus.pending_review])
    )
    
    total = query.count()
    offset = (page - 1) * page_size
    listings = query.offset(offset).limit(page_size).all()
    
    return {
        "items": listings,
        "total": total,
        "page": page,
        "page_size": page_size,  # ← ДОБАВЛЕНО: было пропущено
        "total_pages": (total + page_size - 1) // page_size
    }

# === Получить мои объявления (для владельца) ===
@router.get("/my/listings", response_model=ListingListResponse)
def get_my_listings(
    authorization: str = Header(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Проверка токена
    payload = verify_token(authorization.replace("Bearer ", ""))
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    
    query = db.query(Listing).filter(Listing.owner_id == user_id)
    
    total = query.count()
    offset = (page - 1) * page_size
    listings = query.offset(offset).limit(page_size).all()
    
    return {
        "items": listings,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }