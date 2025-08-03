"""FastAPI service for conversation storage and retrieval."""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from investr.common.exceptions import (
    generic_exception_handler,
    http_exception_handler,
)
from investr.data.database import mongodb_client
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
    async def health_check() -> JSONResponse:
        """Health check endpoint.

        Returns:
            JSON response with service health status

        """
        db_healthy: bool = await mongodb_client.health_check()

        return JSONResponse(
            status_code=status.HTTP_200_OK
            if db_healthy
            else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "service": "data-api",
                "status": "healthy" if db_healthy else "unhealthy",
                "database": "connected" if db_healthy else "disconnected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
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

    @app.delete("/conversations/{session_id}")
    async def delete_conversation(session_id: str) -> JSONResponse:
        """Delete a conversation and all its messages.

        Args:
            session_id: Session identifier

        Returns:
            Deletion confirmation response

        Raises:
            HTTPException: If deletion operation fails

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

            await conversation.delete()

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": f"Conversation deleted for session: {session_id}",
                    "session_id": session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete conversation: {str(e)}",
            ) from e

    @app.get("/conversations")
    async def list_conversations(limit: Optional[int] = 50) -> JSONResponse:
        """List all conversation sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of conversation sessions with metadata

        Raises:
            HTTPException: If listing operation fails

        """
        try:
            query = Conversation.find_all()
            if limit:
                query = query.limit(limit)

            conversations = await query.to_list()

            session_list = [
                {
                    "session_id": conv.session_id,
                    "message_count": len(conv.messages),
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                }
                for conv in conversations
            ]

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "sessions": session_list,
                    "total_count": len(session_list),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list conversations: {str(e)}",
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
