"""Tool providers for the ExistencePhilosopher agent.

This module provides example-specific tool providers:
- MoltbookToolProvider: Tools for interacting with the Moltbook AI social network
- WorkspaceToolProvider: Purpose-built tools for state and perspective management
"""

from .moltbook import MoltbookToolProvider
from .workspace import WorkspaceToolProvider

__all__ = [
    "MoltbookToolProvider",
    "WorkspaceToolProvider",
]
