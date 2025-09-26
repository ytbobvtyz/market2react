#!/bin/bash

# Переходим в директорию проекта backend
cd /var/www/market2react/market2react/backend

# Добавляем путь к Python в PYTHONPATH
export PYTHONPATH="/var/www/market2react/market2react/backend:$PYTHONPATH"

# Активируем виртуальное окружение
source /var/www/market2react/market2react/venv/bin/activate

# Запускаем парсинг через прямое выполнение файла
python /var/www/market2react/market2react/backend/app/utils/parse_on_schedule.py

# Деактивируем виртуальное окружение
deactivate
