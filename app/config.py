"""
Configuration management for Customer Support Engine
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/support")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # AI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "gpt-4")
    auto_response_enabled: bool = os.getenv("AUTO_RESPONSE_ENABLED", "true").lower() == "true"
    
    # Email
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")
    support_email: str = os.getenv("SUPPORT_EMAIL", "support@company.com")
    
    # Knowledge Base
    knowledge_base_url: str = os.getenv("KNOWLEDGE_BASE_URL", "")
    
    # SLA
    default_sla_hours: int = int(os.getenv("DEFAULT_SLA_HOURS", "24"))
    sla_critical_hours: int = int(os.getenv("SLA_CRITICAL_HOURS", "1"))
    sla_high_hours: int = int(os.getenv("SLA_HIGH_HOURS", "4"))
    sla_medium_hours: int = int(os.getenv("SLA_MEDIUM_HOURS", "24"))
    sla_low_hours: int = int(os.getenv("SLA_LOW_HOURS", "48"))
    
    # Application
    app_name: str = "Customer Support Engine"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Integration
    notification_engine_url: str = os.getenv("NOTIFICATION_ENGINE_URL", "http://localhost:8037")
    knowledge_graph_url: str = os.getenv("KNOWLEDGE_GRAPH_URL", "http://localhost:8034")
    revenue_operations_url: str = os.getenv("REVENUE_OPERATIONS_URL", "http://localhost:8036")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
