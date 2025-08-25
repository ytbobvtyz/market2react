from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Создаем Base здесь
Base = declarative_base()

# Создаем engine с настройками
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # True для отладки SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Функция для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()