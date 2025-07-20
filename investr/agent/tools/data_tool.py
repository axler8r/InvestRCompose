"""Data API tool for investment research agent."""

import time

from autogen_core import CancellationToken
from autogen_core.tools import BaseTool

from ..models import DataSearchArgs, DataSearchResult


class DataTool(BaseTool[DataSearchArgs, DataSearchResult]):
    """Tool for searching and retrieving investment data via Data API.

    This tool provides semantic search capabilities over stored investment data,
    including company information, financial statements, and market research.
    """

    def __init__(self, data_api_base_url: str = "http://data-api:8000"):
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
        self.base_url = data_api_base_url

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
        start_time = time.time()

        # TODO: Implement actual HTTP client call to Data API
        # For now, return mock data to establish the interface
        mock_results = [
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
        limited_results = mock_results[: args.limit]

        query_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        return DataSearchResult(
            results=limited_results,
            total_count=len(mock_results),
            query_time_ms=query_time,
        )

    def return_value_as_string(self, value: DataSearchResult) -> str:
        """Convert the search result to a string representation.

        Args:
            value: The search result to convert

        Returns:
            Human-readable string representation of the search results

        """
        if not value.results:
            return f"No results found. Query took {value.query_time_ms:.1f}ms."

        result_str = (
            f"Found {len(value.results)} results (total: {value.total_count}):\n\n"
        )

        for i, result in enumerate(value.results, 1):
            relevance = result.get("relevance_score", 0)
            title = result.get("title", "Untitled")
            content = result.get("content", "")

            # Truncate content for readability
            if len(content) > 200:
                content = content[:200] + "..."

            result_str += f"{i}. {title} (relevance: {relevance:.2f})\n"
            result_str += f"   {content}\n\n"

        result_str += f"Query executed in {value.query_time_ms:.1f}ms"

        return result_str
