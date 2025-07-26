"""MongoDB client configuration and connection management."""

import os
from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from investr.data.models import Conversation


class MongoDBClient:
    """MongoDB client wrapper for conversation storage."""

    def __init__(self, connection_string: Optional[str] = None):
        """Initialize MongoDB client.

        Args:
            connection_string: MongoDB connection string. If None, reads from env.

        """
        self.connection_string = connection_string or os.getenv(
            "MONGODB_URL", "mongodb://localhost:27017"
        )
        self.database_name = os.getenv("MONGODB_DATABASE", "investr")
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None

    async def connect(self) -> None:
        """Establish connection to MongoDB and initialize Beanie."""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.database = self.client[self.database_name]

            # Initialize Beanie with our document models
            await init_beanie(
                database=self.database,  # type: ignore[arg-type]
                document_models=[Conversation],
            )

        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}") from e

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None

    async def health_check(self) -> bool:
        """Check if MongoDB connection is healthy.

        Returns:
            True if connection is healthy, False otherwise

        """
        try:
            if not self.client:
                return False

            # Ping the database
            await self.client.admin.command("ping")
            return True

        except Exception:
            return False


# Global MongoDB client instance
mongodb_client = MongoDBClient()
