import logging
from pathlib import Path
import sys

def setup_logger(name: str, log_file: str = 'app.log') -> logging.Logger:
    """Настройка логгера с записью в файл и выводом в консоль"""
    logs_dir = Path(__file__).parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Файловый обработчик
    file_handler = logging.FileHandler(logs_dir / log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Консольный обработчик
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    # Очищаем существующие обработчики
    logger.handlers.clear()

    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Предотвращаем передачу логов родительским логгерам
    logger.propagate = False

    return logger

# Создаем глобальный логгер
logger = setup_logger('market2react')

# Дополнительные логгеры для разных компонентов
def get_api_logger():
    return setup_logger('api', 'api_requests.log')

def get_db_logger():
    return setup_logger('database', 'db_operations.log')

def get_parser_logger():
    return setup_logger('parser', 'parser.log')

def get_auth_logger():
    return setup_logger('auth', 'auth.log')
