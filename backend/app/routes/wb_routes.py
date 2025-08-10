from fastapi import APIRouter, HTTPException
from app.services.parser_services import ParserService

router = APIRouter()
parser = ParserService()

@router.get("/products/{article}")
async def get_product(article: str):
    try:
        return parser.parse_wb_product(article)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))