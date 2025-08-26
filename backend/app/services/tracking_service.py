from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.tracking import Tracking
from app.models.price_history import PriceHistory
from app.schemas.tracking import TrackingCreate, ParsingResultCreate
from datetime import datetime, timezone

import uuid

def get_or_create_tracking(db: Session, user_id: int, wb_item_id: int, 
                          custom_name: str, desired_price: float) -> Tracking:
    """
    Находит или создает запись в trackings для user_id и wb_item_id
    """
    # Ищем существующую запись
    tracking = db.query(Tracking).filter(
        Tracking.user_id == user_id,
        Tracking.wb_item_id == wb_item_id
    ).first()
    
    if tracking:
        # Обновляем существующую запись
        if custom_name and tracking.custom_name != custom_name:
            tracking.custom_name = custom_name
        if desired_price and tracking.desired_price != desired_price:
            tracking.desired_price = desired_price
        tracking.is_active = True
        
        db.commit()
        db.refresh(tracking)
        return tracking
    
    # Создаем новую запись
    tracking_data = TrackingCreate(
        wb_item_id=wb_item_id,
        custom_name=custom_name,
        desired_price=desired_price,
        is_active=True
    )
    
    tracking = Tracking(
        id=uuid.uuid4(),
        user_id=user_id,
        wb_item_id=tracking_data.wb_item_id,
        custom_name=tracking_data.custom_name,
        desired_price=tracking_data.desired_price,
        min_rating=None,
        min_comment=None,
        is_active=tracking_data.is_active
    )
    
    db.add(tracking)
    db.commit()
    db.refresh(tracking)
    return tracking

def save_price_history(db: Session, tracking_id: uuid.UUID, product_data: dict, wb_code:int):
    """
    Сохраняет данные в price_history
    """
    wb_id = wb_code
    price = product_data.get('price') or product_data.get('salePriceU') or 0
    name = product_data.get('name') or product_data.get('title') or 'Unknown'
    rating = product_data.get('rating') or product_data.get('reviewRating') or 0
    comments = product_data.get('feetback_count') or product_data.get('feedbacks') or 0
    
    price_history = PriceHistory(
        id=uuid.uuid4(),
        tracking_id=tracking_id,
        wb_id=wb_id,
        wb_name=name,
        rating=rating,
        comment_count=comments,
        price=price,
        checked_at=datetime.now(timezone.utc)
    )
    
    db.add(price_history)
    db.commit()
    db.refresh(price_history)
    return price_history

def save_parsing_results(db: Session, parsing_data: ParsingResultCreate, user_id: int):
    """
    - Предполагаем, что results содержит один товар
    - Создаем/обновляем один tracking
    - Сохраняем одну запись в price_history
    """
    if not parsing_data.results:
        return {
            "saved_count": 0,
            "errors": ["No products in results"],
            "total_products": 0
        }
    
    # Берем первый товар из results (предполагаем один товар)
    product = parsing_data.results[0]
    
    try:
        # Извлекаем wb_item_id из товара
        wb_item_id = parsing_data.query
        if not wb_item_id:
            return {
                "saved_count": 0,
                "errors": ["No wb_item_id found in product"],
                "total_products": 1
            }
        
        # Используем кастомное имя или имя из парсинга
        product_name = product.get('name')
        display_name = parsing_data.custom_name or product_name
        
        # 1. Находим или создаем tracking
        tracking = get_or_create_tracking(
            db=db,
            user_id=user_id,
            wb_item_id=wb_item_id,
            custom_name=display_name,
            desired_price=parsing_data.target_price
        )
        
        # 2. Сохраняем данные в price_history
        save_price_history(db, tracking.id, product, wb_item_id)
        
        return {
            "saved_count": 1,
            "errors": [],
            "total_products": 1,
            "tracking_id": tracking.id
        }
        
    except Exception as e:
        return {
            "saved_count": 0,
            "errors": [f"Error: {str(e)}"],
            "total_products": 1
        }


def get_user_trackings(db: Session, user_id: int):
    """Получить все трекинги пользователя"""
    return db.query(Tracking).filter(Tracking.user_id == user_id).all()

def get_tracking_price_history(db: Session, tracking_id: uuid.UUID, user_id: int):
    """Получить историю цен для трекинга"""
    tracking = db.query(Tracking).filter(
        Tracking.id == tracking_id,
        Tracking.user_id == user_id
    ).first()
    
    if not tracking:
        return None
    
    history = db.query(PriceHistory).filter(
        PriceHistory.tracking_id == tracking_id
    ).order_by(PriceHistory.checked_at.desc()).all()
    
    return {
        "tracking": tracking,
        "price_history": history
    }