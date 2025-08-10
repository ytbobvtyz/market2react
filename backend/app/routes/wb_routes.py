from fastapi import APIRouter, HTTPException
import requests
from pydantic import BaseModel

router = APIRouter()

class WBProductResponse(BaseModel):
    nmId: int
    name: str
    brand: str
    rating: float
    price: int
    sellerRating: float
    feedbacks: int
    pics: list[str]
    characteristics: list[dict]


@router.get("/product/{nm_id}", response_model=WBProductResponse)
async def get_wb_product(nm_id: int):
    """
    Получает данные конкретного товара по его артикулу (nm_id) с Wildberries API
    Возвращает словарь с основными характеристиками товара или None, если товар не найден
    """
    # Основной API для получения данных по конкретному товару
    card_url = "https://card.wb.ru/cards/detail"
    params = {
        "nm": nm_id,
        "curr": "rub",
        "dest": -1257786,
        "regions": "80,64,83,4,38,33,70,82,69,68,86,30,40,48,1,22,66,31"
    }
    
    try:
        response = requests.get(card_url, params=params)
        response.raise_for_status()  # Проверка на ошибки HTTP
        
        data = response.json()
        
        # Проверяем, что товар найден
        if not data.get("data", {}).get("products"):
            return None
            
        product = data["data"]["products"][0]
        
        # Формируем структурированный результат
        result = {
            "nm_id": str(product["id"]),
            "name": product["name"],
            "price": float(product["salePriceU"] / 100),
            "brand": product["brand"],
            "seller": product["supplier"],
            "rating": product["supplierRating"],
            "feedbacks": product["feedbacks"],
            "quantity": product["quantity"] if "quantity" in product else None,
            "pics": [f"https://{pic}" for pic in product.get("pics", [])],
            "characteristics": product.get("characteristics", []),
            "wb_url": f"https://www.wildberries.ru/catalog/{product['id']}/detail.aspx"
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к WB API: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Ошибка парсинга ответа WB API: {e}")
        return None

def parse_wb_api(query):
    url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
    params = {
        "query": query,
        "resultset": "catalog",
        "limit": 100,
        "sort": "popular",
        "dest": -1257786,
        "curr": "rub",
        "regions": "80,64,83,4,38,33,70,82,69,68,86,30,40,48,1,22,66,31"
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        products = response.json()["data"]["products"]
        results =[]
        for product in products:
            print(product)
            results.append({
                "name": product["name"],
                "price": float(product["salePriceU"]/100),
                "nm_id": str(product["id"]),
                "vendor_code": str(product["id"]),
                "seller":product["supplier"],
                "brand":product["brand"],
                "rating":product["supplierRating"],
                "quantity":product["totalQuantity"],
                "subjectId":product["subjectId"],
                "entity":product["entity"]
                })
        return results
        # return products
    return []
if __name__ == "__main__":
    print(parse_wb_api("452962756"))
    # import asyncio
    
    # async def test():
    #     result = await get_wb_product(452962756)
    #     print(result)
    
    # asyncio.run(test())