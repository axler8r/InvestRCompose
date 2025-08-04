authors: axl,
date: 2025-08-04
version: 0.9.0
---
# Changelog

All notable changes to the InvestR project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## 0.9.0
**2025-08-04**
### Changed
- **Schemas**
  - Removed unused schema classes from `investr.common.schemas`
  - Removed unused moddel classes from `investr.openbb.models`
  - Removed unused model classes from `investr.agent.models`
  - Removed unused model classes from `investr.data.models`
  - Removed unused API endpoints from `investr.agent.api`
  - Removed unused API endpoints from `investr.data.api`
  - Removed unused API endpoints from `investr.openbb.api`
  - Updated the architecture documentation


## 0.8.0
**2025-08-02**

### Added
- **Real-time Streaming Interface**
  - Implemented AutoGen streaming integration with tool execution events
  - Added server-sent events (SSE) endpoint for real-time progress updates
  - Created Flask streaming response support with content-type detection
  - Added progress indicators with spinners and completion status in Web UI
  - Implemented CSS animations and styling for streaming progress visualization
  - Added seamless fallback between streaming and regular JSON responses

- **Enhanced User Experience**
  - Implemented asynchronous user experience with live feedback during tool execution
  - Added real-time progress tracking for investment research queries
  - Created user-friendly mapping of AutoGen ToolCallRequestEvent and ToolCallExecutionEvent
  - Enhanced visual feedback with loading states and completion indicators

- **Build System Enhancements**
  - Added Docker housekeeping targets to Makefile
  - Implemented docker-rmdi, docker-rmdv, compose-rmi, and docker-clean targets
  - Enhanced build system with improved container management
  - Added comprehensive Docker cleanup utilities

### Changed
- **Architecture Simplification**
  - Adopted streaming-only architecture by retiring /agent/query endpoint
  - Removed parallel code paths to improve maintainability
  - Eliminated UserRequest to AgentRequest conversion layer
  - Simplified agent models by removing unnecessary complexity

- **API Restructuring**
  - Removed process_user_request method (~170 lines) from AgentAPI
  - Eliminated /agent/query endpoint from FastAPI application
  - Refactored AgentAPI to work directly with UserRequest objects
  - Updated stream_user_request() to provide structured SSE events

- **Web UI Modernisation**
  - Separated CSS and JavaScript from HTML template into external files
  - Created static/css/style.css and static/js/app.js
  - Simplified Web UI to streaming-only responses
  - Enhanced maintainability with proper asset separation

- **Code Quality Improvements**
  - Consolidated agent processing logic for better maintainability
  - Removed unused imports (time, ToolResult, AgentResponse, RequestStatus)
  - Simplified agent/__init__.py exports to only include InvestmentAgent
  - Updated endpoint references from /api/query to /agent/query

### Removed
- **Legacy API Components**
  - Removed AgentRequest, TaskType, TaskPriority, and TaskContext classes
  - Eliminated TokenUsage and internal AgentResponse from agent models
  - Removed _convert_user_request_to_agent_request() conversion method
  - Removed _convert_internal_response_to_agent_response() conversion method
  - Deleted process_request() method, consolidated logic into process_user_request()
  - Removed _call_agent_api fallback method from Flask application

- **Redundant Code Paths**
  - Eliminated parallel synchronous and asynchronous processing paths
  - Removed non-streaming API endpoints to focus on superior streaming interface
  - Cleaned up unused model classes and conversion utilities

### Technical Details

#### Streaming Architecture
- **AutoGen Integration**: Deep integration with Microsoft AutoGen streaming capabilities
- **Server-Sent Events**: Real-time progress updates with structured event streaming
- **Tool Execution Mapping**: User-friendly progress messages for tool calls
- **Progressive Enhancement**: Graceful fallback for non-streaming environments

#### API Simplification
- **Direct Processing**: Eliminated intermediate conversion layers for better performance
- **Reduced Complexity**: Removed ~250 lines of conversion and parallel processing code
- **Focused Interface**: Single streaming endpoint replaces multiple API patterns
- **Type Safety**: Maintained comprehensive Pydantic validation throughout

#### Web UI Enhancement
- **Asset Separation**: External CSS and JavaScript files for better maintainability
- **Responsive Design**: Enhanced mobile-friendly interface with real-time feedback
- **Progressive Loading**: Visual indicators for ongoing operations and completions
- **Modern Architecture**: Clean separation of concerns between HTML, CSS, and JavaScript

