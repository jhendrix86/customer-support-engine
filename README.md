# Customer Support Engine

AI-powered customer support system for the Autonomous Company OS. This engine handles ticket management, automated responses, knowledge base integration, and multi-channel support.

## Features

- **AI-Powered Responses** - GPT-4 powered intelligent response generation
- **Ticket Management** - Complete ticket lifecycle management
- **Multi-Channel Support** - Email, chat, social media, phone
- **Knowledge Base Integration** - Automatic article suggestions and responses
- **Priority Routing** - Intelligent ticket routing based on urgency and customer tier
- **SLA Tracking** - Service Level Agreement monitoring and alerts
- **Customer Satisfaction** - CSAT surveys and sentiment analysis
- **Agent Collaboration** - Internal notes and agent handoffs
- **Analytics Dashboard** - Support metrics and performance tracking

## Architecture

```
┌─────────────┐    Tickets    ┌──────────────┐
│   All       │ ────────────> │  Ticket      │
│  Channels   │               │  Ingestion   │
└─────────────┘               └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   Priority   │ │ Routing │ │   AI       │
            │   Engine     │ │ Engine  │ │  Response  │
            └──────────────┘ └─────────┘ └───────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      Knowledge Base            │
                    │      Integration                │
                    └─────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   SLA        │ │ CSAT    │ │ Analytics  │
            │   Tracking   │ │ Engine  │ │  Engine    │
            └──────────────┘ └─────────┘ └───────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (for ticket data)
- Redis (for caching and queues)
- OpenAI API key (for AI responses)
- SendGrid (for email responses)

### Local Development

```bash
# Clone repository
git clone https://github.com/autonomous-company/customer-support-engine.git
cd customer-support-engine

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn app.main:app --reload --port 8038
```

### Docker Deployment

```bash
# Build and start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f support-engine

# Stop services
docker-compose down
```

## Configuration

Configuration is managed via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://localhost/support` | PostgreSQL connection URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `OPENAI_API_KEY` | - | OpenAI API key for AI responses |
| `SENDGRID_API_KEY` | - | SendGrid API key for email |
| `DEFAULT_SLA_HOURS` | `24` | Default SLA in hours |
| `AUTO_RESPONSE_ENABLED` | `true` | Enable AI auto-responses |
| `KNOWLEDGE_BASE_URL` | - | Knowledge base API URL |

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - Service information

### Ticket Management
- `POST /tickets/create` - Create ticket
- `POST /tickets/{ticket_id}/resolve` - Resolve ticket
- `POST /tickets/{ticket_id}/escalate` - Escalate ticket
- `POST /tickets/{ticket_id}/assign` - Assign ticket to agent
- `GET /tickets/{ticket_id}` - Get ticket details
- `GET /tickets` - List tickets

### AI Responses
- `POST /ai/generate-response` - Generate AI response
- `POST /ai/respond/{ticket_id}` - Send AI response
- `GET /ai/suggestions/{ticket_id}` - Get knowledge base suggestions

### Knowledge Base
- `POST /kb/search` - Search knowledge base
- `POST /kb/suggest/{ticket_id}` - Suggest articles for ticket
- `GET /kb/articles/{article_id}` - Get article details

### SLA Management
- `GET /sla/status` - Get SLA status
- `GET /sla/violations` - Get SLA violations
- `POST /sla/escalate/{ticket_id}` - Escalate SLA violation

### Analytics
- `GET /analytics/metrics` - Get support metrics
- `GET /analytics/performance` - Get agent performance
- `GET /analytics/satisfaction` - Get CSAT scores

## Usage Examples

### Create Ticket

```python
import httpx

async def create_ticket():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8038/tickets/create",
            json={
                "customer_id": "cust_123",
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "subject": "Payment processing issue",
                "message": "My payment failed to process",
                "priority": "high",
                "channel": "email"
            }
        )
        return response.json()
```

### Generate AI Response

```python
async def generate_ai_response():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8038/ai/generate-response",
            json={
                "ticket_id": "ticket_123",
                "customer_message": "My payment failed to process",
                "context": {
                    "customer_tier": "professional",
                    "previous_tickets": 2
                }
            }
        )
        return response.json()
```

### Search Knowledge Base

```python
async def search_knowledge_base():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8038/kb/search",
            json={
                "query": "payment processing failed",
                "limit": 5
            }
        )
        return response.json()
```

## Ticket Priorities

- **Critical** - System down, payment issues, security concerns
- **High** - Feature broken, urgent customer need
- **Medium** - Standard support request
- **Low** - General inquiry, feature request

## SLA Tiers

- **Critical**: 1 hour response time
- **High**: 4 hour response time
- **Medium**: 24 hour response time
- **Low**: 48 hour response time

## AI Response Features

- **Context-Aware** - Uses customer history and ticket context
- **Knowledge Base** - Suggests relevant articles automatically
- **Sentiment Analysis** - Detects customer sentiment
- **Multi-Language** - Supports multiple languages
- **Tone Adjustment** - Adapts tone based on customer tier

## Integration with Other Engines

### Knowledge Graph
- Stores customer support history
- Tracks common issues and solutions
- Analyzes support patterns

### Notification Engine
- Alerts on SLA violations
- Notifies agents of high-priority tickets
- Sends customer satisfaction surveys

### Revenue Operations
- Links payment issues to support tickets
- Handles refund-related support requests
- Tracks support impact on revenue

## Monitoring

### Metrics
- Average response time
- First contact resolution rate
- Customer satisfaction score
- Ticket volume by channel
- Agent performance metrics

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
