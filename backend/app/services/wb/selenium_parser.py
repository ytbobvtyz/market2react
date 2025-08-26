from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..base_parser import BaseParser
from app.config import get_selenium_config, get_driver  # Измененный импорт
import re
import time
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import json

class WBSeleniumParser(BaseParser):
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Режим без браузера
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        
    def parse(self, article: str) -> dict:
        """Основной метод парсинга через Selenium"""
        try:
            self.driver = get_driver()
            self.wait = WebDriverWait(self.driver, 15)
            self.driver.get(f"https://www.wildberries.ru/catalog/{article}/detail.aspx")
            # Ожидаем загрузки страницы
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-page")))
            time.sleep(1)
            # Получаем HTML страницы
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')        
            product_data = {
                'name': self._extract_name(soup),
                'price': self._extract_price(soup),
                'brand': self._extract_brand(soup),
                'rating': self._extract_rating(soup),
                'feedback_count': self._extract_feedback_count(soup),
            }
            return product_data
        except Exception as e:
            if self.driver:
                self.driver.quit()
                self.driver = get_driver()  # Пересоздаем драйвер при ошибке
            raise

    def _extract_name(self, soup):
        try:
            return soup.find('h1', class_='product-page__title').text.strip()
        except:
            return None
    
    def _extract_price(self, soup):
        try:
            # Вариант 1: Обычная цена (без скидки)
            price_elem = soup.find('span', class_='price-block__final-price')
            
            # Вариант 2: Акционная цена (перечёркнутая старая цена)
            if not price_elem:
                price_elem = soup.find('ins', class_='price-block__final-price')
            
            # Вариант 3: Цена в "кошельке" (wallet)
            if not price_elem:
                price_elem = soup.find('span', class_=lambda x: x and 'price-block__final-price' in x and 'wallet' in x)
            
            # Вариант 4: Поиск по data-атрибуту (если классы динамические)
            if not price_elem:
                price_elem = soup.find(attrs={"data-tag": "finalPrice"})
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Удаляем всё, кроме цифр (на случай "1 999 ₽", "1999₽" и т.д.)
                return int(''.join(filter(str.isdigit, price_text)))
            
            return None
        except Exception as e:
            print(f"Price extraction error: {e}")
            return None
        
    def _extract_brand(self, soup):
        """
        Извлекает бренд из breadcrumbs (хлебных крошек) на странице Wildberries.
        Это более надежный способ, так как бренд всегда присутствует в пути навигации.
        """
        try:
            # Способ 1: Ищем breadcrumbs контейнер
            breadcrumbs = soup.find('div', class_='breadcrumbs')
            if not breadcrumbs:
                # Способ 2: Альтернативные классы для breadcrumbs
                breadcrumbs = soup.find('nav', {'aria-label': 'Хлебные крошки'})
                if not breadcrumbs:
                    breadcrumbs = soup.find('ol', class_='breadcrumb')
            
            if breadcrumbs:
                # Ищем все ссылки в breadcrumbs
                links = breadcrumbs.find_all('a')
                
                # Предпоследний элемент обычно содержит бренд
                if len(links) >= 2:
                    brand_link = links[-1]  # Предпоследняя ссылка
                    brand_text = brand_link.get_text(strip=True)
                    
                    # Очищаем текст от лишних символов
                    brand_text = re.sub(r'^Бренд[:]?\s*', '', brand_text, flags=re.IGNORECASE)
                    
                    if brand_text and brand_text != 'Главная' and not brand_text.isdigit():
                        return brand_text
                
                # Альтернативно: ищем span элементы (последний элемент может быть текстом)
                spans = breadcrumbs.find_all('span')
                for span in spans[-3:]:  # Проверяем последние 3 элемента
                    span_text = span.get_text(strip=True)
                    if (span_text and span_text != 'Главная' and 
                        not span_text.isdigit() and len(span_text) > 2):
                        return span_text
            
            # Способ 3: Поиск в структурированных данных (JSON-LD)
            script = soup.find('script', type='application/ld+json')
            if script:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        data = data[0]
                    
                    # Проверяем различные возможные расположения бренда в JSON-LD
                    brand = data.get('brand', {}).get('name') if isinstance(data.get('brand'), dict) else data.get('brand')
                    if brand:
                        return str(brand)
                    
                    # Альтернативные пути в JSON-LD
                    if data.get('itemListElement'):
                        for item in data['itemListElement']:
                            if isinstance(item, dict) and item.get('item', {}).get('name'):
                                potential_brand = item['item']['name']
                                if potential_brand and potential_brand != 'Главная':
                                    return potential_brand
                                    
                except (json.JSONDecodeError, AttributeError, IndexError):
                    pass
            
            # Способ 4: Резервный поиск в заголовке страницы
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # Ищем бренд в заголовке (обычно формат: "Название товара - Бренд - Wildberries")
                brand_match = re.search(r' - ([^ -]+) - Wildberries', title_text)
                if brand_match:
                    return brand_match.group(1)
            return None
            
        except Exception as e:
            print(f"Brand extraction error: {e}")
            return None
    
    def _extract_rating(self, soup):
        try:
            # Вариант 1: Основное расположение рейтинга
            rating_elem = soup.find('span', class_='product-review__rating')
            
            # Вариант 2: Альтернативное расположение (для некоторых карточек товаров)
            if not rating_elem:
                rating_elem = soup.find('span', class_='product-card__rating')
            
            # Вариант 3: Поиск по data-атрибуту
            if not rating_elem:
                rating_elem = soup.find(attrs={"data-rating": True})
            
            # Вариант 4: Поиск в скрипте (если рейтинг загружается динамически)
            if not rating_elem:
                script_content = soup.find('script', string=re.compile(r'"rating":\d\.\d'))
                if script_content:
                    match = re.search(r'"rating":(\d\.\d)', script_content.string)
                    if match:
                        return float(match.group(1))
            
            if rating_elem:
                # Обработка разных форматов: "4.8", "4,8", "4 из 5"
                rating_text = rating_elem.get_text(strip=True)
                rating_text = rating_text.split()[0]  # Берем первое слово если есть текст
                rating_text = rating_text.replace(',', '.')  # Заменяем запятую на точку
                
                # Извлекаем только цифры и точку
                rating_clean = re.sub(r'[^\d.]', '', rating_text)
                
                return float(rating_clean) if rating_clean else None
            
            return None
        except Exception as e:
            print(f"Rating extraction error: {e}")
            return None
    
    def _extract_feedback_count(self, soup):
        try:
            review_span = soup.find('span', class_='product-review__count-review')
            if not review_span:
                return None
                
            count_text = review_span.get_text(strip=True)
            
            # Удаляем все пробелы между цифрами и оставляем только числа
            count_text_clean = re.sub(r'[^\d]', '', count_text)
            
            # Преобразуем в число только если есть цифры
            return int(count_text_clean) if count_text_clean else None
            
        except Exception as e:
            print(f"Ошибка при извлечении количества оценок: {e}")
            return None
    
    def _extract_seller_info(self, soup):
        try:
            seller_block = soup.find('div', class_='seller-and-brand__item')
            return {
                'name': seller_block.find('div', class_='seller-and-brand__item-name').text.strip(":"),
                'rating': float(seller_block.find('span', class_='seller-and-brand__item-rating-value').text.strip()),
            }
        except:
            return None

