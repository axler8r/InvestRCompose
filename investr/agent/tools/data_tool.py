"""Data API tool for investment research agent and conversation storage."""

import time
from typing import Any

import httpx
from autogen_core import CancellationToken
from autogen_core.tools import BaseTool

from ..models import DataSearchArgs, DataSearchResult


class DataTool(BaseTool[DataSearchArgs, DataSearchResult]):
    """Tool for searching and retrieving investment data via Data API.

    This tool provides semantic search capabilities over stored investment data,
    including company information, financial statements, and market research.
    Also handles conversation storage and retrieval for session persistence.
    """

    def __init__(self, data_api_base_url: str = "http://data-api:8002") -> None:
        """Initialize the data tool.

        Args:
            data_api_base_url: Base URL for the Data API service

        """
        super().__init__(
            args_type=DataSearchArgs,
            return_type=DataSearchResult,
            name="search_data",
            description=(
                "Search for investment data using semantic search. "
                "Can find company information, financial data, market research, "
                "and other investment-related documents."
            ),
        )
        self.base_url: str = data_api_base_url.rstrip("/")
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
            # For now, return mock data since we haven't implemented search endpoint yet
            # TODO: Implement semantic search endpoint in Data API
            mock_results: list[dict[str, Any]] = [
                {
                    "id": "doc_1",
                    "title": f"Investment Analysis for {args.query}",
                    "content": f"This is a mock result for query: {args.query}",
                    "relevance_score": 0.95,
                    "source": "mock_database",
                    "metadata": {
                        "company": args.query,
                        "sector": "Technology",
                        "date_created": "2024-01-15",
                    },
                },
                {
                    "id": "doc_2",
                    "title": f"Market Research: {args.query} Sector Analysis",
                    "content": f"Comprehensive analysis of {args.query} market trends",
                    "relevance_score": 0.87,
                    "source": "mock_database",
                    "metadata": {
                        "sector": "Technology",
                        "report_type": "market_analysis",
                        "date_created": "2024-01-10",
                    },
                },
            ]

            # Limit results based on args.limit
            limited_results: list[dict[str, Any]] = mock_results[: args.limit]

            query_time: float = (
                time.time() - start_time
            ) * 1000  # Convert to milliseconds

            return DataSearchResult(
                results=limited_results,
                total_count=len(mock_results),
                query_time_ms=query_time,
            )

        except Exception:
            # Return empty results on error
            query_time = (time.time() - start_time) * 1000
            return DataSearchResult(
                results=[],
                total_count=0,
                query_time_ms=query_time,
            )

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
                f"{self.base_url}/conversations",
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
            response: httpx.Response = await self.client.get(
                f"{self.base_url}/conversations/{session_id}"
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
