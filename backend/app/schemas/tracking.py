from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List, Any
import uuid
import json

class TrackingBase(BaseModel):
    wb_item_id: int
    custom_name: Optional[str] = None
    desired_price: Optional[float] = None
    min_rating: Optional[float] = None
    min_comment: Optional[int] = None
    is_active: bool = True

class TrackingCreate(TrackingBase):
    pass

class TrackingResponse(TrackingBase):
    id: uuid.UUID
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ParsingResultCreate(BaseModel):
    query: str
    results: List[dict]  # Список товаров с парсинга
    target_price: Optional[int] = None
    
    @field_validator('results')
    @classmethod
    def validate_results(cls, v):
        if not isinstance(v, list):
            raise ValueError('Results must be a list')
        
        # Дополнительная проверка, что все элементы - словари
        for item in v:
            if not isinstance(item, dict):
                raise ValueError('All items in results must be dictionaries')
        
        return v