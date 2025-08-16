from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.user import UserCreate, UserResponse
from ..services.db_service import get_user_by_email, create_user
from ..utils.db_utils import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = create_user(db, user)
        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "created_at": db_user.created_at.isoformat(),  # Явное преобразование
            "updated_at": db_user.updated_at.isoformat()   # Явное преобразование
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))