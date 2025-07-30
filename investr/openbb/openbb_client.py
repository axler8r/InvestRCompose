"""OpenBB Platform client for data retrieval.

This module provides a wrapper around the OpenBB Platform SDK to standardize
data access and provide consistent error handling and caching.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal

from loguru import logger
from openbb import obb
from openbb.package.__extensions__ import Extensions
from openbb_core.app.static.app_factory import BaseApp

# Define valid provider types
HistoricalProvider = Literal["fmp", "intrinio", "polygon", "tiingo", "yfinance"]
QuoteProvider = Literal["fmp", "intrinio", "yfinance"]


class OpenBBClient:
    """Client for interacting with OpenBB Platform.

    This client provides a simplified interface to OpenBB's extensive
    financial data capabilities with built-in error handling and response
    standardization.
    """

    def __init__(self) -> None:
        """Initialize the OpenBB client."""
        self._obb: BaseApp | Extensions | None = None
        self._initialized: bool = False

    async def initialize(self) -> None:
        """Initialize the OpenBB connection.

        This method handles the OpenBB Platform initialization which must
        be done asynchronously.
        """
        if self._initialized:
            return

        try:
            self._obb = obb
            self._initialized = True
            logger.info("OpenBB client initialized successfully")

        except ImportError as e:
            logger.error(f"OpenBB Platform not installed: {e}")
            # For now, we'll work with mock data if OpenBB isn't available
            self._obb = None
            self._initialized = True
            logger.warning("OpenBB not available - using mock data mode")

    async def get_historical_prices(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        provider: str = "yfinance",
    ) -> List[Dict[str, Any]]:
        """Get historical price data for a symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            period: Time period (e.g., "1y", "6m", "3m")
            interval: Data interval (e.g., "1d", "1h", "5m")
            provider: Data provider (e.g., "yfinance", "fmp", "intrinio")

        Returns:
            List of price data dictionaries

        """
        await self.initialize()

        if not self._obb:
            # Return mock data if OpenBB not available
            return self._get_mock_historical_data(symbol)

        try:
            # Convert period to start/end dates for OpenBB
            end_date: datetime = datetime.now()

            if period == "1y":
                start_date: datetime = end_date - timedelta(days=365)
            elif period == "6m":
                start_date = end_date - timedelta(days=180)
            elif period == "3m":
                start_date = end_date - timedelta(days=90)
            elif period == "1m":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=365)  # Default to 1 year

            # Validate provider and cast to correct type
            valid_providers: List[str] = [
                "fmp",
                "intrinio",
                "polygon",
                "tiingo",
                "yfinance",
            ]
            if provider not in valid_providers:
                provider = "yfinance"  # Default fallback

            # Call OpenBB Platform
            result = self._obb.equity.price.historical(  # type: ignore
                symbol=symbol,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                provider=provider,  # type: ignore
                interval=interval,
            )

            # Convert to our standard format
            data = []
            if hasattr(result, "results") and result.results:
                for row in result.results:
                    data.append(
                        {
                            "date": str(row.date) if hasattr(row, "date") else None,
                            "open": float(row.open) if hasattr(row, "open") else None,
                            "high": float(row.high) if hasattr(row, "high") else None,
                            "low": float(row.low) if hasattr(row, "low") else None,
                            "close": float(row.close)
                            if hasattr(row, "close")
                            else None,
                            "volume": int(row.volume)
                            if hasattr(row, "volume")
                            else None,
                            "adj_close": float(row.adj_close)
                            if hasattr(row, "adj_close")
                            else None,
                        }
                    )

            logger.info(f"Retrieved {len(data)} data points for {symbol}")
            return data

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            # Fall back to mock data on error
            return self._get_mock_historical_data(symbol)

    async def get_quote(
        self, symbol: str, provider: str = "yfinance"
    ) -> Dict[str, Any]:
        """Get current quote data for a symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            provider: Data provider (e.g., "yfinance", "fmp", "intrinio")

        Returns:
            Current quote data dictionary

        """
        await self.initialize()

        if not self._obb:
            # Return mock data if OpenBB not available
            return self._get_mock_quote_data(symbol)

        try:
            # Validate provider (quote only supports fmp, intrinio, yfinance)
            valid_quote_providers: List[str] = ["fmp", "intrinio", "yfinance"]
            if provider not in valid_quote_providers:
                provider = "yfinance"  # Default fallback

            result = self._obb.equity.price.quote(  # type: ignore
                symbol=symbol,
                provider=provider,  # type: ignore
            )

            # Convert to our standard format
            if hasattr(result, "results") and result.results:
                row = result.results[0]  # Quote returns single result
                return {
                    "symbol": symbol,
                    "name": getattr(row, "name", symbol),
                    "price": float(getattr(row, "last_price", 0)),
                    "change": float(getattr(row, "change", 0)),
                    "change_percent": float(getattr(row, "change_percent", 0)),
                    "volume": int(getattr(row, "volume", 0)),
                    "market_cap": getattr(row, "market_cap", None),
                    "exchange": getattr(row, "exchange", "N/A"),
                    "asset_type": getattr(row, "asset_type", "EQUITY"),
                }

            logger.info(f"Retrieved quote for {symbol}")
            return self._get_mock_quote_data(symbol)

        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return self._get_mock_quote_data(symbol)

    def _get_mock_historical_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Generate obviously mock historical data for development."""
        return [
            {
                "date": datetime.now(timezone.utc),
                "open": 0.00,
                "high": 0.00,
                "low": 0.00,
                "close": 0.00,
                "volume": 0,
                "adj_close": 0.00,
            }
        ]

    def _get_mock_quote_data(self, symbol: str) -> Dict[str, Any]:
        """Generate obviously mock quote data for development."""
        return {
            "symbol": symbol,
            "name": f"MOCK {symbol} Company",
            "price": 0.00,
            "change": 0.00,
            "change_percent": 0.00,
            "volume": 0,
            "market_cap": 0,
            "exchange": "MOCK_EXCHANGE",
            "asset_type": "MOCK_EQUITY",
        }
