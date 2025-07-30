"""FastAPI service for OpenBB integration.

This module provides REST API endpoints for accessing OpenBB Platform
data through a standardized interface.
"""

import os
import time
from typing import Annotated, Any, Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException, Query

from investr.common.exceptions import (
    generic_exception_handler,
    http_exception_handler,
)
from investr.common.schemas import HealthCheck
from investr.openbb.openbb_client import OpenBBClient


class OpenBBAPI:
    """FastAPI wrapper for OpenBB Platform access."""

    def __init__(self) -> None:
        """Initialize the OpenBB API service."""
        self.client = OpenBBClient()

    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application.

        Returns:
            Configured FastAPI application

        """
        app = FastAPI(
            title="OpenBB API Service",
            description="Investment data service powered by OpenBB Platform",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # Add exception handlers for standardized error responses
        app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
        app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore

        @app.get("/health")
        async def health_check() -> HealthCheck:
            """Health check endpoint."""
            return HealthCheck(service="openbb-api", status="healthy", version="1.0.0")

        @app.get("/market-data/historical/{symbol}")
        async def get_historical_data(
            symbol: str,
            period: Annotated[
                str, Query(description="Time period (1y, 6m, 3m, 1m)")
            ] = "1y",
            interval: Annotated[
                str, Query(description="Data interval (1d, 1h, 5m)")
            ] = "1d",
            provider: Annotated[str, Query(description="Data provider")] = "yfinance",
        ) -> Dict[str, Any]:
            """Get historical price data for a symbol.

            Args:
                symbol: Stock symbol (e.g., AAPL)
                period: Time period for data
                interval: Data interval
                provider: Data provider to use

            Returns:
                Historical price data with metadata

            """
            try:
                start_time: float = time.time()

                data: List[Dict[str, Any]] = await self.client.get_historical_prices(
                    symbol=symbol.upper(),
                    period=period,
                    interval=interval,
                    provider=provider,
                )

                query_time_ms: float = (time.time() - start_time) * 1000

                return {
                    "symbol": symbol.upper(),
                    "data": data,
                    "metadata": {
                        "symbol": symbol.upper(),
                        "data_type": "historical",
                        "period": period,
                        "interval": interval,
                        "provider": provider,
                        "count": len(data),
                        "query_time_ms": round(query_time_ms, 2),
                        "currency": "USD",
                        "exchange": "NASDAQ",  # This should come from the data
                        "timezone": "US/Eastern",
                    },
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error retrieving historical data for {symbol}: {str(e)}",
                )

        @app.get("/market-data/quote/{symbol}")
        async def get_quote(
            symbol: str,
            provider: Annotated[str, Query(description="Data provider")] = "yfinance",
        ) -> Dict[str, Any]:
            """Get current quote for a symbol.

            Args:
                symbol: Stock symbol (e.g., AAPL)
                provider: Data provider to use

            Returns:
                Current quote data

            """
            try:
                start_time: float = time.time()

                quote_data: Dict[str, Any] = await self.client.get_quote(
                    symbol=symbol.upper(), provider=provider
                )

                query_time_ms = (time.time() - start_time) * 1000
                quote_data["query_time_ms"] = round(query_time_ms, 2)

                return quote_data

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error retrieving quote for {symbol}: {str(e)}",
                )

        @app.get("/market-data/batch")
        async def get_batch_quotes(
            symbols: Annotated[str, Query(description="Comma-separated symbols")],
            provider: Annotated[str, Query(description="Data provider")] = "yfinance",
        ) -> Dict[str, Any]:
            """Get quotes for multiple symbols.

            Args:
                symbols: Comma-separated list of symbols
                provider: Data provider to use

            Returns:
                Batch quote data

            """
            try:
                symbol_list: List[str] = [s.strip().upper() for s in symbols.split(",")]
                results = {}

                for symbol in symbol_list:
                    try:
                        quote_data: Dict[str, Any] = await self.client.get_quote(
                            symbol=symbol, provider=provider
                        )
                        results[symbol] = quote_data
                    except Exception as e:
                        results[symbol] = {"error": str(e)}

                return {
                    "symbols": symbol_list,
                    "results": results,
                    "count": len(symbol_list),
                    "provider": provider,
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error retrieving batch quotes: {str(e)}"
                )

        return app


def create_app() -> FastAPI:
    """Create the OpenBB API application.

    Returns:
        Configured FastAPI application

    """
    openbb_api = OpenBBAPI()
    return openbb_api.create_app()


def main() -> None:
    """Run the OpenBB API service."""
    app: FastAPI = create_app()

    port = int(os.environ.get("PORT", 8001))
    host: str = os.environ.get("HOST", "0.0.0.0")

    print(f"Starting OpenBB API service on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=os.environ.get("RELOAD", "false").lower() == "true",
    )


if __name__ == "__main__":
    main()
