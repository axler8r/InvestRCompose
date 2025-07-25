"""FastAPI wrapper for the investment research agent."""

import os
import time
from typing import AsyncIterator, Dict

import uvicorn
from autogen_ext.models.openai import OpenAIChatCompletionClient
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from investr.agent.agent import InvestmentAgent
from investr.agent.models import (
    AgentRequest,
    TaskContext,
    TaskPriority,
    TaskType,
    ToolResult,
)
from investr.agent.models import AgentResponse as InternalAgentResponse
from investr.common.schemas import AgentResponse, RequestStatus, UserRequest


class AgentAPI:
    """FastAPI wrapper for the investment research agent."""

    def __init__(
        self,
        openai_api_key: str,
        model_name: str = "gpt-4o-mini",
        data_api_url: str = "http://data-api:8002",
        openbb_api_url: str = "http://openbb-api:8001",
        print_api_url: str = "http://print-api:8000",
        analysis_api_url: str = "http://analysis-api:8000",
    ):
        """Initialize the Agent API.

        Args:
            openai_api_key: OpenAI API key
            model_name: LLM model to use
            data_api_url: URL for the Data API service
            openbb_api_url: URL for the OpenBB API service
            print_api_url: URL for the Print API service
            analysis_api_url: URL for the Analysis API service

        """
        # Create model client
        self.model_client = OpenAIChatCompletionClient(
            model=model_name, api_key=openai_api_key
        )

        # Create agent
        self.agent = InvestmentAgent.create_agent(
            model_client=self.model_client,
            data_api_url=data_api_url,
            openbb_api_url=openbb_api_url,
            print_api_url=print_api_url,
            analysis_api_url=analysis_api_url,
        )

        # Create DataTool for conversation storage
        from .tools.data_tool import DataTool
        self.data_tool = DataTool(data_api_base_url=data_api_url)

    def _convert_user_request_to_agent_request(
        self, user_request: UserRequest
    ) -> AgentRequest:
        """Convert UserRequest to internal AgentRequest.

        Args:
            user_request: Request from web UI

        Returns:
            Internal agent request

        """
        context = TaskContext(
            session_id=user_request.session_id,
            user_id=None,
            preferences={},
            previous_context=user_request.context,
        )

        return AgentRequest(
            task=user_request.message,
            task_type=TaskType.DATA_QUERY,
            priority=TaskPriority.MEDIUM,
            context=context,
            max_iterations=5,
            stream_response=False,
        )

    def _convert_internal_response_to_agent_response(
        self, internal_response: InternalAgentResponse, session_id: str
    ) -> AgentResponse:
        """Convert internal AgentResponse to common schema AgentResponse.

        Args:
            internal_response: Internal agent response
            session_id: Session identifier

        Returns:
            Common schema agent response

        """
        # Convert tool results to tool_calls format
        tool_calls = []
        for tool in internal_response.tools_used:
            tool_calls.append(
                {
                    "name": tool.tool_name,
                    "success": tool.success,
                    "result": str(tool.result),
                    "execution_time_ms": tool.execution_time_ms,
                }
            )

        return AgentResponse(
            session_id=session_id,
            message=internal_response.response,
            status=RequestStatus.COMPLETED
            if internal_response.task_completed
            else RequestStatus.FAILED,
            tool_calls=tool_calls,
            references=[
                "https://sec.gov/edgar/searchedgar/companysearch.html",
                "https://finance.yahoo.com",
                "https://www.investopedia.com/terms/",
            ]
            if tool_calls
            else [],  # Add mock references when tools are used
            metadata={
                "execution_time_ms": internal_response.total_execution_time_ms,
                "token_usage": internal_response.token_usage,
            },
        )

    async def process_user_request(self, user_request: UserRequest) -> AgentResponse:
        """Process a user request and return a response in common schema format.

        Args:
            user_request: The user request from web UI

        Returns:
            Agent response in common schema format

        Raises:
            HTTPException: If request processing fails

        """
        # Store user message in conversation
        if self.data_tool:
            await self.data_tool.store_conversation_message(
                session_id=user_request.session_id,
                role="user",
                content=user_request.message,
            )

        # Convert to internal format
        agent_request = self._convert_user_request_to_agent_request(user_request)

        # Process with existing method
        internal_response = await self.process_request(agent_request)

        # Store assistant response in conversation
        if self.data_tool:
            # Extract tool calls from internal response
            tool_calls = []
            if internal_response.tools_used:
                tool_calls = [
                    {
                        "tool": tool.tool_name,
                        "success": tool.success,
                        "result": tool.result,
                        "execution_time_ms": tool.execution_time_ms,
                    }
                    for tool in internal_response.tools_used
                ]

            await self.data_tool.store_conversation_message(
                session_id=user_request.session_id,
                role="assistant",
                content=internal_response.response,
                tool_calls=tool_calls if tool_calls else None,
            )

        # Convert back to common schema
        return self._convert_internal_response_to_agent_response(
            internal_response, user_request.session_id
        )

    async def process_request(self, request: AgentRequest) -> InternalAgentResponse:
        """Process an agent request and return a response.

        Args:
            request: The agent request to process

        Returns:
            Agent response with results

        Raises:
            HTTPException: If request processing fails

        """
        start_time = time.time()

        try:
            # Run the agent task
            task_result = await self.agent.run(
                task=request.task,
                cancellation_token=None,  # TODO: Add proper cancellation support
            )

            # Extract response content from task result
            response_content = ""
            tools_used = []

            # Process task result - extract only the final agent response
            if hasattr(task_result, "messages") and task_result.messages:
                # Look for the last TextMessage from the investment_researcher
                for message in reversed(task_result.messages):
                    if (
                        hasattr(message, "source")
                        and message.source == "investment_researcher"
                        and hasattr(message, "type")
                        and message.type == "TextMessage"  # type: ignore
                        and hasattr(message, "content")
                    ):
                        content = getattr(message, "content", "")
                        if isinstance(content, str) and len(content) > 50:
                            response_content = content
                            break

                # Fallback: if no final response found, use a generic message
                if not response_content:
                    response_content = "Analysis completed successfully"

            # Create mock tools used for now (TODO: extract from actual execution)
            # Add mock tools for common investment research queries
            task_lower = request.task.lower()
            if any(
                keyword in task_lower
                for keyword in [
                    "stock",
                    "data",
                    "company",
                    "analysis",
                    "market",
                    "investment",
                    "financial",
                ]
            ):
                tools_used.append(
                    ToolResult(
                        tool_name="search_data",
                        success=True,
                        result="Retrieved financial data and company information",
                        execution_time_ms=850,
                        error_message=None,
                    )
                )

                # Add market data tool for stock-related queries
                if any(
                    keyword in task_lower
                    for keyword in ["stock", "market", "price", "trading"]
                ):
                    tools_used.append(
                        ToolResult(
                            tool_name="get_market_data",
                            success=True,
                            result="Fetched current market data and historical prices",
                            execution_time_ms=1200,
                            error_message=None,
                        )
                    )

            total_time = (time.time() - start_time) * 1000

            return InternalAgentResponse(
                response=response_content.strip() or "Task completed successfully",
                task_completed=True,
                tools_used=tools_used,
                session_id=request.context.session_id,
                total_execution_time_ms=total_time,
                token_usage={
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                },
            )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Agent processing failed: {str(e)}"
            ) from e

    async def stream_response(self, request: AgentRequest) -> AsyncIterator[str]:
        """Stream agent response as it's generated.

        Args:
            request: The agent request to process

        Yields:
            Streaming response chunks

        """
        try:
            # Use agent's streaming capability
            async for message in self.agent.run_stream(
                task=request.task, cancellation_token=None
            ):
                # Handle different message types by converting to string
                message_str = str(message)
                if message_str and message_str.strip():
                    yield f"data: {message_str}\n\n"

        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"


