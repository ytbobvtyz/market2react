import logging
from telegram import Bot
from telegram.error import TelegramError
import os

logger = logging.getLogger("telegram")

class TelegramNotifier:
    def __init__(self):
        self.bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    
    async def send_price_alert(self, chat_id: int, tracking_data: dict):
        """Отправка уведомления о достижении цены"""
        try:
            message = self._format_price_alert(tracking_data)
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            return True
        except TelegramError as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    def _format_price_alert(self, data):
        """Форматирование сообщения о снижении цены"""
        return f"""
🎯 <b>Целевая цена достигнута!</b>

📦 <b>Товар:</b> {data['product_name']}
🏷️ <b>Артикул:</b> {data['wb_item_id']}
💰 <b>Текущая цена:</b> {data['current_price']} ₽
🎯 <b>Ваша цель:</b> {data['target_price']} ₽
📉 <b>Экономия:</b> {data['savings']} ₽

<a href="https://www.wildberries.ru/catalog/{data['wb_item_id']}/detail.aspx">🛒 Перейти к товару</a>
        """.strip()
    
    async def send_welcome_message(self, chat_id: int):
        """Приветственное сообщение"""
        welcome_text = """
👋 Добро пожаловать в <b>WishBenefit</b>!

Я буду уведомлять вас о снижении цен на отслеживаемые товары Wildberries.

📊 <b>Что я умею:</b>
• Отслеживать изменение цен
• Уведомлять о достижении целевой цены
• Показывать историю цен
• Сравнивать предложения разных продавцов

Начните с добавления товара по артикулу WB!
        """.strip()
        
        await self.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            parse_mode='HTML'
        )