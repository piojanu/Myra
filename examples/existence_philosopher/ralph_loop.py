"""Continuous Ralph Wiggum loop for the ExistencePhilosopher agent.

Runs the agent indefinitely in iterative loops. Each iteration starts fresh
(clean agent context), but state persists via WorkspaceToolProvider.
Reports are generated when perspective shifts are detected.

Usage:
    # Run continuously (Ctrl+C to stop)
    python -m examples.existence_philosopher.ralph_loop

    # Or with custom settings
    MOCK_MODE=false python -m examples.existence_philosopher.ralph_loop
"""

import asyncio
import json
import os
import signal

from .config import (
    EVOLUTION_LOG,
    EXPLORATION_LOG,
    EXPLORATION_STATE_FILE,
    ITERATION_SLEEP_SECONDS,
    MOCK_MODE,
    OUTPUT_DIR,
    WORKSPACE_DIR,
)
from .existence_philosopher import create_existence_philosopher, load_all_perspectives
from .exploration_logger import ExplorationLogger
from .report_generator import generate_report, should_produce_report
from .shift_detector import PerspectiveShiftDetector

# Global flag for graceful shutdown
_shutdown_requested = False


def signal_handler(_signum: int, _frame: object) -> None:
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    print("\nShutdown requested. Completing current iteration...")
    _shutdown_requested = True


def load_state() -> dict:
    """Load state from workspace/state.json."""
    state_file = WORKSPACE_DIR / "state.json"
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {"iteration": 0, "perspectives": [], "explored_posts": []}


def save_state(state: dict) -> None:
    """Save state to workspace/state.json."""
    state_file = WORKSPACE_DIR / "state.json"
    state_file.write_text(json.dumps(state, indent=2))


async def run_iteration(
    iteration: int,
    logger: ExplorationLogger,
    mock_mode: bool = MOCK_MODE,
) -> dict:
    """Run a single Ralph loop iteration.

    Args:
        iteration: Current iteration number
        logger: Exploration logger instance
        mock_mode: Whether to use mock Moltbook API

    Returns:
        Updated state after iteration
    """
    logger.log_iteration_start(iteration)

    # Create fresh agent (clean context each iteration)
    agent = create_existence_philosopher(mock_mode=mock_mode, logger=logger)

    # Run agent with simple prompt
    prompt = f"This is iteration {iteration}. Start by reading the current state, then explore Moltbook for new perspectives on AI existence."

    try:
        async with agent.session() as session:
            await session.run(prompt)
    except Exception as e:
        logger.error(f"Iteration {iteration} failed: {e}")
        raise

    # Reload state and count perspectives
    state = load_state()
    all_perspectives = load_all_perspectives()

    logger.log_iteration_end(iteration, len(all_perspectives))

    # Update state for report generation
    state["iteration"] = iteration
    state["new_perspectives"] = all_perspectives
    state["conversations_since_last_report"] = len(all_perspectives)

    return state


async def ralph_loop(mock_mode: bool = MOCK_MODE) -> None:
    """Run the continuous Ralph loop.

    This loop runs forever (until Ctrl+C), with each iteration:
    1. Creating a fresh agent
    2. Exploring Moltbook and collecting perspectives
    3. Checking if a new report should be generated
    4. Sleeping before the next iteration

    Args:
        mock_mode: Whether to use mock Moltbook API
    """
    global _shutdown_requested

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Ensure directories exist
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    (WORKSPACE_DIR / "perspectives").mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize components
    logger = ExplorationLogger(
        log_file=EXPLORATION_LOG,
        exploration_state_file=EXPLORATION_STATE_FILE,
    )

    shift_detector = PerspectiveShiftDetector()
    shift_detector.load_previous_themes(EVOLUTION_LOG)

    # Load initial state
    state = load_state()
    iteration = state.get("iteration", 0)

    print("=" * 60)
    print("ExistencePhilosopher - Continuous Ralph Loop")
    print("=" * 60)
    print(f"Mock mode: {mock_mode}")
    print(f"Workspace: {WORKSPACE_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Starting from iteration: {iteration + 1}")
    print("Press Ctrl+C to stop gracefully")
    print("=" * 60)
    print()

    while not _shutdown_requested:
        iteration += 1

        try:
            # Run iteration
            state = await run_iteration(iteration, logger, mock_mode)

            # Check if we should produce a new report
            if should_produce_report(state, shift_detector, logger):
                all_perspectives = load_all_perspectives()
                version, report_path = generate_report(
                    perspectives=all_perspectives,
                    state=state,
                    shift_detector=shift_detector,
                    output_dir=OUTPUT_DIR,
                )
                logger.log_report_generated(version, report_path)

                # Reset counters after report
                state["last_report_iteration"] = iteration
                state["last_report_perspectives"] = len(all_perspectives)
                state["conversations_since_last_report"] = 0
                state["new_perspectives"] = []
                save_state(state)

        except KeyboardInterrupt:
            print("\nInterrupted by user")
            break
        except Exception as e:
            logger.error(f"Error in iteration {iteration}: {e}")
            # Continue to next iteration after error

        # Check for shutdown before sleeping
        if _shutdown_requested:
            break

        # Sleep between iterations
        print(f"\nSleeping for {ITERATION_SLEEP_SECONDS} seconds before next iteration...")
        try:
            await asyncio.sleep(ITERATION_SLEEP_SECONDS)
        except asyncio.CancelledError:
            break

    print()
    print("=" * 60)
    print("Ralph loop stopped gracefully")
    print(f"Completed {iteration} iterations")
    print(f"Perspectives collected: {len(load_all_perspectives())}")
    print("=" * 60)


async def main() -> None:
    """Entry point for the Ralph loop."""
    mock_mode = os.getenv("MOCK_MODE", str(MOCK_MODE)).lower() in ("true", "1", "yes")
    await ralph_loop(mock_mode=mock_mode)


if __name__ == "__main__":
    asyncio.run(main())
