"""Analysis API tool for investment research agent."""

from typing import Any, Dict, List

from autogen_core import CancellationToken
from autogen_core.tools import BaseTool

from ..models import AnalysisArgs, AnalysisResult


class AnalysisTool(BaseTool[AnalysisArgs, AnalysisResult]):
    """Tool for performing investment analysis via Analysis API.

    This tool provides analytical capabilities for financial data,
    including statistical analysis, trend detection, and insights generation.
    """

    def __init__(self, analysis_api_base_url: str = "http://analysis-api:8000"):
        """Initialize the analysis tool.

        Args:
            analysis_api_base_url: Base URL for the Analysis API service

        """
        super().__init__(
            args_type=AnalysisArgs,
            return_type=AnalysisResult,
            name="analyze_data",
            description=(
                "Perform statistical and financial analysis on investment data. "
                "Supports trend analysis, correlation studies, risk assessment, "
                "and automated insight generation."
            ),
        )
        self.base_url = analysis_api_base_url

    async def run(
        self, args: AnalysisArgs, cancellation_token: CancellationToken
    ) -> AnalysisResult:
        """Perform analysis on the provided data.

        Args:
            args: Analysis parameters including data and analysis type
            cancellation_token: Token for canceling the operation

        Returns:
            Analysis results with insights and metrics

        """
        # TODO: Implement actual HTTP client call to Analysis API
        # For now, return mock data to establish the interface

        # Mock analysis based on analysis type
        mock_results = self._generate_mock_analysis(args)

        # Generate insights based on analysis type
        insights = self._generate_mock_insights(args.analysis_type, mock_results)

        # Calculate confidence score based on data quality and analysis type
        confidence_score = self._calculate_mock_confidence(args)

        return AnalysisResult(
            analysis_type=args.analysis_type,
            results=mock_results,
            insights=insights,
            confidence_score=confidence_score,
        )

    def _generate_mock_analysis(self, args: AnalysisArgs) -> Dict[str, Any]:
        """Generate mock analysis results based on analysis type.

        Args:
            args: Analysis parameters

        Returns:
            Mock analysis results

        """
        if args.analysis_type == "summary":
            return {
                "total_records": 100,
                "mean_value": 125.45,
                "median_value": 123.20,
                "std_deviation": 15.30,
                "min_value": 98.50,
                "max_value": 165.75,
                "trend": "upward",
                "volatility": "moderate",
            }
        elif args.analysis_type == "trend":
            return {
                "trend_direction": "bullish",
                "trend_strength": 0.75,
                "trend_duration_days": 45,
                "support_levels": [120.00, 115.50, 110.25],
                "resistance_levels": [135.00, 140.50, 145.75],
                "momentum_indicators": {
                    "rsi": 65.2,
                    "macd": 2.15,
                    "moving_average_20": 128.30,
                    "moving_average_50": 125.80,
                },
            }
        elif args.analysis_type == "risk":
            return {
                "value_at_risk_95": -8.25,
                "beta": 1.25,
                "sharpe_ratio": 1.45,
                "max_drawdown": -12.5,
                "volatility_annual": 0.18,
                "risk_category": "moderate-high",
                "stress_test_results": {
                    "market_crash_scenario": -25.3,
                    "interest_rate_shock": -8.7,
                    "sector_specific_risk": -15.2,
                },
            }
        else:
            return {
                "analysis_completed": True,
                "data_points_analyzed": 250,
                "processing_time_seconds": 2.34,
                "status": "success",
            }

    def _generate_mock_insights(
        self, analysis_type: str, results: Dict[str, Any]
    ) -> List[str]:
        """Generate mock insights based on analysis results.

        Args:
            analysis_type: Type of analysis performed
            results: Analysis results

        Returns:
            List of insights

        """
        if analysis_type == "summary":
            return [
                "The data shows strong central tendency with moderate volatility",
                "Current values are trending above the historical median",
                "Distribution appears to be normally distributed with slight positive skew",
            ]
        elif analysis_type == "trend":
            return [
                "Strong bullish momentum detected with 75% trend strength",
                "Price is trading above both 20-day and 50-day moving averages",
                "RSI indicates the asset is approaching overbought territory",
                "Multiple support levels provide downside protection",
            ]
        elif analysis_type == "risk":
            return [
                "Moderate-high risk profile with above-average returns potential",
                "Beta of 1.25 indicates higher sensitivity to market movements",
                "Sharpe ratio of 1.45 suggests good risk-adjusted returns",
                "Maximum drawdown of 12.5% is within acceptable risk parameters",
            ]
        else:
            return [
                "Analysis completed successfully with high data quality",
                "No significant anomalies detected in the dataset",
                "Results are suitable for further modeling and decision making",
            ]

    def _calculate_mock_confidence(self, args: AnalysisArgs) -> float:
        """Calculate mock confidence score for analysis.

        Args:
            args: Analysis parameters

        Returns:
            Confidence score between 0 and 1

        """
        # Base confidence on analysis type and data complexity
        base_confidence = 0.85

        if args.analysis_type in ["summary", "trend"]:
            base_confidence = 0.90
        elif args.analysis_type == "risk":
            base_confidence = 0.75

        # Adjust for data quality (mock assessment)
        if isinstance(args.data, list) and len(args.data) > 50:
            base_confidence += 0.05
        elif isinstance(args.data, str) and len(args.data) > 1000:
            base_confidence += 0.03

        return min(base_confidence, 0.95)  # Cap at 95%

    def return_value_as_string(self, value: AnalysisResult) -> str:
        """Convert the analysis result to a string representation.

        Args:
            value: The analysis result to convert

        Returns:
            Human-readable string representation of the analysis results

        """
        result_str = f"Analysis Complete: {value.analysis_type.title()}\n\n"

        # Add confidence score
        if value.confidence_score is not None:
            confidence_pct = value.confidence_score * 100
            result_str += f"Confidence Score: {confidence_pct:.1f}%\n\n"

        # Add key results
        result_str += "Key Results:\n"
        for key, val in value.results.items():
            if isinstance(val, dict):
                result_str += f"  {key.replace('_', ' ').title()}:\n"
                for sub_key, sub_val in val.items():
                    result_str += (
                        f"    - {sub_key.replace('_', ' ').title()}: {sub_val}\n"
                    )
            elif isinstance(val, list):
                result_str += (
                    f"  {key.replace('_', ' ').title()}: {', '.join(map(str, val))}\n"
                )
            else:
                result_str += f"  {key.replace('_', ' ').title()}: {val}\n"

        # Add insights
        if value.insights:
            result_str += "\nKey Insights:\n"
            for i, insight in enumerate(value.insights, 1):
                result_str += f"  {i}. {insight}\n"

        return result_str
