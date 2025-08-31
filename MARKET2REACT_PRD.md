# Product Requirements: Wishlist App (WB Parser)

## **Основной контекст**
- **Цель**: Многопользовательское приложение для отслеживания цен на Wildberries с опцией монетизации.
- **Порядок работы сервиса**: На основной странице пользователь вводит в основную поисковую  строку артикул WB, в соседнее поле "моя цена" вводит желаемую цену в рублях, а так же выбирает одну из двух опций "отслеживать только это предложение" или "отслеживать схожие товары других продавцов". Если выбран пункт "отслеживать предложения других продавцов", выводится шакала минимального рейтинга продавца и шкала минимального количества отзывов. При нажатии кнопки "проверить результат" внизу страницы появляется таблица с результатами всех продавцов, удовлетворяющих заданным критериям (название, артикул-гиперссылка на wb, цена, рейтинг). При нажатии кнопки "Сохранить мой запрос" запрос фиксируется в базе данных. Начинается ежедневный парсинг по параметрам запроса и сохранение результаов в БД.
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
sql

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    telegram_chat_id VARCHAR(100),
    subscription_tier VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE trackings (
  id UUID PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  wb_item_id BIGINT,
  custom_name TEXT,
  desired_price DECIMAL,
  min_rating FLOAT,
  min_comment INTEGER,
  is_active BOOLEAN,
  created_at TIMESTAMP
);

CREATE INDEX idx_trackings_wb_item_id ON trackings(wb_item_id);

CREATE TABLE price_history (  
  id UUID PRIMARY KEY,  
  tracking_id UUID REFERENCES trackings(id),
  wb_id BIGINT, 
  wb_name TEXT,
  rating FLOAT,
  comment_count INTEGER,
  price DECIMAL,  
  checked_at TIMESTAMP  
);

### 2.3. API-интеграция с Wildberries  
- Используем официальное API WB для поиска товаров и получения актуальных цен.  
- При неудчае используем selenium
 # TODO: API WB на данный момент не работает, необходимо реализовать дублирующий код с помощью SELENIUM
  

### 2.4. Поток данных  
1. Пользователь ищет товар → React отправляет запрос в FastAPI.  
2. FastAPI дергает API WB → возвращает результаты в React.  
3. При сохранении запроса — данные пишутся в PostgreSQL.  
4. Каждую ночь Celery проверяет все активные запросы → обновляет price_history.  
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
│   │   │   └── a6c0ed7c96b7_init_models_fixed.cpython-310.pyc
│   │   └── a6c0ed7c96b7_init_models_fixed.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── app
│   ├── __pycache__
│   │   ├── __init__.cpython-310.pyc
│   │   ├── config.cpython-310.pyc
│   │   ├── database.cpython-310.pyc
│   │   └── main.cpython-310.pyc
│   ├── logs
│   │   ├── app.log
│   │   └── parser.log
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
│   │   │   ├── tracking.cpython-310.pyc
│   │   │   └── wb_routes.cpython-310.pyc
│   │   ├── api.py
│   │   ├── auth.py
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
│   │   │   ├── parser_service.cpython-310.pyc
│   │   │   ├── parser_services.cpython-310.pyc
│   │   │   └── tracking_service.cpython-310.pyc
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
│   │   ├── parser_service.py
│   │   └── tracking_service.py
│   ├── utils
│   │   ├── __pycache__
│   │   │   ├── auth.cpython-310.pyc
│   │   │   ├── db_utils.cpython-310.pyc
│   │   │   └── logger.cpython-310.pyc
│   │   ├── auth.py
│   │   └── logger.py
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   └── main.py
├── migrations
├── .env
├── alembic.ini
└── test_parsers.py

frontend
.
├── public
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
│   │   ├── PriceModal.css
│   │   ├── PriceModal.jsx
│   │   ├── UserMenu.css
│   │   └── UserMenu.jsx
│   ├── contexts
│   │   └── auth-context.jsx
│   ├── pages
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

[TODO]Настроить корректную валидацию при регистарции по почте на сервере
[TODO]Настроить парсинг товаров на сервере
[TODO]Реализовать парсинг по расписанию всех товаров в Tracking
[TODO]Реализовать рассылку сообщений на почту по достижении товаром целевой цены
[TODO]Финально проверить согласованность стилей




