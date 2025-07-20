"""Investment research agent package.

This package provides an AutoGen-based agent for investment research,
including tools for data retrieval, analysis, and report generation.
"""

from .agent import InvestmentAgent
from .models import AgentRequest, AgentResponse, TaskContext

__all__ = [
    "InvestmentAgent",
    "AgentRequest",
    "AgentResponse",
    "TaskContext",
]
