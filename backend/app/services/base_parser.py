from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseParser(ABC):
    @abstractmethod
    def parse(self, article: str) -> Dict[str, Any]:
        """Основной метод парсинга
        Args:
            article: Артикул товара
        Returns:
            Словарь с данными товара
        Raises:
            ParserError: В случае ошибок парсинга
        """
        pass

class ParserError(Exception):
    """Базовое исключение для ошибок парсинга"""
    pass