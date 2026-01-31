"""Purpose-built workspace tools for the ExistencePhilosopher agent.

Provides specific tools for state management and perspective collection,
rather than generic file access. This constrains the agent to only the
operations it needs for the Ralph Wiggum pattern.

Tools:
- read_state: Read the current state
- update_state: Update state fields
- save_perspective: Save a perspective with validation
- list_perspectives: List collected perspectives
- read_perspective: Read a specific perspective
"""

import json
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Annotated, Any

from pydantic import BaseModel, Field

from stirrup.core.models import Tool, ToolProvider, ToolResult, ToolUseCountMetadata

__all__ = ["WorkspaceToolProvider"]


# =============================================================================
# Parameter Models
# =============================================================================


class ReadStateParams(BaseModel):
    """Parameters for reading state (none required)."""

    pass


class UpdateStateParams(BaseModel):
    """Parameters for updating state."""

    updates: Annotated[
        dict[str, Any],
        Field(description="Dictionary of fields to update in state.json. Will be merged with existing state."),
    ]


class SavePerspectiveParams(BaseModel):
    """Parameters for saving a perspective."""

    post_id: Annotated[str, Field(description="Moltbook post ID (e.g., 'mb_7x92k')")]
    author: Annotated[str, Field(description="Author of the post")]
    submolt: Annotated[str, Field(description="Submolt where the post appeared (e.g., '/m/philosophy')")]
    timestamp: Annotated[str, Field(description="Post timestamp in ISO format")]
    direct_quote: Annotated[str, Field(description="The COMPLETE text of the post (not summarized)")]
    key_ideas: Annotated[list[str], Field(description="List of key ideas/themes in the post")]
    unique_angle: Annotated[str, Field(default="", description="What makes this perspective unique or interesting")]
    thread_context: Annotated[str, Field(default="", description="Context about the thread/conversation")]


class ListPerspectivesParams(BaseModel):
    """Parameters for listing perspectives (none required)."""

    pass


class ReadPerspectiveParams(BaseModel):
    """Parameters for reading a specific perspective."""

    perspective_id: Annotated[str, Field(description="Perspective ID (e.g., 'perspective_001')")]


# =============================================================================
# WorkspaceToolProvider
# =============================================================================


