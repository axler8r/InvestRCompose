author: axl
date: 2025-07-30
version: 0.7.0
---
# Changelog

All notable changes to the InvestR project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.7.0
**2025-07-30**

### Added
- **Semantic Search Service Implementation**
  - Implemented standalone Search API service with Azure AI Search integration
  - Added comprehensive semantic search capabilities with vector embeddings
  - Created `AzureSearchClient` with full CRUD operations for document management
  - Integrated OpenAI text-embedding-ada-002 for semantic similarity search
  - Added hybrid search combining semantic, vector, and traditional text search
  - Implemented HNSW algorithm configuration for optimal vector search performance

- **Document Processing System**
  - Added `DocumentProcessor` class for PDF text extraction and chunking
  - Implemented intelligent text chunking with configurable size and overlap
  - Added PDF metadata extraction (title, author, creation date, etc.)
  - Created document-to-search-document conversion pipeline
  - Added support for ETF prospectus and financial document processing

- **Agent Tool Architecture Enhancement**
  - Created `SearchTool` for dedicated document search operations
  - Implemented `ConversationTool` for separate conversation storage
  - Enhanced `DataTool` for backward compatibility with legacy interfaces
  - Added comprehensive error handling and graceful fallback mechanisms
  - Implemented HTTP client-based tool communication patterns

- **Search API Endpoints**
  - Added `/search` endpoint for document semantic search
  - Implemented `/search/status` for service health and index monitoring
  - Created `/search/index` endpoint for bulk document indexing
  - Added comprehensive error handling and mock data fallbacks
  - Implemented proper FastAPI lifecycle management with async initialization

- **ETF Prospectus Indexing System**
  - Created standalone indexing script for ETF prospectus documents
  - Added automated PDF processing from `res/` directory
  - Implemented batch document indexing with progress tracking
  - Added search verification and testing capabilities
  - Created sample ETF document collection for testing

- **Azure AI Search Integration**
  - Implemented vector search with 1536-dimensional embeddings
  - Added semantic configuration with prioritized fields
  - Created custom search index schema for investment documents
  - Integrated Azure credential management (key-based and DefaultAzureCredential)
  - Added document count tracking and health monitoring

### Changed
- **Service Architecture**
  - Separated search functionality into dedicated microservice
  - Updated Docker Compose configuration to include search-api service
  - Enhanced service discovery and inter-service communication
  - Improved environment variable configuration for Azure services

- **Data Models**
  - Enhanced search result models with relevance scoring
  - Added comprehensive document metadata support
  - Improved error response structures across all APIs
  - Updated Pydantic models for better type safety

- **Agent System Enhancement**
  - Refactored tool system to use dedicated search and conversation tools
  - Improved agent factory methods for new and legacy tool configurations
  - Enhanced error handling and fallback mechanisms
  - Added better separation of concerns between tool responsibilities

### Technical Details

#### Search Infrastructure
- **Azure AI Search**: Full integration with semantic search capabilities
- **Vector Embeddings**: OpenAI text-embedding-ada-002 with 1536 dimensions
- **Hybrid Search**: Combines semantic ranking, vector similarity, and keyword matching
- **Index Schema**: Custom schema optimized for investment document search
- **Document Processing**: Intelligent chunking with configurable parameters

#### Service Integration
- **Search API Service**: Dedicated FastAPI service (port 8003)
- **Document Indexing**: Automated processing and indexing pipeline
- **Health Monitoring**: Comprehensive service and index health checks
- **Graceful Degradation**: Mock data fallbacks when services unavailable

#### Development Tools
- **ETF Indexing Script**: Standalone tool for document processing and indexing
- **Search Verification**: Built-in testing and validation capabilities
- **Environment Management**: Enhanced configuration for Azure services
- **Logging**: Comprehensive logging with loguru integration

### Current Status
- [×] **Phase 1**: Core Agent Implementation (Complete)
- [×] **Phase 2**: Conversation Storage (Complete)
- [×] **Phase 3**: OpenBB Microservice Integration (Complete)
- [×] **Phase 4**: Semantic Search Implementation (Complete) ✅ NEW
  - Azure AI Search integration with vector embeddings
  - Document processing and intelligent chunking
  - Hybrid search capabilities (semantic + vector + text)
  - ETF prospectus indexing and search system
  - Dedicated Search API microservice
- [ ] **Phase 5**: Advanced Services (Planned)
  - Print API Service (ReportLab integration)
  - Analysis API Service (Financial analysis)
- [ ] **Phase 6**: Production Readiness (Future)
  - Authentication & Security
  - Monitoring & Observability
  - Performance Optimization

## 0.6.0
**2025-07-28**

### Added
- **Build System Improvements**
  - Updated Makefile with enhanced build and lifecycle targets
  - Added Dependabot configuration for automated dependency updates
  - Implemented Docker image layer caching for improved build performance
  - Added comprehensive test targets and code quality checks

- **Security & Infrastructure**
  - Added Dependabot configuration for security updates
  - Implemented comprehensive Docker Compose infrastructure with multi-service orchestration
  - Added MongoDB integration for persistent data storage
  - Enhanced container security and build optimization

