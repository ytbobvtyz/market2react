import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

async def test_bot():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    print(f"🔑 Token: {token[:10]}...")
    
    try:
        bot = Bot(token=token)
        me = await bot.get_me()
        print(f"✅ Bot info: {me.username} (ID: {me.id})")
        
        # Проверим webhook info
        webhook_info = await bot.get_webhook_info()
        print(f"🌐 Webhook: {webhook_info.url}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bot())