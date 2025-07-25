"""FastAPI service for conversation storage and retrieval."""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from .database import mongodb_client
from .models import (
    Conversation,
    ConversationHistoryResponse,
    ConversationRequest,
    ConversationResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events for database connections.
    """
    # Startup
    try:
        await mongodb_client.connect()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize database: {e}") from e
    
    yield
    
    # Shutdown
    await mongodb_client.disconnect()


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

    @app.get("/health")
    async def health_check() -> JSONResponse:
        """Health check endpoint.

        Returns:
            JSON response with service health status

        """
        db_healthy = await mongodb_client.health_check()

        return JSONResponse(
            status_code=status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "service": "data-api",
                "status": "healthy" if db_healthy else "unhealthy",
                "database": "connected" if db_healthy else "disconnected",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @app.post("/conversations")
    async def add_message(request: ConversationRequest) -> ConversationResponse:
        """Add a message to a conversation.

        Creates a new conversation if one doesn't exist for the session.

        Args:
            request: Conversation request with session_id and message

        Returns:
            ConversationResponse with updated conversation details

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
                conversation.updated_at = datetime.utcnow()
                await conversation.save()

            return ConversationResponse(
                session_id=conversation.session_id,
                message_count=len(conversation.messages),
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save conversation: {str(e)}",
            ) from e

    @app.get("/conversations/{session_id}")
    async def get_conversation(session_id: str) -> ConversationHistoryResponse:
        """Retrieve conversation history for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            ConversationHistoryResponse with message history

        Raises:
            HTTPException: If conversation not found

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

            return ConversationHistoryResponse(
                session_id=conversation.session_id,
                messages=conversation.messages,
                message_count=len(conversation.messages),
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                title=conversation.title,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve conversation: {str(e)}",
            ) from e

    @app.delete("/conversations/{session_id}")
    async def delete_conversation(session_id: str) -> JSONResponse:
        """Delete a conversation.

        Args:
            session_id: Unique session identifier

        Returns:
            JSON response confirming deletion

        Raises:
            HTTPException: If conversation not found

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
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete conversation: {str(e)}",
            ) from e

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.getenv("PORT", 8002))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "investr.data.api:app",
        host=host,
        port=port,
        reload=True,
    )
