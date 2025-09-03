from fastapi import APIRouter, HTTPException
from app.services.parser_service import ParserService
from async_timeout import timeout
import asyncio
import logging

router = APIRouter()
parser_service = ParserService()
logger = logging.getLogger(__name__)

@router.get("/products/{article}")
async def get_product(article: str):
    """
    Парсинг товара с Wildberries через изолированный процесс
    """
    try:
        # Проверяем валидность артикула
        if not article.isdigit() or len(article) < 6:
            raise HTTPException(
                status_code=400, 
                detail="Артикул должен содержать только цифры (минимум 6 символов)"
            )
        
        # Запускаем парсинг в отдельном процессе
        async with timeout(45):
            # Используем run_in_executor для изоляции
            data = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: parser_service.parse_wb_product(article)
            )
            
            return data
                
    except asyncio.TimeoutError:
        logger.warning(f"Timeout parsing article: {article}")
        raise HTTPException(status_code=408, detail="Parser timeout")
        
    except Exception as e:
        logger.error(f"Error parsing {article}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))