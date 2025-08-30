from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List, Any
from pydantic.types import UUID

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
    id: UUID
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
class ParsingResultCreate(BaseModel):
    query: str
    results: List[dict]  # Список товаров с парсинга
    target_price: Optional[int] = None
    custom_name: Optional[str] = None

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

class PriceHistoryResponse(BaseModel):
    id: UUID
    price: float
    rating: Optional[float] = None
    comment_count: Optional[int] = None
    checked_at: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class TrackingWithHistoryResponse(BaseModel):
    id: UUID
    wb_item_id: int
    custom_name: Optional[str] = None
    desired_price: Optional[float] = None
    is_active: bool
    created_at: datetime
    price_history: List[PriceHistoryResponse]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class TrackingUpdate(BaseModel):
    custom_name: Optional[str] = None
    desired_price: Optional[float] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True