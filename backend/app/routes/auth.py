from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import logging
from app.utils.logger import get_auth_logger

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

# Настройка логгера
logger = get_auth_logger()

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/send-verification-code")
async def send_verification_code(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Отправляет код подтверждения на email
    """
    try:
        logger.info(f"Attempting to send verification code to: {request.email}")
        
        # Проверяем, не занят ли email
        existing_user = get_user_by_email(db, request.email)
        if existing_user:
            logger.warning(f"Email already exists: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        
        # Генерируем и отправляем код
        code = generate_verification_code()
        logger.info(f"Generated verification code for {request.email}: {code}")
        
        success = send_verification_email(request.email, code)
        
        if not success:
            logger.error(f"Failed to send verification email to: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось отправить код подтверждения"
            )
        
        logger.info(f"Verification code sent successfully to: {request.email}")
        return {"message": "Код подтверждения отправлен на email"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in send_verification_code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@router.post("/verify-email-code")
async def verify_email_code_endpoint(
    request: EmailVerificationVerify
):
    """
    Проверяет код подтверждения email
    """
    try:
        logger.info(f"Verifying email code for: {request.email}")
        
        is_valid = verify_email_code(request.email, request.code)
        
        if not is_valid:
            logger.warning(f"Invalid verification code for: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный или просроченный код подтверждения"
            )
        
        logger.info(f"Email successfully verified: {request.email}")
        return {"message": "Email успешно подтвержден"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in verify_email_code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@router.post("/register-with-verification", response_model=UserResponse)
async def register_with_verification(
    request: Request,
    user_data: UserCreateWithVerification,
    db: Session = Depends(get_db)
):
    """
    Регистрация с проверкой кода подтверждения
    """
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        logger.info(f"Registration attempt with verification - Email: {user_data.email}, IP: {client_ip}")
        
        # Проверяем код подтверждения
        is_valid = verify_email_code(user_data.email, user_data.verification_code)
        if not is_valid:
            logger.warning(f"Invalid verification code during registration: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный или просроченный код подтверждения"
            )
        
        # Проверяем, не занят ли email
        existing_user = get_user_by_email(db, user_data.email)
        if existing_user:
            logger.warning(f"Email already exists during registration: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        
        # Создаем пользователя
        try:
            db_user = create_user(db, user_data)
            logger.info(f"User registered successfully: {user_data.email}, User ID: {db_user.id}")
            return db_user
            
        except Exception as e:
            logger.error(f"Error creating user {user_data.email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании пользователя: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in register_with_verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@router.post("/register/", response_model=UserResponse)
async def register(
    request: Request,
    user: UserCreate, 
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        logger.info(f"Registration attempt - Email: {user.email}, IP: {client_ip}")
        
        existing_user = get_user_by_email(db, user.email)
        if existing_user:
            logger.warning(f"Email already exists: {user.email}")
            raise HTTPException(
                status_code=400,
                detail="Пользователь с таким email уже существует"
            )
        
        db_user = create_user(db, user)
        logger.info(f"User registered successfully: {user.email}, User ID: {db_user.id}")
        return db_user
        
    except ValueError as e:
        logger.warning(f"Password validation failed for {user.email}: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected registration error for {user.email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера"
        )

@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        logger.info(f"Login attempt - Email: {form_data.username}, IP: {client_ip}")
        
        user = get_user_by_email(db, form_data.username)
        if not user:
            logger.warning(f"Login failed - user not found: {form_data.username}")
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        if not verify_password(form_data.password, user.password_hash):
            logger.warning(f"Login failed - invalid password for: {form_data.username}")
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        access_token = create_access_token({"sub": user.email})
        logger.info(f"Login successful: {form_data.username}, User ID: {user.id}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected login error for {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/me", response_model=CurrentUser)
async def get_current_user_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        logger.info(f"Current user request - Email: {current_user.email}, IP: {client_ip}")
        return CurrentUser(
            id=current_user.id,
            email=current_user.email,
            username=current_user.username
        )
    except Exception as e:
        logger.error(f"Error in get_current_user_endpoint: {str(e)}")
        raise