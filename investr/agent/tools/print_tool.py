"""Print API tool for investment research agent."""

import time

from autogen_core import CancellationToken
from autogen_core.tools import BaseTool

from ..models import ReportGenerationArgs, ReportGenerationResult


class PrintTool(BaseTool[ReportGenerationArgs, ReportGenerationResult]):
    """Tool for generating reports via Print API.

    This tool provides document generation capabilities for creating
    professional investment reports in various formats.
    """

    def __init__(self, print_api_base_url: str = "http://print-api:8000"):
        """Initialize the print tool.

        Args:
            print_api_base_url: Base URL for the Print API service

        """
        super().__init__(
            args_type=ReportGenerationArgs,
            return_type=ReportGenerationResult,
            name="generate_report",
            description=(
                "Generate professional investment reports in PDF, HTML, or Markdown format. "
                "Supports custom templates and styling for professional document output."
            ),
        )
        self.base_url = print_api_base_url

    async def run(
        self, args: ReportGenerationArgs, cancellation_token: CancellationToken
    ) -> ReportGenerationResult:
        """Generate a report from the provided content.

        Args:
            args: Report generation parameters including content and format
            cancellation_token: Token for canceling the operation

        Returns:
            Report generation result with download information

        """
        # TODO: Implement actual HTTP client call to Print API
        # For now, return mock data to establish the interface

        # Generate a mock report ID based on timestamp
        timestamp = int(time.time() * 1000)
        report_id = f"report_{timestamp}"

        # Mock file size calculation (rough estimate based on content length)
        estimated_size = len(args.content) * 2  # Rough multiplier for formatting
        if args.format.lower() == "pdf":
            estimated_size = int(estimated_size * 1.5)  # PDFs tend to be larger

        mock_download_url = f"{self.base_url}/reports/{report_id}/download"

        return ReportGenerationResult(
            report_id=report_id,
            download_url=mock_download_url,
            format=args.format,
            size_bytes=estimated_size,
        )

    def return_value_as_string(self, value: ReportGenerationResult) -> str:
        """Convert the report generation result to a string representation.

        Args:
            value: The report generation result to convert

        Returns:
            Human-readable string representation of the report generation result

        """
        size_mb = value.size_bytes / (1024 * 1024)

        result_str = "Report generated successfully!\n\n"
        result_str += "Report Details:\n"
        result_str += f"  Report ID: {value.report_id}\n"
        result_str += f"  Format: {value.format.upper()}\n"
        result_str += f"  File Size: {size_mb:.2f} MB ({value.size_bytes:,} bytes)\n"
        result_str += f"  Download URL: {value.download_url}\n\n"
        result_str += (
            "The report is ready for download and can be accessed via the provided URL."
        )

        return result_str
