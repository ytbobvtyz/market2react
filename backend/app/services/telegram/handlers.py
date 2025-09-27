from telegram.ext import CommandHandler, CallbackQueryHandler
import logging

logger = logging.getLogger("telegram")

async def start_command(update, context):
    """Обработчик команды /start"""
    logger.info("🔧 start command received")
    user = update.effective_user
    logger.info(f"👋 User {user.username} started the bot")
    
    welcome_text = """
🤖 *Добро пожаловать в WishBenefit!*

Я помогу отслеживать цены на Wildberries.

*Доступные команды:*
/start - Начать работу
/help - Помощь
/track [артикул] [цена] - Добавить отслеживание
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update, context):
    logger.info("🔧 Help command received")
    await update.message.reply_text("Помощь по командам: /track [артикул] [цена]")

async def track_command(update, context):
    logger.info("📦 Track command received")
    
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text(
                "❌ Использование: /track [артикул]\n\n"
                "Пример: /track 12345678"
            )
            return
        
        item_id = args[0]
        
        # Проверяем валидность артикула
        if not item_id.isdigit():
            await update.message.reply_text("❌ Артикул должен быть числом")
            return
        
        # Сообщаем о начале парсинга
        wait_msg = await update.message.reply_text(
            f"🔍 Начинаю парсинг артикула {item_id}...\n"
            f"⏱ Это займет до 60 секунд"
        )
        
        # Вызываем парсинг через API
        product_data = await parse_product_via_api(item_id)
        
        if not product_data:
            await wait_msg.edit_text("❌ Не удалось получить данные по артикулу")
            return
        
        # Показываем результаты
        await show_product_info(update, context, product_data, item_id)
        
    except Exception as e:
        logger.error(f"Track command error: {e}")
        await update.message.reply_text("❌ Ошибка при обработке запроса")

async def parse_product_via_api(item_id):
    """Парсинг товара через FastAPI"""
    import aiohttp
    import os
    
    try:
        api_url = os.getenv('API_URL', 'http://localhost:8000')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_url}/api/products/{item_id}", timeout=60) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API error: {response.status}")
                    return None
                    
    except Exception as e:
        logger.error(f"API request error: {e}")
        return None

async def show_product_info(update, context, product_data, item_id):
    """Показ информации о товаре и предложение отслеживания"""
    
    name = product_data.get('name', 'Неизвестно')
    price = product_data.get('price', 0)
    rating = product_data.get('rating', 'Нет данных')
    feedback_count = product_data.get('feedback_count', 'Нет данных')
    
    message = f"""
📦 *Информация о товаре:*

*Название:* {name}
*Артикул:* {item_id}
*Цена:* {price} ₽
*Рейтинг:* {rating}
*Отзывы:* {feedback_count}

Хотите добавить в отслеживание?
    """.strip()
    
    # Создаем кнопки
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("✅ Да, добавить", callback_data=f"track_yes_{item_id}")],
        [InlineKeyboardButton("❌ Нет", callback_data="track_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

from telegram.ext import CallbackQueryHandler

async def button_handler(update, context):
    """Обработка нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('track_yes_'):
        item_id = data.replace('track_yes_', '')
        await handle_tracking_confirmation(query, context, item_id)
    elif data == 'track_no':
        await query.edit_message_text("❌ Отслеживание отменено")

async def handle_tracking_confirmation(query, context, item_id):
    """Обработка подтверждения отслеживания"""
    user = query.from_user
    
    # Проверяем существование пользователя в БД
    user_exists = await check_user_in_db(user.id)
    
    if not user_exists:
        # Запрашиваем авторизацию
        await request_authorization(query, context, user, item_id)
    else:
        # Добавляем отслеживание
        await add_tracking(query, context, user.id, item_id)

async def check_user_in_db(telegram_id):
    """Проверка пользователя в БД"""
    import aiohttp
    import os
    
    try:
        api_url = os.getenv('API_URL', 'http://localhost:8000')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_url}/api/users/telegram/{telegram_id}") as response:
                return response.status == 200
                
    except Exception as e:
        logger.error(f"Check user error: {e}")
        return False

async def request_authorization(query, context, user, item_id):
    """Запрос авторизации"""
    message = f"""
🔐 *Требуется авторизация*

Для добавления отслеживания необходимо авторизоваться на сайте.

📝 Перейдите на сайт и войдите через Telegram:
https://wblist.ru/telegram-auth

После авторизации повторите команду:
`/track {item_id}`
    """.strip()
    
    await query.edit_message_text(message, parse_mode='Markdown')

async def add_tracking(query, context, telegram_id, item_id):
    """Добавление отслеживания"""
    import aiohttp
    import os
    
    try:
        api_url = os.getenv('API_URL', 'http://localhost:8000')
        
        # Получаем текущую цену для целевого значения
        product_data = await parse_product_via_api(item_id)
        target_price = int(product_data.get('price', 0)) * 0.9  # 10% скидка
        
        tracking_data = {
            "telegram_id": telegram_id,
            "wb_item_id": item_id,
            "desired_price": target_price,
            "custom_name": product_data.get('name', f"Товар {item_id}")
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/api/trackings", 
                json=tracking_data
            ) as response:
                
                if response.status == 200:
                    await query.edit_message_text(
                        f"✅ *Отслеживание добавлено!*\n\n"
                        f"Товар добавлен в ваш список отслеживаний.\n"
                        f"Уведомление придёт при достижении цены: {target_price} ₽",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text("❌ Ошибка при добавлении отслеживания")
                    
    except Exception as e:
        logger.error(f"Add tracking error: {e}")
        await query.edit_message_text("❌ Ошибка при добавлении отслеживания")
        
# Создаем обработчики
start_handler = CommandHandler("start", start_command)
help_handler = CommandHandler("help", help_command)  
track_handler = CommandHandler("track", track_command)