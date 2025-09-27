import os
from dotenv import load_dotenv
from telegram.ext import Application, CallbackQueryHandler
from app.services.telegram.handlers import start_handler, help_handler, track_handler, button_handler

load_dotenv()

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    application = Application.builder().token(token).build()
    
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(track_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("🔄 Starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main()