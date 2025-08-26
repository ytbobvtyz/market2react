from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.tracking_service import save_parsing_results
from app.schemas.tracking import ParsingResultCreate
from app.utils.auth import get_current_user
from app.models.user import User

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