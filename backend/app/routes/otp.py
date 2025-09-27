from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.phone import normalize_phone, is_phone_valid
from app.utils.auth_utils import generate_otp_code, get_otp_expiry
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/otp", tags=["otp"])

@router.post("/request")
async def request_otp(phone: str, db: Session = Depends(get_db)):
    """Запрос OTP-кода для входа"""
    try:
        # Нормализуем и проверяем телефон
        normalized_phone = normalize_phone(phone)
        if not is_phone_valid(normalized_phone):
            raise HTTPException(status_code=400, detail="Неверный формат номера")
        
        # Ищем пользователя
        user = db.query(User).filter(User.phone_number == normalized_phone).first()
        
        # Спам-защита: не чаще 1 раза в 2 минуты
        if user and user.last_otp_request:
            time_since_last = datetime.utcnow() - user.last_otp_request
            if time_since_last < timedelta(minutes=2):
                raise HTTPException(status_code=429, detail="Слишком частые запросы")
        
        # Генерируем OTP
        otp_code = generate_otp_code()
        otp_expires = get_otp_expiry()
        
        if user:
            # Обновляем существующего пользователя
            user.otp_code = otp_code
            user.otp_expires = otp_expires
            user.otp_attempts = 0
            user.last_otp_request = datetime.utcnow()
            user.otp_request_count += 1
        else:
            # Создаем нового пользователя (если нужно)
            # Пока просто возвращаем ошибку - регистрация через бота
            raise HTTPException(status_code=404, detail="Пользователь не найден. Зарегистрируйтесь через бота.")
        
        db.commit()
        
        # Здесь будет отправка OTP в Telegram бот
        # Пока возвращаем для тестирования
        return {
            "message": "Код отправлен в Telegram",
            "otp_code": otp_code,  # Только для разработки!
            "expires_in": "10 минут"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify")
async def verify_otp(phone: str, otp_code: str, db: Session = Depends(get_db)):
    """Проверка OTP-кода"""
    try:
        normalized_phone = normalize_phone(phone)
        user = db.query(User).filter(User.phone_number == normalized_phone).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Проверяем попытки
        if user.otp_attempts >= 5:
            raise HTTPException(status_code=429, detail="Слишком много попыток")
        
        # Проверяем код и срок
        if not user.otp_code or user.otp_code != otp_code:
            user.otp_attempts += 1
            db.commit()
            raise HTTPException(status_code=400, detail="Неверный код")
        
        if datetime.utcnow() > user.otp_expires:
            raise HTTPException(status_code=400, detail="Код истек")
        
        # Код верный - сбрасываем OTP поля
        user.otp_code = None
        user.otp_expires = None
        user.otp_attempts = 0
        db.commit()
        
        # Создаем JWT токен
        from app.utils.auth import create_access_token
        access_token = create_access_token({"sub": user.username})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))