"""
Customer models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class CustomerTier(str, enum.Enum):
    """Customer tier enumeration"""
    FREE = "free"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Customer(Base):
    """Customer model"""
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Contact information
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Customer tier
    tier = Column(Enum(CustomerTier), default=CustomerTier.STANDARD)
    
    # Support history
    total_tickets = Column(Integer, default=0)
    open_tickets = Column(Integer, default=0)
    average_csat = Column(Integer, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tickets = relationship("Ticket", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer {self.id} - {self.email} - {self.tier}>"
