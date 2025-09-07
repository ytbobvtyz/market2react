from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import os
from selenium.common.exceptions import WebDriverException
from app.utils.logger import logger
import tempfile

class Settings(BaseSettings):
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Настройки БД
    DB_NAME: str = Field(..., env="DB_NAME")
    DB_USER: str = Field(..., env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")
    DB_HOST: str = Field(..., env="DB_HOST")
    DB_PORT: str = Field(..., env="DB_PORT")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 300
    # настройки для Selenium
    SELENIUM_HEADLESS: bool = True
    SELENIUM_TIMEOUT: int = 15
    SELENIUM_BINARY_LOCATION: str = "/usr/bin/google-chrome"
    # CHROME_DRIVER_PATH: str = Field(..., env="CHROME_DRIVER_PATH")
    # SMTP настройки
    SMTP_SERVER: str = "smtp.yandex.ru"
    SMTP_PORT: int = 465
    SMTP_USERNAME: str = Field(..., env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(..., env="SMTP_PASSWORD")
    
    # Redis настройки (опционально)
    # REDIS_HOST: str = "localhost"
    # REDIS_PORT: int = 6379
    # REDIS_PASSWORD: str = ""

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env') 
        env_file_encoding = 'utf-8'
        extra = 'allow'

# Инициализация настроек
settings = Settings()


# Конфигурация Selenium (вычисляется при первом использовании)
def get_selenium_config() -> Dict[str, Any]:
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Режим без браузера
    chrome_options.add_argument("--no-sandbox")

    chrome_options.add_argument("--disable-dev-shm-usage")
    if settings.SELENIUM_HEADLESS:
        chrome_options.add_argument("--headless=new")
    
    return {
        'driver': lambda: webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        ),
        'wait_timeout': settings.SELENIUM_TIMEOUT
    }

def get_driver():
    
    # Создаем УНИКАЛЬНЫЙ временный каталог для КАЖДОГО вызова
    temp_dir = tempfile.mkdtemp()
    user_data_dir = os.path.join(temp_dir, "chrome_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    options = Options()

    options.add_argument(f"--user-data-dir={user_data_dir}")
    
    # Основные параметры
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Параметры для обхода антибот-систем
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Для Linux сервера
    options.binary_location = "/usr/bin/google-chrome"

    # Дополнительные параметры
    options.add_argument("--lang=ru-RU,ru")
    options.add_argument("--accept-lang=ru-RU,ru")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--metrics-recording-only")
    options.add_argument("--no-first-run")
    options.add_argument("--safebrowsing-disable-auto-update")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")


    service = None
    driver = None

    try:
        # Автоматическая установка ChromeDriver
        service = Service(
            ChromeDriverManager().install(),
            service_args=['--verbose'],
            log_path='/tmp/chromedriver.log'
        )
        
        driver = webdriver.Chrome(service=service, options=options)

        # Изменяем свойства браузера
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        # Устанавливаем таймауты
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)

        logger.info(f"WebDriver successfully initialized with temp dir: {temp_dir}")
        return driver
     
    except WebDriverException as e:
        logger.error(f"WebDriver initialization failed: {str(e)}")
        if driver:
            driver.quit()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during WebDriver initialization: {str(e)}")
        if driver:
            driver.quit()
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise