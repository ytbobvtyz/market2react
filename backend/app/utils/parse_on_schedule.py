import asyncio
import sys
import os
from datetime import datetime
from typing import List

# Добавляем путь к проекту в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.tracking import Tracking
from app.models.price_history import PriceHistory
from app.models.user import User
from app.services.parser_service import ParserService
from app.utils.logger import get_schedule_logger

# Настройка логгера
logger = get_schedule_logger()

async def parse_all_active_trackings():
    """
    Парсит все активные отслеживания и сохраняет результаты в базу
    """
    db: Session = SessionLocal()
    try:
        # Получаем все активные отслеживания
        active_trackings = db.query(Tracking).filter(
            Tracking.is_active == True
        ).all()
        
        logger.info(f"Найдено {len(active_trackings)} активных отслеживаний для парсинга")
        
        # Парсим каждое отслеживание
        for tracking in active_trackings:
            try:
                await parse_single_tracking(tracking, db)
                # Небольшая задержка чтобы не нагружать WB
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Ошибка при парсинге отслеживания {tracking.id}: {str(e)}")
                continue
        
    except Exception as e:
        logger.error(f"Ошибка в основном цикле парсинга: {str(e)}")
    finally:
        db.close()

async def parse_single_tracking(tracking: Tracking, db: Session):
    """
    Парсит одно отслеживание и сохраняет результат
    """
    try:
        # Получаем парсер
        parser_service = ParserService()
        result = parser_service.parse_wb_product(tracking.wb_item_id)
        
        if not result:
            logger.warning(f"Не удалось получить данные для артикула {tracking.wb_item_id}")
            return
        
        # Сохраняем результат в историю цен
        price_history = PriceHistory(
            tracking_id=tracking.id,
            wb_id=tracking.wb_item_id,
            wb_name=result['name'],
            rating=result.get('rating'),
            comment_count=result.get('feedback_count'),
            price=result['price'],
            checked_at=datetime.now()
        )
    
        db.add(price_history)
        db.commit()
        logger.info(f"Успешно сохранена запись для отслеживания {tracking.id}")
        
        # Проверяем достижение целевой цены
        await check_target_price_reached(tracking, result, db)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при парсинге артикула {tracking.wb_item_id}: {str(e)}")
        raise

async def check_target_price_reached(tracking: Tracking, result: dict, db: Session):
    """
    Проверяет достижение целевой цены и отправляет уведомления
    """
    try:
        if result['price'] <= tracking.desired_price:
            logger.info(f"Целевая цена достигнута для отслеживания {tracking.id}: {result['price']} <= {tracking.desired_price}")
            
            # TODO: Реализовать отправку уведомления
            # await send_notification(tracking.user_id, tracking, result['price'])
            
    except Exception as e:
        logger.error(f"Ошибка при проверке целевой цены: {str(e)}")

def run_scheduled_parsing():
    """
    Функция для запуска из cron
    """
    asyncio.run(parse_all_active_trackings())

if __name__ == "__main__":
    run_scheduled_parsing()