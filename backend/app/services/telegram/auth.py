import hashlib
import hmac
import time
from fastapi import HTTPException
from app.database import get_db
from app.models.user import User
from app.services.db_service import create_oauth_user

class TelegramAuth:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
    
    def verify_telegram_data(self, auth_data: dict) -> bool:
        """
        Проверяет подлинность данных от Telegram Widget
        https://core.telegram.org/widgets/login
        """
        try:
            # Извлекаем необходимые поля
            hash_str = auth_data.pop('hash')
            auth_date = auth_data.get('auth_date')
            
            # Проверяем срок действия (не старше 1 дня)
            if time.time() - int(auth_date) > 86400:
                return False
            
            # Создаем data-check-string
            data_check_string = '\n'.join(
                f"{key}={value}" for key, value in sorted(auth_data.items())
            )
            
            # Вычисляем секретный ключ
            secret_key = hashlib.sha256(self.bot_token.encode()).digest()
            
            # Проверяем хэш
            computed_hash = hmac.new(
                secret_key, 
                data_check_string.encode(), 
                hashlib.sha256
            ).hexdigest()
            
            return computed_hash == hash_str
            
        except Exception:
            return False
    
    async def authenticate_user(self, auth_data: dict, db):
        """Аутентификация пользователя через Telegram"""
        if not self.verify_telegram_data(auth_data):
            raise HTTPException(status_code=401, detail="Invalid Telegram auth data")
        
        telegram_id = auth_data['id']
        username = auth_data.get('username')
        first_name = auth_data.get('first_name', '')
        last_name = auth_data.get('last_name', '')
        
        # Ищем пользователя в БД
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user:
            # Создаем нового пользователя
            user_data = {
                "username": username or f"tg_{telegram_id}",
                "telegram_id": telegram_id,
                "first_name": first_name,
                "last_name": last_name,
                "is_verified": True
            }
            user = create_oauth_user(db, user_data, "telegram")
        
        return user