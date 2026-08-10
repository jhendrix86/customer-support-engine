"""
Customer Support Engine smoke tests
"""
import pytest


@pytest.mark.asyncio
async def test_app_instantiation():
    """Verify FastAPI app instantiates without error"""
    from app.main import app
    assert app is not None
    assert app.title == "Customer Support Engine"


@pytest.mark.asyncio
async def test_models_import():
    """Verify core models import without error"""
    from app.models import Ticket, Conversation, Knowledge
    assert Ticket is not None
    assert Conversation is not None
    assert Knowledge is not None