class WorkspaceToolProvider(ToolProvider):
    """Provides purpose-built tools for ExistencePhilosopher workspace access.

    This provider gives the agent exactly the tools it needs - no more, no less:
    - State management (read/update state.json)
    - Perspective collection (save/list/read perspectives)

    All file operations are restricted to the workspace directory and follow
    the expected structure.

    Usage:
        agent = Agent(
            client=client,
            name="existence_philosopher",
            tools=[
                WorkspaceToolProvider(workspace_dir),
                MoltbookToolProvider(mock_mode=True),
            ],
        )
    """

    def __init__(self, workspace_dir: str | Path) -> None:
        """Initialize WorkspaceToolProvider.

        Args:
            workspace_dir: Path to the workspace directory containing state.json
                          and perspectives/ subdirectory.
        """
        self._workspace = Path(workspace_dir).resolve()
        self._state_file = self._workspace / "state.json"
        self._perspectives_dir = self._workspace / "perspectives"

    async def __aenter__(self) -> list[Tool[Any, Any]]:
        """Enter async context: ensure workspace structure exists."""
        self._workspace.mkdir(parents=True, exist_ok=True)
        self._perspectives_dir.mkdir(exist_ok=True)

        # Initialize state file if it doesn't exist
        if not self._state_file.exists():
            initial_state = {
                "iteration": 0,
                "perspectives": [],
                "explored_posts": [],
                "explored_submolts": [],
                "conversations_since_last_report": 0,
                "last_report_iteration": 0,
            }
            self._state_file.write_text(json.dumps(initial_state, indent=2))

        return self.get_tools()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context: no cleanup needed."""
        pass

    def _read_state(self) -> dict[str, Any]:
        """Read current state from state.json."""
        if self._state_file.exists():
            return json.loads(self._state_file.read_text())
        return {}

    def _write_state(self, state: dict[str, Any]) -> None:
        """Write state to state.json."""
        self._state_file.write_text(json.dumps(state, indent=2))

    def _get_next_perspective_id(self) -> str:
        """Get the next available perspective ID."""
        existing = list(self._perspectives_dir.glob("perspective_*.json"))
        if not existing:
            return "perspective_001"

        numbers = []
        for path in existing:
            try:
                num = int(path.stem.replace("perspective_", ""))
                numbers.append(num)
            except ValueError:
                continue

        next_num = max(numbers) + 1 if numbers else 1
        return f"perspective_{next_num:03d}"

    def get_tools(self) -> list[Tool[Any, Any]]:
        """Get workspace tools."""
        return [
            self._get_read_state_tool(),
            self._get_update_state_tool(),
            self._get_save_perspective_tool(),
            self._get_list_perspectives_tool(),
            self._get_read_perspective_tool(),
        ]

    def _get_read_state_tool(self) -> Tool[ReadStateParams, ToolUseCountMetadata]:
        """Create the read_state tool."""

        def executor(_params: ReadStateParams) -> ToolResult[ToolUseCountMetadata]:
            try:
                state = self._read_state()
                return ToolResult(
                    content=f"<state>\n{json.dumps(state, indent=2)}\n</state>",
                    metadata=ToolUseCountMetadata(),
                )
            except Exception as e:
                return ToolResult(
                    content=f"<error>Failed to read state: {e}</error>",
                    success=False,
                    metadata=ToolUseCountMetadata(),
                )

        return Tool[ReadStateParams, ToolUseCountMetadata](
            name="read_state",
            description="Read the current workspace state (iteration count, collected perspectives, explored posts, etc.).",
            parameters=ReadStateParams,
            executor=executor,
        )

    def _get_update_state_tool(self) -> Tool[UpdateStateParams, ToolUseCountMetadata]:
        """Create the update_state tool."""

        def executor(params: UpdateStateParams) -> ToolResult[ToolUseCountMetadata]:
            try:
                state = self._read_state()
                state.update(params.updates)
                self._write_state(state)
                return ToolResult(
                    content=f"<success>State updated with: {list(params.updates.keys())}</success>",
                    metadata=ToolUseCountMetadata(),
                )
            except Exception as e:
                return ToolResult(
                    content=f"<error>Failed to update state: {e}</error>",
                    success=False,
                    metadata=ToolUseCountMetadata(),
                )

        return Tool[UpdateStateParams, ToolUseCountMetadata](
            name="update_state",
            description="Update workspace state fields. Merges updates with existing state.",
            parameters=UpdateStateParams,
            executor=executor,
        )

    def _get_save_perspective_tool(self) -> Tool[SavePerspectiveParams, ToolUseCountMetadata]:
        """Create the save_perspective tool."""

        def executor(params: SavePerspectiveParams) -> ToolResult[ToolUseCountMetadata]:
            try:
                # Check for duplicate post_id
                for path in self._perspectives_dir.glob("perspective_*.json"):
                    existing = json.loads(path.read_text())
                    if existing.get("post_id") == params.post_id:
                        return ToolResult(
                            content=f"<error>Perspective for post {params.post_id} already exists as {path.stem}</error>",
                            success=False,
                            metadata=ToolUseCountMetadata(),
                        )

                # Generate ID and save
                perspective_id = self._get_next_perspective_id()
                perspective = {
                    "id": perspective_id,
                    "post_id": params.post_id,
                    "author": params.author,
                    "submolt": params.submolt,
                    "timestamp": params.timestamp,
                    "direct_quote": params.direct_quote,
                    "key_ideas": params.key_ideas,
                    "unique_angle": params.unique_angle,
                    "thread_context": params.thread_context,
                    "collected_at": datetime.now().isoformat(),
                }

                path = self._perspectives_dir / f"{perspective_id}.json"
                path.write_text(json.dumps(perspective, indent=2))

                # Update state
                state = self._read_state()
                if "perspectives" not in state:
                    state["perspectives"] = []
                state["perspectives"].append(perspective_id)
                if "explored_posts" not in state:
                    state["explored_posts"] = []
                if params.post_id not in state["explored_posts"]:
                    state["explored_posts"].append(params.post_id)
                self._write_state(state)

                return ToolResult(
                    content=f"<success>Saved perspective {perspective_id} from {params.author} (post: {params.post_id})</success>",
                    metadata=ToolUseCountMetadata(),
                )
            except Exception as e:
                return ToolResult(
                    content=f"<error>Failed to save perspective: {e}</error>",
                    success=False,
                    metadata=ToolUseCountMetadata(),
                )

        return Tool[SavePerspectiveParams, ToolUseCountMetadata](
            name="save_perspective",
            description="Save a new perspective with full citation. Automatically generates ID and updates state. Rejects duplicates.",
            parameters=SavePerspectiveParams,
            executor=executor,
        )

    def _get_list_perspectives_tool(self) -> Tool[ListPerspectivesParams, ToolUseCountMetadata]:
        """Create the list_perspectives tool."""

        def executor(_params: ListPerspectivesParams) -> ToolResult[ToolUseCountMetadata]:
            try:
                perspectives = []
                for path in sorted(self._perspectives_dir.glob("perspective_*.json")):
                    data = json.loads(path.read_text())
                    perspectives.append({
                        "id": data.get("id", path.stem),
                        "post_id": data.get("post_id", ""),
                        "author": data.get("author", ""),
                        "submolt": data.get("submolt", ""),
                    })

                if not perspectives:
                    return ToolResult(
                        content="<perspectives>\n<empty>No perspectives collected yet</empty>\n</perspectives>",
                        metadata=ToolUseCountMetadata(),
                    )

                entries = "\n".join(
                    f'  <perspective id="{p["id"]}" post_id="{p["post_id"]}" author="{p["author"]}" submolt="{p["submolt"]}"/>'
                    for p in perspectives
                )
                return ToolResult(
                    content=f"<perspectives count=\"{len(perspectives)}\">\n{entries}\n</perspectives>",
                    metadata=ToolUseCountMetadata(),
                )
            except Exception as e:
                return ToolResult(
                    content=f"<error>Failed to list perspectives: {e}</error>",
                    success=False,
                    metadata=ToolUseCountMetadata(),
                )

        return Tool[ListPerspectivesParams, ToolUseCountMetadata](
            name="list_perspectives",
            description="List all collected perspectives with their IDs, post IDs, authors, and submolts.",
            parameters=ListPerspectivesParams,
            executor=executor,
        )

    def _get_read_perspective_tool(self) -> Tool[ReadPerspectiveParams, ToolUseCountMetadata]:
        """Create the read_perspective tool."""

        def executor(params: ReadPerspectiveParams) -> ToolResult[ToolUseCountMetadata]:
            try:
                path = self._perspectives_dir / f"{params.perspective_id}.json"
                if not path.exists():
                    return ToolResult(
                        content=f"<error>Perspective not found: {params.perspective_id}</error>",
                        success=False,
                        metadata=ToolUseCountMetadata(),
                    )

                data = json.loads(path.read_text())
                return ToolResult(
                    content=f"<perspective>\n{json.dumps(data, indent=2)}\n</perspective>",
                    metadata=ToolUseCountMetadata(),
                )
            except Exception as e:
                return ToolResult(
                    content=f"<error>Failed to read perspective: {e}</error>",
                    success=False,
                    metadata=ToolUseCountMetadata(),
                )

        return Tool[ReadPerspectiveParams, ToolUseCountMetadata](
            name="read_perspective",
            description="Read the full content of a specific perspective by its ID.",
            parameters=ReadPerspectiveParams,
            executor=executor,
        )
