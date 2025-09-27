# Product Requirements: Wishlist App (WB Parser)

## **Основной контекст**
- **Цель**: Многопользовательское приложение для отслеживания цен на Wildberries с опцией монетизации.
- **Порядок работы сервиса**: На основной странице пользователь вводит в основную поисковую  строку артикул WB, в соседнее поле "моя цена" вводит желаемую цену в рублях, а так же выбирает одну из двух опций "отслеживать только это предложение" или "отслеживать схожие товары других продавцов". Если выбран пункт "отслеживать предложения других продавцов", выводится шакала минимального рейтинга продавца и шкала минимального количества отзывов. При нажатии кнопки "проверить результат" внизу страницы появляется таблица с результатами всех продавцов, удовлетворяющих заданным критериям (название, артикул-гиперссылка на wb, цена, рейтинг). При нажатии кнопки "Сохранить мой запрос" запрос фиксируется в базе данных. Начинается ежедневный парсинг по параметрам запроса и сохранение результаов в БД.
- **Работа telegram-бота** Бот WishbenefitBot позволяет пользователю зарегистрироваться и добавить отслеживание.
- **Структура сайта**: Основная страница - окно формирования новых поисковых запросов. Лимиты - 2 запроса для отслеживания бесплатно, 20 - по подписке. Дополнительная страница - "все запросы" (от 1 до 20 на каждого пользователя), где пользователь выбирает запросы для просморта (слева) и просматривает график изменения цены (справа).

    ## 1. Основные требования  
### 1.1. Пользовательские сценарии  
1. Поиск товара:  
   - Пользователь вводит WB артикул.  
   - Если выбран пункт "отслеживать схожие товары других продавцов", Сервис через API WB выдает список аналогичных товаров с:  
     - Названием, ценой, рейтингом, ссылкой.  
     - Возможностью фильтрации (бренд, категория, цена).  
2. Сохранение запроса:  
   - После выбора товара пользователь указывает:  
     - Желаемую цену.  
     - При необходимости редактирует название запроса (например, "Айфон 15 в синем").  
   - Лимиты: 3 запроса бесплатно, 20 — по подписке.  
3. Отслеживание и уведомления:  
   - Ежедневная проверка цен через API WB.  
   - Уведомления в Telegram и Email при достижении целевой цены.  
4. Личный кабинет:  
   - Просмотр всех отслеживаемых товаров.  
   - История изменения цен (график).  
   - Ручной запуск проверки ("Проверить сейчас").  
   - Редактирование параметров (например, изменить желаемую цену).  

### 1.2. Монетизация  
- Бесплатно: 3 активных запроса.  
- Подписка (200 руб/мес):  
  - 20 запросов.  
  - Приоритетные уведомления (Telegram + Email).  

---

## 2. Техническая реализация  
### 2.1. Стек  
- Frontend: React (двухстраничный интерфейс, без сложного UX).  
- Backend: Python (FastAPI для API + Celery для задач).  
- База данных: PostgreSQL (SQLAlchemy для ORM).  
- Парсинг: Официальное API Wildberries + Selenium 
- Уведомления:  
  - Telegram: через Bot API.  
  - Email: SMTP (SendGrid/Mailgun).  
- Асинхронные задачи: Celery + Redis (расписание проверок).  

