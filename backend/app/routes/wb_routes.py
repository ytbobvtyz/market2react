from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter(prefix="/api/wb", tags=["Wildberries"])

@router.get("/product/{nm_id}")
async def get_wb_product(nm_id: str):
    try:
        async with httpx.AsyncClient() as client:
            # Проксируем запрос к WB API
            response = await client.get(
                f"https://card.wb.ru/cards/detail?nm={nm_id}",
                timeout=10.0
            )
            data = response.json()
            
            # Преобразуем данные WB в нашу структуру
            product = data["data"]["products"][0]
            return {
                "name": product["name"],
                "price": product["salePriceU"] / 100,
                "image": f"https://images.wbstatic.net/big/new/{product['id']}/1.jpg",
                "brand": product["brand"],
                "rating": product["rating"],
                "feedbacks": product["feedbacks"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))