import bcrypt
from sqlalchemy.orm import Session
from ..models.user import User

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_data):
    # Генерация соли и хеширование пароля с помощью bcrypt
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), salt)
    
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password.decode('utf-8'),  # Сохраняем как строку
        telegram_chat_id=user_data.telegram_chat_id,
        subscription_tier=user_data.subscription_tier
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )