import sys
print(sys.path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import concurrent.futures
import logging

from app.routes.wb_routes import router as wb_router
from app.routes.auth import router as auth_router
from app.routes.tracking import router as tracking_router
from app.database import engine
from app.models import user, tracking as tracking_models, price_history

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для Process Pool Executor
process_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan менеджер для управления жизненным циклом приложения
    """
    global process_pool
    
    # Startup логика
    logger.info("Starting application...")
    
    # Создаем таблицы БД
    logger.info("Creating database tables...")
    user.Base.metadata.create_all(bind=engine)
    tracking_models.Base.metadata.create_all(bind=engine)
    price_history.Base.metadata.create_all(bind=engine)
    
    # Инициализируем Process Pool Executor для Selenium
    logger.info("Initializing Process Pool Executor...")
    process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=2)
    
    yield
    
    # Shutdown логика
    logger.info("Shutting down application...")
    
    # Завершаем Process Pool Executor
    if process_pool:
        logger.info("Shutting down Process Pool Executor...")
        process_pool.shutdown(wait=False)
    
    logger.info("Application shutdown completed")

# Создаем приложение с lifespan
app = FastAPI(
    title="Market2React API", 
    version="1.0.0",
    lifespan=lifespan
)

# Сохраняем process_pool в state приложения для доступа из роутеров
app.state.process_pool = process_pool

# CORS настройки 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://wblist.ru",
        "https://wblist.ru", 
        "http://localhost:5173",
        "http://localhost:8000",
        "http://147.45.102.68",
        "http://localhost:3000"
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры (сохраняем вашу текущую структуру)
app.include_router(wb_router, prefix="/api")
app.include_router(auth_router)
app.include_router(tracking_router, prefix="/api", tags=["tracking"])




@app.get("/")
def read_root():
    return {"message": "Market2React API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}

@app.get("/debug/env")
async def debug_env():
    import os, sys, subprocess
    return {
        "python_executable": sys.executable,
        "python_path": sys.path,
        "current_directory": os.getcwd(),
        "environment_variables": {k: v for k, v in os.environ.items() if any(x in k.lower() for x in ['path', 'python', 'home', 'user'])},
        "process_user": subprocess.run(['whoami'], capture_output=True, text=True).stdout.strip(),
        "selenium_test": subprocess.run([sys.executable, '-c', 'from selenium import webdriver; print("Selenium import OK")'], capture_output=True, text=True).stdout
    }