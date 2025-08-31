import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import random
# import redis
from app.config import settings

# Конфигурация SMTP
SMTP_SERVER = settings.SMTP_SERVER
SMTP_PORT = settings.SMTP_PORT
SMTP_USERNAME = settings.SMTP_USERNAME
SMTP_PASSWORD = settings.SMTP_PASSWORD

# Подключение к Redis для хранения кодов (если нет Redis, можно использовать базу)
# try:
#     redis_client = redis.Redis(
#         host=settings.REDIS_HOST,
#         port=settings.REDIS_PORT,
#         password=settings.REDIS_PASSWORD,
#         decode_responses=True
#     )
# except:
#     redis_client = None

# Временное хранилище кодов (замените на Redis в продакшене)
verification_codes = {}

def generate_verification_code() -> str:
    """Генерирует 6-значный код подтверждения"""
    return str(random.randint(100000, 999999))

def send_verification_email(email: str, code: str) -> bool:
    """
    Отправляет код подтверждения на email
    """
    try:
        # Формируем письмо
        msg = MIMEText(
            f"""Добро пожаловать в WishBenefit!\n\n
            Ваш код подтверждения: {code}\n\n
            Код действителен в течение 10 минут.\n
            Если вы не запрашивали этот код, проигнорируйте это письмо.\n\n
            С уважением,\nКоманда WishBenefit"""
        )
        msg["Subject"] = "Код подтверждения для WishBenefit"
        msg["From"] = SMTP_USERNAME
        msg["To"] = email

        # Отправка через SMTP
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        # Сохраняем код (временное решение)
        verification_codes[email] = {
            'code': code,
            'expires_at': datetime.now() + timedelta(minutes=10)
        }
        
        return True
        
    except Exception as e:
        print(f"Ошибка отправки email: {str(e)}")
        return False

def verify_email_code(email: str, code: str) -> bool:
    """
    Проверяет код подтверждения
    """
    if email not in verification_codes:
        return False
    
    stored_data = verification_codes[email]
    
    # Проверяем срок действия
    if datetime.now() > stored_data['expires_at']:
        del verification_codes[email]
        return False
    
    # Проверяем код
    if stored_data['code'] == code:
        del verification_codes[email]
        return True
    
    return False

def cleanup_expired_codes():
    """Очищает просроченные коды"""
    current_time = datetime.now()
    expired_emails = [
        email for email, data in verification_codes.items()
        if current_time > data['expires_at']
    ]
    
    for email in expired_emails:
        del verification_codes[email]