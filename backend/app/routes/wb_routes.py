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
    try:
        # Основной запрос к WB API
        url = f"https://card.wb.ru/cards/detail?nm={nm_id}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('data', {}).get('products'):
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = data['data']['products'][0]
        
        # Дополнительный запрос для характеристик
        detail_url = f"https://wbx-content-v2.wbstatic.net/ru/{nm_id}.json"
        detail_response = requests.get(detail_url)
        characteristics = detail_response.json().get('grouped_options', []) if detail_response.status_code == 200 else []
        
        return {
            "nmId": product['id'],
            "name": product['name'],
            "brand": product['brand'],
            "rating": product['rating'],
            "price": product['salePriceU'],
            "sellerRating": product['supplierRating'],
            "feedbacks": product['feedbacks'],
            "pics": [f"https://{pic}" for pic in product.get('pics', [])],
            "characteristics": characteristics
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))