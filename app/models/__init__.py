"""
Database models for Customer Support Engine
"""

from .ticket import Ticket, TicketPriority, TicketStatus, TicketChannel
from .customer import Customer, CustomerTier
from .agent import Agent, AgentStatus
from .response import Response, ResponseType
from .knowledge_article import KnowledgeArticle
from .tenant import Tenant
from .tenant_base import TenantBase, apply_tenant_context

__all__ = [
    'Ticket',
    'TicketPriority',
    'TicketStatus',
    'TicketChannel',
    'Customer',
    'CustomerTier',
    'Agent',
    'AgentStatus',
    'Response',
    'ResponseType',
    'KnowledgeArticle',
    'Tenant',
    'TenantBase',
    'apply_tenant_context'
]
