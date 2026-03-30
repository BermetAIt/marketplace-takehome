from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.database import Base, engine
from app.routers import (
    admin,
    attachments,
    auth,
    categories,
    conversations,
    favorites,
    listing_media,
    listings,
    notifications,
    payments,
    promotion_packages,
    public_users,
    reports,
    user_promotions,
    users,
)

Base.metadata.create_all(bind=engine)
settings.upload_path.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    description="Full-Stack Marketplace Platform Backend",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/uploads",
    StaticFiles(directory=str(settings.upload_path)),
    name="uploads",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(public_users.router)
app.include_router(categories.router)
app.include_router(listings.router)
app.include_router(listing_media.router)
app.include_router(favorites.router)
app.include_router(conversations.router)
app.include_router(attachments.router, prefix="/api")
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(payments.router)
app.include_router(promotion_packages.router)
app.include_router(user_promotions.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {
        "message": "Marketplace API",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "marketplace-api",
        "database": "connected",
    }
