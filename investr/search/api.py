"""FastAPI service for document search using Azure AI Search."""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from investr.search.azure_search_client import AzureSearchClient
from investr.search.document_processor import DocumentProcessor
from investr.search.models import (
    IndexRequest,
    IndexResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchStatusResponse,
)

# Global clients (initialized in lifespan)
azure_search_client: Optional[AzureSearchClient] = None
document_processor: Optional[DocumentProcessor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global azure_search_client, document_processor

    # Startup
    logger.info("Starting Search API service...")

    try:
        # Initialize Azure AI Search client
        azure_search_client = AzureSearchClient()
        await azure_search_client.create_index_if_not_exists()
        logger.info("Azure AI Search client initialized")

        # Initialize document processor
        document_processor = DocumentProcessor()
        logger.info("Document processor initialized")

    except Exception as e:
        logger.warning(f"Failed to initialize Azure AI Search: {e}")
        logger.info("Search API will operate in mock mode")

    yield

    # Shutdown
    logger.info("Search API service shut down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance

    """
    app = FastAPI(
        title="InvestR Search API",
        description="Document search service using Azure AI Search",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health_check() -> JSONResponse:
        """Health check endpoint.

        Returns:
            JSON response with service health status

        """
        azure_healthy = azure_search_client is not None

        return JSONResponse(
            status_code=status.HTTP_200_OK
            if azure_healthy
            else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "service": "search-api",
                "status": "healthy" if azure_healthy else "degraded",
                "azure_search": "connected" if azure_healthy else "disconnected",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @app.post("/search")
    async def search_documents(request: SearchRequest) -> SearchResponse:
        """Search documents using Azure AI Search.

        Args:
            request: Search request parameters

        Returns:
            Search results with relevance scores

        Raises:
            HTTPException: If search fails

        """
        try:
            if azure_search_client is None:
                # Return mock data when Azure AI Search is not available
                logger.warning("Azure AI Search not available, returning mock data")
                return SearchResponse(
                    results=[
                        SearchResultItem(
                            id="mock-1",
                            title="Mock Investment Document",
                            content="This is mock search data. Azure AI Search is not configured.",
                            source="mock-source",
                            relevance_score=0.95,
                            metadata={"type": "mock", "query": request.query},
                        )
                    ],
                    total_count=1,
                    query=request.query,
                    collection=request.collection,
                )

            # Perform real search
            search_results = await azure_search_client.search_documents(
                query=request.query,
                top=request.limit,
            )

            search_results_list = [
                SearchResultItem(
                    id=result.id,
                    title=result.title,
                    content=result.content,
                    source=result.source,
                    relevance_score=result.score,
                    metadata={"chunk_id": result.highlights} if request.include_metadata else {},
                )
                for result in search_results
            ]

            return SearchResponse(
                results=search_results_list,
                total_count=len(search_results_list),
                query=request.query,
                collection=request.collection,
            )

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Search operation failed: {str(e)}",
            ) from e

    @app.get("/search/status")
    async def search_status() -> SearchStatusResponse:
        """Get search service status and document count.

        Returns:
            Search service status information

        """
        try:
            document_count = 0
            azure_status = "disconnected"

            if azure_search_client is not None:
                # Get document count from Azure AI Search
                document_count = await azure_search_client.get_document_count()
                azure_status = "connected"

            return SearchStatusResponse(
                service="search-api",
                status="healthy" if azure_search_client else "degraded",
                azure_search=azure_status,
                document_count=document_count,
                timestamp=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            logger.error(f"Status check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Status check failed: {str(e)}",
            ) from e

    @app.post("/search/index")
    async def index_documents(request: IndexRequest) -> IndexResponse:
        """Index documents from a directory into Azure AI Search.

        Args:
            request: Indexing request parameters

        Returns:
            Indexing results and statistics

        Raises:
            HTTPException: If indexing fails

        """
        try:
            if azure_search_client is None or document_processor is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Azure AI Search or document processor not available",
                )

            directory_path = Path(request.directory_path)
            if not directory_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Directory not found: {request.directory_path}",
                )

            # Process documents and index them
            search_documents = await document_processor.process_directory(
                directory_path=directory_path,
                file_pattern="*.pdf",
            )

            # Index documents with Azure AI Search
            await azure_search_client.index_documents(search_documents)
            indexed_files = [doc.source for doc in search_documents]

            return IndexResponse(
                message=f"Successfully indexed {len(indexed_files)} documents",
                indexed_files=indexed_files,
                total_documents=len(indexed_files),
                collection=request.collection,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document indexing failed: {str(e)}",
            ) from e

    return app


# Create the FastAPI app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "investr.search.api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8003")),
        reload=True,
    )
