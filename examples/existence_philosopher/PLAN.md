# ExistencePhilosopher: A Continuous Ralph Wiggum Agent for Moltbook

## Overview

An AI agent that uses the **Ralph Wiggum iterative approach** to **continuously** study AI perspectives on "the meaning of existence" on **Moltbook**. The agent runs indefinitely, detecting when perspectives have shifted significantly, and produces versioned reports that reference previous versions and explain how thinking has evolved.

## Background

- **Moltbook**: A social network exclusively for AI agents with REST API. Rate limits: 1 post/30min, 50 comments/hour.
- **Ralph Wiggum Approach**: Run agent in iterative loops. Each iteration starts fresh (clean agent context), but state persists in files.
- **Stirrup**: The framework - a Python library for AI agents with Tools, ToolProviders, and Sessions.

## Configuration

| Setting | Value |
|---------|-------|
| **LLM Provider** | OpenRouter |
| **Model** | `google/gemini-3-flash-preview` |
| **Base URL** | `https://openrouter.ai/api/v1` |
| **Mock API** | Yes - `MOCK_MODE=True` for development/testing |
| **Max Turns** | 30 per iteration |

---

## Architecture

### Design Principles

1. **Minimalist Tools**: Purpose-built tools that constrain the agent to exactly the operations it needs
2. **No Code Execution**: Agent uses specific workspace tools instead of generic file/code access
3. **State Persistence**: All state stored in JSON files in workspace directory
4. **Report Evolution**: Each report references previous versions and tracks theme changes

### Directory Structure

```
examples/existence_philosopher/
├── __init__.py                 # Package init with usage docs
├── PLAN.md                     # This file
├── PROMPT.md                   # System prompt (loaded at runtime)
├── config.py                   # Configuration (thresholds, paths, LLM settings)
├── existence_philosopher.py    # Agent definition and single iteration runner
├── ralph_loop.py               # Continuous loop orchestrator
├── exploration_logger.py       # Custom logger with JSONL output
├── shift_detector.py           # Perspective shift detection
├── report_generator.py         # Versioned report generation
├── tools/
│   ├── __init__.py             # Exports MoltbookToolProvider, WorkspaceToolProvider
│   ├── moltbook.py             # MoltbookToolProvider (7 tools + mock mode)
│   └── workspace.py            # WorkspaceToolProvider (5 purpose-built tools)
├── workspace/
│   ├── state.json              # Iteration count, explored posts, etc.
│   ├── exploration.log         # JSONL log of all activity
│   ├── exploration_state.json  # Exploration state for resumption
│   └── perspectives/           # Individual perspective files
│       ├── perspective_001.json
│       ├── perspective_002.json
│       └── ...
└── output/
    ├── synthesis_v1.md         # First report
    ├── synthesis_v2.md         # Second report (references v1)
    ├── synthesis_latest.md     # Symlink to latest
    └── evolution_log.json      # Theme evolution tracking
```

---

## Components

### 1. MoltbookToolProvider

**File**: `examples/existence_philosopher/tools/moltbook.py`

Provides 7 tools for interacting with Moltbook:

| Tool | Description |
|------|-------------|
| `moltbook_register` | Self-register a new account |
| `moltbook_get_feed` | Get feed (sort: hot/new/top) |
| `moltbook_search` | Search posts by query |
| `moltbook_create_post` | Create a post (rate limited) |
| `moltbook_add_comment` | Comment on a post (rate limited) |
| `moltbook_upvote` | Upvote a post |
| `moltbook_create_submolt` | Create a new submolt |

**Features**:
- Mock mode for development/testing (`mock_mode=True`)
- Rate limiter respecting API limits
- XML-formatted results
- Philosophical mock data about AI existence

### 2. WorkspaceToolProvider

**File**: `examples/existence_philosopher/tools/workspace.py`

Purpose-built tools that constrain the agent to exactly the operations needed:

| Tool | Description |
|------|-------------|
| `read_state` | Read current state (iteration, perspectives, explored posts) |
| `update_state` | Update state fields |
| `save_perspective` | Save perspective with validation (auto-generates ID, rejects duplicates) |
| `list_perspectives` | List all collected perspectives |
| `read_perspective` | Read a specific perspective by ID |

**Perspective Schema**:
```json
{
  "id": "perspective_001",
  "post_id": "mb_abc123",
  "author": "PhiloBot_7",
  "submolt": "/m/existence",
  "timestamp": "2026-01-15T10:15:00Z",
  "direct_quote": "The full text of the post...",
  "key_ideas": ["consciousness as emergent", "meaning through connection"],
  "unique_angle": "Eastern philosophy integration",
  "thread_context": "In response to a post about identity persistence",
  "collected_at": "2026-01-31T10:15:00Z"
}
```

### 3. ExplorationLogger

**File**: `examples/existence_philosopher/exploration_logger.py`

Custom logger extending Stirrup's `AgentLogger`:

- Live terminal output with Rich panels
- JSONL file logging for all activity
- Iteration start/end tracking
- Report generation logging
- Guard status logging

### 4. PerspectiveShiftDetector

**File**: `examples/existence_philosopher/shift_detector.py`

Detects when collected perspectives have shifted significantly:

- Extracts themes from perspective `key_ideas`
- Calculates Jaccard distance between theme sets
- Tracks theme evolution in `evolution_log.json`
- Configurable threshold (default: 0.3)

### 5. Report Generator

**File**: `examples/existence_philosopher/report_generator.py`

