import requests
from ..base_parser import BaseParser

class WBApiParser(BaseParser):
    BASE_URL = "https://wbx-content-v2.wbstatic.net/ru/{article}.json"
    
    def parse(self, article: str) -> dict:
        try:
            response = requests.get(self.BASE_URL.format(article=article), timeout=5)
            response.raise_for_status()
            data = response.json()
            
            return {
                'name': data.get('imt_name'),
                'price': data.get('salePriceU') / 100 if data.get('salePriceU') else None,
                'brand': data.get('selling', {}).get('brand_name'),
                'rating': data.get('reviewRating'),
                'feedback_count': data.get('feedbacks')
            }
        except Exception as e:
            raise Exception(f"WB API Error: {str(e)}")