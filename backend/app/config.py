from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Settings(BaseSettings):
    CORS_ORIGINS: list = [
        "http://localhost:5173",  # Для разработки (React)
        "http://127.0.0.1:5173",
    ]
    
    class Config:
        env_file = ".env"

settings = Settings()