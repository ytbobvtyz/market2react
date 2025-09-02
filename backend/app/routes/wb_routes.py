from fastapi import APIRouter, HTTPException
from app.services.parser_service import ParserService
from async_timeout import timeout
import asyncio

router = APIRouter()
parser_service = ParserService()

@router.get("/products/{article}")
async def get_product(article: str):
    try:
        async with timeout(30):  # 30 секунд таймаут
            data = await asyncio.get_event_loop().run_in_executor(
                None, parser_service.parse_wb_product, article
            )
            return data
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Parser timeout")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))