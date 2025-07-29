"""Azure AI Search client for semantic document search."""

import os
from typing import Any, Dict, List, Optional

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery
from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel


class SearchDocument(BaseModel):
    """Document model for Azure AI Search indexing."""

    id: str
    title: str
    content: str
    source: str
    chunk_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    content_vector: Optional[List[float]] = None


class SearchResult(BaseModel):
    """Search result model."""

    id: str
    title: str
    content: str
    source: str
    score: float
    highlights: Optional[Dict[str, List[str]]] = None
    metadata: Dict[str, Any] = {}


class AzureSearchClient:
    """Azure AI Search client for document indexing and semantic search."""

    def __init__(
        self,
        service_endpoint: Optional[str] = None,
        admin_key: Optional[str] = None,
        index_name: Optional[str] = None,
        openai_client: Optional[AsyncOpenAI] = None,
    ) -> None:
        """Initialize Azure Search client.

        Args:
            service_endpoint: Azure Search service endpoint
            admin_key: Azure Search admin key
            index_name: Search index name
            openai_client: OpenAI client for embeddings

        """
        self.service_endpoint = service_endpoint or os.getenv(
            "AZURE_AI_SEARCH_SERVICE_ENDPOINT"
        )
        self.admin_key = admin_key or os.getenv("AZURE_AI_SEARCH_ADMIN_KEY")
        self.index_name = index_name or os.getenv(
            "AZURE_AI_SEARCH_INDEX_NAME", "investr-documents"
        )

        if not self.service_endpoint:
            raise ValueError("Azure Search service endpoint is required")

        # Initialize credentials
        if self.admin_key:
            self.credential = AzureKeyCredential(self.admin_key)
        else:
            self.credential = DefaultAzureCredential()

        # Initialize clients
        self.index_client = SearchIndexClient(
            endpoint=self.service_endpoint, credential=self.credential
        )

        self.search_client = SearchClient(
            endpoint=self.service_endpoint,
            index_name=self.index_name,
            credential=self.credential,
        )

        # Initialize OpenAI client for embeddings
        if openai_client:
            self.openai_client = openai_client
        else:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                self.openai_client = AsyncOpenAI(api_key=openai_api_key)
            else:
                logger.warning(
                    "OpenAI API key not found, embeddings will not be available"
                )
                self.openai_client = None

    async def create_index_if_not_exists(self) -> bool:
        """Create search index if it doesn't exist.

        Returns:
            True if index was created or already exists

        """
        try:
            # Check if index exists
            try:
                self.index_client.get_index(self.index_name)
                logger.info(f"Index '{self.index_name}' already exists")
                return True
            except Exception:
                logger.info(f"Index '{self.index_name}' does not exist, creating...")

            # Define search fields
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="title", type=SearchFieldDataType.String),
                SearchableField(name="content", type=SearchFieldDataType.String),
                SimpleField(
                    name="source", type=SearchFieldDataType.String, filterable=True
                ),
                SimpleField(
                    name="chunk_id", type=SearchFieldDataType.String, filterable=True
                ),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,  # OpenAI text-embedding-ada-002 dimensions
                    vector_search_profile_name="investr-vector-profile",
                ),
            ]

            # Configure vector search
            vector_search = VectorSearch(
                algorithms=[HnswAlgorithmConfiguration(name="investr-hnsw")],
                profiles=[
                    VectorSearchProfile(
                        name="investr-vector-profile",
                        algorithm_configuration_name="investr-hnsw",
                    )
                ],
            )

            # Configure semantic search
            semantic_config = SemanticConfiguration(
                name="investr-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    content_fields=[SemanticField(field_name="content")],
                ),
            )

            semantic_search = SemanticSearch(configurations=[semantic_config])

            # Create index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search,
            )

            self.index_client.create_index(index)
            logger.info(f"Successfully created index '{self.index_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using OpenAI.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector or None if generation fails

        """
        if not self.openai_client:
            logger.warning("OpenAI client not available, skipping embedding generation")
            return None

        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-ada-002", input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def index_document(self, document: SearchDocument) -> bool:
        """Index a single document.

        Args:
            document: Document to index

        Returns:
            True if indexing succeeded

        """
        try:
            # Generate embedding if not provided
            if not document.content_vector and self.openai_client:
                embedding = await self.generate_embedding(document.content)
                if embedding:
                    document.content_vector = embedding

            # Convert to dict for Azure Search
            doc_dict = document.model_dump()

            # Upload document
            result = self.search_client.upload_documents([doc_dict])

            if result[0].succeeded:
                logger.info(f"Successfully indexed document: {document.id}")
                return True
            else:
                logger.error(
                    f"Failed to index document {document.id}: {result[0].error_message}"
                )
                return False

        except Exception as e:
            logger.error(f"Error indexing document {document.id}: {e}")
            return False

    async def index_documents(self, documents: List[SearchDocument]) -> int:
        """Index multiple documents.

        Args:
            documents: List of documents to index

        Returns:
            Number of successfully indexed documents

        """
        success_count = 0

        for document in documents:
            if await self.index_document(document):
                success_count += 1

        logger.info(f"Successfully indexed {success_count}/{len(documents)} documents")
        return success_count

    async def search_documents(
        self,
        query: str,
        top: int = 10,
        include_total_count: bool = True,
        semantic_configuration: Optional[str] = "investr-semantic-config",
        filters: Optional[str] = None,
    ) -> List[SearchResult]:
        """Search documents using semantic search.

        Args:
            query: Search query
            top: Number of results to return
            include_total_count: Whether to include total count
            semantic_configuration: Semantic configuration to use
            filters: OData filter expression

        Returns:
            List of search results

        """
        try:
            # Generate query embedding for vector search
            query_vector = None
            if self.openai_client:
                query_vector = await self.generate_embedding(query)

            # Prepare search parameters
            search_params = {
                "search_text": query,
                "top": top,
                "include_total_count": include_total_count,
                "highlight_fields": ["title", "content"],
            }

            # Add semantic search if configured
            if semantic_configuration:
                search_params["query_type"] = "semantic"
                search_params["semantic_configuration_name"] = semantic_configuration

            # Add vector search if embedding is available
            if query_vector:
                vector_query = VectorizedQuery(
                    vector=query_vector,
                    k_nearest_neighbors=top,
                    fields="content_vector",
                )
                search_params["vector_queries"] = [vector_query]

            # Add filters if provided
            if filters:
                search_params["filter"] = filters

            # Execute search
            results = self.search_client.search(**search_params)

            # Convert results to SearchResult objects
            search_results = []
            for result in results:
                search_result = SearchResult(
                    id=result["id"],
                    title=result["title"],
                    content=result["content"],
                    source=result["source"],
                    score=result.get("@search.score", 0.0),
                    highlights=result.get("@search.highlights"),
                    metadata={
                        "chunk_id": result.get("chunk_id"),
                        "search_score": result.get("@search.score"),
                        "semantic_score": result.get("@search.reranker_score"),
                    },
                )
                search_results.append(search_result)

            logger.info(f"Found {len(search_results)} results for query: {query}")
            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the index.

        Args:
            document_id: ID of document to delete

        Returns:
            True if deletion succeeded

        """
        try:
            result = self.search_client.delete_documents([{"id": document_id}])

            if result[0].succeeded:
                logger.info(f"Successfully deleted document: {document_id}")
                return True
            else:
                logger.error(
                    f"Failed to delete document {document_id}: {result[0].error_message}"
                )
                return False

        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False

    async def get_document_count(self) -> int:
        """Get total number of documents in the index.

        Returns:
            Number of documents in the index

        """
        try:
            results = self.search_client.search(
                search_text="*", include_total_count=True, top=0
            )
            return results.get_count() or 0
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            return 0

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the Azure Search service.

        Returns:
            Health status information

        """
        try:
            # Try to get index information
            index = self.index_client.get_index(self.index_name)
            document_count = await self.get_document_count()

            return {
                "status": "healthy",
                "index_name": self.index_name,
                "document_count": document_count,
                "fields_count": len(index.fields),
                "service_endpoint": self.service_endpoint,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service_endpoint": self.service_endpoint,
            }
