from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
from app.database import get_db
from app.models.user import User
from app.utils.auth import create_access_token, get_current_user
from app.services.db_service import get_user_by_email, create_oauth_user
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/oauth", tags=["oauth"])

# Конфигурация Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

@router.get("/google")
async def google_oauth():
    """Перенаправление на Google OAuth"""
    google_oauth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        "response_type=code&"
        f"redirect_uri=http://localhost:8000/oauth/google/callback&"
        "scope=openid%20email%20profile&"
        "access_type=offline&"
    )
    return RedirectResponse(google_oauth_url)

@router.get("/google/callback")
async def google_oauth_callback(
    request: Request,
    code: str,
    db: Session = Depends(get_db)
):
    """Обработка callback от Google"""
    try:
        # 1. Обмен code на access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
        
        # 2. Получение данных пользователя
        userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(userinfo_url, headers=headers)
            userinfo_response.raise_for_status()
            user_data = userinfo_response.json()
        
        # 3. Создание/поиск пользователя в БД
        email = user_data["email"]
        user = get_user_by_email(db, email)
        
        if not user:
            # Создаем нового пользователя через OAuth
            user_data_for_db = {
                "email": email,
                "username": user_data.get("name", email.split('@')[0]),
                "oauth_provider": "google",
                "oauth_id": user_data["sub"],
                "is_verified": True  # Google уже проверил email
            }
            user = create_oauth_user(db, user_data_for_db)
        
        # 4. Создание JWT токена
        access_token = create_access_token({"sub": user.email})
        
        # 5. Перенаправление на фронтенд с токеном
        frontend_success_url = f"{FRONTEND_URL}/oauth/success?token={access_token}&user_id={user.id}"
        print(f"🎯 Redirecting to: {frontend_success_url}")  # Для дебага
        return RedirectResponse(frontend_success_url)
        
    except Exception as e:
        # В случае ошибки перенаправляем на фронтенд с ошибкой
        error_url = f"{FRONTEND_URL}/oauth/error?message={str(e)}"
        return RedirectResponse(error_url)

@router.get("/userinfo")
async def get_oauth_userinfo(current_user: User = Depends(get_current_user)):
    """Получение информации о OAuth пользователе"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "oauth_provider": current_user.oauth_provider,
        "is_verified": current_user.is_verified
    }