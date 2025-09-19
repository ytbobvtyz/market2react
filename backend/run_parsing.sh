#!/bin/bash

# Переходим в директорию проекта
cd /var/www/market2react/market2react/

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем парсинг
python -m app.utils.parse_on_schedule

# Деактивируем виртуальное окружение
deactivate