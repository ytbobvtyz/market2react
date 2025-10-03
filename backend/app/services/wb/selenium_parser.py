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
        self.temp_dir = None  # Добавляем хранение пути к temp dir
# Добавляем свойство для хранения текущего артикула
    @property
    def current_article(self):
        return getattr(self, '_current_article', 'unknown')

    @current_article.setter
    def current_article(self, value):
        self._current_article = value

    def get_full_page_text(self):
        """
        Получает весь видимый текст страницы (аналог Ctrl+A)
        Этот метод должен быть объявлен в классе
        """
        try:
            # Ожидаем загрузки body
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Получаем весь текст body
            body_element = self.driver.find_element(By.TAG_NAME, "body")
            full_text = body_element.text
            
            print(f"Получено текста: {len(full_text)} символов")
            return full_text
            
        except Exception as e:
            print(f"Ошибка получения текста страницы: {e}")
            return None
        
    def parse(self, article: str) -> dict:
        try:
            self.current_article = article
            # Инициализируем драйвер
            self.driver = get_driver()
            # Сохраняем temp_dir из драйвера для последующей очистки
            self.temp_dir = getattr(self.driver, 'temp_dir', None)
            
            # ... остальная логика парсинга без изменений ...
            
        except Exception as e:
            self._cleanup()
            raise
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Очистка ресурсов включая временные файлы"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
                self.wait = None
        
        # Очищаем временные файлы
        if hasattr(self, 'temp_dir') and self.temp_dir:
            try:
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except:
                pass
            
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
            # with open(f"debug_{self.current_article}.html", "w", encoding="utf-8") as f:
            #     f.write(html)
            # print(f"HTML сохранен в debug_{self.current_article}.html")
            
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
        """Улучшенный метод извлечения цены с приоритетом поиска пар"""
        try:
            # Сначала пробуем традиционные методы
            traditional_price = self._try_traditional_methods(soup)
            if traditional_price:
                print(f"Цена найдена традиционным методом: {traditional_price} ₽")
                return traditional_price
            
            # Если не сработало - получаем весь текст страницы
            print("Традиционные методы не сработали, ищем в полном тексте...")
            full_text = self.get_full_page_text()
            
            if not full_text:
                return None
            
            # Сохраняем текст для отладки
            # with open(f"full_text_{self.current_article}.txt", "w", encoding="utf-8") as f:
            #     f.write(full_text)
            # print(f"Полный текст сохранён в full_text_{self.current_article}.txt")
            
            # Сначала ищем пары цен (более надёжный метод)
            price = self._find_price_in_text(full_text)
            if price:
                print(f"Цена найдена через поиск пар: {price} ₽")
                return price
            
            print("Цена не найдена даже в полном тексте")
            return None
            
        except Exception as e:
            print(f"Ошибка в улучшенном extract_price: {e}")
            return None
    
    def _try_traditional_methods(self, soup):
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
            return None
        except Exception as e:
            print(f"Ошибка извлечения цены: {e}")
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

    def _find_price_in_text(self, text):
        """Ищет первую пару цен в тексте, предварительно проверяя наличие товара"""
        try:
            print("Проверяем наличие товара...")
            
            # Сначала проверяем, есть ли товар в наличии
            out_of_stock_phrases = [
                'нет в наличии',
                'товара нет в наличии',
                'недоступен для покупки',
                'раскупили',
                'закончился',
                'out of stock',
                'недоступно'
            ]
            
            text_lower = text.lower()
            for phrase in out_of_stock_phrases:
                if phrase in text_lower:
                    print(f"Товар отсутствует: найдена фраза '{phrase}'")
                    return None
            
            print("Товар в наличии, ищем цену...")
            
            # Основной паттерн для поиска пар цен: "ЦЕНА ₽ ЦЕНА ₽"
            price_pair_patterns = [
                r'(\d{1,3}(?:\s\d{3})*)\s*₽\s*(\d{1,3}(?:\s\d{3})*)\s*₽',  # 1 196 ₽ 3 000 ₽
                r'(\d+)\s*₽\s*(\d+)\s*₽',  # 1196 ₽ 3000 ₽
                r'цена[^\d]*(\d[\d\s]*)\s*₽[^\d]*(\d[\d\s]*)\s*₽',  # цена 1 196 ₽ 3 000 ₽
            ]
            
            # Ищем первую подходящую пару цен
            for pattern in price_pair_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    price1_text = match.group(1)
                    price2_text = match.group(2)
                    
                    price1 = self._parse_single_price(price1_text)
                    price2 = self._parse_single_price(price2_text)
                    
                    if price1 and price2:
                        # Выбираем меньшую цену как актуальную
                        actual_price = min(price1, price2)
                        print(f"Найдена пара цен: {price1} ₽ и {price2} ₽ → берём {actual_price} ₽")
                        return actual_price
            
            # Если не нашли пар, ищем одиночные цены
            print("Пар цен не найдено, ищем одиночные цены...")
            return self._find_single_price_in_text(text)
            
        except Exception as e:
            print(f"Ошибка поиска пар цен в тексте: {e}")
            return None
        
    def _find_single_price_in_text(self, text):
        """Резервный метод для поиска одиночных цен"""
        try:
            single_price_patterns = [
                r'(\d{1,3}(?:\s\d{3})*)\s*₽',  # 1 196 ₽
                r'цена[^\d]*(\d[\d\s]*)\s*₽',  # цена 1 196 ₽
                r'купить за[^\d]*(\d[\d\s]*)\s*₽',  # купить за 1 196 ₽
                r'final.price[^\d]*(\d+)\s*₽',  # final price 1196 ₽
            ]
            
            found_prices = []
            
            for pattern in single_price_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for price_text in matches:
                    price = self._parse_single_price(price_text)
                    if price and self._is_realistic_price(price):
                        found_prices.append(price)
                        print(f"Найдена одиночная цена: {price} ₽")
            
            if found_prices:
                # Для одиночных цен берём минимальную (наиболее вероятно актуальную)
                actual_price = min(found_prices)
                print(f"Выбрана минимальная из одиночных цен: {actual_price} ₽")
                return actual_price
            
            return None
            
        except Exception as e:
            print(f"Ошибка поиска одиночных цен: {e}")
            return None

    def _parse_single_price(self, price_text):
        """Парсит отдельную цену из текста"""
        try:
            if not price_text:
                return None
                
            # Очищаем текст: убираем пробелы, &nbsp; и нецифровые символы
            cleaned_text = str(price_text).replace(' ', '').replace('&nbsp;', '').replace('\u202f', '')
            cleaned_text = re.sub(r'[^\d]', '', cleaned_text)
            
            if cleaned_text and cleaned_text.isdigit():
                price = int(cleaned_text)
                return price
                
            return None
            
        except Exception as e:
            print(f"Ошибка парсинга отдельной цены '{price_text}': {e}")
            return None

    def _is_realistic_price(self, price):
        """Проверяет, что цена реалистичная (отсеивает артикулы, рейтинги и т.д.)"""
        try:
            # Цены обычно в диапазоне 10 - 500 000 рублей
            return 10 <= price <= 500000
        except:
            return False

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

