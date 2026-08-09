"""
Real tests for the SQLAlchemy models - these were previously completely
untested despite being the only real (non-mock) part of this engine. Verifies
the schema actually creates, relationships resolve in both directions, and
enum columns round-trip correctly - the same class of bug (a broken
relationship, a missing column) found and fixed elsewhere in this fleet this
session.
"""

import uuid

from sqlalchemy import select

from app.models.customer import Customer, CustomerTier
from app.models.agent import Agent, AgentStatus
from app.models.ticket import Ticket, TicketPriority, TicketStatus, TicketChannel
from app.models.response import Response, ResponseType
from app.models.knowledge_article import KnowledgeArticle


async def test_customer_and_ticket_relationship_round_trips(db_session):
    customer = Customer(email="jane@example.com", name="Jane Doe", tier=CustomerTier.PROFESSIONAL)
    db_session.add(customer)
    await db_session.flush()

    ticket = Ticket(
        customer_id=customer.id,
        subject="Billing question",
        message="Why was I charged twice?",
        priority=TicketPriority.HIGH,
        status=TicketStatus.OPEN,
        channel=TicketChannel.EMAIL,
    )
    db_session.add(ticket)
    await db_session.commit()

    result = await db_session.execute(select(Customer).where(Customer.id == customer.id))
    fetched_customer = result.scalar_one()
    await db_session.refresh(fetched_customer, attribute_names=["tickets"])

    assert len(fetched_customer.tickets) == 1
    assert fetched_customer.tickets[0].subject == "Billing question"
    assert fetched_customer.tickets[0].priority == TicketPriority.HIGH


async def test_agent_assignment_relationship_round_trips(db_session):
    customer = Customer(email="cust@example.com")
    agent = Agent(name="Alice", email="alice@company.com", status=AgentStatus.AVAILABLE)
    db_session.add_all([customer, agent])
    await db_session.flush()

    ticket = Ticket(
        customer_id=customer.id,
        assigned_agent_id=agent.id,
        subject="Login issue",
        message="Can't log in",
        channel=TicketChannel.CHAT,
    )
    db_session.add(ticket)
    await db_session.commit()

    result = await db_session.execute(select(Agent).where(Agent.id == agent.id))
    fetched_agent = result.scalar_one()
    await db_session.refresh(fetched_agent, attribute_names=["tickets"])

    assert len(fetched_agent.tickets) == 1
    assert fetched_agent.tickets[0].id == ticket.id
    assert fetched_agent.tickets[0].assigned_agent.name == "Alice"


async def test_response_belongs_to_ticket(db_session):
    customer = Customer(email="cust2@example.com")
    db_session.add(customer)
    await db_session.flush()

    ticket = Ticket(customer_id=customer.id, subject="Refund", message="I want a refund", channel=TicketChannel.WEB)
    db_session.add(ticket)
    await db_session.flush()

    response = Response(ticket_id=ticket.id, message="Refund processed", response_type=ResponseType.AGENT)
    db_session.add(response)
    await db_session.commit()

    result = await db_session.execute(select(Ticket).where(Ticket.id == ticket.id))
    fetched_ticket = result.scalar_one()
    await db_session.refresh(fetched_ticket, attribute_names=["responses"])

    assert len(fetched_ticket.responses) == 1
    assert fetched_ticket.responses[0].response_type == ResponseType.AGENT
    assert fetched_ticket.responses[0].ticket_id == ticket.id


async def test_knowledge_article_is_standalone(db_session):
    article = KnowledgeArticle(title="How to reset your password", content="Go to settings...", category="Account")
    db_session.add(article)
    await db_session.commit()

    result = await db_session.execute(select(KnowledgeArticle).where(KnowledgeArticle.title.contains("password")))
    fetched = result.scalar_one()
    assert fetched.is_published is True
    assert fetched.view_count == 0


async def test_ticket_requires_a_customer(db_session):
    """customer_id is a NOT NULL FK - a ticket can't exist without a customer."""
    from sqlalchemy.exc import IntegrityError

    ticket = Ticket(customer_id=uuid.uuid4(), subject="Orphan ticket", message="...", channel=TicketChannel.EMAIL)
    db_session.add(ticket)
    try:
        await db_session.commit()
        assert False, "expected an IntegrityError for a nonexistent customer_id"
    except IntegrityError:
        await db_session.rollback()
