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
    current_user: User = Depends(get_current_user)  # Защищенный эндпоинт
):
    try:
        result = save_parsing_results(db=db, parsing_data=parsing_data, user_id=current_user.id)
        
        return {
            "message": f"Успешно сохранено {result['saved_count']} из {result['total_products']} товаров",
            "details": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving parsing results: {str(e)}"
        )