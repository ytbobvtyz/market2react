from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import (
    UserCreate, UserResponse, 
    EmailVerificationRequest, EmailVerificationVerify,
    UserCreateWithVerification, CurrentUser
)
from app.services.email_service import send_verification_email, verify_email_code, generate_verification_code
from ..services.db_service import get_user_by_email, create_user
from app.database import get_db
from ..utils.auth import create_access_token, verify_password, get_current_user
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/send-verification-code")
async def send_verification_code(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Отправляет код подтверждения на email
    """
    # Проверяем, не занят ли email
    existing_user = get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # Генерируем и отправляем код
    code = generate_verification_code()
    success = send_verification_email(request.email, code)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось отправить код подтверждения"
        )
    
    return {"message": "Код подтверждения отправлен на email"}

@router.post("/verify-email-code")
async def verify_email_code_endpoint(
    request: EmailVerificationVerify
):
    """
    Проверяет код подтверждения email
    """
    is_valid = verify_email_code(request.email, request.code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или просроченный код подтверждения"
        )
    
    return {"message": "Email успешно подтвержден"}

@router.post("/register-with-verification", response_model=UserResponse)
async def register_with_verification(
    user_data: UserCreateWithVerification,
    db: Session = Depends(get_db)
):
    """
    Регистрация с проверкой кода подтверждения
    """
    # Проверяем код подтверждения
    is_valid = verify_email_code(user_data.email, user_data.verification_code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или просроченный код подтверждения"
        )
    
    # Проверяем, не занят ли email
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # Создаем пользователя
    try:
        db_user = create_user(db, user_data)
        return db_user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании пользователя: {str(e)}"
        )

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