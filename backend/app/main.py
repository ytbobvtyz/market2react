import sys
print(sys.path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.wb_routes import router as wb_router
from .routes.auth import router as auth_router
from .routes.tracking import router as tracking_router

app = FastAPI()
app.include_router(wb_router)
app.include_router(auth_router)
app.include_router(tracking_router, prefix="/api/v1", tags=["tracking"])

# CORS настройки для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Market2React API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}