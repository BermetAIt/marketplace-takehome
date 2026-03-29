from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import Base, engine

# Создаем таблицы в БД (если их нет)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Full-Stack Marketplace Platform Backend",
    version="0.1.0"
)

# CORS для Flutter приложения
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замени на конкретные origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Welcome to Marketplace API",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "marketplace-api",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)