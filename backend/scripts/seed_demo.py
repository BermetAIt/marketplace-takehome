"""
Seed demo data: admin user, categories, promotion packages.
Run from backend root: python -m scripts.seed_demo
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.models  # noqa: F401
from decimal import Decimal

from app.db.database import SessionLocal
from app.models.enums import UserRole
from app.models.promotion_package import PromotionPackage
from app.models.category import Category
from app.models.user import AccountStatus, User
from app.core.security import get_password_hash


def main():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                email="admin@example.com",
                full_name="Demo Admin",
                password_hash=get_password_hash("Admin12345!"),
                account_status=AccountStatus.active,
                role=UserRole.admin,
                preferred_language="en",
            )
            db.add(admin)
            db.commit()
            print("Created admin@example.com / Admin12345!")
        else:
            print("Admin user already exists")

        if db.query(Category).count() == 0:
            cats = [
                Category(
                    name="Electronics",
                    slug="electronics",
                    display_order=1,
                    attribute_schema={"brand": "string", "condition": "string"},
                ),
                Category(
                    name="Vehicles",
                    slug="vehicles",
                    display_order=2,
                    attribute_schema={
                        "brand": "string",
                        "year": "number",
                        "mileage": "number",
                    },
                ),
                Category(
                    name="Real Estate",
                    slug="real-estate",
                    display_order=3,
                    attribute_schema={"rooms": "number", "area_sqm": "number"},
                ),
            ]
            for c in cats:
                db.add(c)
            db.commit()
            print("Seeded categories")
        else:
            print("Categories already present")

        if db.query(PromotionPackage).count() == 0:
            pkgs = [
                PromotionPackage(
                    code="boost_7d",
                    title_en="Boost 7 days",
                    title_ru="Буст 7 дней",
                    promotion_type="boost",
                    base_price=Decimal("9.99"),
                    duration_days=7,
                ),
                PromotionPackage(
                    code="featured_14d",
                    title_en="Featured 14 days",
                    title_ru="В топе 14 дней",
                    promotion_type="featured",
                    base_price=Decimal("19.99"),
                    duration_days=14,
                ),
                PromotionPackage(
                    code="city_target_7d",
                    title_en="City targeting 7 days",
                    title_ru="Таргет по городу 7 дней",
                    promotion_type="city_target",
                    base_price=Decimal("14.99"),
                    duration_days=7,
                ),
            ]
            for p in pkgs:
                db.add(p)
            db.commit()
            print("Seeded promotion packages")
        else:
            print("Promotion packages already present")
    finally:
        db.close()


if __name__ == "__main__":
    main()
