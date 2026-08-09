"""
Customer Support Engine - Main Application
AI-powered customer support system for the Autonomous Company OS
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from loguru import logger
import os

from app.config import settings
from app.database import init_db
from app.routers import tickets, ai_responses, knowledge_base, sla, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Customer Support Engine...")
    
    # Initialize database
    await init_db()
    
    logger.info("Customer Support Engine started successfully")
    yield
    
    logger.info("Shutting down Customer Support Engine...")


# Create FastAPI application
app = FastAPI(
    title="Customer Support Engine",
    description="AI-powered customer support system for the Autonomous Company OS",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
app.include_router(ai_responses.router, prefix="/ai", tags=["ai"])
app.include_router(knowledge_base.router, prefix="/kb", tags=["knowledge-base"])
app.include_router(sla.router, prefix="/sla", tags=["sla"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Customer Support Engine",
        "version": "1.0.0",
        "status": "operational",
        "description": "AI-powered customer support system",
        "features": [
            "AI-powered responses",
            "Ticket management",
            "Multi-channel support",
            "Knowledge base integration",
            "SLA tracking",
            "Analytics dashboard"
        ],
        "endpoints": {
            "tickets": "/tickets",
            "ai": "/ai",
            "knowledge-base": "/kb",
            "sla": "/sla",
            "analytics": "/analytics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "customer-support-engine",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8038,
        reload=True
    )
