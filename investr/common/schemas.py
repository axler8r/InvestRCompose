"""Common schemas for data exchange between services.

This module defines Pydantic schemas for payloads flowing between the Web UI
and Agent API, ensuring type safety and validation across service boundaries.

PURPOSE: Service boundary schemas - use for API contracts between services
SCOPE: External communication between microservices (Web UI ↔ Agent API)
CHARACTERISTICS: Simple, stable, focused on API contracts

For internal agent operations and complex domain models, use investr.agent.models instead.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UserRequest(BaseModel):
    """Request from Web UI to Agent API."""

    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., description="User's input message")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context for the request"
    )


class RequestStatus(str, Enum):
    """Status of a request processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentResponse(BaseModel):
    """Response from Agent API to Web UI."""

    session_id: str
    message: str
    status: RequestStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Details of tool calls made during processing"
    )
    references: Optional[List[str]] = Field(
        default=None, description="Links or document references provided by the agent"
    )
    metadata: Optional[Dict[str, Any]] = None


class MessageRole(str, Enum):
    """Role of a message in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """A single message in a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = None


class ConversationHistory(BaseModel):
    """Complete conversation history for a session."""

    session_id: str
    messages: List[Message]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthCheck(BaseModel):
    """Health check response schema."""

    service: str
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Optional[Dict[str, Any]] = None
