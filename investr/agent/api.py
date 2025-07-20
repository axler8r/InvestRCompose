"""FastAPI wrapper for the investment research agent."""

import time
from typing import AsyncIterator, Dict

from autogen_ext.models.openai import OpenAIChatCompletionClient
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from .agent import InvestmentAgent
from .models import AgentRequest, AgentResponse, ToolResult


class AgentAPI:
    """FastAPI wrapper for the investment research agent."""

    def __init__(
        self,
        openai_api_key: str,
        model_name: str = "gpt-4o-mini",
        data_api_url: str = "http://data-api:8000",
        openbb_api_url: str = "http://openbb-api:8000",
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

    async def process_request(self, request: AgentRequest) -> AgentResponse:
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

            # Process task result - extract meaningful content
            if hasattr(task_result, "messages") and task_result.messages:
                for message in task_result.messages:
                    # Handle string representation of messages
                    message_str = str(message)
                    if message_str and message_str.strip():
                        response_content += message_str + "\n"

            # Create mock tools used for now (TODO: extract from actual execution)
            if "data" in request.task.lower():
                tools_used.append(
                    ToolResult(
                        tool_name="search_data",
                        success=True,
                        result="Data search completed",
                        execution_time_ms=50,
                        error_message=None,
                    )
                )

            total_time = (time.time() - start_time) * 1000

            return AgentResponse(
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
    data_api_url: str = "http://data-api:8000",
    openbb_api_url: str = "http://openbb-api:8000",
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

    @app.post("/agent/query")
    async def query_agent(request: AgentRequest) -> AgentResponse:
        """Process an investment research query."""
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