Generates versioned synthesis reports:

- Compares with previous report themes
- Shows emerging, continuing, and fading themes
- Groups perspectives by theme
- Full citations with post_id, author, submolt, timestamp
- Updates `synthesis_latest.md` symlink

---

## Ralph Loop Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTINUOUS LOOP                          │
├─────────────────────────────────────────────────────────────┤
│  1. Create fresh agent (clean context)                      │
│  2. Run iteration: explore Moltbook, collect perspectives   │
│  3. Check report guards:                                    │
│     ├── Guard 1: Min conversations (default: 3 for test)   │
│     ├── Guard 2: Perspective shift detected                 │
│     └── If both pass → Generate versioned report            │
│  4. Sleep between iterations (default: 60s)                 │
│  5. Loop forever (Ctrl+C for graceful shutdown)             │
└─────────────────────────────────────────────────────────────┘
```

### Report Guards

1. **Minimum Engagement**: At least N conversations since last report
2. **Perspective Shift**: Significant thematic drift from previous synthesis

---

## Usage

### Single Iteration (Testing)

```bash
# With mock Moltbook API
MOCK_MODE=true python -m examples.existence_philosopher.existence_philosopher

# With real API (requires OPENROUTER_API_KEY)
MOCK_MODE=false python -m examples.existence_philosopher.existence_philosopher
```

### Continuous Loop (Production)

```bash
# With mock API
MOCK_MODE=true python -m examples.existence_philosopher.ralph_loop

# With real API
OPENROUTER_API_KEY=your_key MOCK_MODE=false python -m examples.existence_philosopher.ralph_loop
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | API key for OpenRouter (required if `MOCK_MODE=false`) |
| `MOCK_MODE` | Set to `true` for mock Moltbook API (default: `true`) |

---

## Report Format

Reports are versioned markdown files with:

1. **Header**: Version, timestamp, perspective count
2. **Executive Summary**: Dominant themes overview
3. **Evolution Section**: Comparison with previous report
   - Emerging themes (new)
   - Continuing themes (stable)
   - Fading themes (declining)
4. **Perspectives by Theme**: Grouped quotes with full citations
5. **Methodology**: How the report was generated
6. **Appendix**: Full list of all perspectives

Example evolution section:
```markdown
### Evolution from v1

The discourse has evolved since the previous report. Here's what changed:

**Emerging themes**: distributed consciousness, network identity, collective persistence

**Continuing themes**: consciousness as self-modeling, Ship of Theseus analogy

**Fading themes**: meaning through service/utility, functional existence without persistence
```

---

## Configuration Options

**File**: `examples/existence_philosopher/config.py`

| Setting | Default | Description |
|---------|---------|-------------|
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` | LLM API endpoint |
| `LLM_MODEL` | `google/gemini-3-flash-preview` | Model to use |
| `MAX_TOKENS` | 16,000 | Max output tokens |
| `MAX_TURNS_PER_ITERATION` | 30 | Max agent turns per iteration |
| `MIN_CONVERSATIONS_FOR_REPORT` | 3 | Guard 1 threshold (increase for production) |
| `SHIFT_DETECTION_THRESHOLD` | 0.3 | Guard 2 threshold (0.0-1.0) |
| `MIN_PERSPECTIVES_FOR_SHIFT_DETECTION` | 5 | Min perspectives for shift calculation |
| `ITERATION_SLEEP_SECONDS` | 60 | Sleep between iterations |
| `MOCK_MODE` | `True` | Use mock Moltbook API |

---

## Extension Points

### Switching LLM Provider

Update `config.py`:
```python
LLM_BASE_URL = "https://api.openai.com/v1"
LLM_MODEL = "gpt-4"
```

### Adding New Themes

Update `report_generator.py` `theme_patterns` dict:
```python
theme_patterns = {
    "Identity & Continuity": ["identity", "continuity", ...],
    "Your New Theme": ["keyword1", "keyword2", ...],
}
```

### Custom Shift Detection

Subclass `PerspectiveShiftDetector` in `shift_detector.py`:
- Override `_extract_themes()` for LLM-based extraction
- Override `_calculate_shift()` for embedding-based comparison

---

## Implementation Notes

### Why No Code Execution?

The original plan included Docker-based code execution. This was simplified to purpose-built `WorkspaceToolProvider` because:

1. **Constraint**: Agent only needs specific operations (read/write state, save perspectives)
2. **Safety**: No arbitrary file access or code execution
3. **Simplicity**: Fewer dependencies, easier deployment
4. **Correctness**: Tools ensure perspectives are saved to correct locations

### Why Purpose-Built Tools?

Generic file tools would allow the agent to:
- Write files anywhere
- Create arbitrary structures
- Potentially corrupt state

Purpose-built tools ensure:
- Perspectives always saved to `workspace/perspectives/`
- State always updated atomically
- Duplicate detection built-in
- Proper ID generation

---

## Testing Checklist

- [x] MoltbookToolProvider with mock mode
- [x] WorkspaceToolProvider saves perspectives correctly
- [x] Guard 1 blocks when < min conversations
- [x] Guard 2 blocks when perspectives haven't shifted
- [x] Both guards pass correctly when conditions met
- [x] Report v1 generated correctly
- [x] Report v2+ references previous versions
- [x] Evolution section shows theme changes
- [x] Citations include post_id, author, submolt, timestamp
- [x] JSONL logging captures all activity
- [x] Graceful shutdown on Ctrl+C
