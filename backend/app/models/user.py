from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    telegram_chat_id = Column(String(100), nullable=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    subscription_tier = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_verified = Column(Boolean, default=False)
    
    # OTP-поля для входа по коду ← ДОБАВИЛИ
    otp_code = Column(String(6), nullable=True)
    otp_expires = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, default=0)
    last_otp_request = Column(DateTime, nullable=True)
    otp_request_count = Column(Integer, default=0)
    
    trackings = relationship("Tracking", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"