from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    telegram_chat_id: Optional[str] = None
    subscription_tier: Optional[str] = None

    @field_validator('password')
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
    email: EmailStr
    telegram_chat_id: Optional[str] = None
    subscription_tier: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CurrentUser(BaseModel):
    id: int
    email: str
    username: str
    
    class Config:
        from_attributes = True


class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationVerify(BaseModel):
    email: EmailStr
    code: str

class UserCreateWithVerification(BaseModel):
    username: str
    email: EmailStr
    password: str
    verification_code: str
    telegram_chat_id: Optional[str] = None
    subscription_tier: Optional[str] = None