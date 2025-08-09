from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

# Инициализация приложения FastAPI
app = FastAPI(
    title="WB Wishlist API",
    description="API для отслеживания товаров на Wildberries",
    version="0.1.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Настройка CORS (разрешаем запросы с фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Импорт и подключение роутеров
from .routes import wb_routes, api  # api.py из вашей структуры

app.include_router(api.router, prefix="/api")
app.include_router(wb_routes.router, prefix="/api/wb")

# Тестовый эндпоинт для проверки работы
@app.get("/api/healthcheck")
async def healthcheck():
    return {"status": "ok", "message": "WB Wishlist API работает"}