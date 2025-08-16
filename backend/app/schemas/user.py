from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    telegram_chat_id: Optional[str] = None
    subscription_tier: Optional[str] = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    telegram_chat_id: Optional[str] = None
    subscription_tier: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True  # Заменяет orm_mode в Pydantic v2