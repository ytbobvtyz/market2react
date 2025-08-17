from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..schemas.user import UserCreate, UserResponse
from ..services.db_service import get_user_by_email, create_user
from ..utils.db_utils import get_db
from ..utils.auth import create_access_token, verify_password

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

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(f"Полученные данные: username='{form_data.username}' password='{form_data.password}'")
    print(f"Login attempt for: {form_data.username}") 
    user = get_user_by_email(db, form_data.username)
    print(f"User found: {bool(user)}")  # Логирование
    if not user:
        print("User not found")  # Логирование
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    print(f"Password verification: {verify_password(form_data.password, user.password_hash)}")  # Логирование
    if not  verify_password(form_data.password, user.password_hash):
        print("Invalid password")  # Логирование
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    print("Login successful")  # Логирование
    access_token = create_access_token({"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }

# @router.get("/me", response_model=UserResponse)
# async def get_current_user(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)  # Реализуйте эту зависимость
# ):
#     return current_user