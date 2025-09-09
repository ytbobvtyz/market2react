import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import logging


# Настройка логирования в файл вместо stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/isolated_parser.log'),
        logging.StreamHandler(sys.stderr)  # Логи в stderr вместо stdout
    ]
)

logger = logging.getLogger("isolated_parser")

# Загружаем .env
env_path = Path(__file__).parent.parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Получаем путь из .env
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', '/var/www/market2react/market2react'))
print(f"Project root: {PROJECT_ROOT}")

# Добавляем путь к backend в PYTHONPATH
BACKEND_PATH = PROJECT_ROOT / 'backend'
sys.path.insert(0, str(BACKEND_PATH))
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Article required"}))
        sys.exit(1)
    
    article = sys.argv[1]
    
    try:
        logger.info(f"Starting parsing for article: {article}")

        from app.services.parser_service import ParserService
        result = ParserService().parse_wb_product(article)

        logger.info(f"Parsing completed for article: {article}")

        # ВЫВОДИМ ТОЛЬКО JSON в stdout!
        print(json.dumps(result))

    except ImportError as e:
        logger.error(f"Error parsing article {article}: {str(e)}")
        # ВЫВОДИМ ТОЛЬКО JSON в stdout!
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()