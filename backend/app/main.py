import sys
print(sys.path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.wb_routes import router as wb_router


app = FastAPI()
app.include_router(wb_router)

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