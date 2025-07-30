# InvestRCompose
A learning-focused microservices application for investment research, built with
Docker Compose and Python. This project demonstrates modern microservice
architecture patterns using AI agents, real-time market data, and conversation
persistence.


## Architecture
InvestRCompose consists of five containerized microservices:
- **Agent API**: AI-powered investment research using AutoGen and OpenAI
- **Web UI**: Interactive chat interface with markdown rendering and tool call visualization
- **Data API**: Conversation storage and retrieval using MongoDB and Beanie ODM
- **OpenBB API**: Real-time and historical market data via OpenBB Platform SDK
- **CLI Interface**: Command-line client for development and testing


## Quick Start

### Prerequisites
- Python 3.12+
- [Docker and Docker Compose](https://docs.docker.com/compose/)
- [uv](https://github.com/astral-sh/uv)
- OpenAI API key

### Installation
1. Clone the repository:
```bash
git clone https://github.com/axler8r/InvestRCompose.git
cd InvestRCompose
```

2. Install dependencies:
```bash
make install
```

3. Configure environment:
```bash
cp app/.env.example app/.env
# Edit app/.env with your OpenAI API key
```

4. Start the application:
```bash
make up
```

5. Access the web interface:
```bash
make browse
# Or visit http://localhost:5000
```

### Development Commands
```bash
make help          # Show all available commands
make install       # Install Python dependencies
make up            # Start all services
make down          # Stop all services  
make logs          # View service logs
make status        # Check service status
make test          # Run tests
make lint          # Run code linting
make cli           # Start CLI interface
make mongosh       # Connect to MongoDB shell
```


## Services

### Agent API (Port 8000)
- Investment research assistant powered by AutoGen framework
- Integrates with OpenAI LLM for natural language processing
- Orchestrates tools for market data retrieval and conversation storage
- Supports both streaming and standard response modes

### Web UI (Port 5000)
- Modern chat interface with markdown rendering
- Real-time tool call visualization and disclosure widgets
- Session-based conversation history
- Responsive design for desktop and mobile

### Data API (Port 8002)
- MongoDB-based conversation persistence using Beanie ODM
- Session management for conversation organization
- RESTful endpoints for conversation CRUD operations
- Async architecture with Motor MongoDB driver

### OpenBB API (Port 8001)
- Real-time market data via OpenBB Platform SDK v4.4.5
- Historical price data and financial metrics
- Multiple data provider support (yfinance, fmp, polygon, etc.)
- Graceful fallback to mock data when SDK unavailable

### CLI Interface
- Command-line access to the investment research agent
- Useful for development, testing, and automation
- Session persistence and conversation history


## Technology Stack
- **Containerization**: Docker Compose
- **Backend APIs**: FastAPI, Flask
- **AI Framework**: Microsoft AutoGen, OpenAI API
- **Database**: MongoDB with Beanie ODM
- **Market Data**: OpenBB Platform SDK
- **Frontend**: Vanilla JavaScript with Marked.js for markdown
- **Development**: Python 3.12, uv package manager, ruff linting


## Project Structure
```
InvestRCompose/
├── investr/                # Python package source code
│   ├── agent/              # Agent API and AutoGen integration
│   ├── web/                # Flask web application
│   ├── data/               # Data API and MongoDB models
│   ├── openbb/             # OpenBB API service
│   ├── cli/                # Command-line interface
│   └── common/             # Shared schemas and utilities
├── app/                    # Docker deployment configuration
│   ├── compose.yml         # Docker Compose services
│   └── services/           # Service-specific Dockerfiles
├── docs/                   # Documentation
└── tests/                  # Test suite
```


## Configuration
Key environment variables in `app/.env`:
- `OPENAI_API_KEY` - Required for AI functionality
- `MONGODB_URL` - MongoDB connection string
- `MODEL_NAME` - OpenAI model selection (default: gpt-4o-mini)


## Contributing
1. Follow PEP 8 and use type hints
2. Run `make lint test` before committing
3. Use conventional commit messages
4. Create feature branches for new development


## License
This project is licensed under the MIT License - see the LICENSE file for details.
