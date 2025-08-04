"""FastAPI wrapper for the investment research agent."""

import json
import os
import time
import traceback
from datetime import datetime, timezone
from typing import AsyncIterator

import uvicorn
from autogen_agentchat.agents._assistant_agent import AssistantAgent
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from investr.agent.agent import InvestmentAgent
from investr.agent.models import (
    ConversationArgs,
)
from investr.agent.tools.conversation_tool import ConversationTool
from investr.common.exceptions import (
    generic_exception_handler,
    http_exception_handler,
)
from investr.common.schemas import HealthCheck, ToolResult, UserRequest


class AgentAPI:
    """FastAPI wrapper for the investment research agent."""

    def __init__(
        self,
        openai_api_key: str,
        model_name: str = "gpt-4o-mini",
        data_api_url: str = "http://data-api:8002",
        openbb_api_url: str = "http://openbb-api:8001",
        analysis_api_url: str = "http://analysis-api:8000",
    ) -> None:
        """Initialize the Agent API.

        Args:
            openai_api_key: OpenAI API key
            model_name: LLM model to use
            data_api_url: URL for the Data API service
            openbb_api_url: URL for the OpenBB API service
            analysis_api_url: URL for the Analysis API service

        """
        # Create model client
        self.model_client = OpenAIChatCompletionClient(
            model=model_name, api_key=openai_api_key
        )

        # Create agent
        self.agent: AssistantAgent = InvestmentAgent.create_agent(
            model_client=self.model_client,
            data_api_url=data_api_url,
            openbb_api_url=openbb_api_url,
            analysis_api_url=analysis_api_url,
        )

        # Create ConversationTool for conversation storage
        self.conversation_tool = ConversationTool(data_api_base_url=data_api_url)

    async def stream_user_request(
        self, user_request: UserRequest
    ) -> AsyncIterator[str]:
        """Stream agent response with progress events for web UI.

        Args:
            user_request: The user request from web UI

        Yields:
            SSE-formatted events with progress updates

        """
        # Store user message in conversation first
        if self.conversation_tool:
            conversation_args = ConversationArgs(
                session_id=user_request.session_id,
                message={
                    "role": "user",
                    "content": user_request.message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                message_type="user",
            )
            await self.conversation_tool.run(conversation_args, CancellationToken())

        try:
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting your investment research...'})}\n\n"

            # Tool name to user-friendly message mapping
            tool_messages = {
                "get_market_data": "Getting latest stock market data...",
                "analyze_data": "Analyzing financial trends...",
                "store_conversation": "Saving conversation...",
                "search_data": "Searching financial databases...",
            }

            final_response_content = ""
            tool_calls_for_storage = []
            tool_execution_times = {}  # Track execution timing for each tool

            # Stream from AutoGen agent
            async for message in self.agent.run_stream(
                task=user_request.message,
                cancellation_token=None,
            ):
                message_type = getattr(message, "type", None)

                # Handle ToolCallRequestEvent - when agent starts calling a tool
                if message_type == "ToolCallRequestEvent":
                    content = getattr(message, "content", None)
                    if content and len(content) > 0:
                        # Extract tool name from first function call
                        first_call = content[0]
                        tool_name = getattr(first_call, "name", "unknown_tool")
                        
                        # Start timing this tool execution
                        tool_execution_times[tool_name] = time.time()
                        
                        friendly_message = tool_messages.get(
                            tool_name, f"Using {tool_name} tool..."
                        )

                        tool_start_event = {
                            "type": "tool_start",
                            "message": friendly_message,
                            "tool": tool_name,
                        }
                        yield f"data: {json.dumps(tool_start_event)}\n\n"

                # Handle ToolCallExecutionEvent - when tool execution completes
                elif message_type == "ToolCallExecutionEvent":
                    content = getattr(message, "content", None)
                    if content and len(content) > 0:
                        # Extract tool result from first execution result
                        execution_result = content[0]
                        tool_name = getattr(execution_result, "name", "unknown_tool")
                        tool_result = getattr(execution_result, "content", "")
                        is_error = getattr(execution_result, "is_error", False)

                        success = not is_error
                        
                        # Calculate execution time
                        execution_time_ms = None
                        if tool_name in tool_execution_times:
                            execution_time_ms = (time.time() - tool_execution_times[tool_name]) * 1000
                            del tool_execution_times[tool_name]  # Clean up

                        # Create user-friendly completion message
                        if success:
                            completion_messages = {
                                "get_market_data": "Retrieved market data successfully",
                                "analyze_data": "Analysis completed successfully",
                                "store_conversation": "Conversation saved",
                                "search_data": "Financial data retrieved",
                            }
                            friendly_message = completion_messages.get(
                                tool_name, f"{tool_name} completed successfully"
                            )
                        else:
                            friendly_message = f"Failed to complete {tool_name}"

                        # Create structured ToolResult for storage
                        tool_result_obj = ToolResult(
                            tool_name=tool_name,
                            success=success,
                            result=str(tool_result)[:500],  # Truncate for storage
                            error_message=str(tool_result) if not success else None,
                            execution_time_ms=execution_time_ms
                        )
                        tool_calls_for_storage.append(tool_result_obj)

                        tool_complete_event = {
                            "type": "tool_complete",
                            "message": friendly_message,
                            "tool": tool_name,
                            "success": success,
                            "tool_result": tool_result_obj.model_dump()  # Send structured data
                        }
                        yield f"data: {json.dumps(tool_complete_event)}\n\n"

                # Handle ToolCallSummaryMessage - agent's final response after tool use
                elif message_type == "ToolCallSummaryMessage":
                    content = getattr(message, "content", "")
                    if isinstance(content, str) and len(content) > 10:
                        final_response_content = content

                # Handle TextMessage - agent's direct response (when no tools used)
                elif message_type == "TextMessage":
                    source = getattr(message, "source", "")
                    content = getattr(message, "content", "")
                    if (
                        source == "investment_researcher"
                        and isinstance(content, str)
                        and len(content) > 10
                    ):
                        final_response_content = content

            # Send final response
            if not final_response_content:
                final_response_content = "Investment research completed successfully"

            response_event = {
                "type": "response",
                "message": final_response_content,
                "final": True,
            }
            yield f"data: {json.dumps(response_event)}\n\n"

            # Store assistant response in conversation
            if self.conversation_tool:
                # Convert ToolResult objects to dicts for JSON serialization
                tool_calls_dict = [tool_call.model_dump() for tool_call in tool_calls_for_storage] if tool_calls_for_storage else None
                
                conversation_args = ConversationArgs(
                    session_id=user_request.session_id,
                    message={
                        "role": "assistant",
                        "content": final_response_content,
                        "tool_calls": tool_calls_dict,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    message_type="assistant",
                )
                await self.conversation_tool.run(conversation_args, CancellationToken())

        except Exception as e:
            error_event = {"type": "error", "message": f"An error occurred: {str(e)}"}
            yield f"data: {json.dumps(error_event)}\n\n"


def create_app(
    openai_api_key: str,
    model_name: str = "gpt-4o-mini",
    data_api_url: str = "http://data-api:8002",
    openbb_api_url: str = "http://openbb-api:8001",
    analysis_api_url: str = "http://analysis-api:8000",
) -> FastAPI:
    """Create a FastAPI application with the investment agent.

    Args:
        openai_api_key: OpenAI API key
        model_name: LLM model to use
        data_api_url: URL for the Data API service
        openbb_api_url: URL for the OpenBB API service
        analysis_api_url: URL for the Analysis API service

    Returns:
        Configured FastAPI application

    """
    app = FastAPI(
        title="Investment Research Agent API",
        description="AI-powered investment research assistant",
        version="1.0.0",
    )

    # Add exception handlers for standardized error responses
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore

    # Initialize agent API
    agent_api = AgentAPI(
        openai_api_key=openai_api_key,
        model_name=model_name,
        data_api_url=data_api_url,
        openbb_api_url=openbb_api_url,
        analysis_api_url=analysis_api_url,
    )

    @app.post("/agent/stream")
    async def stream_agent_user(request: UserRequest) -> StreamingResponse:
        """Stream agent response with progress events for web UI."""
        return StreamingResponse(
            agent_api.stream_user_request(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    @app.get("/health")
    async def health_check() -> HealthCheck:
        """Health check endpoint."""
        return HealthCheck(
            service="investment-agent", status="healthy", version="1.0.0"
        )

    return app


if __name__ == "__main__":
    print("Starting Investment Agent API...")

    # Get configuration from environment variables
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "placeholder-key")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    port: int = int(os.getenv("PORT", 8000))

    print(
        f"Configuration: API Key: {'***' if openai_api_key != 'placeholder-key' else 'placeholder'}, Model: {model_name}, Port: {port}"
    )

    try:
        # Create the FastAPI app
        print("Creating FastAPI app...")
        app: FastAPI = create_app(
            openai_api_key=openai_api_key,
            model_name=model_name,
        )
        print("FastAPI app created successfully")

        # Run the server
        print(f"Starting server on 0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Error starting agent API: {e}")
        traceback.print_exc()
        raise
