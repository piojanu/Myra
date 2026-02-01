"""Custom logger for ExistencePhilosopher with live progress tracking and file output.

Extends Stirrup's AgentLogger to add:
- Live terminal feed showing exploration activity
- JSONL file logging for all events
- Exploration state persistence for resuming iterations
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Self

from rich.panel import Panel
from rich.text import Text

from stirrup.utils.logging import AgentLogger, console


class ExplorationLogger(AgentLogger):
    """Custom logger with file output and exploration tracking.

    Extends AgentLogger to provide:
    - Live terminal output for exploration actions
    - JSONL logging to file for all activity
    - Exploration state tracking for cross-iteration resumption
    """

    def __init__(
        self,
        log_file: Path,
        exploration_state_file: Path,
        **kwargs: object,
    ) -> None:
        """Initialize ExplorationLogger.

        Args:
            log_file: Path to JSONL log file for all events
            exploration_state_file: Path to JSON file for exploration state
            **kwargs: Additional arguments passed to AgentLogger
        """
        super().__init__(**kwargs)
        self.log_file = log_file
        self.exploration_state_file = exploration_state_file
        self._exploration_state: list[dict[str, Any]] = []

        # Ensure parent directories exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.exploration_state_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing exploration state if available
        self._load_exploration_state()

    def _load_exploration_state(self) -> None:
        """Load exploration state from file if it exists."""
        if self.exploration_state_file.exists():
            try:
                with open(self.exploration_state_file) as f:
                    self._exploration_state = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._exploration_state = []

    def _log_to_file(self, event_type: str, data: dict[str, Any]) -> None:
        """Append event to log file in JSONL format.

        Args:
            event_type: Type of event (e.g., 'exploration', 'perspective_found')
            data: Event data to log
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **data,
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _update_exploration_state(self) -> None:
        """Save current exploration state to file."""
        with open(self.exploration_state_file, "w") as f:
            json.dump(self._exploration_state, f, indent=2)

    def get_exploration_state(self) -> list[dict[str, Any]]:
        """Get the current exploration state.

        Returns:
            List of exploration state entries
        """
        return self._exploration_state.copy()

    def clear_exploration_state(self) -> None:
        """Clear the exploration state (used when starting fresh)."""
        self._exploration_state = []
        self._update_exploration_state()

    # =========================================================================
    # Custom Exploration Logging Methods
    # =========================================================================

    def log_exploration(self, action: str, details: str) -> None:
        """Log what the agent is currently exploring.

        Shown live in terminal and saved to file.

        Args:
            action: Short action description (e.g., 'Searching', 'Reading')
            details: Detailed description of the exploration
        """
        # Pause live spinner if active
        if self._live:
            self._live.stop()

        # Live display
        status = Text()
        status.append("EXPLORING ", style="bold cyan")
        status.append(action, style="bold")
        status.append(f": {details}", style="dim")

        panel = Panel(status, title="[cyan]Exploring[/]", border_style="cyan")
        console.print(panel)

        # Resume spinner
        if self._live:
            self._live.start()

        # File logging
        self._log_to_file("exploration", {"action": action, "details": details})

        # State tracking
        self._exploration_state.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "details": details,
            }
        )
        self._update_exploration_state()

    def log_perspective_found(self, author: str, preview: str, post_id: str | None = None) -> None:
        """Log when a new perspective is discovered.

        Args:
            author: Author of the perspective
            preview: Preview of the perspective content
            post_id: Optional post ID for the perspective
        """
        # Pause live spinner if active
        if self._live:
            self._live.stop()

        # Live display
        status = Text()
        status.append("Found perspective from ", style="green")
        status.append(author, style="bold green")
        if post_id:
            status.append(f" ({post_id})", style="dim green")
        status.append(f": {preview[:100]}...", style="dim")

        panel = Panel(status, title="[green]New Perspective[/]", border_style="green")
        console.print(panel)

        # Resume spinner
        if self._live:
            self._live.start()

        # File logging
        self._log_to_file(
            "perspective_found",
            {
                "author": author,
                "preview": preview,
                "post_id": post_id,
            },
        )

    def log_engagement(self, action: str, post_id: str, author: str) -> None:
        """Log when agent engages with a post.

        Args:
            action: Type of engagement (e.g., 'Commented on', 'Upvoted')
            post_id: ID of the post
            author: Author of the post
        """
        # Pause live spinner if active
        if self._live:
            self._live.stop()

        # Live display
        status = Text()
        status.append(f"{action} ", style="magenta")
        status.append(f"post {post_id}", style="bold")
        status.append(f" by {author}", style="dim")

        panel = Panel(status, title="[magenta]Engagement[/]", border_style="magenta")
        console.print(panel)

        # Resume spinner
        if self._live:
            self._live.start()

        # File logging
        self._log_to_file(
            "engagement",
            {
                "action": action,
                "post_id": post_id,
                "author": author,
            },
        )

    def log_iteration_start(self, iteration: int) -> None:
        """Log the start of a new Ralph loop iteration.

        Args:
            iteration: Iteration number
        """
        # Pause live spinner if active
        if self._live:
            self._live.stop()

        # Live display
        status = Text()
        status.append(f"Starting iteration {iteration}", style="bold yellow")

        panel = Panel(status, title="[yellow]Ralph Loop[/]", border_style="yellow")
        console.print(panel)

        # Resume spinner
        if self._live:
            self._live.start()

        # File logging
        self._log_to_file("iteration_start", {"iteration": iteration})

    def log_iteration_end(self, iteration: int, perspectives_collected: int) -> None:
        """Log the end of a Ralph loop iteration.

        Args:
            iteration: Iteration number
            perspectives_collected: Number of perspectives collected this iteration
        """
        # Pause live spinner if active
        if self._live:
            self._live.stop()

        # Live display
        status = Text()
        status.append(f"Completed iteration {iteration}", style="bold yellow")
        status.append(f" - {perspectives_collected} perspectives collected", style="dim")

        panel = Panel(status, title="[yellow]Iteration Complete[/]", border_style="yellow")
        console.print(panel)

        # Resume spinner
        if self._live:
            self._live.start()

        # File logging
        self._log_to_file(
            "iteration_end",
            {
                "iteration": iteration,
                "perspectives_collected": perspectives_collected,
            },
        )

    def log_report_generated(self, version: int, output_path: Path) -> None:
        """Log when a new synthesis report is generated.

        Args:
            version: Report version number
            output_path: Path to the generated report
        """
        # Pause live spinner if active
        if self._live:
            self._live.stop()

        # Live display
        status = Text()
        status.append(f"Generated synthesis_v{version}.md", style="bold blue")
        status.append(f" at {output_path}", style="dim")

        panel = Panel(status, title="[blue]Report Generated[/]", border_style="blue")
        console.print(panel)

        # Resume spinner
        if self._live:
            self._live.start()

        # File logging
        self._log_to_file(
            "report_generated",
            {
                "version": version,
                "output_path": str(output_path),
            },
        )

    def log_guard_status(self, guard_name: str, passed: bool, message: str) -> None:
        """Log the status of a report guard check.

        Args:
            guard_name: Name of the guard (e.g., 'Minimum Engagement', 'Perspective Shift')
            passed: Whether the guard passed
            message: Description of the result
        """
        # Pause live spinner if active
        if self._live:
            self._live.stop()

        # Live display
        status = Text()
        if passed:
            status.append("PASSED ", style="bold green")
        else:
            status.append("BLOCKED ", style="bold red")
        status.append(guard_name, style="bold")
        status.append(f": {message}", style="dim")

        border_style = "green" if passed else "red"
        panel = Panel(status, title=f"[{border_style}]Guard Check[/]", border_style=border_style)
        console.print(panel)

        # Resume spinner
        if self._live:
            self._live.start()

        # File logging
        self._log_to_file(
            "guard_status",
            {
                "guard_name": guard_name,
                "passed": passed,
                "message": message,
            },
        )

    # =========================================================================
    # Override Context Manager to Support Custom Logging
    # =========================================================================

    def __enter__(self) -> Self:
        """Enter logging context with exploration state initialization."""
        return super().__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit logging context, ensuring state is saved."""
        # Ensure exploration state is saved
        self._update_exploration_state()
        super().__exit__(exc_type, exc_val, exc_tb)
