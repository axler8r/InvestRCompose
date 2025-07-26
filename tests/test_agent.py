"""Tests for the investment research agent."""

from unittest.mock import Mock

import pytest

from investr.agent import InvestmentAgent
from investr.agent.models import (
    AnalysisArgs,
    DataSearchArgs,
    MarketDataArgs,
    ReportGenerationArgs,
)
from investr.agent.tools import AnalysisTool, DataTool, OpenBBTool, PrintTool


class TestInvestmentAgent:
    """Test suite for the InvestmentAgent class."""

    def test_create_agent(self):
        """Test that agent creation works with mock model client."""
        # Create a mock model client with required model_info
        mock_client = Mock()
        mock_client.model_info = {"function_calling": True}

        # Create agent
        agent = InvestmentAgent.create_agent(model_client=mock_client)

        # Verify agent was created
        assert agent is not None
        assert agent.name == "investment_researcher"

    def test_create_workbench(self):
        """Test that workbench creation works."""
        # Create workbench
        workbench = InvestmentAgent.create_workbench()

        # Verify workbench was created
        assert workbench is not None

    def test_create_tools(self):
        """Test that tools are created correctly."""
        tools = InvestmentAgent._create_tools(
            data_api_url="http://localhost:8001",
            openbb_api_url="http://localhost:8002",
            print_api_url="http://localhost:8003",
            analysis_api_url="http://localhost:8004",
        )

        # Verify all tools are created
        assert len(tools) == 4

        # Verify tool types
        tool_types = [type(tool) for tool in tools]
        assert DataTool in tool_types
        assert OpenBBTool in tool_types
        assert PrintTool in tool_types
        assert AnalysisTool in tool_types


class TestDataTool:
    """Test suite for the DataTool class."""

    def test_initialization(self):
        """Test DataTool initialization."""
        tool = DataTool()

        assert tool.name == "search_data"
        assert "search" in tool.description.lower()
        assert tool.base_url == "http://data-api:8002"

    @pytest.mark.asyncio
    async def test_run_mock_data(self):
        """Test DataTool run method with mock data."""
        tool = DataTool()

        args = DataSearchArgs(
            query="Apple", collection="default", limit=2, include_metadata=True
        )

        # Mock cancellation token
        cancellation_token = Mock()

        # Run the tool
        result = await tool.run(args, cancellation_token)

        # Verify result structure
        assert result.total_count > 0
        assert len(result.results) <= args.limit
        assert result.query_time_ms >= 0

        # Verify result content
        for res in result.results:
            assert "id" in res
            assert "title" in res
            assert "content" in res

    def test_return_value_as_string(self):
        """Test string representation of DataTool results."""
        tool = DataTool()

        # Create mock result
        from investr.agent.models import DataSearchResult

        result = DataSearchResult(
            results=[
                {
                    "id": "test_1",
                    "title": "Test Document",
                    "content": "Test content",
                    "relevance_score": 0.95,
                }
            ],
            total_count=1,
            query_time_ms=50.0,
        )

        # Convert to string
        result_str = tool.return_value_as_string(result)

        # Verify string contains expected information
        assert "Test Document" in result_str
        assert "0.95" in result_str
        assert "50.0ms" in result_str


class TestOpenBBTool:
    """Test suite for the OpenBBTool class."""

    def test_initialization(self):
        """Test OpenBBTool initialization."""
        tool = OpenBBTool()

        assert tool.name == "get_market_data"
        assert "market data" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_run_mock_data(self):
        """Test OpenBBTool run method with mock data."""
        tool = OpenBBTool()

        args = MarketDataArgs(
            symbol="AAPL", data_type="price", period="1y", interval="1d"
        )

        cancellation_token = Mock()

        # Run the tool
        result = await tool.run(args, cancellation_token)

        # Verify result structure
        assert result.symbol == "AAPL"
        assert len(result.data) > 0
        assert "symbol" in result.metadata
        assert "query_time_ms" in result.metadata


class TestPrintTool:
    """Test suite for the PrintTool class."""

    def test_initialization(self):
        """Test PrintTool initialization."""
        tool = PrintTool()

        assert tool.name == "generate_report"
        assert "report" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_run_mock_data(self):
        """Test PrintTool run method with mock data."""
        tool = PrintTool()

        args = ReportGenerationArgs(
            title="Test Report",
            content="This is test content for the report",
            format="pdf",
            template=None,
        )

        cancellation_token = Mock()

        # Run the tool
        result = await tool.run(args, cancellation_token)

        # Verify result structure
        assert result.format == "pdf"
        assert result.size_bytes > 0
        assert "report_" in result.report_id
        assert result.download_url.startswith("http")


class TestAnalysisTool:
    """Test suite for the AnalysisTool class."""

    def test_initialization(self):
        """Test AnalysisTool initialization."""
        tool = AnalysisTool()

        assert tool.name == "analyze_data"
        assert "analysis" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_run_summary_analysis(self):
        """Test AnalysisTool run method with summary analysis."""
        tool = AnalysisTool()

        args = AnalysisArgs(
            data=[{"price": 100}, {"price": 110}, {"price": 105}],
            analysis_type="summary",
        )

        cancellation_token = Mock()

        # Run the tool
        result = await tool.run(args, cancellation_token)

        # Verify result structure
        assert result.analysis_type == "summary"
        assert len(result.results) > 0
        assert len(result.insights) > 0
        assert result.confidence_score is not None
        assert 0 <= result.confidence_score <= 1


if __name__ == "__main__":
    pytest.main([__file__])
