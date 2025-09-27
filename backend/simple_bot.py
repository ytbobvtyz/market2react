import asyncio
import logging
from telegram.ext import Application, CommandHandler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_command(update, context):
    """Простая команда /start"""
    user = update.effective_user
    logger.info(f"User {user.username} started the bot")
    await update.message.reply_text(f"👋 Привет, {user.first_name}! Бот работает!")

async def main():
    # Твой токен
    TOKEN = "8274423588:AAHmC0rN8jU1W9vXXXXX"  # замени на реальный
    
    print("🔧 Creating bot application...")
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем команду
    application.add_handler(CommandHandler("start", start_command))
    
    print("✅ Bot created, starting polling...")
    print("💡 Send /start to @wishbenefitBot in Telegram")
    
    # Запускаем бесконечный polling
    await application.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")