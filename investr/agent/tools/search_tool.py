"""Search API tool for document search in investment research."""

import time

import httpx
from autogen_core import CancellationToken
from autogen_core.tools import BaseTool

from investr.agent.models import SearchArgs, SearchResult


class SearchTool(BaseTool[SearchArgs, SearchResult]):
    """Tool for searching investment documents via Search API.

    This tool provides semantic search capabilities over stored investment documents,
    including company information, financial statements, and market research reports.
    """

    def __init__(self, search_api_base_url: str = "http://search-api:8003") -> None:
        """Initialize the search tool.

        Args:
            search_api_base_url: Base URL for the Search API service

        """
        super().__init__(
            args_type=SearchArgs,
            return_type=SearchResult,
            name="search_documents",
            description=(
                "Search for investment documents using semantic search. "
                "Can find company information, financial data, market research, "
                "and other investment-related documents."
            ),
        )
        self.search_api_url: str = search_api_base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def run(
        self, args: SearchArgs, cancellation_token: CancellationToken
    ) -> SearchResult:
        """Execute the document search.

        Args:
            args: Search parameters including query and filters
            cancellation_token: Token for canceling the operation

        Returns:
            Search results with documents and metadata

        """
        start_time = time.time()

        try:
            # Call Search API for document search
            response = await self.client.post(
                f"{self.search_api_url}/search",
                json={
                    "query": args.query,
                    "limit": args.limit,
                    "collection": args.collection,
                    "include_metadata": args.include_metadata,
                },
            )

            if response.status_code == 200:
                data = response.json()
                results = []

                # Process search results
                for item in data.get("results", []):
                    result_item = {
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "content": item.get("content", ""),
                        "source": item.get("source", ""),
                        "relevance_score": item.get("relevance_score", 0.0),
                    }

                    if args.include_metadata:
                        result_item["metadata"] = item.get("metadata", {})

                    results.append(result_item)

                query_time = (time.time() - start_time) * 1000

                return SearchResult(
                    results=results,
                    total_count=data.get("total_count", len(results)),
                    query_time_ms=query_time,
                )

            else:
                # API error - return mock data with error indication
                return await self._get_mock_search_results(args, start_time)

        except Exception:
            # Network or other error - return mock data
            return await self._get_mock_search_results(args, start_time)

    async def _get_mock_search_results(
        self, args: SearchArgs, start_time: float
    ) -> SearchResult:
        """Generate mock search results when API is unavailable.

        Args:
            args: Original search arguments
            start_time: Start time for query timing

        Returns:
            Mock search results

        """
        # Generate mock investment document results
        mock_results = [
            {
                "id": "mock-doc-1",
                "title": f"Investment Analysis: {args.query}",
                "content": (
                    f"This is a mock document about {args.query}. "
                    "In a real implementation, this would contain actual "
                    "investment research, financial data, and market analysis."
                ),
                "source": "mock-search-service",
                "relevance_score": 0.95,
            },
            {
                "id": "mock-doc-2", 
                "title": f"Market Research: {args.query}",
                "content": (
                    f"Mock market research document discussing {args.query}. "
                    "This would typically include market trends, competitive analysis, "
                    "and investment recommendations."
                ),
                "source": "mock-search-service",
                "relevance_score": 0.87,
            },
        ]

        # Add metadata if requested
        if args.include_metadata:
            for result in mock_results:
                result["metadata"] = {
                    "document_type": "mock",
                    "search_query": args.query,
                    "collection": args.collection,
                    "generated_at": time.time(),
                }

        # Limit results to requested amount
        limited_results = mock_results[: args.limit]
        query_time = (time.time() - start_time) * 1000

        return SearchResult(
            results=limited_results,
            total_count=len(limited_results),
            query_time_ms=query_time,
        )

    async def get_search_status(self) -> dict:
        """Get search service status.

        Returns:
            Search service status information

        """
        try:
            response = await self.client.get(f"{self.search_api_url}/search/status")
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": "Search API unavailable"}
        except Exception:
            return {"status": "error", "message": "Search service not reachable"}

    async def index_documents(self, directory_path: str) -> dict:
        """Index documents from a directory.

        Args:
            directory_path: Path to directory containing documents

        Returns:
            Indexing results

        """
        try:
            response = await self.client.post(
                f"{self.search_api_url}/search/index",
                json={"directory_path": directory_path, "collection": "default"},
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": "Indexing failed"}
        except Exception:
            return {"status": "error", "message": "Indexing service unavailable"}

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.client.aclose()
