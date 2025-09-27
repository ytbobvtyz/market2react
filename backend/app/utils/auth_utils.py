import secrets
import string
from datetime import datetime, timedelta, timezone

def generate_otp_code(length: int = 6) -> str:
    """Генерация OTP-кода"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def generate_readable_password() -> str:
    """Генерация читаемого пароля типа Sun8#Wave3"""
    adjectives = ["Red", "Blue", "Fast", "Smart", "Happy", "Cool", "Sun", "Moon"]
    nouns = ["Cat", "Dog", "Sun", "Moon", "Star", "Wave", "Bird", "Fish"]
    
    adj = secrets.choice(adjectives)
    noun = secrets.choice(nouns)
    number = secrets.choice(string.digits)
    symbol = secrets.choice("!@#$%")
    
    return f"{adj}{number}{symbol}{noun}"

def is_otp_valid(otp_expires: datetime) -> bool:
    """Проверка срока действия OTP (10 минут)"""
    return otp_expires and datetime.utcnow() < otp_expires

def get_otp_expiry() -> datetime:
    """Время истечения OTP"""
    return datetime.now(timezone.utc) + timedelta(minutes=10)