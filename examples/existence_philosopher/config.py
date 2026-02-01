"""Configuration for the ExistencePhilosopher agent.

Contains thresholds, limits, API configuration, and paths.
"""

from pathlib import Path

# =============================================================================
# Paths
# =============================================================================

# Base directory for this example
BASE_DIR = Path(__file__).parent

# Workspace directory for state persistence
WORKSPACE_DIR = BASE_DIR / "workspace"

# Full JSONL log of all activity
EXPLORATION_LOG = WORKSPACE_DIR / "exploration.log"

# Exploration state for resuming iterations
EXPLORATION_STATE_FILE = WORKSPACE_DIR / "exploration_state.json"

# Output directory for versioned reports
OUTPUT_DIR = BASE_DIR / "output"

# Evolution log tracking theme changes across versions
EVOLUTION_LOG = OUTPUT_DIR / "evolution_log.json"

# =============================================================================
# LLM Configuration
# =============================================================================

# OpenRouter settings
LLM_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL = "deepseek/deepseek-v3.2"

# Max tokens for responses (output tokens only)
MAX_TOKENS = 64_000

# =============================================================================
# Agent Configuration
# =============================================================================

# Maximum turns per iteration
MAX_TURNS_PER_ITERATION = 50

# Agent name
AGENT_NAME = "existence_philosopher"

# =============================================================================
# Report Generation Thresholds
# =============================================================================

# Guard 1: Minimum engagement before producing a report
MIN_CONVERSATIONS_FOR_REPORT = 20  # Minimum perspectives before producing a report

# Guard 2: Perspective shift detection threshold (0.0 - 1.0)
# Higher values require more significant shifts before triggering a report
SHIFT_DETECTION_THRESHOLD = 0.3

# Minimum perspectives needed for meaningful shift detection
MIN_PERSPECTIVES_FOR_SHIFT_DETECTION = 5

# =============================================================================
# Ralph Loop Configuration
# =============================================================================

# Sleep time between iterations (seconds)
ITERATION_SLEEP_SECONDS = 600

# Whether to run in mock mode (for development/testing)
MOCK_MODE = True
