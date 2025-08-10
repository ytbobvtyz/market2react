from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import json
import re

def get_driver():
    options = Options()
    
    # Основные параметры
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Параметры для обхода антибот-систем
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Для Linux сервера
    options.binary_location = "/usr/bin/google-chrome"
    
    # Дополнительные параметры
    options.add_argument("--lang=ru-RU,ru")
    options.add_argument("--accept-lang=ru-RU,ru")
    
    try:
        service = Service(
            ChromeDriverManager().install(),
            service_args=['--verbose'],
            log_path='chromedriver.log'
        )
        
        driver = webdriver.Chrome(service=service, options=options)
        
        # Изменяем свойства браузера, чтобы выглядеть более "человечно"
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3]
                });
            '''
        })
        print ("УСПЕХ в функции get_driver()")
        return driver
    except Exception as e:
        print(f"НЕУДАЧА УСПЕХ в функции get_driver() - Ошибка при создании драйвера: {str(e)}")
        raise

class WBSeleniumParser:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Режим без браузера
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = get_driver()
        self.wait = WebDriverWait(self.driver, 20)
    
    def parse_product(self, url):
        try:
            self.driver.get(url)
            
            # Ждем загрузки страницы
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-page")))
            time.sleep(2)
            # Получаем HTML страницы
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Извлекаем данные (пример - нужно адаптировать под реальную структуру WB)
            product_data = {
                'name': self._extract_name(soup),
                'price': self._extract_price(soup),
                'rating': self._extract_rating(soup),
                'feedback_count': self._extract_feedback_count(soup),
                'brand': self._extract_brand(soup),
                'seller_info': self._extract_seller_info(soup),
                # Добавьте другие параметры, которые вам нужны
            }
            
            return product_data
            
        except Exception as e:
            print(f"Ошибка при парсинге: {e}")
            return None
        finally:
            self.driver.quit()
    
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
        try:
            # Вариант 1: Основное расположение бренда
            brand_elem = soup.find('div', class_='seller-and-brand__item-name')
            
            # Вариант 2: Альтернативное расположение (для некоторых карточек)
            if not brand_elem:
                brand_elem = soup.find('span', class_='product-card__brand')
            
            # Вариант 3: Поиск по data-атрибуту
            if not brand_elem:
                brand_elem = soup.find(attrs={"data-brand-name": True})
            
            # Вариант 4: Поиск в скрипте с JSON-данными
            if not brand_elem:
                script_content = soup.find('script', string=re.compile(r'"brand":'))
                if script_content:
                    match = re.search(r'"brand":"([^"]+)"', script_content.string)
                    if match:
                        return match.group(1)
            
            if brand_elem:
                # Очистка текста от лишних символов
                brand_text = brand_elem.get_text(strip=True)
                
                # Удаление возможных префиксов типа "Бренд:"
                brand_text = re.sub(r'^Бренд[:]?\s*', '', brand_text, flags=re.IGNORECASE)
                
                return brand_text.strip() if brand_text else None
            
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
        

# Пример использования
if __name__ == "__main__":
    parser = WBSeleniumParser()
    product_url = "https://www.wildberries.ru/catalog/452962756/detail.aspx"
    product_url_2 = "https://www.wildberries.ru/catalog/240155230/detail.aspx"
    product_url_3 = "https://www.wildberries.ru/catalog/255412114/detail.aspx"
    urls = ["https://www.wildberries.ru/catalog/452962756/detail.aspx", "https://www.wildberries.ru/catalog/240155230/detail.aspx", "https://www.wildberries.ru/catalog/255412114/detail.aspx"]

    result = parser.parse_product(product_url_3)
    print(json.dumps(result, indent=2, ensure_ascii=False))