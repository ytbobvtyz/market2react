from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..schemas.user import UserCreate, UserResponse, CurrentUser
from ..services.db_service import get_user_by_email, create_user
from app.database import get_db
from ..utils.auth import create_access_token, verify_password, get_current_user
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = get_user_by_email(db, user.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Пользователь с таким email уже существует"
            )
        
        db_user = create_user(db, user)
        return db_user  # ← Просто возвращаем объект, Pydantic сам сериализует
    except ValueError as e:
        # Ловим ошибки валидации пароля
        raise HTTPException(
            status_code=422,
            detail=str(e)  # "Пароль должен содержать минимум 8 символов" и т.д.
        )
    except HTTPException:
        # Пробрасываем уже созданные HTTPException
        raise
    except Exception as e:
        # Ловим все остальные ошибки
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера"
        )
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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

@router.get("/me", response_model=CurrentUser)
async def get_current_user_endpoint(
    current_user: User = Depends(get_current_user)
):
    return CurrentUser(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username
    )