from app.services.parser_service import ParserService
from app.utils.logger import logger

def test_parser():
    parser = ParserService()
    test_articles = [
        "452962756",  # Рабочий артикул
        "240155230",  # Несуществующий (проверка fallback)
        "255412114"  # Некорректный
    ]

    for article in test_articles:
        try:
            logger.info(f"\nTesting article {article}")
            result = parser.parse_wb_product(article)
            logger.info(f"Success: {result}")
        except Exception as e:
            logger.error(f"Failed: {str(e)}")

if __name__ == "__main__":
    test_parser()