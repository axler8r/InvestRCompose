"""FastAPI service for conversation storage and retrieval."""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Response, status
from loguru import logger

from investr.common.exceptions import (
    generic_exception_handler,
    http_exception_handler,
)
from investr.common.schemas import HealthCheck
from investr.data.client import mongodb_client
from investr.data.models import (
    Conversation,
    ConversationHistoryResponse,
    ConversationRequest,
    ConversationResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Starting Data API service...")
    await mongodb_client.connect()
    logger.info("MongoDB client connected")

    yield

    # Shutdown
    await mongodb_client.disconnect()
    logger.info("Data API service shut down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance

    """
    app = FastAPI(
        title="InvestR Data API",
        description="Conversation storage and retrieval service",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add exception handlers for standardized error responses
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore

    @app.get("/health")
    async def health_check(response: Response) -> HealthCheck:
        """Health check endpoint.

        Returns:
            HealthCheck response with service health status including database connectivity

        """
        db_healthy: bool = await mongodb_client.health_check()

        # Set appropriate HTTP status code
        if not db_healthy:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return HealthCheck(
            service="data-api",
            status="healthy" if db_healthy else "unhealthy",
            version="1.0.0",
            metadata={"database": "connected" if db_healthy else "disconnected"},
        )

    @app.post("/conversations")
    async def store_conversation(request: ConversationRequest) -> ConversationResponse:
        """Store a conversation message.

        Args:
            request: Conversation storage request

        Returns:
            Response with conversation metadata

        Raises:
            HTTPException: If storage operation fails

        """
        try:
            # Find existing conversation or create new one
            conversation = await Conversation.find_one(
                Conversation.session_id == request.session_id
            )

            if conversation is None:
                # Create new conversation
                conversation = Conversation(
                    session_id=request.session_id,
                    messages=[request.message],
                )
                await conversation.insert()
            else:
                # Add message to existing conversation
                conversation.messages.append(request.message)
                conversation.updated_at = datetime.now(timezone.utc)
                await conversation.save()

            return ConversationResponse(
                session_id=conversation.session_id,
                message_count=len(conversation.messages),
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )

        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store conversation: {str(e)}",
            ) from e

    @app.get("/conversations/{session_id}")
    async def get_conversation_history(
        session_id: str,
        limit: Optional[int] = None,
    ) -> ConversationHistoryResponse:
        """Retrieve conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return

        Returns:
            Conversation history with messages

        Raises:
            HTTPException: If retrieval operation fails

        """
        try:
            conversation = await Conversation.find_one(
                Conversation.session_id == session_id
            )

            if conversation is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation not found for session: {session_id}",
                )

            # Apply limit if specified
            messages = conversation.messages
            if limit is not None and limit > 0:
                messages = messages[-limit:]

            return ConversationHistoryResponse(
                session_id=conversation.session_id,
                messages=messages,
                total_messages=len(conversation.messages),  # type: ignore
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )  # type: ignore

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve conversation: {str(e)}",
            ) from e

    return app


# Create the FastAPI app instance
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "investr.data.api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8002")),
        reload=True,
    )
