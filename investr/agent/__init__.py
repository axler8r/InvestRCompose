"""Investment research agent package.

This package provides an AutoGen-based agent for investment research,
including tools for data retrieval, analysis, and report generation.
"""

from investr.agent.agent import InvestmentAgent
from investr.agent.models import AgentRequest, AgentResponse, TaskContext

__all__: list[str] = [
    "InvestmentAgent",
    "AgentRequest",
    "AgentResponse",
    "TaskContext",
]
