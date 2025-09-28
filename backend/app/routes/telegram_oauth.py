from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from app.services.db_service import get_user_by_telegram_id

router = APIRouter(prefix="/api/telegram-oauth", tags=["telegram-oauth"])

@router.post("/link-telegram")
async def link_telegram_to_user(
    link_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Привязка Telegram ID к существующему OAuth пользователю
    """
    try:
        telegram_id = link_data.get('telegram_id')
        telegram_username = link_data.get('telegram_username')
        
        if not telegram_id:
            raise HTTPException(status_code=400, detail="Telegram ID is required")
        
        # Проверяем, не привязан ли уже этот Telegram ID к другому пользователю
        existing_user = get_user_by_telegram_id(db, telegram_id)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=409, detail="Telegram ID already linked to another account")
        
        # Привязываем Telegram ID к текущему пользователю
        current_user.telegram_id = telegram_id
        current_user.telegram_username = telegram_username
        db.commit()
        
        return {
            "status": "success",
            "message": "Telegram account linked successfully",
            "user_id": current_user.id,
            "telegram_id": current_user.telegram_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-telegram-link")
async def check_telegram_link(
    current_user: User = Depends(get_current_user)
):
    """Проверка привязки Telegram аккаунта"""
    return {
        "has_telegram": current_user.telegram_id is not None,
        "telegram_id": current_user.telegram_id,
        "telegram_username": current_user.telegram_username
    }