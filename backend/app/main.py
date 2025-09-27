import sys
print(sys.path)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import concurrent.futures
import logging
import time
import os
from datetime import datetime
from pathlib import Path

from app.routes.wb_routes import router as wb_router
from app.routes.auth import router as auth_router
from app.routes.oauth import router as oauth_router
from app.routes.tracking import router as tracking_router
from app.routes.otp import router as otp_router
from app.routes.telegram import router as telegram_router
from app.routes.telegram_auth import router as telegram_auth_router

from app.database import engine
from app.models import user, tracking as tracking_models, price_history

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan менеджер для управления жизненным циклом приложения
    """
    global process_pool
    
    # === STARTUP LOGIC === 
    logger.info("Starting application...")
    
    # Создаем таблицы БД
    logger.info("Creating database tables...")
    user.Base.metadata.create_all(bind=engine)
    tracking_models.Base.metadata.create_all(bind=engine)
    price_history.Base.metadata.create_all(bind=engine)
    
    # Инициализируем Process Pool Executor для Selenium
    logger.info("Initializing Process Pool Executor...")
    process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=2)
    app.state.process_pool = process_pool
    
    logger.info("✅ Telegram bot: Run separately with 'python run_bot.py'")
    logger.info("✅ Application startup completed")
    
    yield  # Приложение работает здесь
    
    # === SHUTDOWN LOGIC ===
    logger.info("Shutting down application...")
    
    # Завершаем Process Pool Executor
    if process_pool:
        logger.info("Shutting down Process Pool Executor...")
        process_pool.shutdown(wait=False)
    
    logger.info("✅ Application shutdown completed")

# Создаем приложение с современным lifespan
app = FastAPI(
    title="Market2React API", 
    description="API для отслеживания цен Wildberries",
    version="1.0.0",
    lifespan=lifespan
)

# Мидлварь для логирования всех запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Логируем входящий запрос
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"→ {request.method} {request.url.path} | IP: {client_ip} | Query: {dict(request.query_params)}")
    
    try:
        response = await call_next(request)
        
        # Логируем ответ
        process_time = time.time() - start_time
        logger.info(f"← {response.status_code} | Time: {process_time:.3f}s | Size: {response.headers.get('content-length', '0')}b")
        
        return response
        
    except Exception as e:
        # Логируем ошибки
        process_time = time.time() - start_time
        logger.error(f"✗ ERROR: {str(e)} | Time: {process_time:.3f}s")
        raise

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

# Подключаем роутеры
app.include_router(wb_router, prefix="/api")
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(tracking_router, prefix="/api")
app.include_router(otp_router)
app.include_router(telegram_router)
app.include_router(telegram_auth_router)

@app.get("/")
def read_root():
    return {"message": "Market2React API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {
        "status": "ok", 
        "message": "API is running",
        "timestamp": datetime.utcnow().isoformat()
    }

# Эндпоинт для просмотра логов
@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """
    Просмотр последних логов
    """
    try:
        log_file = Path(__file__).parent.parent / 'logs' / 'app.log'
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-limit:]
            return {"logs": lines}
        else:
            return {"error": "Log file not found"}
    except Exception as e:
        return {"error": str(e)}

# Эндпоинт для проверки работы парсера
@app.get("/api/test/parser/{item_id}")
async def test_parser(item_id: int):
    """Тестовый эндпоинт для проверки парсера"""
    from app.services.wb.selenium_parser import WBSeleniumParser
    
    try:
        parser = WBSeleniumParser()
        result = await parser.parse_item(item_id)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
