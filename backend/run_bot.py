import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application

# Загружаем .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN not set")
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Импортируем и настраиваем обработчики
    try:
        from app.services.telegram.handlers import setup_handlers
        setup_handlers(application)
        logger.info("✅ Handlers setup completed successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import handlers: {e}")
        return
    except Exception as e:
        logger.error(f"❌ Error setting up handlers: {e}")
        return
    
    print("🔄 Starting Telegram Bot with OTP support...")
    logger.info("🤖 Bot is starting...")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        raise

if __name__ == "__main__":
    main()