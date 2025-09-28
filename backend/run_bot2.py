import os
import logging
import re
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Основная команда start"""
    # Проверяем есть ли аргументы (для deep linking)
    if context.args and context.args[0] == 'phone':
        await deep_link_start(update, context)
        return
    
    # Обычный старт
    keyboard = [
        [InlineKeyboardButton("📱 Получить номер", callback_data="get_phone")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📞 Для работы с ботом нам нужен ваш номер телефона.\n\n"
        "Вы можете:\n"
        "1. Нажать кнопку '📱 Получить номер'\n"
        "2. Отправить номер вручную в формате: +79123456789\n\n"
        "Мы используем номер только для идентификации.",
        reply_markup=reply_markup
    )

async def deep_link_start(update, context):
    """Обработка deep link с параметром phone"""
    await update.message.reply_text(
        "🔐 Для настройки доступа к номеру:\n\n"
        "Настройки Telegram → Конфиденциальность → Номер телефона\n\n"
        "Убедитесь, что в настройках конфиденциальности разрешен доступ к номеру телефона."
    )

async def handle_phone_input(update, context):
    """Обрабатываем ручной ввод номера"""
    text = update.message.text.strip()
    
    # Очищаем номер от лишних символов
    cleaned = re.sub(r'[^\d+]', '', text)
    
    # Проверяем различные форматы номеров
    if re.match(r'^\+7\d{10}$', cleaned):  # +79123456789
        phone = cleaned
    elif re.match(r'^7\d{10}$', cleaned):   # 79123456789
        phone = '+' + cleaned
    elif re.match(r'^8\d{10}$', cleaned):   # 89123456789
        phone = '+7' + cleaned[1:]
    elif re.match(r'^9\d{9}$', cleaned):    # 9123456789
        phone = '+7' + cleaned
    else:
        await update.message.reply_text("❌ Неверный формат номера. Примеры:\n+79123456789\n89123456789\n9123456789")
        return
    
    await update.message.reply_text(f"✅ Ваш номер телефона: {phone}")

async def button_handler(update, context):
    """Обработчик нажатия на inline кнопку"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "get_phone":
        await query.edit_message_text(
            "📱 Пожалуйста, отправьте ваш номер телефона вручную в формате:\n\n"
            "• +79123456789\n"
            "• 89123456789\n"
            "• 9123456789\n\n"
            "Мы гарантируем конфиденциальность ваших данных."
        )

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN not set")
    
    application = Application.builder().token(token).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_input))
    
    logger.info("✅ Handlers setup completed successfully")
    print("🔄 Starting Telegram Bot...")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        raise

if __name__ == "__main__":
    main()