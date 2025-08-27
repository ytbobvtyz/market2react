from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..base_parser import BaseParser
from app.config import get_driver
import re
import time
from bs4 import BeautifulSoup
import json

class WBSeleniumParser(BaseParser):
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def parse(self, article: str) -> dict:
        """Основной метод парсинга через Selenium"""
        try:
            # Инициализируем драйвер и wait
            self.driver = get_driver()
            self.wait = WebDriverWait(self.driver, 20)
            
            print(f"Парсим артикул: {article}")
            self.driver.get(f"https://www.wildberries.ru/catalog/{article}/detail.aspx")
            
            # Добавляем подробное логирование
            print("URL загружен, ожидаем элементы...")
            
            # Ожидаем различные элементы с таймаутами
            try:
                # Ожидаем загрузки страницы по разным элементам
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("Body загружен")
                
                # Дополнительные ожидания для ключевых элементов
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                print("H1 найден")
                
                # Ждем немного для полной загрузки
                time.sleep(2)
                
            except Exception as e:
                print(f"Ошибка ожидания элементов: {e}")
                # Продолжаем парсинг даже если некоторые элементы не загрузились
                
            # Получаем HTML страницы
            html = self.driver.page_source
            
            # Сохраняем HTML для отладки
            with open(f"debug_{article}.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"HTML сохранен в debug_{article}.html")
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Детальный парсинг с логированием
            product_data = {
                'name': self._extract_name(soup),
                'price': self._extract_price(soup),
                'brand': self._extract_brand(soup),
                'rating': self._extract_rating(soup),
                'feedback_count': self._extract_feedback_count(soup),
            }
            
            print("Результат парсинга:", product_data)
            
            # Проверяем, что хотя бы некоторые данные получены
            if all(value is None for value in product_data.values()):
                print("ВНИМАНИЕ: Все данные None! Возможно, антибот-защита")
                
            return product_data
            
        except Exception as e:
            print(f"Критическая ошибка парсинга: {e}")
            if self.driver:
                self.driver.quit()
                self.driver = None
            raise
        finally:
            # Всегда закрываем драйвер
            if self.driver:
                self.driver.quit()
                self.driver = None

    def _extract_name(self, soup):
        try:
            name = soup.find('h1', class_='product-page__title')
            if name:
                result = name.text.strip()
                print(f"Найдено название: {result}")
                return result
            
            # Альтернативные селекторы
            selectors = [
                'h1.product-name',
                'h1.title',
                '[data-tag="productName"]',
                '.product-card__name'
            ]
            
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    result = elem.text.strip()
                    print(f"Найдено название (альтернативный селектор): {result}")
                    return result
            
            print("Название не найдено")
            return None
            
        except Exception as e:
            print(f"Ошибка извлечения названия: {e}")
            return None

    def _extract_price(self, soup):
        try:
            price_selectors = [
                'span.price-block__final-price',
                'ins.price-block__final-price',
                '[data-tag="finalPrice"]',
                '.price-block__wallet-price',
                '.final-price',
                '.j-final-price',
                '.price-block__price'  # Добавляем дополнительные селекторы
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem and price_elem.text.strip():
                    price_text = price_elem.text.strip()
                    print(f"Найдена цена через селектор {selector}: {price_text}")
                    
                    # Извлекаем цифры
                    digits = re.sub(r'[^\d]', '', price_text)
                    if digits:
                        result = int(digits)
                        print(f"Цена после обработки: {result}")
                        return result
            
            # Поиск в JSON-LD
            script = soup.find('script', type='application/ld+json')
            if script:
                try:
                    data = json.loads(script.string)
                    # Проверяем разные возможные пути к цене в JSON-LD
                    price_paths = [
                        data.get('offers', {}).get('price'),
                        data.get('offers', {}).get('priceCurrency'),
                        data.get('mainEntity', {}).get('offers', {}).get('price'),
                        data.get('product', {}).get('offers', {}).get('price')
                    ]
                    
                    for price in price_paths:
                        if price and isinstance(price, (int, float)):
                            print(f"Цена из JSON-LD: {price}")
                            return float(price)
                except Exception as json_error:
                    print(f"Ошибка парсинга JSON-LD: {json_error}")
            
            # РЕЗЕРВНЫЙ СПОСОБ: Поиск цены в title и meta-тегах
            return self._extract_price_from_meta(soup)
                
        except Exception as e:
            print(f"Ошибка извлечения цены: {e}")
            return None

    def _extract_price_from_meta(self, soup):
        """
        Резервный метод извлечения цены из meta-тегов и title
        """
        try:
            print("Пытаемся извлечь цену из meta-тегов и title...")
            
            # 1. Поиск в meta description
            meta_description = soup.find('meta', {'name': 'description'})
            if meta_description and meta_description.get('content'):
                description = meta_description['content']
                print(f"Meta description: {description}")
                
                # Ищем паттерны типа "купить за 44 404 ₽"
                price_patterns = [
                    r'купить за\s+([\d\s&nbsp;]+?₽)',
                    r'цена\s+([\d\s&nbsp;]+?₽)',
                    r'стоимость\s+([\d\s&nbsp;]+?₽)',
                    r'за\s+([\d\s&nbsp;]+?₽)'
                ]
                
                for pattern in price_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        price_text = match.group(1)
                        print(f"Найдена цена в description: {price_text}")
                        return self._parse_price_text(price_text)
            
            # 2. Поиск в title
            title = soup.find('title')
            if title and title.text:
                title_text = title.text
                print(f"Title: {title_text}")
                
                # Ищем паттерны в title
                title_patterns = [
                    r'купить за\s+([\d\s&nbsp;]+?₽)',
                    r'за\s+([\d\s&nbsp;]+?₽)',
                    r'([\d\s&nbsp;]+?₽)\s+в интернет',
                    r'цена\s+([\d\s&nbsp;]+?₽)'
                ]
                
                for pattern in title_patterns:
                    match = re.search(pattern, title_text, re.IGNORECASE)
                    if match:
                        price_text = match.group(1)
                        print(f"Найдена цена в title: {price_text}")
                        return self._parse_price_text(price_text)
            
            # 3. Поиск в других meta-тегах
            meta_og_price = soup.find('meta', property='og:price:amount')
            if meta_og_price and meta_og_price.get('content'):
                price = meta_og_price['content']
                print(f"Цена из og:price:amount: {price}")
                return float(price)
            
            meta_product_price = soup.find('meta', {'itemprop': 'price'})
            if meta_product_price and meta_product_price.get('content'):
                price = meta_product_price['content']
                print(f"Цена из itemprop=price: {price}")
                return float(price)
            
            print("Цена не найдена в meta-тегах")
            return None
            
        except Exception as e:
            print(f"Ошибка извлечения цены из meta: {e}")
            return None

    def _parse_price_text(self, price_text):
        """
        Преобразует текстовое представление цены в число
        Пример: "44&nbsp;404&nbsp;₽" -> 44404
        """
        try:
            # Заменяем &nbsp; на пробелы и удаляем всё кроме цифр
            cleaned_text = price_text.replace('&nbsp;', ' ').replace(' ', '')
            
            # Удаляем всё кроме цифр
            digits = re.sub(r'[^\d]', '', cleaned_text)
            
            if digits:
                result = int(digits)
                print(f"Цена преобразована: {price_text} -> {result}")
                return result
            else:
                print(f"Не удалось извлечь цифры из: {price_text}")
                return None
                
        except Exception as e:
            print(f"Ошибка преобразования цены: {e}")
            return None
        
    def _extract_brand(self, soup):
        """
        Простой метод извлечения бренда из ссылок, содержащих /brands/
        """
        try:
            # Ищем все ссылки на странице
            all_links = soup.find_all('a', href=True)
            
            # Фильтруем ссылки, содержащие /brands/
            brand_links = [link for link in all_links if '/brands/' in link['href']]
            
            print(f"Найдено {len(brand_links)} ссылок с /brands/")
            
            for link in brand_links:
                href = link['href']
                print(f"Анализируем ссылку: {href}")
                
                # Извлекаем бренд из URL
                brand = self._extract_brand_from_url(href)
                if brand:
                    print(f"Найден бренд: {brand}")
                    return brand
            
            # Если в ссылках не нашли, ищем в JavaScript данных
            return self._extract_brand_from_scripts(soup)
            
        except Exception as e:
            print(f"Ошибка извлечения бренда: {e}")
            return None

    def _extract_brand_from_url(self, url):
        """
        Извлекает бренд из URL вида /brands/BRAND_NAME/
        """
        try:
            # Ищем паттерн /brands/название-бренда/
            pattern = r'/brands/([^/"/?]+)'
            match = re.search(pattern, url)
            
            if match:
                brand = match.group(1)
                
                # Декодируем URL-encoded символы
                import urllib.parse
                brand = urllib.parse.unquote(brand)
                
                # Заменяем дефисы на пробелы и capitalizе
                brand = brand.replace('-', ' ').replace('_', ' ').title()
                
                # Убираем цифры и специальные символы в конце
                brand = re.sub(r'[\d\-_]+$', '', brand).strip()
                
                return brand if brand else None
                
            return None
            
        except Exception as e:
            print(f"Ошибка извлечения бренда из URL: {e}")
            return None

    def _extract_brand_from_scripts(self, soup):
        """
        Резервный метод: поиск бренда в script тегах
        """
        try:
            # Ищем в JSON-LD данных
            script = soup.find('script', type='application/ld+json')
            if script:
                try:
                    data = json.loads(script.string)
                    brand = data.get('brand', {}).get('name') if isinstance(data.get('brand'), dict) else data.get('brand')
                    if brand:
                        print(f"Найден бренд в JSON-LD: {brand}")
                        return str(brand)
                except:
                    pass
            
            # Ищем в JavaScript переменных
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Ищем паттерны типа brand: "NAME", brandName: "NAME"
                    patterns = [
                        r'brand["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        r'brandName["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        r'vendor["\']?\s*[:=]\s*["\']([^"\']+)["\']'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, script.string)
                        if match:
                            brand = match.group(1)
                            print(f"Найден бренд в script: {brand}")
                            return brand
            
            return None
            
        except Exception as e:
            print(f"Ошибка извлечения бренда из scripts: {e}")
            return None
    
    def _extract_rating(self, soup):
        """
        Универсальный метод извлечения рейтинга по классам содержащим 'product' и 'rating'
        """
        try:
            # Ищем все span элементы
            all_spans = soup.find_all('span')
            
            # Фильтруем span'ы у которых в классе есть и 'product' и 'rating'
            rating_spans = []
            for span in all_spans:
                if span.get('class'):
                    classes = ' '.join(span.get('class')).lower()
                    if 'product' in classes and 'rating' in classes:
                        rating_spans.append(span)
                        print(f"Найден потенциальный рейтинг-span: {span}")
            
            print(f"Найдено {len(rating_spans)} span'ов с product и rating в классах")
            
            # Проверяем найденные span'ы
            for span in rating_spans:
                rating_text = span.get_text(strip=True)
                print(f"Текст рейтинга: '{rating_text}'")
                
                if rating_text:
                    rating_value = self._parse_rating_text(rating_text)
                    if rating_value is not None:
                        print(f"Успешно извлечен рейтинг: {rating_value}")
                        return rating_value
            
            # Если не нашли, пробуем альтернативные методы
            return self._find_rating_alternative(soup)
                
        except Exception as e:
            print(f"Ошибка извлечения рейтинга: {e}")
            return None

    def _parse_rating_text(self, rating_text):
        """
        Парсит текст рейтинга в float
        """
        try:
            # Очищаем текст: удаляем лишние символы, заменяем запятые на точки
            cleaned_text = rating_text.strip()
            cleaned_text = re.sub(r'[^\d,.]', '', cleaned_text)  # Оставляем только цифры и разделители
            cleaned_text = cleaned_text.replace(',', '.')  # Заменяем запятые на точки
            
            # Пробуем преобразовать в float
            rating_value = float(cleaned_text)
            
            # Проверяем что рейтинг в разумных пределах (обычно 0-5)
            if 0 <= rating_value <= 5:
                return rating_value
            else:
                print(f"Рейтинг вне диапазона 0-5: {rating_value}")
                return None
                
        except (ValueError, TypeError):
            print(f"Не удалось преобразовать в число: '{rating_text}'")
            return None

    def _find_rating_alternative(self, soup):
        """
        Альтернативные методы поиска рейтинга
        """
        try:
            # 1. Поиск по data-атрибутам
            rating_elements = soup.find_all(attrs={"data-rating": True})
            for elem in rating_elements:
                rating_value = self._parse_rating_text(elem['data-rating'])
                if rating_value is not None:
                    print(f"Найден рейтинг в data-атрибуте: {rating_value}")
                    return rating_value
            
            # 2. Поиск в мета-тегах
            meta_rating = soup.find('meta', itemprop="ratingValue")
            if meta_rating and meta_rating.get('content'):
                rating_value = self._parse_rating_text(meta_rating['content'])
                if rating_value is not None:
                    print(f"Найден рейтинг в meta-теге: {rating_value}")
                    return rating_value
            
            # 4. Поиск в JSON-LD
            script = soup.find('script', type='application/ld+json')
            if script:
                try:
                    data = json.loads(script.string)
                    rating = data.get('aggregateRating', {}).get('ratingValue')
                    if rating:
                        rating_value = self._parse_rating_text(str(rating))
                        if rating_value is not None:
                            print(f"Найден рейтинг в JSON-LD: {rating_value}")
                            return rating_value
                except:
                    pass
            
            print("Рейтинг не найден")
            return None
            
        except Exception as e:
            print(f"Ошибка альтернативного поиска рейтинга: {e}")
            return None
    
    def _extract_feedback_count(self, soup):
        """
        Универсальный метод извлечения количества отзывов по классам содержащим 'product' и 'count'
        """
        try:
            # Ищем все span элементы
            all_spans = soup.find_all('span')
            
            # Фильтруем span'ы у которых в классе есть и 'product' и 'count'
            count_spans = []
            for span in all_spans:
                if span.get('class'):
                    classes = ' '.join(span.get('class')).lower()
                    if 'product' in classes and 'count' in classes:
                        count_spans.append(span)
                        print(f"Найден потенциальный count-span: {span}")
            
            print(f"Найдено {len(count_spans)} span'ов с product и count в классах")
            
            # Проверяем найденные span'ы
            for span in count_spans:
                count_text = span.get_text(strip=True)
                print(f"Текст количества отзывов: '{count_text}'")
                
                if count_text:
                    count_value = self._parse_count_text(count_text)
                    if count_value is not None:
                        print(f"Успешно извлечено количество отзывов: {count_value}")
                        return count_value
            
            # Если не нашли, пробуем альтернативные методы
            return self._find_feedback_count_alternative(soup)
                
        except Exception as e:
            print(f"Ошибка извлечения количества отзывов: {e}")
            return None

    def _parse_count_text(self, count_text):
        """
        Парсит текст количества отзывов в int
        Обрабатывает форматы: "4&nbsp;529 оценок", "152 отзыва", "1,234 reviews"
        """
        try:
            # Очищаем текст: оставляем только цифры и пробелы/разделители
            cleaned_text = count_text.strip()
            
            # Удаляем все не-цифровые символы кроме пробелов и запятых (для тысяч)
            cleaned_text = re.sub(r'[^\d\s,]', '', cleaned_text)
            
            # Заменяем запятые на пробелы (для формата "1,234")
            cleaned_text = cleaned_text.replace(',', ' ')
            
            # Заменяем множественные пробелы на одинарные
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            
            # Удаляем все пробелы и преобразуем в число
            digits_only = cleaned_text.replace(' ', '')
            
            if digits_only:
                count_value = int(digits_only)
                
                # Проверяем что количество в разумных пределах
                if count_value >= 0:
                    return count_value
                else:
                    print(f"Количество отзывов отрицательное: {count_value}")
                    return None
            else:
                print("Не найдено цифр в тексте")
                return None
                
        except (ValueError, TypeError) as e:
            print(f"Не удалось преобразовать в число: '{count_text}' - {e}")
            return None

    def _find_feedback_count_alternative(self, soup):
        """
        Альтернативные методы поиска количества отзывов
        """
        try:
            # 1. Поиск по data-атрибутам
            count_elements = soup.find_all(attrs={"data-count": True})
            for elem in count_elements:
                count_value = self._parse_count_text(elem['data-count'])
                if count_value is not None:
                    print(f"Найдено количество в data-атрибуте: {count_value}")
                    return count_value
            
            # 2. Поиск по классам содержащим 'review', 'feedback', 'comment'
            count_patterns = ['review', 'feedback', 'comment', 'оцен', 'отзыв']
            
            for pattern in count_patterns:
                elements = soup.find_all(class_=re.compile(pattern, re.IGNORECASE))
                for elem in elements:
                    count_text = elem.get_text(strip=True)
                    count_value = self._parse_count_text(count_text)
                    if count_value is not None:
                        print(f"Найдено количество в элементе с '{pattern}': {count_value}")
                        return count_value
            
            # 3. Поиск в мета-тегах
            meta_review_count = soup.find('meta', itemprop="reviewCount")
            if meta_review_count and meta_review_count.get('content'):
                count_value = self._parse_count_text(meta_review_count['content'])
                if count_value is not None:
                    print(f"Найдено количество в meta-теге: {count_value}")
                    return count_value
            
            # 4. Поиск в JSON-LD
            script = soup.find('script', type='application/ld+json')
            if script:
                try:
                    data = json.loads(script.string)
                    review_count = data.get('aggregateRating', {}).get('reviewCount')
                    if review_count:
                        count_value = self._parse_count_text(str(review_count))
                        if count_value is not None:
                            print(f"Найдено количество в JSON-LD: {count_value}")
                            return count_value
                except:
                    pass
            
            # 5. Поиск по тексту содержащему "оценок", "отзывов", "reviews"
            text_patterns = [
                r'(\d[\d\s]*) оценок',
                r'(\d[\d\s]*) отзывов',
                r'(\d[\d\s]*) reviews',
                r'(\d[\d\s]*) feedbacks'
            ]
            
            for pattern in text_patterns:
                matches = re.findall(pattern, soup.get_text(), re.IGNORECASE)
                for match in matches:
                    if match:
                        count_value = self._parse_count_text(match)
                        if count_value is not None:
                            print(f"Найдено количество по текстовому паттерну: {count_value}")
                            return count_value
            
            print("Количество отзывов не найдено")
            return None
            
        except Exception as e:
            print(f"Ошибка альтернативного поиска количества отзывов: {e}")
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

