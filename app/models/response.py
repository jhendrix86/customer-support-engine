"""
Response models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, Text, JSON
from sqlalchemy import Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class ResponseType(str, enum.Enum):
    """Response type enumeration"""
    AI_GENERATED = "ai_generated"
    AGENT = "agent"
    SYSTEM = "system"


class Response(TenantBase, Base):
    """Response model"""
    __tablename__ = "responses"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(Uuid(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    agent_id = Column(Uuid(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    
    # Response details
    message = Column(Text, nullable=False)
    response_type = Column(Enum(ResponseType), nullable=False)
    
    # AI-specific
    ai_model = Column(String(50), nullable=True)
    confidence_score = Column(Integer, nullable=True)
    knowledge_articles_used = Column(JSON, nullable=True)
    
    # Sentiment
    sentiment = Column(String(20), nullable=True)
    sentiment_score = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="responses")
    
    def __repr__(self):
        return f"<Response {self.id} - {self.response_type}>"
