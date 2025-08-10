from app.services.wb.api_parser import WBApiParser
from app.services.wb.selenium_parser import WBSeleniumParser
from app.utils.logger import get_logger
from app.config import get_selenium_config

logger = get_logger(__name__)

class ParserService:
    def __init__(self):
        self.api_parser = WBApiParser()
        self.selenium_config = get_selenium_config()
        self.selenium_parser = WBSeleniumParser()  # Инициализируем здесь
        
    def get_selenium_driver(self):
        """Получение драйвера с текущими настройками"""
        return self.selenium_config['driver']()

    def parse_wb_product(self, article: str) -> dict:
        """
        Парсинг товара с Wildberries
        :param article: Артикул товара
        :return: Словарь с данными товара
        :raises Exception: Если все методы парсинга не сработали
        """
        try:
            logger.info(f"Trying API parser for article {article}")
            return self.api_parser.parse(article)
        except Exception as api_error:
            logger.warning(f"API parser failed: {str(api_error)}")
            try:
                logger.info("Falling back to Selenium parser")
                return self.selenium_parser.parse(article)
            except Exception as selenium_error:
                error_msg = f"All parsing attempts failed: {str(selenium_error)}"
                logger.error(error_msg)
                raise Exception(error_msg)