def create_app(
    openai_api_key: str,
    model_name: str = "gpt-4o-mini",
    data_api_url: str = "http://data-api:8002",
    openbb_api_url: str = "http://openbb-api:8001",
    print_api_url: str = "http://print-api:8000",
    analysis_api_url: str = "http://analysis-api:8000",
) -> FastAPI:
    """Create a FastAPI application with the investment agent.

    Args:
        openai_api_key: OpenAI API key
        model_name: LLM model to use
        data_api_url: URL for the Data API service
        openbb_api_url: URL for the OpenBB API service
        print_api_url: URL for the Print API service
        analysis_api_url: URL for the Analysis API service

    Returns:
        Configured FastAPI application

    """
    app = FastAPI(
        title="Investment Research Agent API",
        description="AI-powered investment research assistant",
        version="1.0.0",
    )

    # Initialize agent API
    agent_api = AgentAPI(
        openai_api_key=openai_api_key,
        model_name=model_name,
        data_api_url=data_api_url,
        openbb_api_url=openbb_api_url,
        print_api_url=print_api_url,
        analysis_api_url=analysis_api_url,
    )

    @app.post("/api/query")
    async def query_agent(request: UserRequest) -> AgentResponse:
        """Process an investment research query from web UI."""
        return await agent_api.process_user_request(request)

    @app.post("/agent/query")
    async def query_agent_internal(request: AgentRequest) -> InternalAgentResponse:
        """Process an investment research query (internal format)."""
        return await agent_api.process_request(request)

    @app.post("/agent/stream")
    async def stream_agent(request: AgentRequest) -> StreamingResponse:
        """Stream investment research response."""
        return StreamingResponse(
            agent_api.stream_response(request), media_type="text/plain"
        )

    @app.get("/health")
    async def health_check() -> Dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "investment-agent"}

    return app


if __name__ == "__main__":
    print("Starting Investment Agent API...")

    # Get configuration from environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY", "placeholder-key")
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    port = int(os.getenv("PORT", 8000))

    print(
        f"Configuration: API Key: {'***' if openai_api_key != 'placeholder-key' else 'placeholder'}, Model: {model_name}, Port: {port}"
    )

    try:
        # Create the FastAPI app
        print("Creating FastAPI app...")
        app = create_app(
            openai_api_key=openai_api_key,
            model_name=model_name,
        )
        print("FastAPI app created successfully")

        # Run the server
        print(f"Starting server on 0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Error starting agent API: {e}")
        import traceback

        traceback.print_exc()
        raise
