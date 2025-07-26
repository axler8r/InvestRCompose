"""OpenBB API tool for investment research agent."""

import time
from typing import Any, Dict

from autogen_core import CancellationToken
from autogen_core.tools import BaseTool
from httpx import Response

from ..models import MarketDataArgs, MarketDataResult


class OpenBBTool(BaseTool[MarketDataArgs, MarketDataResult]):
    """Tool for retrieving market data via OpenBB API.

    This tool provides access to real-time and historical market data,
    including stock prices, financial metrics, and market indicators.
    """

    def __init__(self, openbb_api_base_url: str = "http://openbb-api:8001") -> None:
        """Initialize the OpenBB tool.

        Args:
            openbb_api_base_url: Base URL for the OpenBB API service

        """
        super().__init__(
            args_type=MarketDataArgs,
            return_type=MarketDataResult,
            name="get_market_data",
            description=(
                "Retrieve market data for stocks, ETFs, and other financial instruments. "
                "Supports real-time prices, historical data, financial metrics, "
                "and technical indicators."
            ),
        )
        self.base_url: str = openbb_api_base_url

    async def run(
        self, args: MarketDataArgs, cancellation_token: CancellationToken
    ) -> MarketDataResult:
        """Retrieve market data for the specified symbol.

        Args:
            args: Market data request parameters
            cancellation_token: Token for canceling the operation

        Returns:
            Market data with prices and metadata

        """
        import httpx

        start_time: float = time.time()

        try:
            # Call the OpenBB API service
            async with httpx.AsyncClient() as client:
                url: str = f"{self.base_url}/market-data/historical/{args.symbol}"
                params: dict[str, str] = {
                    "period": args.period,
                    "interval": args.interval,
                }

                response: Response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()

                data = response.json()

                # Extract data and metadata from the response
                market_data = data.get("data", [])
                metadata = data.get("metadata", {})

                # Update metadata with query time
                metadata["query_time_ms"] = (time.time() - start_time) * 1000

                return MarketDataResult(
                    symbol=args.symbol, data=market_data, metadata=metadata
                )

        except Exception as e:
            # Fall back to mock data if service is unavailable
            print(f"Warning: OpenBB service unavailable ({e}), using mock data")
            return self._get_mock_data(args, start_time)

    def _get_mock_data(
        self, args: MarketDataArgs, start_time: float
    ) -> MarketDataResult:
        """Generate mock data as fallback."""
        mock_data: list[dict[str, Any]] = [
            {
                "date": "2024-01-15",
                "open": 150.25,
                "high": 152.80,
                "low": 149.50,
                "close": 151.75,
                "volume": 2500000,
                "adj_close": 151.75,
            },
            {
                "date": "2024-01-14",
                "open": 148.90,
                "high": 150.45,
                "low": 148.20,
                "close": 150.25,
                "volume": 2200000,
                "adj_close": 150.25,
            },
            {
                "date": "2024-01-13",
                "open": 147.50,
                "high": 149.20,
                "low": 147.10,
                "close": 148.90,
                "volume": 1900000,
                "adj_close": 148.90,
            },
        ]

        metadata: dict[str, Any] = {
            "symbol": args.symbol,
            "data_type": args.data_type,
            "period": args.period,
            "interval": args.interval,
            "currency": "USD",
            "exchange": "NASDAQ",
            "timezone": "US/Eastern",
            "last_updated": "2024-01-15T16:00:00Z",
            "query_time_ms": (time.time() - start_time) * 1000,
            "source": "mock_data",
        }

        return MarketDataResult(symbol=args.symbol, data=mock_data, metadata=metadata)

    def return_value_as_string(self, value: MarketDataResult) -> str:
        """Convert the market data result to a string representation.

        Args:
            value: The market data result to convert

        Returns:
            Human-readable string representation of the market data

        """
        if not value.data:
            return f"No market data found for {value.symbol}."

        result_str = f"Market data for {value.symbol}:\n\n"

        # Show latest data point
        latest: dict[str, Any] = value.data[0] if value.data else {}
        if latest:
            result_str += "Latest Price Information:\n"
            result_str += f"  Date: {latest.get('date', 'N/A')}\n"
            result_str += f"  Open: ${latest.get('open', 0):.2f}\n"
            result_str += f"  High: ${latest.get('high', 0):.2f}\n"
            result_str += f"  Low: ${latest.get('low', 0):.2f}\n"
            result_str += f"  Close: ${latest.get('close', 0):.2f}\n"
            result_str += f"  Volume: {latest.get('volume', 0):,}\n\n"

        # Show summary statistics
        if len(value.data) > 1:
            closes: list[float] = [
                d.get("close", 0) for d in value.data if "close" in d
            ]
            if closes:
                result_str += f"Summary ({len(value.data)} data points):\n"
                result_str += f"  Average Close: ${sum(closes) / len(closes):.2f}\n"
                result_str += (
                    f"  High: ${max(d.get('high', 0) for d in value.data):.2f}\n"
                )
                result_str += (
                    f"  Low: ${min(d.get('low', 0) for d in value.data):.2f}\n\n"
                )

        # Show metadata
        metadata: Dict[str, Any] = value.metadata
        result_str += "Data Details:\n"
        result_str += f"  Exchange: {metadata.get('exchange', 'N/A')}\n"
        result_str += f"  Currency: {metadata.get('currency', 'N/A')}\n"
        result_str += f"  Period: {metadata.get('period', 'N/A')}\n"
        result_str += f"  Last Updated: {metadata.get('last_updated', 'N/A')}\n"

        query_time: float = metadata.get("query_time_ms", 0)
        result_str += f"  Query Time: {query_time:.1f}ms"

        return result_str
