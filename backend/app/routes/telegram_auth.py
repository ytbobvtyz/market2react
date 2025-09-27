from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.phone import normalize_phone
from app.utils.auth_utils import generate_readable_password
from datetime import datetime, timezone
import hashlib
import logging

router = APIRouter(prefix="/api/auth", tags=["telegram-auth"])
logger = logging.getLogger(__name__)

@router.post("/telegram")
async def telegram_auth(request: dict, db: Session = Depends(get_db)):
    """Регистрация/авторизация пользователя через Telegram"""
    try:
        # Валидация данных
        phone_number = request.get('phone_number')
        telegram_id = request.get('telegram_id')
        
        if not phone_number or not telegram_id:
            raise HTTPException(status_code=400, detail="Phone number and telegram_id are required")
        
        # Нормализуем телефон
        normalized_phone = normalize_phone(phone_number)
        
        # Ищем пользователя по telegram_id или phone_number
        user = db.query(User).filter(
            (User.telegram_id == telegram_id) | 
            (User.phone_number == normalized_phone)
        ).first()
        
        if user:
            # Обновляем существующего пользователя
            return await update_existing_user(user, request, db, normalized_phone)
        else:
            # Создаем нового пользователя
            return await create_new_user(request, db, normalized_phone)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telegram auth error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def update_existing_user(user: User, request: dict, db: Session, normalized_phone: str):
    """Обновление существующего пользователя"""
    # Проверяем конфликты
    if user.phone_number != normalized_phone and user.telegram_id != request.get('telegram_id'):
        # Пытаемся привязать к другому аккаунту - конфликт
        raise HTTPException(status_code=409, detail="Phone number or Telegram ID already in use")
    
    # Обновляем данные
    user.telegram_id = request.get('telegram_id')
    user.phone_number = normalized_phone
    user.username = request.get('username', user.username)
    user.first_name = request.get('first_name', user.first_name)
    user.last_name = request.get('last_name', user.last_name)
    user.is_verified = True
    user.updated_at = datetime.utcnow()
    
    # Если у пользователя нет пароля - генерируем
    password = None
    if not user.password_hash:
        password = generate_readable_password()
        user.password_hash = hash_password(password)
    
    db.commit()
    
    return {
        "message": "User updated successfully",
        "user_id": user.id,
        "username": user.username,
        "phone_number": user.phone_number,
        "password": password,  # Только если был сгенерирован новый
        "is_new_password": password is not None
    }

async def create_new_user(request: dict, db: Session, normalized_phone: str):
    """Создание нового пользователя"""
    # Генерируем пароль
    password = generate_readable_password()
    
    # Создаем username если не предоставлен
    username = request.get('username')
    if not username:
        base_username = f"user{request.get('telegram_id')}"
        username = await generate_unique_username(db, base_username)
    
    # Создаем пользователя
    user = User(
        phone_number=normalized_phone,
        telegram_id=request.get('telegram_id'),
        username=username,
        # first_name=request.get('first_name'),
        # last_name=request.get('last_name'),
        password_hash=hash_password(password),
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"✅ New user created via Telegram: {user.id}")
    
    return {
        "message": "User created successfully",
        "user_id": user.id,
        "username": user.username,
        "phone_number": user.phone_number,
        "password": password,
        "is_new_password": True
    }

async def generate_unique_username(db: Session, base_username: str, counter: int = 0):
    """Генерация уникального username"""
    if counter == 0:
        test_username = base_username
    else:
        test_username = f"{base_username}{counter}"
    
    # Проверяем существование
    existing = db.query(User).filter(User.username == test_username).first()
    if not existing:
        return test_username
    
    return await generate_unique_username(db, base_username, counter + 1)

def hash_password(password: str) -> str:
    """Хэширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

@router.get("/telegram/{telegram_id}")
async def check_telegram_user(telegram_id: int, db: Session = Depends(get_db)):
    """Проверка существования пользователя по Telegram ID"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if user:
        return {
            "exists": True,
            "user_id": user.id,
            "username": user.username,
            "phone_number": user.phone_number
        }
    else:
        return {"exists": False}