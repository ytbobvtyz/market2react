from fastapi import APIRouter, HTTPException, Request
from app.services.parser_service import ParserService
from async_timeout import timeout
import asyncio
import sys
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
                parse_via_subprocess, 
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
    
def parse_via_subprocess(article: str) -> dict:
    """
    Запуск парсинга через отдельный процесс
    """
    import subprocess
    import json
    import os
    from pathlib import Path
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting subprocess for article: {article}")
        
        # Загружаем .env
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
        
        # Получаем путь из .env
        PROJECT_ROOT = os.getenv('PROJECT_ROOT', '/var/www/market2react/market2react')
        script_path = os.path.join(PROJECT_ROOT, "backend", "app", "utils", "isolated_parser.py")
        
        logger.info(f"Project root: {PROJECT_ROOT}")
        logger.info(f"Script path: {script_path}")
        
        if not os.path.exists(script_path):
            raise Exception(f"Parser script not found: {script_path}")
        
        # Запускаем процесс
        result = subprocess.run([
            sys.executable, 
            script_path,
            article
        ], 
        capture_output=True, 
        text=True,
        timeout=120,
        cwd=PROJECT_ROOT
        )
        
        logger.info(f"Subprocess return code: {result.returncode}")

        # Ищем JSON в выводе (последняя строка)
        output_lines = result.stdout.strip().split('\n')
        json_output = output_lines[-1] if output_lines else ""

        logger.info(f"JSON output: {repr(json_output)}")

        if result.returncode == 0 and json_output.strip():
            try:
                return json.loads(json_output)
            except json.JSONDecodeError:
                # Если последняя строка не JSON, ищем любую JSON строку в выводе
                for line in reversed(output_lines):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            return json.loads(line)
                        except json.JSONDecodeError:
                            continue
                raise Exception("No valid JSON found in output")
        else:
            error_msg = f"Subprocess failed: {result.stderr}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        logger.error(f"Subprocess error: {str(e)}")
        raise