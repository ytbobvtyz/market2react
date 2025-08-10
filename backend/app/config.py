from pydantic_settings import BaseSettings
from typing import List, Dict, Any
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver

class Settings(BaseSettings):
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Новые настройки для Selenium
    SELENIUM_HEADLESS: bool = True
    SELENIUM_TIMEOUT: int = 15
    SELENIUM_BINARY_LOCATION: str = "/usr/bin/google-chrome"
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

# Инициализация настроек
settings = Settings()

# Конфигурация Selenium (вычисляется при первом использовании)
def get_selenium_config() -> Dict[str, Any]:
    chrome_options = webdriver.ChromeOptions()
    if settings.SELENIUM_HEADLESS:
        chrome_options.add_argument("--headless=new")
    
    return {
        'driver': lambda: webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        ),
        'wait_timeout': settings.SELENIUM_TIMEOUT
    }
