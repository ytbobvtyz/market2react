from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.tracking import Tracking
from app.schemas.tracking import TrackingCreate
import os
from ..utils.auth import create_access_token

router = APIRouter(prefix="/api/trackings", tags=["trackings"])

@router.post("/")
async def create_tracking_from_telegram(tracking_data: dict, db: Session = Depends(get_db)):
    """Создание отслеживания из Telegram"""
    try:
        telegram_id = tracking_data.get('telegram_id')
        
        if not telegram_id:
            raise HTTPException(status_code=400, detail="Telegram ID is required")
        
        # Находим пользователя по telegram_id
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found. Please authorize first.")
        
        # Проверяем лимиты отслеживаний
        active_trackings = db.query(Tracking).filter(
            Tracking.user_id == user.id,
            Tracking.is_active == True
        ).count()
        
        max_trackings = 20 if user.subscription_tier == "premium" else 3
        if active_trackings >= max_trackings:
            raise HTTPException(
                status_code=400, 
                detail=f"Limit exceeded. Maximum {max_trackings} active trackings allowed."
            )
        
        # Проверяем, не отслеживается ли уже этот товар
        existing_tracking = db.query(Tracking).filter(
            Tracking.user_id == user.id,
            Tracking.wb_item_id == tracking_data['wb_item_id'],
            Tracking.is_active == True
        ).first()
        
        if existing_tracking:
            raise HTTPException(status_code=400, detail="This item is already being tracked")
        
        # Создаем отслеживание
        tracking = Tracking(
            user_id=user.id,
            wb_item_id=tracking_data['wb_item_id'],
            desired_price=tracking_data['desired_price'],
            custom_name=tracking_data.get('custom_name', f"Товар {tracking_data['wb_item_id']}"),
            is_active=True
        )
        
        db.add(tracking)
        db.commit()
        db.refresh(tracking)
        
        return {
            "id": tracking.id,
            "wb_item_id": tracking.wb_item_id,
            "custom_name": tracking.custom_name,
            "desired_price": tracking.desired_price,
            "message": "Tracking added successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating tracking: {str(e)}")

@router.get("/user/{telegram_id}")
async def get_user_trackings(telegram_id: int, db: Session = Depends(get_db)):
    """Получение всех отслеживаний пользователя по Telegram ID"""
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        trackings = db.query(Tracking).filter(
            Tracking.user_id == user.id,
            Tracking.is_active == True
        ).all()
        
        return {
            "user_id": user.id,
            "trackings": [
                {
                    "id": t.id,
                    "wb_item_id": t.wb_item_id,
                    "custom_name": t.custom_name,
                    "desired_price": t.desired_price,
                    "created_at": t.created_at
                } for t in trackings
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{tracking_id}/user/{telegram_id}")
async def delete_tracking(tracking_id: int, telegram_id: int, db: Session = Depends(get_db)):
    """Удаление отслеживания по ID для пользователя"""
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        tracking = db.query(Tracking).filter(
            Tracking.id == tracking_id,
            Tracking.user_id == user.id
        ).first()
        
        if not tracking:
            raise HTTPException(status_code=404, detail="Tracking not found")
        
        # Мягкое удаление (деактивация)
        tracking.is_active = False
        db.commit()
        
        return {"message": "Tracking deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/telegram/{telegram_id}")
async def check_telegram_user(telegram_id: int, db: Session = Depends(get_db)):
    """Проверка существования пользователя по Telegram ID"""
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        return {
            "exists": user is not None,
            "user_id": user.id if user else None,
            "username": user.username if user else None,
            "email": user.email if user else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Эндпоинты для управления отслеживаниями через web-интерфейс
@router.get("/")
async def get_trackings(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """Получение всех отслеживаний (для админки)"""
    trackings = db.query(Tracking).filter(Tracking.is_active == True).offset(skip).limit(limit).all()
    return trackings

@router.post("/web")
async def create_tracking(tracking: TrackingCreate, db: Session = Depends(get_db)):
    """Создание отслеживания через web-интерфейс"""
    db_tracking = Tracking(**tracking.dict())
    db.add(db_tracking)
    db.commit()
    db.refresh(db_tracking)
    return db_tracking

@router.get("/{tracking_id}")
async def get_tracking(tracking_id: int, db: Session = Depends(get_db)):
    """Получение отслеживания по ID"""
    tracking = db.query(Tracking).filter(Tracking.id == tracking_id).first()
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking not found")
    return tracking

# Эндпоинт для проверки цен для всех активных отслеживаний
@router.post("/check-prices")
async def check_all_prices(db: Session = Depends(get_db)):
    """Проверка цен для всех активных отслеживаний"""
    try:
        active_trackings = db.query(Tracking).filter(Tracking.is_active == True).all()
        
        results = []
        for tracking in active_trackings:
            # Здесь будет логика проверки цены через парсер
            # Пока заглушка
            results.append({
                "tracking_id": tracking.id,
                "wb_item_id": tracking.wb_item_id,
                "current_price": None,  # Будет из парсера
                "desired_price": tracking.desired_price,
                "price_reached": False
            })
        
        return {"checked_trackings": len(results), "results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))