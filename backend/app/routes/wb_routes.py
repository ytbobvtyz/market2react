from fastapi import APIRouter, HTTPException, Request
from app.services.parser_service import ParserService
from async_timeout import timeout
import asyncio
import logging
from app.utils.logger import get_parser_logger

router = APIRouter()
logger = get_parser_logger()

@router.get("/products/{article}")
async def get_product(article: str, request: Request):
    """
    Парсинг товара с Wildberries через изолированный процесс
    """
    # Получаем process_pool из state приложения
    process_pool = request.app.state.process_pool

    try:
        logger.info(f"Parsing product: {article}")
        # Проверяем валидность артикула
        if not article.isdigit() or len(article) < 6:
            raise HTTPException(
                status_code=400, 
                detail="Артикул должен содержать только цифры (минимум 6 символов)"
            )
        
        # Запускаем парсинг в отдельном процессе с таймаутом
        async with timeout(45):
            # Используем ProcessPoolExecutor для изоляции
            data = await asyncio.get_event_loop().run_in_executor(
                process_pool, 
                parse_product_wrapper, 
                article
            )
            logger.info(f"Successfully parsed product: {article}")
            return data
                
    except asyncio.TimeoutError:
        logger.warning(f"Timeout parsing article: {article}")
        raise HTTPException(status_code=408, detail="Parser timeout")
        
    except Exception as e:
        logger.error(f"Error parsing {article}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

def parse_product_wrapper(article: str):
    """
    Обертка для запуска в отдельном процессе
    Каждый процесс создает свой экземпляр ParserService
    """
    try:
        # Создаем новый экземпляр для каждого процесса
        parser_service = ParserService()
        return parser_service.parse_wb_product(article)
    except Exception as e:
        logger.error(f"Error in process for article {article}: {str(e)}")
        raise
