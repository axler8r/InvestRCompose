"""OpenBB API service for investment data retrieval.

This package provides a FastAPI service that integrates with the OpenBB Platform
to deliver real-time and historical market data, company fundamentals, and
financial metrics.
"""

from .api import create_app
from .openbb_client import OpenBBClient

__all__ = ["create_app", "OpenBBClient"]