#### Development Experience
- **Docker Management**: Comprehensive container cleanup and management tools
- **Build Optimisation**: Enhanced Makefile with docker housekeeping capabilities
- **Code Organisation**: Simplified imports and reduced architectural complexity
- **Maintainability**: Streamlined codebase with single responsibility patterns

### Benefits
- **Superior User Experience**: Real-time feedback replaces blocking request/response patterns
- **Reduced Complexity**: Eliminated unnecessary conversion layers and parallel code paths
- **Better Maintainability**: Cleaner architecture with focused streaming interface
- **Enhanced Performance**: Direct processing without intermediate conversions
- **Improved Development**: Better asset organisation and Docker management tools


## 0.7.1
**2025-07-31**

### Added
- **ErrorResponse Standardization**
  - Implemented unified error handling across all microservices
  - Created `investr.common.exceptions` module with standardized exception utilities
  - Added `create_error_response()` function for structured ErrorResponse format
  - Implemented `http_exception_handler()` for HTTPException conversion
  - Added `generic_exception_handler()` for unexpected exception handling

- **Exception Handler Integration**
  - Registered exception handlers in Agent API (FastAPI + AutoGen)
  - Added ErrorResponse support to Data API (conversation storage)
  - Integrated standardized error handling in OpenBB API (market data)
  - Enhanced Web UI JavaScript to handle both ErrorResponse and legacy formats

- **Comprehensive Documentation**
  - Updated README.md with complete project overview and quick start guide
  - Added detailed service descriptions and technology stack information
  - Created comprehensive ErrorResponse implementation documentation
  - Enhanced project structure documentation and development guidelines

### Changed
- **Error Handling Architecture**
  - Migrated from inconsistent HTTPException responses to structured ErrorResponse format
  - Standardized error type mapping (400→BadRequest, 401→Unauthorized, 404→NotFound, etc.)
  - Improved error parsing and display in web interface
  - Enhanced debugging capabilities with structured error details

- **Code Quality Improvements**
  - Applied consistent error handling patterns across all FastAPI services
  - Added type safety annotations for exception handlers
  - Improved backward compatibility while introducing new standards
  - Enhanced logging and error tracking capabilities

- **Web Interface Enhancement**
  - Updated JavaScript error handling to support ErrorResponse format
  - Maintained backward compatibility with legacy error responses
  - Improved error message display and user feedback
  - Enhanced error parsing for both successful and failed HTTP responses

### Removed
- **Semantic Search Components**
  - Removed Semantic Search API service
  - Deleted `AzureSearchClient` and related document management code
  - Removed semantic search capabilities and vector embeddings
  - Eliminated hybrid search implementation and HNSW algorithm configuration

- **Print Service Components**
  - Removed `PrintTool` from agent tool orchestration
  - Cleaned up print service references from agent factory
  - Simplified agent architecture to focus on core functionality (3 tools instead of 4)
  - Removed unused print service Docker configurations and placeholders

- **Architecture Simplification**
  - Streamlined microservice architecture by removing non-essential services
  - Focused on core investment research capabilities
  - Reduced complexity in agent tool management and orchestration

- **Schema**
  - Removed unused schema classes

### Technical Details

#### Error Response Schema
```json
{
    "error": "ErrorType",
    "message": "Human-readable error message",
    "details": {
        "additional": "context_data"
    }
}
```

#### Exception Handler Implementation
- **Agent API**: Registered HTTPException and generic Exception handlers
- **Data API**: Integrated ErrorResponse for conversation storage operations
- **OpenBB API**: Added standardized error responses for market data endpoints
- **Web UI**: Enhanced JavaScript with dual-format error support

#### Backward Compatibility
- Web interface supports both ErrorResponse format and legacy error handling
- Existing API contracts maintained while adding structured error responses
- Graceful fallback mechanisms for error parsing and display

### Benefits
- **Consistent Error Format**: All microservices return errors in the same structured format
- **Better Error Handling**: Frontend can reliably parse and display error messages
- **Improved Debugging**: Structured error details help with troubleshooting
- **Type Safety**: Pydantic-based ErrorResponse ensures schema validation
- **Maintainability**: Centralized exception handling reduces code duplication


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
