"""Pydantic models for conversation storage using Beanie ODM."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from beanie import Document
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Individual message within a conversation."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Agent tool executions for this message"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional message metadata"
    )


class Conversation(Document):
    """Conversation document for MongoDB storage."""

    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(
        default=None, description="User ID (reserved for future auth)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[Message] = Field(
        default_factory=list, description="List of messages in conversation"
    )
    title: Optional[str] = Field(
        default=None, description="Optional conversation title"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional conversation metadata"
    )

    class Settings:
        """Beanie document settings."""

        name = "conversations"
        indexes = [
            "session_id",
            "user_id",
            "created_at",
        ]


class ConversationRequest(BaseModel):
    """Request model for creating/updating conversations."""

    session_id: str = Field(..., description="Session identifier")
    message: Message = Field(..., description="New message to add")


class ConversationResponse(BaseModel):
    """Response model for conversation operations."""

    session_id: str
    message_count: int
    created_at: datetime
    updated_at: datetime
    success: bool = True


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history retrieval."""

    session_id: str
    messages: List[Message]
    message_count: int
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None