### 2.2. Схема базы данных  
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    telegram_chat_id = Column(String(100), nullable=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    subscription_tier = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_verified = Column(Boolean, default=False)
    
    # OTP-поля для входа по коду ← ДОБАВИЛИ
    otp_code = Column(String(6), nullable=True)
    otp_expires = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, default=0)
    last_otp_request = Column(DateTime, nullable=True)
    otp_request_count = Column(Integer, default=0)
    
    trackings = relationship("Tracking", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

class Tracking(Base):
    __tablename__ = "trackings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wb_item_id = Column(Integer, nullable=False) 
    custom_name = Column(String)
    desired_price = Column(Numeric(10, 2))
    min_rating = Column(Numeric(3, 2))
    min_comment = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    from sqlalchemy.orm import relationship
    
    # Связи
    user = relationship("User", back_populates="trackings")
    price_history = relationship("PriceHistory", back_populates="tracking", cascade="all, delete-orphan")

CREATE INDEX idx_trackings_wb_item_id ON trackings(wb_item_id);

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_id = Column(UUID(as_uuid=True), ForeignKey("trackings.id"), nullable=False)
    wb_id = Column(Integer, nullable=False)
    wb_name = Column(Text)
    rating = Column(Numeric(3, 2))
    comment_count = Column(Integer)
    price = Column(Numeric(10, 2), nullable=False)
    checked_at = Column(TIMESTAMP, server_default=func.now())
    
    # Связь
    tracking = relationship("Tracking", back_populates="price_history")

### 2.3. API-интеграция с Wildberries  
- Используем официальное API WB для поиска товаров и получения актуальных цен.  
- При неудчае используем selenium
  

### 2.4. Поток данных  
1. Пользователь ищет товар → React отправляет запрос в FastAPI.  
2. FastAPI дергает API WB → возвращает результаты в React.  
3. При сохранении запроса — данные пишутся в PostgreSQL.  
4. Каждую ночь скрипт на сервере проверяет все активные запросы → обновляет price_history.  
5. Если цена упала → отправляет уведомление.  

---

## 3. Ограничения и риски  
- Лимиты API WB: возможны квоты на запросы → нужен retry-механизм.   

---

## 4. План разработки  
### Этап 1 (2 недели)  
- База данных + FastAPI (эндпоинты для поиска/сохранения).  
- Интеграция с API WB.  
- Прототип REACT (поиск + список отслеживаемого).  

### Этап 2 (1 неделя)  
- Celery-задачи для ежедневных проверок.  
- Уведомления в Telegram/Email.  

### Этап 3 (1 неделя)  
- Личный кабинет: графики цен, ручной запуск.  
- Настройка подписки.  

---

## 5. Метрики успеха  
- Количество активных пользователей: > 100 за первый месяц.  
- Конверсия в подписку: 5% от бесплатных пользователей.  
- Среднее количество запросов на пользователя: 2.5 (цель — мотивировать на апгрейд).  

## 6. Структура проекта.
backend
.
├── alembic
│   ├── __pycache__
│   │   └── env.cpython-310.pyc
│   ├── versions
│   │   ├── __pycache__
│   │   │   ├── 0898da381eb8_add_phone_number_to_users.cpython-310.pyc
│   │   │   ├── 20d9013b090c_add_otp_fields_and_telegram_id_to_users.cpython-310.pyc
│   │   │   ├── 4e2ee99e76e4_add_oauth_fields_to_users.cpython-310.pyc
│   │   │   └── a6c0ed7c96b7_init_models_fixed.cpython-310.pyc
│   │   ├── 0898da381eb8_add_phone_number_to_users.py
│   │   ├── 20d9013b090c_add_otp_fields_and_telegram_id_to_users.py
│   │   ├── 4e2ee99e76e4_add_oauth_fields_to_users.py
│   │   └── a6c0ed7c96b7_init_models_fixed.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── app
│   ├── __pycache__
│   │   ├── __init__.cpython-310.pyc
│   │   ├── celery.cpython-310.pyc
│   │   ├── config.cpython-310.pyc
│   │   ├── database.cpython-310.pyc
│   │   └── main.cpython-310.pyc
│   ├── logs
│   │   ├── app.log
│   │   ├── auth.log
│   │   ├── parser.log
│   │   ├── schedule.log
│   │   └── tracking.log
│   ├── models
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-310.pyc
│   │   │   ├── price_history.cpython-310.pyc
│   │   │   ├── relationships.cpython-310.pyc
│   │   │   ├── tracking.cpython-310.pyc
│   │   │   └── user.cpython-310.pyc
│   │   ├── __init__.py
│   │   ├── price_history.py
│   │   ├── tracking.py
│   │   └── user.py
│   ├── routes
│   │   ├── __pycache__
│   │   │   ├── api.cpython-310.pyc
│   │   │   ├── auth.cpython-310.pyc
│   │   │   ├── oauth.cpython-310.pyc
│   │   │   ├── otp.cpython-310.pyc
│   │   │   ├── telegram.cpython-310.pyc
│   │   │   ├── tracking.cpython-310.pyc
│   │   │   └── wb_routes.cpython-310.pyc
│   │   ├── api.py
│   │   ├── auth.py
│   │   ├── oauth.py
│   │   ├── otp.py
│   │   ├── telegram.py
│   │   ├── tracking.py
│   │   └── wb_routes.py
│   ├── schemas
│   │   ├── __pycache__
│   │   │   ├── tracking.cpython-310.pyc
│   │   │   └── user.cpython-310.pyc
│   │   ├── tracking.py
│   │   └── user.py
│   ├── services
│   │   ├── __pycache__
│   │   │   ├── base_parser.cpython-310.pyc
│   │   │   ├── db_service.cpython-310.pyc
│   │   │   ├── email_service.cpython-310.pyc
│   │   │   ├── parser_service_v2.cpython-310.pyc
│   │   │   ├── parser_service.cpython-310.pyc
│   │   │   ├── parser_services.cpython-310.pyc
│   │   │   └── tracking_service.cpython-310.pyc
│   │   ├── telegram
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-310.pyc
│   │   │   │   ├── auth.cpython-310.pyc
│   │   │   │   ├── bot.cpython-310.pyc
│   │   │   │   ├── handlers.cpython-310.pyc
│   │   │   │   └── notifications.cpython-310.pyc
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── handlers.py
│   │   │   ├── notifications.py
│   │   │   └── test_bot.py
│   │   ├── wb
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-310.pyc
│   │   │   │   ├── api_parser.cpython-310.pyc
│   │   │   │   └── selenium_parser.cpython-310.pyc
│   │   │   ├── __init__.py
│   │   │   ├── api_parser.py
│   │   │   └── selenium_parser.py
│   │   ├── base_parser.py
│   │   ├── db_service.py
│   │   ├── email_service.py
│   │   ├── parser_service.py
│   │   └── tracking_service.py
│   ├── utils
│   │   ├── __pycache__
│   │   │   ├── auth_utils.cpython-310.pyc
│   │   │   ├── auth.cpython-310.pyc
│   │   │   ├── db_utils.cpython-310.pyc
│   │   │   ├── logger.cpython-310.pyc
│   │   │   └── phone.cpython-310.pyc
│   │   ├── auth_utils.py
│   │   ├── auth.py
│   │   ├── logger.py
│   │   ├── parse_on_schedule.py
│   │   └── phone.py
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   └── main.py
├── migrations
├── alembic.ini
├── debug_145677475.html
├── debug_155604983.html
├── debug_25887546.html
├── deepseek.md
├── google-chrome-stable_current_amd64.deb
├── run_bot.py
├── run_parsing.sh
├── simple_bot.py
└── test_parsers.py

frontend
.
├── dist
│   ├── assets
│   │   ├── index-D_z34LL_.js
│   │   └── index-kp7oB-f3.css
│   ├── index.html
│   └── vite.svg
├── public
│   ├── favicon.png
│   └── vite.svg
├── src
│   ├── api
│   │   ├── apiService.js
│   │   ├── authService.js
│   │   ├── config.js
│   │   └── parsingService.js
│   ├── assets
│   │   └── react.svg
│   ├── components
│   │   ├── AuthModal.css
│   │   ├── AuthModal.jsx
│   │   ├── OAuthButton.css
│   │   ├── OAuthButton.jsx
│   │   ├── PriceModal.css
│   │   ├── PriceModal.jsx
│   │   ├── TelegramAuth.jsx
│   │   ├── UserMenu.css
│   │   └── UserMenu.jsx
│   ├── contexts
│   │   └── auth-context.jsx
│   ├── pages
│   │   ├── OAuthCallback.jsx
│   │   ├── OAuthSuccess.jsx
│   │   ├── TrackingHistory.css
│   │   └── TrackingHistory.jsx
│   ├── App.css
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
├── .env
├── .gitignore
├── eslint.config.js
├── index.html
├── package-lock.json
├── package.json
├── README.md
└── vite.config.js

## 7. Этапы разработки
[DONE] Разработать структуру проекта
[DONE] Разработать парсеры API и selenium
[DONE] Минимальная страница поиска на frontend
[DONE] Пробросить вывод результатов парсинга из backend в frontend
[DONE] Frontend: Установить элементы дизайна страницы поиска - login/регистрация, переход на страницу отслеживания запросов, кнопка "Добавить в список отслеживания"
[DONE]Backend - реализовать форму регистрации и логина, добавить регистрацию/логин при попытке добавить в список отслеживания при отсутсвии запросов
[DONE]Backend - развернуть базу данных на внешнем сервере, продумать структуру таблиц и взаимосвязей.
[DONE]Backend - Реализовать сохранение запроса в базу данных по нажатию кнопки (с привязкой к user)
[DONE]Frontend - Установить элементы дизайна страницы отображения запросов: *список запросов, *графики цены, рейтинга и отзывов,  * кнопки управленя запросами (удалить, редактировать, перименовать) 
[DONE]Backend - Добавить функции вывода информации из таблиц в frontend
[DONE]Реализовать регистрацию по коду на эл. почту на сервере
[DONE]Арендовать домен для проекта и вылжожить его на сервер.
[DONE]Разработать единый стиль для проекта
[DONE]Настроить парсинг товаров на сервере
[DONE]Реализовать парсинг по расписанию всех товаров в Tracking
[DONE]Финально проверить согласованность стилей

[TODO]Реализовать рассылку сообщений на почту по достижении товаром целевой цены
[TODO]Усовершенствовать функцию парсинга: картинки, успех цены, верыне названия, количество товара в наличии
[TODO]Пробросить картинку, и количество шт во front
[TODO]Упаковать приложение в контейнере докер, переразвернуть на сервере
[TODO]Прикрутить телеграмм-бот для рассылки уведомлений





