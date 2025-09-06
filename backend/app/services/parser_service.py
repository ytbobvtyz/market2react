from app.services.wb.api_parser import WBApiParser
from app.services.wb.selenium_parser import WBSeleniumParser
from app.utils.logger import logger  # Импортируем готовый логгер

class ParserService:
    def __init__(self):
        # Ленивая инициализация - создаем парсеры только при первом использовании
        self._api_parser = None
        self._selenium_parser = None
        
    @property
    def api_parser(self):
        if self._api_parser is None:
            self._api_parser = WBApiParser()
        return self._api_parser
    
    @property
    def selenium_parser(self):
        if self._selenium_parser is None:
            self._selenium_parser = WBSeleniumParser()
        return self._selenium_parser
        

        
    def parse_wb_product(self, article: str) -> dict:
        try:
        #     logger.info(f"Trying API parser for article {article}")
        #     return self.api_parser.parse(article)
        # except Exception as api_error:
        #     logger.warning(f"API failed: {str(api_error)}")
        #     try:
            logger.info("Falling back to Selenium parser")
            return self.selenium_parser.parse(article)
        except Exception as selenium_error:
            error_msg = f"All parsers failed: {str(selenium_error)}"
            logger.error(error_msg)
            raise Exception(error_msg)