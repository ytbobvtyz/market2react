import logging
from pathlib import Path

def setup_logger(name: str, log_file: str = 'app.log') -> logging.Logger:
    """Настройка логгера с записью в файл и выводом в консоль"""
    logs_dir = Path(__file__).parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Файловый обработчик
    file_handler = logging.FileHandler(logs_dir / log_file)
    file_handler.setFormatter(formatter)
    
    # Консольный обработчик
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger

# Создаем глобальный логгер
logger = setup_logger('app')