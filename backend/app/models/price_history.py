from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_id = Column(UUID(as_uuid=True), ForeignKey("trackings.id"), nullable=False)
    wb_id = Column(Integer, nullable=False)
    wb_name = Column(Text)
    rating = Column(Numeric(3, 2))
    comment_count = Column(Integer)
    price = Column(Numeric(10, 2), nullable=False)
    checked_at = Column(TIMESTAMP, server_default=func.now())
    
    # Связь
    tracking = relationship("Tracking", back_populates="price_history")