- **Conversation Storage**
  - Implemented MongoDB-based conversation storage service with async operations
  - Added Data API service with full CRUD operations for conversation management
  - Integrated conversation capture in agent workflows with automatic storage
  - Added session-based conversation organization for future authentication
  - Implemented comprehensive tool call metadata capture and storage
  - Added RESTful endpoints for conversation management (`/conversations`, `/conversations/{session_id}`)
  - Integrated Beanie ODM for type-safe MongoDB operations

- **OpenBB Microservice Integration**
  - Implemented standalone OpenBB API service with FastAPI
  - Added real-time market data integration via OpenBB Platform SDK v4.4.5
  - Created RESTful endpoints for market data (`/health`, `/market-data/historical/{symbol}`, `/market-data/quote/{symbol}`, `/market-data/batch`)
  - Implemented LLM-driven parameter extraction for natural language queries
  - Added graceful fallback to mock data when SDK unavailable
  - Containerized OpenBB service with Docker integration
  - Enhanced type safety with Pydantic models and Literal types for provider validation
  - Added multi-provider support (yfinance, fmp, intrinio, polygon, tiingo)

- **Web UI Enhancements**
  - Implemented Flask web UI for investment research agent interaction
  - Added markdown rendering capabilities for rich text display
  - Created disclosure widgets for tool call visualization
  - Enhanced user interface with responsive design and error handling
  - Added session management and conversation history tracking

- **CLI Interface**
  - Developed command-line interface for direct agent interaction
  - Added session management for persistent CLI conversations
  - Implemented debugging capabilities for agent responses

- **Agent System (AutoGen Framework)**
  - Implemented Investment Research Agent using Microsoft AutoGen framework
  - Integrated OpenAI LLM (gpt-4o-mini) for natural language processing
  - Created comprehensive tool orchestration system with HTTP client tools:
    - **DataTool**: Semantic search capabilities and conversation storage
    - **OpenBBTool**: Real-time market data retrieval via OpenBB API
    - **PrintTool**: Report generation (mock implementation)
    - **AnalysisTool**: Financial analysis capabilities (mock implementation)
  - Added streaming response capabilities for real-time interactions
  - Enhanced agent configuration and response extraction
  - Implemented automatic conversation storage with session management

- **Testing & Quality Assurance**
  - Added comprehensive test suite with pytest (12/12 tests passing)
  - Implemented test prompts for agent validation
  - Added code quality tools with ruff for linting and formatting
  - Created test structure mirroring source code organization

- **Documentation**
  - Created comprehensive architecture documentation
  - Added detailed agent implementation documentation
  - Updated project README with current implementation status
  - Documented microservice architecture patterns and service relationships
  - Added development workflow and contribution guidelines

### Changed
- **Code Quality & Style**
  - Applied consistent style conventions across codebase
  - Improved type declarations throughout the project
  - Updated import statements for better organization
  - Enhanced error handling and logging patterns

- **Project Structure**
  - Reorganized project structure for better microservice architecture
  - Simplified gitignore configuration
  - Made build targets less verbose for improved developer experience
  - Updated service port configurations for consistency

- **Dependencies**
  - Added core dependencies for agent functionality (AutoGen, OpenAI)
  - Integrated web application dependencies (Flask, FastAPI)
  - Added database dependencies (MongoDB, Motor, Beanie)
  - Included testing and code quality dependencies (pytest, ruff)
  - Added OpenBB Platform SDK for financial data integration

### Technical Details

#### Architecture Improvements
- Transitioned from monolithic to microservices architecture
- Implemented Docker Compose orchestration with 5 services:
  - Web UI (Flask) - port 5000
  - Agent API (FastAPI + AutoGen) - port 8000
  - Data API (FastAPI + MongoDB) - port 8002
  - OpenBB API (FastAPI + OpenBB SDK) - port 8001
  - MongoDB database - port 27017
- Added `investr-network` bridge network for service communication

#### Data Layer
- Implemented async MongoDB operations with Motor driver
- Added Beanie ODM for type-safe document operations
- Created conversation storage with session management
- Implemented automatic tool call metadata capture

#### Integration Patterns
- HTTP client-based tool implementations for microservice communication
- RESTful API design across all services
- Type safety with comprehensive Pydantic model validation
- Graceful error handling and fallback mechanisms

#### Development Experience
- Enhanced Makefile with comprehensive build and lifecycle commands
- Added CLI interface for testing and development
- Implemented hot-reloading and development-friendly configurations
- Created comprehensive test coverage and quality checks

### Current Status
- [×] **Phase 1**: Core Agent Implementation (Complete)
- [×] **Phase 2**: Conversation Storage (Complete)
- [×] **Phase 3**: OpenBB Microservice Integration (Complete)
- [ ] **Phase 4**: Advanced Services (Planned)
  - Print API Service (ReportLab integration)
  - Analysis API Service (Financial analysis)
- [ ] **Phase 5**: Production Readiness (Future)
  - Authentication & Security
  - Monitoring & Observability
  - Performance Optimization
