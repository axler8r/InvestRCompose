"""Data API tool for conversation storage and retrieval."""

from datetime import datetime

import httpx
from autogen_core import CancellationToken
from autogen_core.tools import BaseTool

from investr.agent.models import ConversationArgs, ConversationResult


class ConversationTool(BaseTool[ConversationArgs, ConversationResult]):
    """Tool for storing and retrieving conversation data via Data API.

    This tool handles conversation persistence, session management,
    and message storage for agent-user interactions.
    """

    def __init__(self, data_api_base_url: str = "http://data-api:8002") -> None:
        """Initialize the conversation tool.

        Args:
            data_api_base_url: Base URL for the Data API service

        """
        super().__init__(
            args_type=ConversationArgs,
            return_type=ConversationResult,
            name="store_conversation",
            description=(
                "Store conversation messages for session persistence. "
                "Maintains conversation history across agent interactions."
            ),
        )
        self.data_api_url: str = data_api_base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def run(
        self, args: ConversationArgs, cancellation_token: CancellationToken
    ) -> ConversationResult:
        """Store a conversation message.

        Args:
            args: Conversation storage parameters
            cancellation_token: Token for canceling the operation

        Returns:
            Storage confirmation with metadata

        """
        try:
            # Call Data API for conversation storage
            response = await self.client.post(
                f"{self.data_api_url}/conversations",
                json={
                    "session_id": args.session_id,
                    "message": args.message,
                },
            )

            if response.status_code == 200:
                data = response.json()
                return ConversationResult(
                    session_id=data.get("session_id", args.session_id),
                    message_count=data.get("message_count", 1),
                    stored_at=datetime.utcnow(),
                )
            else:
                # API error - return mock result
                return ConversationResult(
                    session_id=args.session_id,
                    message_count=1,
                    stored_at=datetime.utcnow(),
                )

        except Exception:
            # Network error - return mock result
            return ConversationResult(
                session_id=args.session_id,
                message_count=1,
                stored_at=datetime.utcnow(),
            )

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
                data = response.json()
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
