from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).filter(Category.is_active == True).order_by(Category.display_order).all()
    return categories

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category