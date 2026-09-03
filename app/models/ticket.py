"""
Ticket models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, Text, JSON
from sqlalchemy import Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class TicketPriority(str, enum.Enum):
    """Ticket priority enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TicketStatus(str, enum.Enum):
    """Ticket status enumeration"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class TicketChannel(str, enum.Enum):
    """Ticket channel enumeration"""
    EMAIL = "email"
    CHAT = "chat"
    PHONE = "phone"
    SOCIAL = "social"
    WEB = "web"


class Ticket(TenantBase, Base):
    """Ticket model"""
    __tablename__ = "tickets"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(Uuid(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    assigned_agent_id = Column(Uuid(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    
    # Ticket details
    subject = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    channel = Column(Enum(TicketChannel), nullable=False)
    
    # SLA
    sla_deadline = Column(DateTime, nullable=True)
    sla_violated = Column(Boolean, default=False)
    
    # Resolution
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Customer satisfaction
    csat_score = Column(Integer, nullable=True)
    csat_comment = Column(Text, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="tickets")
    assigned_agent = relationship("Agent", back_populates="tickets")
    responses = relationship("Response", back_populates="ticket")
    
    def __repr__(self):
        return f"<Ticket {self.id} - {self.priority} - {self.status}>"
