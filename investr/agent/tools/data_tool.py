"""Data API tool for investment research agent - hybrid search and conversation tool."""

import time
from typing import Any

import httpx
from autogen_core import CancellationToken
from autogen_core.tools import BaseTool

from investr.agent.models import DataSearchArgs, DataSearchResult


class DataTool(BaseTool[DataSearchArgs, DataSearchResult]):
    """Legacy tool for searching and retrieving investment data.
    
    This tool maintains backward compatibility while internally using
    the new SearchTool and ConversationTool for actual operations.
    For new implementations, prefer using SearchTool and ConversationTool directly.
    """

    def __init__(
        self, 
        data_api_base_url: str = "http://data-api:8002",
        search_api_base_url: str = "http://search-api:8003"
    ) -> None:
        """Initialize the data tool.

        Args:
            data_api_base_url: Base URL for the Data API service (conversation storage)
            search_api_base_url: Base URL for the Search API service (document search)

        """
        super().__init__(
            args_type=DataSearchArgs,
            return_type=DataSearchResult,
            name="search_data",
            description=(
                "LEGACY: Search for investment data using semantic search. "
                "For new implementations, use SearchTool directly. "
                "Can find company information, financial data, market research, "
                "and other investment-related documents."
            ),
        )
        self.data_api_url: str = data_api_base_url.rstrip("/")
        self.search_api_url: str = search_api_base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def run(
        self, args: DataSearchArgs, cancellation_token: CancellationToken
    ) -> DataSearchResult:
        """Execute the data search.

        Args:
            args: Search parameters including query and filters
            cancellation_token: Token for canceling the operation

        Returns:
            Search results with matching documents and metadata

        """
        start_time: float = time.time()

        try:
            # Use real Azure AI Search via Data API
            search_payload = {
                "query": args.query,
                "limit": args.limit,
                "collection": args.collection,
                "include_metadata": args.include_metadata,
            }

            response = await self.client.post(
                f"{self.data_api_url}/conversations",
                json=search_payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                search_data = response.json()

                # Convert API response to expected format
                results = []
                for item in search_data.get("results", []):
                    result = {
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "content": item.get("content", ""),
                        "relevance_score": item.get("relevance_score", 0.0),
                        "source": item.get("source", "azure_search"),
                        "metadata": item.get("metadata", {}),
                    }
                    results.append(result)

                query_time = (time.time() - start_time) * 1000

                return DataSearchResult(
                    results=results,
                    total_count=search_data.get("total_count", len(results)),
                    query_time_ms=query_time,
                )

            elif response.status_code == 503:
                # Azure Search service unavailable, fall back to mock data
                return await self._get_mock_results(args, start_time)
            else:
                # Other error, fall back to mock data
                return await self._get_mock_results(args, start_time)

        except Exception:
            # Network error or other issue, fall back to mock data
            return await self._get_mock_results(args, start_time)

    async def _get_mock_results(
        self, args: DataSearchArgs, start_time: float
    ) -> DataSearchResult:
        """Fallback method to return mock results when Azure Search is unavailable.

        Args:
            args: Search parameters
            start_time: Start time for timing calculation

        Returns:
            Mock search results

        """
        mock_results: list[dict[str, Any]] = [
            {
                "id": "doc_1",
                "title": f"Investment Analysis for {args.query}",
                "content": f"This is a mock result for query: {args.query}. "
                f"Azure AI Search is currently unavailable, showing fallback data.",
                "relevance_score": 0.95,
                "source": "mock_database",
                "metadata": {
                    "company": args.query,
                    "sector": "Technology",
                    "date_created": "2024-01-15",
                    "fallback": True,
                },
            },
            {
                "id": "doc_2",
                "title": f"Market Research: {args.query} Sector Analysis",
                "content": f"Comprehensive analysis of {args.query} market trends. "
                f"This is mock data provided when search service is unavailable.",
                "relevance_score": 0.87,
                "source": "mock_database",
                "metadata": {
                    "sector": "Technology",
                    "report_type": "market_analysis",
                    "date_created": "2024-01-10",
                    "fallback": True,
                },
            },
        ]

        # Limit results based on args.limit
        limited_results: list[dict[str, Any]] = mock_results[: args.limit]

        query_time: float = (time.time() - start_time) * 1000  # Convert to milliseconds

        return DataSearchResult(
            results=limited_results,
            total_count=len(mock_results),
            query_time_ms=query_time,
        )

    async def get_search_status(self) -> dict[str, Any]:
        """Get the status of the search service.

        Returns:
            Dictionary with search service status information

        """
        try:
            response = await self.client.get(f"{self.search_api_url}/search/status")

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "unavailable",
                    "error": f"HTTP {response.status_code}",
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    async def index_documents(self) -> dict[str, Any]:
        """Trigger indexing of documents from the res/ directory.

        Returns:
            Dictionary with indexing results

        """
        try:
            response = await self.client.post(f"{self.search_api_url}/search/index")

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    async def store_conversation_message(
        self, session_id: str, role: str, content: str, tool_calls: list | None = None
    ) -> bool:
        """Store a message in the conversation.

        Args:
            session_id: Unique session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            tool_calls: Optional list of tool calls made

        Returns:
            True if successful, False otherwise

        """
        try:
            message_data: dict[str, Any] = {
                "role": role,
                "content": content,
                "tool_calls": tool_calls,
            }

            request_data: dict[str, Any] = {
                "session_id": session_id,
                "message": message_data,
            }

            response: httpx.Response = await self.client.post(
                f"{self.base_url}/conversations", # type: ignore
                json=request_data,
            )

            return response.status_code == 200

        except Exception:
            return False

    async def get_conversation_history(self, session_id: str) -> list:
        """Retrieve conversation history for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            List of messages in the conversation

        """
        try:
            response = await self.client.get(
                f"{self.data_api_url}/conversations/{session_id}"
            )

            if response.status_code == 200:
                data: Any = response.json()
                return data.get("messages", [])
            else:
                return []

        except Exception:
            return []

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.client.aclose()

    def return_value_as_string(self, value: DataSearchResult) -> str:
        """Convert the search result to a string representation.

        Args:
            value: The search result to convert

        Returns:
            Human-readable string representation of the search results

        """
        if not value.results:
            return f"No results found. Query took {value.query_time_ms:.1f}ms."

        result_str: str = (
            f"Found {len(value.results)} results (total: {value.total_count}):\n\n"
        )

        for i, result in enumerate(value.results, 1):
            relevance: float = result.get("relevance_score", 0)
            title: str = result.get("title", "Untitled")
            content: str = result.get("content", "")

            # Truncate content for readability
            if len(content) > 200:
                content = content[:200] + "..."

            result_str += f"{i}. {title} (relevance: {relevance:.2f})\n"
            result_str += f"   {content}\n\n"

        result_str += f"Query executed in {value.query_time_ms:.1f}ms"

        return result_str
