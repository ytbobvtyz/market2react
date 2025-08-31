import sys
print(sys.path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.wb_routes import router as wb_router
from app.routes.auth import router as auth_router
from app.routes.tracking import router as tracking_router
from app.database import engine
from app.models import user, tracking as tracking_models, price_history

# Создаем таблицы
user.Base.metadata.create_all(bind=engine)
tracking_models.Base.metadata.create_all(bind=engine)
price_history.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS настройки для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://wblist.ru",
        "https://wblist.ru", 
        "http://localhost:5173",
        "http://localhost:8000"
        "http://147.45.102.68",
        "http://localhost:3000"
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры (сохраняем вашу текущую структуру)
app.include_router(wb_router)
app.include_router(auth_router)
app.include_router(tracking_router, prefix="/api/v1", tags=["tracking"])




@app.get("/")
def read_root():
    return {"message": "Market2React API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}