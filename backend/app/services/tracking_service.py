from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.tracking import Tracking
from app.models.price_history import PriceHistory
from app.schemas.tracking import TrackingCreate, ParsingResultCreate
from datetime import datetime
import uuid

def create_tracking_with_price(db: Session, tracking_data: TrackingCreate, user_id: int, 
                              price: float, wb_name: str, rating: float, comment_count: int):
    """
    Создает запись в trackings и сразу добавляет цену в price_history
    """
    try:
        # Проверяем, существует ли уже tracking для этого товара и пользователя
        existing_tracking = db.query(Tracking).filter(
            Tracking.user_id == user_id,
            Tracking.wb_item_id == tracking_data.wb_item_id
        ).first()
        
        if existing_tracking:
            # Обновляем существующий tracking
            if tracking_data.custom_name:
                existing_tracking.custom_name = tracking_data.custom_name
            if tracking_data.desired_price is not None:
                existing_tracking.desired_price = tracking_data.desired_price
            if tracking_data.min_rating is not None:
                existing_tracking.min_rating = tracking_data.min_rating
            if tracking_data.min_comment is not None:
                existing_tracking.min_comment = tracking_data.min_comment
            existing_tracking.is_active = tracking_data.is_active
            
            tracking = existing_tracking
        else:
            # Создаем новый tracking
            tracking = Tracking(
                id=uuid.uuid4(),
                user_id=user_id,
                wb_item_id=tracking_data.wb_item_id,
                custom_name=tracking_data.custom_name,
                desired_price=tracking_data.desired_price,
                min_rating=tracking_data.min_rating,
                min_comment=tracking_data.min_comment,
                is_active=tracking_data.is_active
            )
            db.add(tracking)
        
        # Создаем запись в price_history
        price_history = PriceHistory(
            id=uuid.uuid4(),
            tracking_id=tracking.id,
            wb_id=tracking_data.wb_item_id,
            wb_name=wb_name,
            rating=rating,
            comment_count=comment_count,
            price=price,
            checked_at=datetime.now(datetime.timezone.utc)
        )
        db.add(price_history)
        
        db.commit()
        db.refresh(tracking)
        db.refresh(price_history)
        
        return tracking
        
    except IntegrityError as e:
        db.rollback()
        raise Exception(f"Database integrity error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise Exception(f"Error creating tracking: {str(e)}")

def save_parsing_results(db: Session, parsing_data: ParsingResultCreate, user_id: int):
    """
    Сохраняет результаты парсинга в trackings и price_history
    """
    saved_count = 0
    errors = []
    print(parsing_data)
    print(parsing_data.target_price)
    for product in parsing_data.results:
        try:
            print(product)
            # Извлекаем данные из продукта 
            wb_item_id = parsing_data.query
            price = product.get('price') or product.get('salePriceU') or 0
            name = product.get('name') or product.get('title') or 'Unknown'
            rating = product.get('rating') or product.get('reviewRating') or 0
            comments = product.get('comments') or product.get('feedbacks') or 0
            
            if not wb_item_id:
                continue
            
            # Создаем tracking данные
            tracking_data = TrackingCreate(
                wb_item_id=wb_item_id,
                custom_name=f"Авто-трекинг: {parsing_data.query}",
                is_active=True
            )
            
            # Сохраняем в базу
            create_tracking_with_price(
                db=db,
                tracking_data=tracking_data,
                user_id=user_id,
                price=price,
                wb_name=name,
                rating=rating,
                comment_count=comments
            )
            
            saved_count += 1
            
        except Exception as e:
            errors.append(f"Product {product.get('id', 'unknown')}: {str(e)}")
    
    return {
        "saved_count": saved_count,
        "errors": errors,
        "total_products": len(parsing_data.results)
    }