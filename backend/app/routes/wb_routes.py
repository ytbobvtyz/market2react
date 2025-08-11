from fastapi import APIRouter, HTTPException
from app.services.parser_service import ParserService

router = APIRouter()
parser_service = ParserService()

@router.get("/products/{article}")
async def get_product(article: str):  # Можно оставить async (FastAPI поддерживает)
    try:
        data = parser_service.parse_wb_product(article)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))