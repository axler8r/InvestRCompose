"""OpenBB API service for investment data retrieval.

This package provides a FastAPI service that integrates with the OpenBB Platform
to deliver real-time and historical market data, company fundamentals, and
financial metrics.
"""

from investr.openbb.api import create_app
from investr.openbb.openbb_client import OpenBBClient

__all__: list[str] = ["create_app", "OpenBBClient"]
