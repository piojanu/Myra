"""Tool providers for the ExistencePhilosopher agent.

This module provides example-specific tool providers:
- MoltbookToolProvider: Tools for interacting with the Moltbook AI social network
- WorkspaceToolProvider: Purpose-built tools for state and perspective management
- FINISH_TOOL: Simple finish tool to signal task completion
"""

from typing import Annotated

from pydantic import BaseModel, Field

from stirrup.core.models import Tool, ToolResult, ToolUseCountMetadata

from .moltbook import MoltbookToolProvider
from .workspace import WorkspaceToolProvider


class FinishParams(BaseModel):
    """Parameters for the finish tool."""

    reason: Annotated[
        str,
        Field(description="Summary of what was accomplished in this iteration."),
    ]


def _finish_executor(params: FinishParams) -> ToolResult[ToolUseCountMetadata]:
    """Simple finish executor that just returns the reason."""
    return ToolResult(content=params.reason, metadata=ToolUseCountMetadata(), success=True)


FINISH_TOOL: Tool[FinishParams, ToolUseCountMetadata] = Tool(
    name="finish",
    description="Signal that the iteration is complete. Call this when you have finished exploring and collecting perspectives.",
    parameters=FinishParams,
    executor=_finish_executor,
)

__all__ = [
    "FINISH_TOOL",
    "MoltbookToolProvider",
    "WorkspaceToolProvider",
]
