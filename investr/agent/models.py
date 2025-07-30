"""Pydantic models for agent requests, responses, and data structures.

PURPOSE: Agent domain models - use for internal agent operations and workflows
SCOPE: Internal agent module operations, task execution, tool orchestration
CHARACTERISTICS: Complex, detailed, rich domain logic and business rules

This module defines rich domain models for the agent's internal operations including:
- Task execution contexts and workflows
- Tool execution arguments and results
- Detailed agent responses with execution metadata
- Investment research domain-specific data structures

For simple service-to-service communication schemas, use investr.common.schemas instead.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Types of investment research tasks."""

    COMPANY_ANALYSIS = "company_analysis"
    MARKET_RESEARCH = "market_research"
    PORTFOLIO_REVIEW = "portfolio_review"
    REPORT_GENERATION = "report_generation"
    DATA_QUERY = "data_query"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskContext(BaseModel):
    """Context information for task execution."""

    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    preferences: Dict[str, Any] = Field(
        default_factory=dict, description="User preferences"
    )
    previous_context: Optional[Dict[str, Any]] = Field(
        None, description="Previous conversation context"
    )


class AgentRequest(BaseModel):
    """Request model for agent interactions."""

    task: str = Field(..., description="The task or question for the agent")
    task_type: TaskType = Field(
        TaskType.DATA_QUERY, description="Type of task to perform"
    )
    priority: TaskPriority = Field(
        TaskPriority.MEDIUM, description="Task priority level"
    )
    context: TaskContext = Field(..., description="Task execution context")
    max_iterations: int = Field(5, description="Maximum number of tool calls allowed")
    stream_response: bool = Field(False, description="Whether to stream the response")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ToolResult(BaseModel):
    """Result from a tool execution."""

    tool_name: str = Field(..., description="Name of the executed tool")
    success: bool = Field(..., description="Whether the tool execution was successful")
    result: Union[str, Dict[str, Any], List[Any]] = Field(
        ..., description="Tool execution result"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if execution failed"
    )
    execution_time_ms: Optional[float] = Field(
        None, description="Tool execution time in milliseconds"
    )


class AgentResponse(BaseModel):
    """Response model for agent interactions."""

    response: str = Field(..., description="The agent's response")
    task_completed: bool = Field(
        ..., description="Whether the task was completed successfully"
    )
    tools_used: List[ToolResult] = Field(
        default_factory=list, description="Tools that were executed"
    )
    session_id: str = Field(..., description="Session identifier")
    total_execution_time_ms: Optional[float] = Field(
        None, description="Total execution time"
    )
    token_usage: Optional["TokenUsage"] = Field(
        None, description="Token usage statistics"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class TokenUsage(BaseModel):
    """Token usage statistics."""

    prompt_tokens: int = Field(0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(0, description="Number of tokens in the completion")
    total_tokens: int = Field(0, description="Total number of tokens used")


# Tool-specific models
class ConversationArgs(BaseModel):
    """Arguments for conversation storage tool."""

    session_id: str = Field(..., description="Unique session identifier")
    message: Dict[str, Any] = Field(..., description="Message to store")
    message_type: str = Field("user", description="Type of message (user, agent, tool)")


class ConversationResult(BaseModel):
    """Result from conversation storage tool."""

    session_id: str = Field(..., description="Session identifier")
    message_count: int = Field(..., description="Total messages in conversation")
    stored_at: datetime = Field(..., description="When the message was stored")


class MarketDataArgs(BaseModel):
    """Arguments for market data tool."""

    symbol: str = Field(..., description="Stock symbol or ticker")
    data_type: str = Field("price", description="Type of data to retrieve")
    period: str = Field("1y", description="Time period for data")
    interval: str = Field("1d", description="Data interval")


class MarketDataResult(BaseModel):
    """Result from market data tool."""

    symbol: str = Field(..., description="Stock symbol")
    data: List[Dict[str, Any]] = Field(..., description="Market data points")
    metadata: Dict[str, Any] = Field(..., description="Data metadata")


class AnalysisArgs(BaseModel):
    """Arguments for analysis tool."""

    data: Union[List[Dict[str, Any]], str] = Field(..., description="Data to analyze")
    analysis_type: str = Field("summary", description="Type of analysis to perform")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Analysis parameters"
    )


class AnalysisResult(BaseModel):
    """Result from analysis tool."""

    analysis_type: str = Field(..., description="Type of analysis performed")
    results: Dict[str, Any] = Field(..., description="Analysis results")
    insights: List[str] = Field(..., description="Key insights from the analysis")
    confidence_score: Optional[float] = Field(
        None, description="Confidence score for the analysis"
    )


# Export all models
__all__ = [
    # Enums
    "TaskType",
    "TaskPriority",
    # Core models
    "TaskContext",
    "AgentRequest",
    "AgentResponse",
    "ToolResult",
    "TokenUsage",
    # Tool-specific models
    "ConversationArgs",
    "ConversationResult",
    "MarketDataArgs",
    "MarketDataResult",
    "AnalysisArgs",
    "AnalysisResult",
]
