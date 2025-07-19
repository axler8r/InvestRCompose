# InvestR High-Level Architecture


## Overview
A modular, containerised Docker Compose architecture comprising Python-based
microservices, each serving distinct responsibilities.


## Architectural Diagram
```text
InvestR Compose (Docker Compose)
│
├── Web UI (Flask)
│   └── Presents UI; interacts with Agent Orchestration API.
│
├── Agent API (FastAPI + AutoGen2)
│   ├── Execute agentic workflow and tool calls.
│   └── Calls out to modular tool services:
│       ├── Data API (FastAPI + AutoGen2)
│       ├── Print API (FastAPI + OpenAI)
│       ├── Analysis API (placeholder; FastAPI)
│       └── OpenBB (investment data)
│
├── Data API (FastAPI + MongoDB + Chroma)
│   ├── Stores and retrieves embeddings in Chroma.
│   ├── Stores user sessions, structured historical data, and workflow states in MongoDB.
│   └── Persists structured data & workflow history in MongoDB.
│
├── OpenBB API (FastAPI + OpenBB)
│   └── Provides investment data via OpenBB SDK.
│
├── Print API (FastAPI + OpenAI)
│   └── Generates Markdown/PDF prospectus via OpenAI LLM calls.
│
└── Analysis API (placeholder; FastAPI)
    └── Placeholder endpoints for future time-series models.
```


## Components

### Web UI (Flask)
- Handles user interactions and UI.
- Communicates with the Agent Orchestration API.

### Agent API (FastAPI + AutoGen2)
- Central orchestrator for agent workflows.
- Manages calls to financial APIs and downstream services.

### Data API
- Embedding storage for efficient retrieval.
- Persistent structured data storage.

### OpenBB API
- Provides access to investment data via OpenBB SDK.

### Print API (FastAPI + OpenAI)
- Dedicated service for creating prospectuses from structured inputs using OpenAI.

### Analysis API (Placeholder)
- Future-oriented service reserved for time-series analysis.


## Advantages
- **Modularity:** Clearly defined, replaceable services.
- **Scalability:** Each service independently scalable.
- **Maintainability:** Simple service boundaries ease debugging.
- **Flexibility:** Easy experimentation and service swaps.


## Project Structure & Containerization
To maintain a clean project root and organize containerization concerns, all
Docker-related files are located in the `app/` directory:
```text
InvestRCompose/
├── README.md
├── pyproject.toml
├── uv.lock
├── LICENSE
├── docs/
│   └── architecture.md
├── investr/                    # Python package source code
├── tests/                      # Test suite
└── app/                        # All deployment/containerization
    ├── compose.yml             # Main Docker Compose file
    ├── compose.dev.yml         # Development overrides
    ├── compose.prod.yml        # Production overrides (future)
    ├── .env.example            # Environment template
    ├── Makefile                # Docker-specific tasks
    └── services/               # Service-specific Dockerfiles
        ├── web/
        │   └── Dockerfile
        ├── agent/
        │   └── Dockerfile
        ├── data/
        │   └── Dockerfile
        ├── openbb/
        │   └── Dockerfile
        ├── print/
        │   └── Dockerfile
        └── analysis/
            └── Dockerfile
```

### Benefits of This Structure
- **Clean root directory:** Only essential project files at the top level
- **Deployment separation:** All containerization concerns isolated in `app/`
- **Environment management:** Easy to maintain dev/prod compose configurations
- **Service organization:** Each service gets dedicated folder for Docker configs

### Build Context Strategy
- Dockerfiles use the project root as build context to access `investr/` package
- Compose files reference `../` as build context from `app/` directory
- This allows services to import from the shared `investr` Python package


## Next Steps
- Define REST API contracts and data schemas (e.g., Pydantic).
- Implement placeholder services with dummy endpoints.
- Document data flows and interaction patterns clearly.
