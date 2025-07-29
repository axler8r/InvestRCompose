"""Search API package for Azure AI Search integration."""

from investr.search.api import create_app
from investr.search.azure_search_client import AzureSearchClient
from investr.search.document_processor import DocumentProcessor
from investr.search.models import SearchRequest, SearchResponse, SearchResultItem

__all__ = [
    "create_app",
    "AzureSearchClient", 
    "DocumentProcessor",
    "SearchRequest",
    "SearchResponse", 
    "SearchResultItem",
]
