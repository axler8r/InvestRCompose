"""Pydantic models for the Search API."""

from typing import Any, Dict, List

from pydantic import BaseModel


class SearchRequest(BaseModel):
    """Request model for document search."""

    query: str
    limit: int = 10
    collection: str = "default"
    include_metadata: bool = True


class SearchResultItem(BaseModel):
    """Individual search result item."""

    id: str
    title: str
    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Response model for document search."""

    results: List[SearchResultItem]
    total_count: int
    query: str
    collection: str


class SearchStatusResponse(BaseModel):
    """Response model for search service status."""

    service: str
    status: str
    azure_search: str
    document_count: int
    timestamp: str


class IndexRequest(BaseModel):
    """Request model for document indexing."""

    directory_path: str
    collection: str = "default"
    force_reindex: bool = False


class IndexResponse(BaseModel):
    """Response model for document indexing."""

    message: str
    indexed_files: List[str]
    total_documents: int
    collection: str
