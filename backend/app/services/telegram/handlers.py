from telegram import (
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove, 
    KeyboardButton, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
import logging
from datetime import datetime, timedelta
from app.utils.auth_utils import generate_readable_password, generate_otp_code, get_otp_expiry

logger = logging.getLogger("telegram")

async def start_command(update, context):
    """Обработчик команды /start"""
    logger.info("🔧 start command received")
    user = update.effective_user
    logger.info(f"👋 User {user.username} started the bot")
    
    welcome_text = """
🤖 Добро пожаловать в WishBenefit!

Я помогу отслеживать цены на Wildberries.

Доступные команды:
/start - Начать работу
/help - Помощь  
/track [артикул] - Добавить отслеживание
/auth - Авторизация
/forgot_password - Восстановление пароля
"""
    
    # Без Markdown для теста
    await update.message.reply_text(welcome_text)

async def help_command(update, context):
    logger.info("🔧 Help command received")
    await update.message.reply_text("Помощь по командам: /track [артикул]")

async def auth_command(update, context):
    """Обработчик команды /auth"""
    context.user_data['last_command'] = 'auth'
    logger.info("🔐 Auth command received")
    
    # Очищаем возможный предыдущий контекст
    context.user_data.pop('pending_tracking', None)
    
    message = """
🔐 *Авторизация в WishBenefit*

Для авторизации используйте одну из опций ниже:
    """.strip()
    
    # Создаем inline-кнопки вместо reply-клавиатуры
    keyboard = [
        [InlineKeyboardButton("📱 Авторизоваться через номер телефона", callback_data="direct_phone_auth")],
        [InlineKeyboardButton("🌐 Войти через сайт", url="https://wblist.ru")],
        [InlineKeyboardButton("❌ Отмена", callback_data="auth_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_auth_contact(update, context, contact):
    """Обработка номера телефона для авторизации"""
    try:
        phone_number = contact.phone_number
        telegram_user = update.effective_user
        logger.info(f"🔐 Auth contact for: {phone_number}")
        
        # Регистрируем/авторизуем пользователя
        user_data = await register_or_auth_user(phone_number, telegram_user)
        
        if user_data:
            await update.message.reply_text(
                f"✅ *Авторизация успешна!*\n\n"
                f"👋 Добро пожаловать, {user_data.get('username', 'пользователь')}!\n"
                f"📱 Логин: {phone_number}\n"
                f"🔑 Пароль: `{user_data.get('password', 'установлен ранее')}`\n\n"
                f"Теперь вы можете добавлять отслеживания!",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка авторизации. Попробуйте снова.",
                reply_markup=ReplyKeyboardRemove()
            )
            
    except Exception as e:
        logger.error(f"Auth contact error: {e}")
        await update.message.reply_text(
            "❌ Ошибка при авторизации.",
            reply_markup=ReplyKeyboardRemove()
        )

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
                else:
                    logger.error(f"Registration error: {response.status}")
                    return None
                    
    except Exception as e:
        logger.error(f"Register/auth error: {e}")
        return None

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
        
        # УДАЛЯЕМ старые данные если есть
        if 'last_product' in context.user_data:
            del context.user_data['last_product']
        
        # СОХРАНЯЕМ данные товара в context
        context.user_data['last_product'] = {
            'data': product_data,
            'item_id': item_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"💾 Saved product data to context: {item_id}")
        
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

async def button_handler(update, context):
    """Обработка нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    logger.info(f"🔍 Button pressed: {data}")
    
    if data.startswith('track_yes_'):
        item_id = data.replace('track_yes_', '')
        await handle_tracking_confirmation(query, context, item_id)
    elif data == 'track_no':
        await query.edit_message_text("❌ Отслеживание отменено")
    elif data == 'start_phone_auth':
        logger.info("🔍 Start phone auth button pressed")
        await start_phone_auth_from_button(query, context)
    elif data == 'direct_phone_auth':
        logger.info("🔍 Direct phone auth button pressed")
        await direct_phone_auth(query, context)
    elif data == 'auth_cancel':
        await query.edit_message_text("❌ Авторизация отменена")
    else:
        logger.warning(f"🔍 Unknown button data: {data}")
        await query.edit_message_text("❌ Неизвестная команда")

async def direct_phone_auth(query, context):
    """Прямая авторизация через номер телефона"""
    try:
        logger.info("🔍 Starting direct phone auth")
        
        # Редактируем сообщение с инструкцией
        await query.edit_message_text(
            "📱 *Авторизация через номер телефона*\n\n"
            "Отправьте ваш номер телефона в любом формате:\n"
            "• +79123456789\n"
            "• 89123456789\n"
            "• 9123456789\n\n"
            "После отправки номера вы будете автоматически зарегистрированы/авторизованы.",
            parse_mode='Markdown',
            reply_markup=None
        )
        
        # Устанавливаем флаг ожидания номера телефона
        context.user_data['waiting_for_phone'] = True
        context.user_data['last_command'] = 'auth'
        
        logger.info("🔍 Waiting for phone number input")
        
    except Exception as e:
        logger.error(f"❌ Error in direct_phone_auth: {e}")
        await query.edit_message_text("❌ Ошибка при запуске авторизации")

async def handle_tracking_confirmation(query, context, item_id):
    """Обработка подтверждения отслеживания"""
    user = query.from_user
    
    logger.info(f"🔍 === START TRACKING CONFIRMATION ===")
    logger.info(f"🔍 User ID: {user.id}, Username: {user.username}")
    logger.info(f"🔍 Item ID: {item_id}")
    logger.info(f"🔍 Context keys: {list(context.user_data.keys())}")
    
    # Проверяем существование пользователя в БД
    user_exists = await check_user_in_db(user.id)
    logger.info(f"🔍 User exists result: {user_exists}")
    
    if not user_exists:
        logger.info(f"🔍 → Going to immediate auth flow")
        # СРАЗУ предлагаем авторизацию через номер телефона
        await request_immediate_authorization(query, context, user, item_id)
    else:
        logger.info(f"🔍 → Going to direct tracking flow")
        # Добавляем отслеживание с уже полученными данными
        await add_tracking(query, context, user.id, item_id)
    
    logger.info(f"🔍 === END TRACKING CONFIRMATION ===")

async def request_immediate_authorization(query, context, user, item_id):
    """Непосредственный запрос авторизации через номер телефона"""
    try:
        logger.info("🔍 Starting immediate authorization flow")
        
        # Сохраняем информацию о товаре для использования после авторизации
        context.user_data['pending_tracking'] = {
            'item_id': item_id,
            'user_id': user.id,
            'query_message_id': query.message.message_id
        }
        
        message = """
🔐 *Для сохранения требуется авторизация*

Используйте команду /auth для авторизации через номер телефона.

После авторизации товар будет автоматически добавлен в отслеживание.
        """.strip()
        
        # Создаем inline-кнопки вместо reply-клавиатуры
        keyboard = [
            [InlineKeyboardButton("📱 Авторизоваться с помощью номера телефона", callback_data="start_phone_auth")],
            [InlineKeyboardButton("❌ Отмена", callback_data="auth_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Редактируем сообщение с новыми кнопками
        await query.edit_message_text(
            message, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        logger.info("🔍 Auth inline buttons sent successfully")
        logger.info("🔍 Immediate authorization flow completed")
        
    except Exception as e:
        logger.error(f"❌ Error in request_immediate_authorization: {e}")
        await query.edit_message_text("❌ Ошибка при запросе авторизации")

async def start_phone_auth_from_button(query, context):
    """Запуск авторизации через кнопку номера телефона"""
    try:
        logger.info("🔍 Starting phone auth from button")
        
        # Устанавливаем контекст команды
        context.user_data['last_command'] = 'auth'
        
        # Редактируем сообщение
        await query.edit_message_text(
            "🔐 *Авторизация*\n\nНажмите кнопку ниже чтобы поделиться номером телефона:",
            parse_mode='Markdown',
            reply_markup=None
        )
        
        # Создаем кнопку для авторизации
        keyboard = [
            [KeyboardButton("📱 Предоставить номер телефона", request_contact=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            resize_keyboard=True, 
            one_time_keyboard=True
        )
        
        # Отправляем новое сообщение с кнопкой
        await query.message.reply_text(
            "Нажмите кнопку для авторизации:",
            reply_markup=reply_markup
        )
        
        logger.info("🔍 Phone auth button sent successfully")
        
    except Exception as e:
        logger.error(f"❌ Error in start_phone_auth_from_button: {e}")
        await query.edit_message_text("❌ Ошибка при запуске авторизации")

async def start_phone_auth_from_button(query, context):
    """Запуск авторизации по номеру телефона из inline-кнопки"""
    try:
        logger.info("🔍 Starting phone auth from inline button")
        
        # Создаем специальную клавиатуру для запуска авторизации
        keyboard = [
            [InlineKeyboardButton("📱 Нажмите здесь для авторизации", url="https://t.me/wishbenefitbot?start=auth")]  # ← Замени your_bot_username
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """
🔐 *Авторизация через номер телефона*

Нажмите кнопку ниже чтобы открыть интерфейс авторизации:
        """.strip()
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        logger.info("🔍 Auth deep link sent successfully")
        
    except Exception as e:
        logger.error(f"❌ Error in start_phone_auth_from_button: {e}")
        await query.edit_message_text("❌ Ошибка при запуске авторизации")

async def start_auth_from_button(query, context):
    """Запуск авторизации из inline-кнопки"""
    user = query.from_user
    
    # Показываем сообщение с Reply-клавиатурой
    keyboard = [
        [KeyboardButton("📱 Предоставить номер телефона", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        one_time_keyboard=True
    )
    
    await query.edit_message_text(
        "🔐 *Авторизация*\n\nНажмите кнопку ниже чтобы поделиться номером телефона:",
        parse_mode='Markdown',
        reply_markup=None
    )
    
    await query.message.reply_text(
        "Нажмите кнопку для авторизации:",
        reply_markup=reply_markup
    )

async def check_user_in_db(telegram_id):
    """Проверка пользователя в БД"""
    import aiohttp
    import os
    
    try:
        api_url = os.getenv('API_URL', 'http://localhost:8000')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_url}/api/auth/telegram/{telegram_id}") as response:
                logger.info(f"🔍 Check user API response: {response.status}")
                
                if response.status == 200:
                    # Парсим JSON ответ чтобы проверить exists
                    user_data = await response.json()
                    logger.info(f"🔍 User check response: {user_data}")
                    
                    # Возвращаем True только если exists: true
                    return user_data.get('exists', False)
                else:
                    logger.info(f"🔍 User check failed with status: {response.status}")
                    return False
                
    except Exception as e:
        logger.error(f"Check user error: {e}")
        return False

async def request_authorization(query, context, user, item_id):
    """Запрос авторизации"""
    message = f"""
🔐 *Требуется авторизация*

Для добавления отслеживания необходимо авторизоваться.

Используйте команду:
`/auth`

Или перейдите на сайт:
https://wblist.ru
    """.strip()
    
    await query.edit_message_text(message, parse_mode='Markdown')

async def add_tracking(query, context, telegram_id, item_id):
    """Добавление отслеживания для авторизованного пользователя"""
    try:
        # ИСПОЛЬЗУЕМ СОХРАНЕННЫЕ ДАННЫЕ из context
        last_product = context.user_data.get('last_product', {})
        product_data = last_product.get('data')
        
        if not product_data or last_product.get('item_id') != item_id:
            # Если данных нет или item_id не совпадает, парсим заново
            logger.warning(f"🔍 No saved data for {item_id}, parsing again")
            product_data = await parse_product_via_api(item_id)
        else:
            logger.info(f"🔍 Using saved product data for {item_id}")
        
        if product_data:
            target_price = int(float(product_data.get('price', 0)) * 0.9)  # 10% скидка
            
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
                    f"Товар добавлен в ваш список отслеживаний.\n"
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

async def forgot_password_command(update, context):
    """Обработчик команды восстановления пароля"""
    context.user_data['last_command'] = 'forgot_password'
    await update.message.reply_text(
        "🔐 *Восстановление доступа к сайту*\n\n"
        "Для безопасности подтвердите владение аккаунтом.\n"
        "Нажмите кнопку чтобы поделиться номером телефона:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("📱 Отправить номер телефона", request_contact=True)]
        ], resize_keyboard=True, one_time_keyboard=True)
    )

async def handle_password_recovery_contact(update, context, contact=None):
    """Обработка номера телефона для восстановления пароля"""
    try:
        if contact is None:
            contact = update.message.contact
            
        telegram_user = update.effective_user
        
        if contact.user_id != telegram_user.id:
            await update.message.reply_text("❌ Можно использовать только свой номер телефона")
            return
        
        phone_number = contact.phone_number
        logger.info(f"🔐 Password recovery for: {phone_number}")
        
        # Генерируем новый пароль
        new_password = generate_readable_password()
        
        # Обновляем пароль в БД
        success = await update_user_password(phone_number, new_password)
        
        if success:
            await update.message.reply_text(
                f"✅ *Пароль обновлен!*\n\n"
                f"📱 Логин: {phone_number}\n"
                f"🔑 Новый пароль: `{new_password}`\n\n"
                f"*Рекомендуем:*\n"
                f"• Сохраните пароль в надежном месте\n"
                f"• Смените пароль на сайте после входа",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                "❌ Пользователь с таким номером не найден.\n"
                "Проверьте номер или зарегистрируйтесь через /auth",
                reply_markup=ReplyKeyboardRemove()
            )
            
    except Exception as e:
        logger.error(f"Password recovery error: {e}")
        await update.message.reply_text(
            "❌ Ошибка при восстановлении доступа.",
            reply_markup=ReplyKeyboardRemove()
        )

async def update_user_password(phone_number, new_password):
    """Обновление пароля пользователя"""
    import aiohttp
    import os
    from hashlib import sha256
    
    try:
        api_url = os.getenv('API_URL', 'http://localhost:8000')
        
        # Хэшируем пароль
        password_hash = sha256(new_password.encode()).hexdigest()
        
        update_data = {
            "phone_number": phone_number,
            "password_hash": password_hash
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{api_url}/api/auth/password", json=update_data) as response:
                return response.status == 200
                
    except Exception as e:
        logger.error(f"Update password error: {e}")
        return False

async def handle_contact(update, context):
    """Умный обработчик контактов - определяет контекст"""
    try:
        contact = update.message.contact
        telegram_user = update.effective_user
        
        logger.info(f"🔍 Contact received from user {telegram_user.id}")
        logger.info(f"🔍 Context data: {context.user_data}")
        
        if contact.user_id != telegram_user.id:
            await update.message.reply_text("❌ Можно использовать только свой номер телефона")
            return
        
        # ПРОВЕРЯЕМ КОНТЕКСТ СОХРАНЕНИЯ ТОВАРА
        pending_tracking = context.user_data.get('pending_tracking')
        
        if pending_tracking:
            logger.info("🔍 Context: Immediate auth for tracking")
            # Это авторизация при сохранении товара
            await handle_tracking_auth_contact(update, context, contact)
        else:
            # Проверяем последнюю команду
            last_command = context.user_data.get('last_command')
            logger.info(f"🔍 Last command: {last_command}")
            
            if last_command == 'auth':
                logger.info("🔍 Context: Standard auth command")
                await handle_auth_contact(update, context, contact)
            elif last_command == 'forgot_password':
                logger.info("🔍 Context: Password recovery")
                await handle_password_recovery_contact(update, context, contact)
            else:
                logger.info("🔍 Context: Unknown, falling back to standard auth")
                # Если контекст неясен, делаем стандартную авторизацию
                await handle_auth_contact(update, context, contact)
                
    except Exception as e:
        logger.error(f"❌ Error in handle_contact: {e}")
        await update.message.reply_text("❌ Ошибка при обработке номера телефона")

async def handle_tracking_auth_contact(update, context, contact):
    """Обработка номера телефона при немедленной авторизации для отслеживания"""
    try:
        phone_number = contact.phone_number
        telegram_user = update.effective_user
        
        logger.info(f"🔐 Tracking auth contact for: {phone_number}")
        
        # Регистрируем/авторизуем пользователя
        user_data = await register_or_auth_user(phone_number, telegram_user)
        
        if user_data:
            # Добавляем отслеживание после успешной авторизации
            await add_tracking_after_immediate_auth(update, context, telegram_user.id, phone_number, user_data)
        else:
            await update.message.reply_text(
                "❌ Ошибка авторизации. Попробуйте снова: /track",
                reply_markup=ReplyKeyboardRemove()
            )
            
    except Exception as e:
        logger.error(f"❌ Tracking auth contact error: {e}")
        await update.message.reply_text(
            "❌ Ошибка при авторизации. Попробуйте снова: /track",
            reply_markup=ReplyKeyboardRemove()
        )
            
    except Exception as e:
        logger.error(f"Immediate auth contact error: {e}")
        await update.message.reply_text(
            "❌ Ошибка при авторизации. Попробуйте снова: /track",
            reply_markup=ReplyKeyboardRemove()
        )

async def add_tracking_after_immediate_auth(update, context, telegram_id):
    """Добавление отслеживания после немедленной авторизации"""
    try:
        pending_tracking = context.user_data.get('pending_tracking')
        if not pending_tracking:
            await update.message.reply_text(
                "✅ Авторизация успешна! Используйте /track для добавления товаров.",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        item_id = pending_tracking['item_id']
        
        # Используем сохраненные данные товара
        product_data = context.user_data.get('last_product', {}).get('data')

        if not product_data:
            # Если данных нет, парсим заново
            product_data = await parse_product_via_api(item_id)
        
        if product_data:
            target_price = int(float(product_data.get('price', 0)) * 0.9)  # 10% скидка
            
            tracking_data = {
                "telegram_id": telegram_id,
                "wb_item_id": item_id,
                "desired_price": target_price,
                "custom_name": product_data.get('name', f"Товар {item_id}")
            }
            
            success = await save_tracking_via_api(tracking_data)
            
            if success:
                # Редактируем оригинальное сообщение с товаром
                try:
                    query_message_id = pending_tracking.get('query_message_id')
                    if query_message_id:
                        await update._bot.edit_message_text(
                            chat_id=update.effective_chat.id,
                            message_id=query_message_id,
                            text="✅ *Товар успешно добавлен в отслеживание!*",
                            parse_mode='Markdown'
                        )
                except Exception as e:
                    logger.error(f"Error editing message: {e}")
                
                # Отправляем финальное сообщение
                await update.message.reply_text(
                    f"✅ Авторизация и добавление отслеживания успешны!\n\n"
                    f"👋 Добро пожаловать!\n"
                    f"🔑 Ваш пароль: `{context.user_data.get('password', 'установлен ранее')}`\n\n"
                    f"*Товар добавлен в отслеживание:*\n"
                    f"• {product_data.get('name', f'Товар {item_id}')}\n"
                    f"• Целевая цена: {target_price} ₽\n\n"
                    f"Для управления отслеживаниями посетите сайт: https://wblist.ru",
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                await update.message.reply_text(
                    "✅ Авторизация успешна, но не удалось добавить отслеживание.\n"
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
        logger.error(f"Add tracking after immediate auth error: {e}")
        await update.message.reply_text(
            "✅ Авторизация успешна, но произошла ошибка при добавлении отслеживания.\n"
            "Попробуйте снова: /track",
            reply_markup=ReplyKeyboardRemove()
        )

async def save_tracking_via_api(tracking_data):
    """Сохранение отслеживания через API"""
    import aiohttp
    import os
    
    try:
        api_url = os.getenv('API_URL', 'http://localhost:8000')
        
        # ДВА ВАРИАНТА URL - пробуем оба
        urls_to_try = [
            f"{api_url}/api/trackings/",  # со слешем
            f"{api_url}/api/trackings"    # без слеша
        ]
        
        for url in urls_to_try:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=tracking_data) as response:
                        logger.info(f"🔍 Tracking save to {url}: {response.status}")
                        
                        if response.status == 200:
                            return True
                        elif response.status == 404:
                            logger.warning(f"🔍 404 for {url}, trying next...")
                            continue
                        else:
                            logger.error(f"🔍 Tracking save error: {response.status}")
                            return False
            except Exception as e:
                logger.error(f"🔍 Error with {url}: {e}")
                continue
                
        return False
                
    except Exception as e:
        logger.error(f"Save tracking API error: {e}")
        return False

async def handle_text_message(update, context):
    """Обработка текстовых сообщений (не команд)"""
    text = update.message.text.strip()
    logger.info(f"📝 Text message: {text}")
    
    # Проверяем, ожидаем ли мы номер телефона
    if context.user_data.get('waiting_for_phone'):
        await handle_phone_number_input(update, context, text)
        return
    
    # Если сообщение похоже на артикул (только цифры)
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
            "/auth - Авторизация"
        )

async def handle_phone_number_input(update, context, phone_text):
    """Обработка введенного номера телефона"""
    try:
        logger.info(f"🔍 Processing phone number input: {phone_text}")
        
        # Нормализуем номер телефона
        from app.utils.phone import normalize_phone, is_phone_valid
        
        normalized_phone = normalize_phone(phone_text)
        
        if not is_phone_valid(normalized_phone):
            await update.message.reply_text(
                "❌ Неверный формат номера телефона.\n"
                "Пожалуйста, введите номер в формате: +79123456789"
            )
            return
        
        # Создаем fake contact object
        from telegram import Contact
        contact = Contact(
            phone_number=normalized_phone,
            first_name=update.effective_user.first_name or "",
            last_name=update.effective_user.last_name or "",
            user_id=update.effective_user.id
        )
        
        # Обрабатываем как контакт
        await handle_contact(update, context, contact)
        
        # Снимаем флаг ожидания
        context.user_data.pop('waiting_for_phone', None)
        
    except Exception as e:
        logger.error(f"❌ Error processing phone number: {e}")
        await update.message.reply_text("❌ Ошибка при обработке номера телефона")

async def error_handler(update, context):
    """Обработчик ошибок для бота"""
    try:
        logger.error(f"🚨 Error occurred: {context.error}", exc_info=True)
        
        # Логируем детали update
        if update:
            if update.effective_message:
                logger.error(f"📝 Update details - Chat ID: {update.effective_chat.id if update.effective_chat else 'N/A'}, "
                           f"User: {update.effective_user.id if update.effective_user else 'N/A'}, "
                           f"Text: {update.effective_message.text if update.effective_message.text else 'N/A'}")
            
            if update.callback_query:
                logger.error(f"🔘 Callback query data: {update.callback_query.data}")
        
        # Пытаемся отправить сообщение об ошибке пользователю
        if update and update.effective_chat:
            try:
                await update.effective_chat.send_message(
                    "❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте еще раз или обратитесь в поддержку."
                )
            except Exception as e:
                logger.error(f"❌ Failed to send error message to user: {e}")
                
    except Exception as e:
        logger.error(f"💥 Error in error handler: {e}")


def handle_bot_errors(application):
    """Обработчик ошибок на уровне приложения"""
    async def on_error(update, context):
        await error_handler(update, context)
    
    application.add_error_handler(on_error)

async def log_update(update, context):
    """Логирование всех входящих updates"""
    if update.message:
        logger.info(f"📨 Message: {update.message.text} from {update.effective_user.id}")
    elif update.callback_query:
        logger.info(f"🔘 Callback: {update.callback_query.data} from {update.effective_user.id}")
    elif update.edited_message:
        logger.info(f"✏️ Edited: {update.edited_message.text} from {update.effective_user.id}")


def setup_handlers(application):
    """Настройка всех обработчиков"""
    logger.info("🔧 Setting up Telegram bot handlers...")
    
    try:
        # Команды
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("track", track_command))
        application.add_handler(CommandHandler("auth", auth_command))
        application.add_handler(CommandHandler("forgot_password", forgot_password_command))
        
        # Обработчики сообщений - ВАЖНО: только один для CONTACT!
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        application.add_handler(MessageHandler(filters.ALL, log_update))

        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("✅ All handlers setup completed")
        
    except Exception as e:
        logger.error(f"❌ Error setting up handlers: {e}")
        raise