from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.services.tracking_service import save_parsing_results
from app.schemas.tracking import ParsingResultCreate, TrackingResponse, TrackingWithHistoryResponse
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.tracking import Tracking
from app.models.price_history import PriceHistory


router = APIRouter()

@router.post("/save-parsing-results/", status_code=status.HTTP_201_CREATED)
async def save_parsing_results_endpoint(
    parsing_data: ParsingResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Сохраняет результаты парсинга одного товара
    """
    result = save_parsing_results(
        db=db, 
        parsing_data=parsing_data, 
        user_id=current_user.id
    )
    
    if result["saved_count"] > 0:
        return {
            "message": "Данные успешно сохранены",
            "tracking_id": result.get("tracking_id"),
            "details": result
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["errors"][0] if result["errors"] else "Ошибка при сохранении данных"
        )
    
@router.get("/user-trackings/", response_model=list[TrackingResponse])
async def get_user_trackings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить все трекинги текущего пользователя
    """
    try:
        from app.services.tracking_service import get_trackings_by_user
        trackings = get_trackings_by_user(db, current_user.id)
        return trackings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user trackings: {str(e)}"
        )
    
@router.get("/tracking/{tracking_id}/", response_model=TrackingWithHistoryResponse)
async def get_tracking_with_history(
    tracking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить информацию о трекинге с историей цен
    """
    # Проверяем, что трекинг принадлежит текущему пользователю
    tracking = db.query(Tracking).filter(
        Tracking.id == tracking_id,
        Tracking.user_id == current_user.id
    ).first()

    if not tracking:
        raise HTTPException(status_code=404, detail="Трекинг не найден")

    # Получаем историю цен для этого трекинга
    price_history = db.query(PriceHistory).filter(
        PriceHistory.tracking_id == tracking_id
    ).order_by(PriceHistory.checked_at.desc()).all()

    # Формируем ответ
    return {
        "id": tracking.id,
        "wb_item_id": tracking.wb_item_id,
        "custom_name": tracking.custom_name,
        "desired_price": tracking.desired_price,
        "is_active": tracking.is_active,
        "created_at": tracking.created_at,
        "price_history": price_history
    }