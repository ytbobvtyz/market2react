#!/bin/bash

# Переходим в директорию проекта
cd /var/www/market2react/market2react/

# Активируем виртуальное окружение
source venv/bin/activate

# Переходим в директорию проекта
cd /var/www/market2react/market2react/backend

# Запускаем парсинг
python -m app.utils.parse_on_schedule

# Переходим в директорию проекта
cd /var/www/market2react/market2react/

# Деактивируем виртуальное окружение
deactivate
