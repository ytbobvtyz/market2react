import re

def normalize_phone(phone: str) -> str:
    """Нормализация номера телефона к формату +79123456789"""
    if not phone:
        return phone
    
    # Удаляем все кроме цифр и +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Обработка российских номеров
    if cleaned.startswith('8') and len(cleaned) == 11:
        return '+7' + cleaned[1:]
    elif cleaned.startswith('7') and len(cleaned) == 11:
        return '+' + cleaned
    elif cleaned.startswith('9') and len(cleaned) == 10:
        return '+7' + cleaned
    elif cleaned.startswith('+7') and len(cleaned) == 12:
        return cleaned
    
    return cleaned  # Для международных номеров

def is_phone_valid(phone: str) -> bool:
    """Проверка валидности номера телефона"""
    normalized = normalize_phone(phone)
    return len(normalized) >= 10 and normalized.startswith('+')