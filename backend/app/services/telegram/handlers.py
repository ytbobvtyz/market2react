from telegram import (
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove, 
    KeyboardButton, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    WebAppInfo
)
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
import logging
from datetime import datetime
from app.utils.auth_utils import generate_readable_password
import json
import aiohttp

logger = logging.getLogger("telegram")

# ==================== КОМАНДЫ ====================

async def start_command(update, context):
    """Обработчик команды /start"""
    logger.info("🔧 start command received")
    
    welcome_text = """
🤖 Добро пожаловать в WishBenefit!

Я помогу отслеживать цены на Wildberries.

*Доступные команды:*
/start - Начать работу
/track [артикул] - Добавить отслеживание
/auth - Авторизация
/help - Помощь
"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update, context):
    """Обработчик команды /help"""
    help_text = """
📖 *Помощь по командам:*

*/track [артикул]* - Добавить товар для отслеживания
*/auth* - Авторизация/регистрация
*/forgot_password* - Восстановление пароля

*Пример:*
`/track 12345678` - отслеживать товар с артикулом 12345678
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def auth_command(update, context):
    """Простая авторизация через кнопку номера телефона"""
    logger.info("🔐 Auth command received")

    keyboard = [[
        InlineKeyboardButton(
            "📱 Авторизация через сайт",
            web_app=WebAppInfo(url="https://wblist.ru/telegram-auth")
        )
    ]]
    
    await update.message.reply_text(
        "Нажмите кнопку для авторизации через Web App:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
async def forgot_password_command(update, context):
    """Заглушка для восстановления пароля"""
    await update.message.reply_text(
        "🔐 *Восстановление пароля*\n\n"
        "Для восстановления доступа обратитесь в поддержку или войдите через номер телефона командой /auth\n\n"
        "В будущем мы добавим автоматическое восстановление.",
        parse_mode='Markdown'
    )

# ==================== ОСНОВНОЙ FLOW ====================

async def track_command(update, context):
    """Обработчик команды /track"""
    logger.info("📦 Track command received")
    
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text(
                "❌ *Использование:* /track [артикул]\n\n"
                "*Пример:* `/track 12345678`",
                parse_mode='Markdown'
            )
            return
        
        item_id = args[0]
        
        if not item_id.isdigit():
            await update.message.reply_text("❌ Артикул должен содержать только цифры")
            return
        
        # Сообщаем о начале парсинга
        wait_msg = await update.message.reply_text(
            f"🔍 Ищу товар {item_id}...\n⏱ Это займет до 60 секунд"
        )
        
        # Парсим товар
        product_data = await parse_product_via_api(item_id)
        
        if not product_data:
            await wait_msg.edit_text("❌ Не удалось найти товар. Проверьте артикул.")
            return
        
        # Сохраняем данные товара
        context.user_data['last_product'] = {
            'data': product_data,
            'item_id': item_id
        }
        
        # Показываем товар и предлагаем сохранить
        await show_product_info(update, context, product_data, item_id)
        
    except Exception as e:
        logger.error(f"Track command error: {e}")
        await update.message.reply_text("❌ Ошибка при обработке запроса")

async def show_product_info(update, context, product_data, item_id):
    """Показ информации о товаре"""
    name = product_data.get('name', 'Неизвестно')
    price = product_data.get('price', 0)
    rating = product_data.get('rating', 'Нет данных')
    feedback_count = product_data.get('feedback_count', 'Нет данных')
    
    message = f"""
📦 *Информация о товаре:*

*Название:* {name}
*Цена:* {price} ₽
*Рейтинг:* {rating}
*Отзывы:* {feedback_count}

Хотите добавить в отслеживание?
""".strip()
    
    keyboard = [
        [InlineKeyboardButton("✅ Да, добавить", callback_data=f"track_yes_{item_id}")],
        [InlineKeyboardButton("❌ Нет", callback_data="track_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

# ==================== ОБРАБОТКА КНОПОК ====================

async def button_handler(update, context):
    """Обработка нажатий inline-кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"🔍 Button pressed: {data}")
    
    if data.startswith('track_yes_'):
        item_id = data.replace('track_yes_', '')
        await handle_tracking_confirmation(query, context, item_id)
    elif data == 'track_no':
        await query.edit_message_text("❌ Отслеживание отменено")
    elif data == 'cancel_auth':
        await handle_auth_cancel(query, context)
    else:
        await query.edit_message_text("❌ Неизвестная команда")

async def handle_tracking_confirmation(query, context, item_id):
    """Обработка подтверждения отслеживания"""
    user = query.from_user
    
    # Проверяем авторизацию пользователя
    user_exists = await check_user_in_db(user.id)
    
    if user_exists:
        # Пользователь авторизован - сохраняем отслеживание
        await add_tracking(query, context, user.id, item_id)
    else:
        # Пользователь не авторизован - запрашиваем авторизацию
        await request_immediate_authorization(query, context, user, item_id)

async def request_immediate_authorization(query, context, user, item_id):
    """Запрос авторизации при сохранении товара"""
    logger.info("🔐 Requesting immediate authorization for tracking")
    
    # Сохраняем информацию о товаре
    context.user_data['pending_tracking'] = {
        'item_id': item_id,
        'user_id': user.id,
        'message_id': query.message.message_id
    }
    
    # Создаем клавиатуру с кнопкой номера телефона
    keyboard = [[KeyboardButton("📱 Поделиться номером", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    # Редактируем сообщение с товаром
    await query.edit_message_text(
        "🔐 *Для сохранения требуется авторизация*\n\n"
        "Нажмите кнопку ниже чтобы поделиться номером телефона и автоматически добавить товар.",
        parse_mode='Markdown',
        reply_markup=None
    )
    
    # Отправляем сообщение с кнопкой
    await query.message.reply_text(
        "Нажмите для авторизации:",
        reply_markup=reply_markup
    )

async def handle_auth_cancel(query, context):
    """Обработка отмены авторизации"""
    await query.edit_message_text(
        "❌ Авторизация отменена.\n\n"
        "Вы можете в любой момент проверить стоимость товара через бота или авторизоваться по почте на сайте wblist.ru",
        reply_markup=None
    )

# ==================== ОБРАБОТКА ДАННЫХ ИЗ WEB APP ====================

async def handle_web_app_data(update, context):
    """Обработка данных из Web App"""
    try:
        data = json.loads(update.message.web_app_data.data)
        
        if data.get('type') == 'oauth_success':
            await handle_oauth_success(update, context, data)
        else:
            logger.warning(f"Unknown web app data type: {data}")
            
    except Exception as e:
        logger.error(f"Web app data handling error: {e}")

async def handle_oauth_success(update, context, data):
    """Обработка успешной OAuth авторизации из Web App"""
    try:
        jwt_token = data.get('jwt_token')
        telegram_user = data.get('telegram_user')
        
        if not jwt_token or not telegram_user:
            await update.message.reply_text("❌ Недостаточно данных для привязки")
            return
        
        # Используем JWT токен для привязки Telegram ID
        link_data = {
            'telegram_id': telegram_user.get('id'),
            'telegram_username': telegram_user.get('username')
        }
        
        # Вызываем API привязки с JWT авторизацией
        api_url = "http://localhost:8000/api/telegram-oauth/link-telegram"
        headers = {'Authorization': f'Bearer {jwt_token}'}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=link_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    await handle_successful_link(update, context, result)
                else:
                    error_text = await response.text()
                    logger.error(f"Link API error: {error_text}")
                    await update.message.reply_text("❌ Ошибка при привязке аккаунта")
                    
    except Exception as e:
        logger.error(f"OAuth success handling error: {e}")
        await update.message.reply_text("❌ Ошибка при обработке авторизации")

async def handle_successful_link(update, context, result):
    """Обработка успешной привязки"""
    await update.message.reply_text(
        f"✅ *Аккаунт успешно привязан!*\n\n"
        f"Теперь вы можете использовать все функции бота.\n\n"
        f"*Команды:*\n"
        f"/track - Добавить отслеживание\n"
        f"/list - Просмотр ваших отслеживаний\n"
        f"/help - Помощь",
        parse_mode='Markdown'
    )
    
    # Сохраняем ожидающее отслеживание если есть
    pending_tracking = context.user_data.get('pending_tracking')
    if pending_tracking:
        await save_tracking_via_api(update, context, result['user_id'])

# ==================== ОБРАБОТКА КОНТАКТОВ ====================

async def handle_contact(update, context):
    """Обработка номера телефона от пользователя"""
    try:
        contact = update.message.contact
        user = update.effective_user
        
        logger.info(f"🔍 Contact received from user {user.id}")
        
        # Проверяем что пользователь отправил свой номер
        if contact.user_id != user.id:
            await update.message.reply_text("❌ Можно использовать только свой номер телефона")
            return
        
        # Регистрируем/авторизуем пользователя
        user_data = await register_or_auth_user(contact.phone_number, user)
        
        if not user_data:
            await update.message.reply_text("❌ Ошибка при регистрации. Попробуйте снова.")
            return
        
        # Проверяем контекст (сохранение товара или обычная авторизация)
        pending_tracking = context.user_data.get('pending_tracking')
        
        if pending_tracking:
            # Авторизация при сохранении товара
            await handle_tracking_after_auth(update, context, user.id, contact.phone_number, user_data)
        else:
            # Обычная авторизация
            await handle_successful_auth(update, context, contact.phone_number, user_data)
            
    except Exception as e:
        logger.error(f"❌ Error in handle_contact: {e}")
        await update.message.reply_text("❌ Ошибка при обработке номера телефона")

async def handle_successful_auth(update, context, phone_number, user_data):
    """Обработка успешной авторизации"""
    await update.message.reply_text(
        f"✅ *Авторизация успешна!*\n\n"
        f"👋 Добро пожаловать, {user_data.get('username', 'пользователь')}!\n"
        f"📱 Логин: {phone_number}\n"
        f"🔑 Пароль: `{user_data.get('password', 'установлен ранее')}`\n\n"
        f"Теперь вы можете добавлять отслеживания командой /track",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )

async def handle_tracking_after_auth(update, context, telegram_id, phone_number, user_data):
    """Добавление отслеживания после авторизации"""
    try:
        pending_tracking = context.user_data.get('pending_tracking')
        if not pending_tracking:
            await handle_successful_auth(update, context, phone_number, user_data)
            return
        
        item_id = pending_tracking['item_id']
        
        # Получаем данные товара
        product_data = context.user_data.get('last_product', {}).get('data')
        if not product_data:
            product_data = await parse_product_via_api(item_id)
        
        if product_data:
            # Сохраняем отслеживание
            target_price = int(float(product_data.get('price', 0)) * 0.9)  # 10% скидка
            
            tracking_data = {
                "telegram_id": telegram_id,
                "wb_item_id": item_id,
                "desired_price": target_price,
                "custom_name": product_data.get('name', f"Товар {item_id}")
            }
            
            success = await save_tracking_via_api(tracking_data)
            
            if success:
                # Успешное сохранение
                await update.message.reply_text(
                    f"✅ *Авторизация и сохранение успешны!*\n\n"
                    f"👋 Добро пожаловать!\n"
                    f"📱 Логин: {phone_number}\n"
                    f"🔑 Пароль: `{user_data.get('password', 'установлен ранее')}`\n\n"
                    f"*Товар добавлен в отслеживание:*\n"
                    f"• {product_data.get('name', f'Товар {item_id}')}\n"
                    f"• Целевая цена: {target_price} ₽\n\n"
                    f"Уведомление придёт при достижении целевой цены!",
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                await update.message.reply_text(
                    "✅ Авторизация успешна, но не удалось сохранить товар.\n"
                    "Попробуйте снова: /track",
                    reply_markup=ReplyKeyboardRemove()
                )
        else:
            await update.message.reply_text(
                "✅ Авторизация успешна, но не удалось получить данные товара.\n"
                "Попробуйте снова: /track",
                reply_markup=ReplyKeyboardRemove()
            )
        
        # Очищаем контекст
        context.user_data.pop('pending_tracking', None)
        context.user_data.pop('last_product', None)
            
    except Exception as e:
        logger.error(f"❌ Error in handle_tracking_after_auth: {e}")
        await update.message.reply_text(
            "✅ Авторизация успешна, но произошла ошибка при сохранении.\n"
            "Попробуйте снова: /track",
            reply_markup=ReplyKeyboardRemove()
        )

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

async def parse_product_via_api(item_id):
    """Парсинг товара через API"""
    import aiohttp
    import os
    
    try:
        api_url = os.getenv('API_URL', 'http://localhost:8000')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_url}/api/products/{item_id}", timeout=60) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception as e:
        logger.error(f"API request error: {e}")
        return None

async def check_user_in_db(telegram_id):
    """Проверка существования пользователя"""
    import aiohttp
    import os
    
    try:
        api_url = os.getenv('API_URL', 'http://localhost:8000')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_url}/api/auth/telegram/{telegram_id}") as response:
                if response.status == 200:
                    user_data = await response.json()
                    return user_data.get('exists', False)
                return False
    except Exception as e:
        logger.error(f"Check user error: {e}")
        return False

async def register_or_auth_user(phone_number, telegram_user):
    """Регистрация или авторизация пользователя"""
    import aiohttp
    import os
    
    try:
        api_url = os.getenv('API_URL', 'http://localhost:8000')
        
        user_data = {
            "phone_number": phone_number,
            "telegram_id": telegram_user.id,
            "username": telegram_user.username or f"user_{telegram_user.id}",
            "first_name": telegram_user.first_name,
            "last_name": telegram_user.last_name
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{api_url}/api/auth/telegram", json=user_data) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception as e:
        logger.error(f"Register/auth error: {e}")
        return None

async def add_tracking(query, context, telegram_id, item_id):
    """Добавление отслеживания для авторизованного пользователя"""
    try:
        product_data = context.user_data.get('last_product', {}).get('data')
        if not product_data:
            product_data = await parse_product_via_api(item_id)
        
        if product_data:
            target_price = int(float(product_data.get('price', 0)) * 0.9)
            
            tracking_data = {
                "telegram_id": telegram_id,
                "wb_item_id": item_id,
                "desired_price": target_price,
                "custom_name": product_data.get('name', f"Товар {item_id}")
            }
            
            success = await save_tracking_via_api(tracking_data)
            
            if success:
                await query.edit_message_text(
                    f"✅ *Отслеживание добавлено!*\n\n"
                    f"Уведомление придёт при достижении цены: {target_price} ₽",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text("❌ Ошибка при добавлении отслеживания")
        else:
            await query.edit_message_text("❌ Не удалось получить данные товара")
    except Exception as e:
        logger.error(f"Add tracking error: {e}")
        await query.edit_message_text("❌ Ошибка при добавлении отслеживания")

async def save_tracking_via_api(tracking_data):
    """Сохранение отслеживания через API"""
    import aiohttp
    import os
    
    try:
        api_url = os.getenv('API_URL', 'http://localhost:8000')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{api_url}/api/trackings/", json=tracking_data) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Save tracking error: {e}")
        return False

# ==================== ОБРАБОТКА ТЕКСТА ====================

async def handle_text_message(update, context):
    """Обработка текстовых сообщений"""
    text = update.message.text.strip()
    
    # Если сообщение похоже на артикул
    if text.isdigit() and len(text) >= 6:
        await update.message.reply_text(
            f"🔍 Вижу артикул {text}\n\n"
            f"Для отслеживания используйте команду:\n"
            f"`/track {text}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🤖 Используйте команды:\n"
            "/start - Начать работу\n"
            "/track [артикул] - Добавить отслеживание\n"
            "/auth - Авторизация\n"
            "/help - Помощь"
        )

# ==================== ОБРАБОТЧИК ОШИБОК ====================

async def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(f"🚨 Error: {context.error}", exc_info=True)
    
    if update and update.effective_chat:
        try:
            await update.effective_chat.send_message(
                "❌ Произошла ошибка. Попробуйте еще раз."
            )
        except:
            pass

# ==================== НАСТРОЙКА ОБРАБОТЧИКОВ ====================

def setup_handlers(application):
    """Настройка всех обработчиков"""
    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("track", track_command))
    application.add_handler(CommandHandler("auth", auth_command))
    application.add_handler(CommandHandler("forgot_password", forgot_password_command))
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)