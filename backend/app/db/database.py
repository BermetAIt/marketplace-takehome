from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Создаем движок подключения к БД
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Показывать SQL запросы в режиме отладки
    pool_pre_ping=True,   # Проверка подключения
    pool_recycle=3600     # Переподключение каждые 1 час
)

# Сессия для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()