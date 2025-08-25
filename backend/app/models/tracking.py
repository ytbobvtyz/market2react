from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Tracking(Base):
    __tablename__ = "trackings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wb_item_id = Column(Integer, nullable=False) 
    custom_name = Column(String)
    desired_price = Column(Numeric(10, 2))
    min_rating = Column(Numeric(3, 2))
    min_comment = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    from sqlalchemy.orm import relationship
    
    # Связи
    user = relationship("User", back_populates="trackings")
    price_history = relationship("PriceHistory", back_populates="tracking", cascade="all, delete-orphan")