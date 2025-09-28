import os
import logging
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Загружаем .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Отправляет приветственное сообщение с кнопкой поделиться телефоном"""
    # Создаем кнопку для отправки номера телефона
    keyboard = [[KeyboardButton("📱 Поделиться телефоном", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        one_time_keyboard=True
    )
    
    await update.message.reply_text(
        "Привет! Нажмите кнопку ниже, чтобы поделиться своим номером телефона:",
        reply_markup=reply_markup
    )

async def handle_contact(update, context):
    """Обрабатывает полученный контакт (номер телефона)"""
    contact = update.message.contact
    phone_number = contact.phone_number
    
    # Убираем клавиатуру после отправки номера
    remove_keyboard = ReplyKeyboardMarkup([[KeyboardButton(" ")]]).to_dict()
    remove_keyboard['keyboard'] = []
    
    await update.message.reply_text(
        f"✅ Ваш номер телефона: {phone_number}",
        reply_markup=ReplyKeyboardMarkup.from_button(KeyboardButton(" ")).to_dict()
    )

async def handle_message(update, context):
    """Обрабатывает текстовые сообщения"""
    await update.message.reply_text(
        "Пожалуйста, используйте кнопку '📱 Поделиться телефоном' для отправки номера."
    )

def setup_handlers(application):
    """Настраивает обработчики команд и сообщений"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN not set")
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Настраиваем обработчики
    try:
        setup_handlers(application)
        logger.info("✅ Handlers setup completed successfully")
    except Exception as e:
        logger.error(f"❌ Error setting up handlers: {e}")
        return
    
    print("🔄 Starting Telegram Bot with phone sharing functionality...")
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