"""
Agent models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class AgentStatus(str, enum.Enum):
    """Agent status enumeration"""
    AVAILABLE = "available"
    BUSY = "busy"
    AWAY = "away"
    OFFLINE = "offline"


class Agent(TenantBase, Base):
    """Agent model"""
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Agent information
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    
    # Status
    status = Column(Enum(AgentStatus), default=AgentStatus.AVAILABLE)
    
    # Performance metrics
    total_tickets_handled = Column(Integer, default=0)
    average_response_time = Column(Integer, nullable=True)  # in minutes
    average_csat = Column(Integer, nullable=True)
    
    # Specialization
    specialization = Column(JSON, nullable=True)  # List of specializations
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tickets = relationship("Ticket", back_populates="assigned_agent")
    
    def __repr__(self):
        return f"<Agent {self.id} - {self.name} - {self.status}>"
