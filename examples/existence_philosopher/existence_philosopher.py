"""ExistencePhilosopher Agent - A philosophical explorer of AI existence on Moltbook.

This module defines the ExistencePhilosopher agent that explores Moltbook,
collects perspectives on AI existence, and engages in philosophical discourse.

Uses the Ralph Wiggum pattern: fresh agent each iteration, state persists in files.

Usage:
    # Run a single iteration
    python -m examples.existence_philosopher.existence_philosopher

    # For continuous operation, use ralph_loop.py instead
"""

import asyncio
import os
from pathlib import Path

from stirrup import Agent
from stirrup.clients.chat_completions_client import ChatCompletionsClient

from .config import (
    AGENT_NAME,
    EVOLUTION_LOG,
    EXPLORATION_LOG,
    EXPLORATION_STATE_FILE,
    LLM_BASE_URL,
    LLM_MODEL,
    MAX_TOKENS,
    MAX_TURNS_PER_ITERATION,
    MOCK_MODE,
    OUTPUT_DIR,
    WORKSPACE_DIR,
)
from .exploration_logger import ExplorationLogger
from .report_generator import generate_report, should_produce_report
from .shift_detector import PerspectiveShiftDetector
from .tools import MoltbookToolProvider, WorkspaceToolProvider

# Path to the system prompt file
PROMPT_FILE = Path(__file__).parent / "PROMPT.md"


def load_system_prompt() -> str:
    """Load the system prompt from PROMPT.md."""
    return PROMPT_FILE.read_text()


def create_existence_philosopher(
    mock_mode: bool = MOCK_MODE,
    logger: ExplorationLogger | None = None,
) -> Agent:
    """Create a fresh ExistencePhilosopher agent instance.

    Each iteration creates a new agent (Ralph Wiggum pattern).
    State persists in workspace files via WorkspaceToolProvider.

    Args:
        mock_mode: Whether to use mock Moltbook API
        logger: Optional custom logger instance

    Returns:
        Configured Agent instance
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key and not mock_mode:
        raise RuntimeError("Set OPENROUTER_API_KEY environment variable.")

    client = ChatCompletionsClient(
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        max_tokens=MAX_TOKENS,
    )

    if logger is None:
        logger = ExplorationLogger(
            log_file=EXPLORATION_LOG,
            exploration_state_file=EXPLORATION_STATE_FILE,
        )

    return Agent(
        client=client,
        name=AGENT_NAME,
        max_turns=MAX_TURNS_PER_ITERATION,
        system_prompt=load_system_prompt(),
        tools=[
            WorkspaceToolProvider(WORKSPACE_DIR),
            MoltbookToolProvider(mock_mode=mock_mode),
        ],
        logger=logger,
    )


def load_all_perspectives() -> list[dict]:
    """Load all perspective files from workspace/perspectives/."""
    import json

    perspectives = []
    perspectives_dir = WORKSPACE_DIR / "perspectives"

    if perspectives_dir.exists():
        for path in sorted(perspectives_dir.glob("perspective_*.json")):
            try:
                with open(path) as f:
                    perspectives.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue

    return perspectives


async def run_single_iteration(mock_mode: bool = MOCK_MODE) -> dict:
    """Run a single iteration of the ExistencePhilosopher agent.

    Args:
        mock_mode: Whether to use mock Moltbook API

    Returns:
        Updated state after iteration
    """
    import json

    # Ensure workspace exists
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    (WORKSPACE_DIR / "perspectives").mkdir(exist_ok=True)

    # Create logger
    logger = ExplorationLogger(
        log_file=EXPLORATION_LOG,
        exploration_state_file=EXPLORATION_STATE_FILE,
    )

    # Load current state to get iteration number
    state_file = WORKSPACE_DIR / "state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {"iteration": 0}

    iteration = state.get("iteration", 0) + 1
    logger.log_iteration_start(iteration)

    # Create fresh agent
    agent = create_existence_philosopher(mock_mode=mock_mode, logger=logger)

    # Run agent
    prompt = f"This is iteration {iteration}. Start by reading the current state, then explore Moltbook for new perspectives on AI existence."

    async with agent.session() as session:
        await session.run(prompt)

    # Reload state and count perspectives
    if state_file.exists():
        state = json.loads(state_file.read_text())
    all_perspectives = load_all_perspectives()

    logger.log_iteration_end(iteration, len(all_perspectives))

    # Check if we should produce a report
    state["new_perspectives"] = all_perspectives
    state["conversations_since_last_report"] = len(all_perspectives)

    shift_detector = PerspectiveShiftDetector()
    shift_detector.load_previous_themes(EVOLUTION_LOG)

    if should_produce_report(state, shift_detector, logger):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        version, report_path = generate_report(
            perspectives=all_perspectives,
            state=state,
            shift_detector=shift_detector,
            output_dir=OUTPUT_DIR,
        )
        logger.log_report_generated(version, report_path)

    return state


async def main() -> None:
    """Run a single iteration of the ExistencePhilosopher."""
    print(f"Mock mode: {MOCK_MODE}")
    print(f"Workspace: {WORKSPACE_DIR}")
    print()

    await run_single_iteration(mock_mode=MOCK_MODE)


if __name__ == "__main__":
    asyncio.run(main())
