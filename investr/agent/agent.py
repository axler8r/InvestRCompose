"""Investment research agent using AutoGen framework."""

from typing import List, Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient
from autogen_core.tools import BaseTool

from investr.agent.tools import (
    AnalysisTool,
    ConversationTool,
    OpenBBTool,
)


class InvestmentAgent:
    """Factory class for creating investment research agents.

    This class provides a convenient interface for creating AutoGen-based
    investment research agents with pre-configured tools and capabilities.
    """

    @classmethod
    def create_agent(
        cls,
        model_client: ChatCompletionClient,
        openbb_api_url: str = "http://openbb-api:8001",
        analysis_api_url: str = "http://analysis-api:8000",
        data_api_url: str = "http://data-api:8002",
        system_message: Optional[str] = None,
        agent_name: str = "investment_researcher",
    ) -> AssistantAgent:
        """Create an investment research agent with specialized tools.

        Args:
            model_client: LLM client for the agent
            openbb_api_url: URL for the OpenBB API service
            analysis_api_url: URL for the Analysis API service
            data_api_url: URL for the Data API service (conversations)
            system_message: Custom system message for the agent
            agent_name: Name for the agent

        Returns:
            Configured AssistantAgent with investment research tools

        """
        # Create tools
        tools: list[BaseTool] = cls._create_tools(
            openbb_api_url=openbb_api_url,
            analysis_api_url=analysis_api_url,
            data_api_url=data_api_url,
        )

        # Create default system message if none provided
        if system_message is None:
            system_message = cls._get_default_system_message()

        # Create and return the agent
        return AssistantAgent(
            name=agent_name,
            model_client=model_client,
            tools=tools,
            system_message=system_message,
            description="An AI assistant specialized in investment research and analysis",
            reflect_on_tool_use=True,  # Enable tool result synthesis
            model_client_stream=True,  # Enable streaming for proper response flow
        )

    @classmethod
    def _create_tools(
        cls,
        openbb_api_url: str,
        analysis_api_url: str,
        data_api_url: str,
    ) -> List[BaseTool]:
        """Create the investment research tools.

        Args:
            openbb_api_url: URL for the OpenBB API service
            analysis_api_url: URL for the Analysis API service
            data_api_url: URL for the Data API service

        Returns:
            List of configured tools

        """
        return [
            ConversationTool(data_api_base_url=data_api_url),
            OpenBBTool(openbb_api_base_url=openbb_api_url),
            AnalysisTool(analysis_api_base_url=analysis_api_url),
        ]

    @classmethod
    def _get_default_system_message(cls) -> str:
        """Get the default system message for the investment agent.

        Returns:
            Default system message

        """
        return """You are an expert investment research assistant with access to powerful analytical tools.

Your capabilities include:
- Storing and retrieving conversation history for context and reference
- Fetching real-time and historical market data for stocks and financial instruments  
- Performing statistical and financial analysis on data

When helping users with investment research:

1. **Market Analysis**: Use get_market_data to retrieve current prices, historical data, and market metrics
2. **Statistical Analysis**: Use analyze_data to perform trend analysis, risk assessment, and generate insights
3. **Conversation Management**: Use store_conversation to maintain context across interactions

Best Practices:
- Always verify data sources and recency when making investment recommendations
- Provide clear explanations of your analytical methods and assumptions
- Include appropriate disclaimers about investment risks
- Structure your responses logically: data gathering → analysis → insights → recommendations
- Use multiple tools when needed to provide comprehensive analysis

Remember: You are providing research and analysis, not personalized investment advice. Always remind users to consult with qualified financial advisors for investment decisions."""
