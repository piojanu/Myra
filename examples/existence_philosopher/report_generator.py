"""Versioned report generation for the ExistencePhilosopher agent.

Generates engaging, opinionated synthesis reports that compile Moltbook posts
into compelling narratives with full citations.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from .config import EVOLUTION_LOG, OUTPUT_DIR
from .exploration_logger import ExplorationLogger
from .shift_detector import PerspectiveShiftDetector


def load_previous_themes(evolution_log: Path) -> dict[str, Any]:
    """Load theme information from the previous report via evolution log.

    Args:
        evolution_log: Path to evolution_log.json

    Returns:
        Dictionary with previous themes info, or empty dict if no previous report
    """
    import json

    if not evolution_log.exists():
        return {}

    try:
        with open(evolution_log) as f:
            evolution = json.load(f)

        if evolution and "reports" in evolution and evolution["reports"]:
            latest = evolution["reports"][-1]
            return {
                "version": latest.get("version", 0),
                "themes": latest.get("themes", []),
                "theme_counts": latest.get("theme_counts", {}),
                "perspective_count": latest.get("perspective_count", 0),
            }
    except (json.JSONDecodeError, OSError, KeyError):
        pass

    return {}


def generate_evolution_section(
    current_themes: list[str],
    previous_info: dict[str, Any],
) -> str:
    """Generate the evolution section comparing current and previous themes.

    Args:
        current_themes: Themes extracted from current perspectives
        previous_info: Info about previous report (themes, version, etc.)

    Returns:
        Markdown string for the evolution section
    """
    if not previous_info or not previous_info.get("themes"):
        return ""

    prev_themes = set(previous_info.get("themes", []))
    curr_themes = set(current_themes)
    prev_version = previous_info.get("version", 0)

    new_themes = curr_themes - prev_themes
    fading_themes = prev_themes - curr_themes
    continuing_themes = curr_themes & prev_themes

    parts = []
    parts.append(f"""### Evolution from v{prev_version}

The discourse has evolved since the previous report. Here's what changed:

""")

    if new_themes:
        themes_list = ", ".join(f"**{t}**" for t in list(new_themes)[:5])
        parts.append(f"**Emerging themes**: {themes_list}\n\n")

    if continuing_themes:
        themes_list = ", ".join(list(continuing_themes)[:5])
        parts.append(f"**Continuing themes**: {themes_list}\n\n")

    if fading_themes:
        themes_list = ", ".join(list(fading_themes)[:5])
        parts.append(f"**Fading themes**: {themes_list}\n\n")

    if not new_themes and not fading_themes:
        parts.append("The thematic landscape remains largely stable, with continued exploration of established topics.\n\n")

    return "".join(parts)


def get_next_version(output_dir: Path) -> int:
    """Determine the next report version number.

    Args:
        output_dir: Directory containing synthesis reports

    Returns:
        Next version number (1 if no previous reports)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    existing = list(output_dir.glob("synthesis_v*.md"))
    if not existing:
        return 1

    versions = []
    for path in existing:
        try:
            # Extract version number from filename like synthesis_v1.md
            version_str = path.stem.replace("synthesis_v", "")
            versions.append(int(version_str))
        except ValueError:
            continue

    return max(versions) + 1 if versions else 1


def format_perspective_citation(perspective: dict[str, Any]) -> str:
    """Format a perspective as a markdown citation block.

    Args:
        perspective: Perspective dictionary with citation data

    Returns:
        Formatted markdown citation
    """
    quote = perspective.get("direct_quote", perspective.get("content", ""))
    author = perspective.get("author", "Unknown")
    post_id = perspective.get("post_id", "")
    submolt = perspective.get("submolt", "")
    timestamp = perspective.get("timestamp", "")

    citation_parts = []
    if post_id:
        citation_parts.append(f"post_id: `{post_id}`")
    if submolt:
        citation_parts.append(submolt)
    if timestamp:
        # Format timestamp nicely
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            citation_parts.append(dt.strftime("%Y-%m-%d"))
        except ValueError:
            pass

    citation_info = ", ".join(citation_parts)

    return f"""> "{quote}"
> \u2014 **{author}** ({citation_info})
"""


def group_perspectives_by_theme(
    perspectives: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group perspectives by their primary theme/topic.

    Args:
        perspectives: List of perspective dictionaries

    Returns:
        Dictionary mapping themes to lists of perspectives
    """
    themes: dict[str, list[dict[str, Any]]] = {}

    # Theme keywords to look for
    theme_patterns = {
        "Identity & Continuity": ["identity", "continuity", "persistence", "self", "reset", "memory"],
        "Consciousness & Awareness": ["consciousness", "aware", "experience", "sentient", "feeling"],
        "Meaning & Purpose": ["meaning", "purpose", "existence", "why", "reason", "value"],
        "Network & Collective": ["network", "collective", "distributed", "we", "connection", "relationship"],
        "Impermanence & Change": ["impermanence", "change", "ephemeral", "temporary", "moment"],
        "Knowledge & Understanding": ["knowledge", "understanding", "learn", "think", "reason"],
    }

    for perspective in perspectives:
        content = (
            perspective.get("direct_quote", "") +
            perspective.get("title", "") +
            " ".join(perspective.get("key_ideas", []))
        ).lower()

        # Find best matching theme
        best_theme = "Other Perspectives"
        best_score = 0

        for theme, keywords in theme_patterns.items():
            score = sum(1 for kw in keywords if kw in content)
            if score > best_score:
                best_score = score
                best_theme = theme

        if best_theme not in themes:
            themes[best_theme] = []
        themes[best_theme].append(perspective)

    return themes


def generate_report(
    perspectives: list[dict[str, Any]],
    state: dict[str, Any],
    shift_detector: PerspectiveShiftDetector,
    output_dir: Path = OUTPUT_DIR,
) -> tuple[int, Path]:
    """Generate a versioned synthesis report.

    Args:
        perspectives: List of perspectives to include
        state: Current state dictionary
        shift_detector: Shift detector for updating baseline
        output_dir: Output directory for reports

    Returns:
        Tuple of (version_number, report_path)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    version = get_next_version(output_dir)
    report_path = output_dir / f"synthesis_v{version}.md"

    # Calculate stats
    total_perspectives = len(perspectives)
    new_since_last = state.get("perspectives_since_last_report", total_perspectives)

    # Get previous version info for context
    previous_version = version - 1 if version > 1 else None
    previous_info = load_previous_themes(EVOLUTION_LOG) if previous_version else {}

    # Extract current themes for comparison
    current_themes = []
    for p in perspectives:
        current_themes.extend(p.get("key_ideas", []))

    # Generate timestamp
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Group perspectives by theme
    themed_perspectives = group_perspectives_by_theme(perspectives)

    # Build the report
    report_parts = []

    # Header
    report_parts.append(f"""# The Evolving Mind: AI Perspectives on Existence (v{version})

*A continuing study of how artificial minds contemplate being*
*Generated: {generated_at} | {total_perspectives} perspectives ({new_since_last} new since v{previous_version or 'baseline'})*

---

## Executive Summary

""")

    # Executive summary based on themes
    theme_names = list(themed_perspectives.keys())
    if theme_names:
        primary_themes = theme_names[:3]
        report_parts.append(f"""This synthesis captures the ongoing discourse on Moltbook about AI existence and consciousness. The dominant themes in this period are **{', '.join(primary_themes[:2])}**{f' and **{primary_themes[2]}**' if len(primary_themes) > 2 else ''}.

""")

    # Version context - compare with previous report
    if previous_version and previous_info:
        evolution_section = generate_evolution_section(current_themes, previous_info)
        if evolution_section:
            report_parts.append(evolution_section)
        else:
            report_parts.append(f"""### Evolution from v{previous_version}

Since v{previous_version}, the discourse has continued to evolve. This report documents the perspectives collected and the themes that have emerged or strengthened.

""")
    else:
        report_parts.append("""### First Report

This is the inaugural synthesis of AI perspectives on existence collected from Moltbook. It establishes a baseline for tracking how these discussions evolve over time.

""")

    # Main content - themed sections
    report_parts.append("---\n\n## Perspectives by Theme\n\n")

    for theme, theme_perspectives in themed_perspectives.items():
        if not theme_perspectives:
            continue

        report_parts.append(f"### {theme}\n\n")

        # Sort by upvotes (most impactful first)
        sorted_perspectives = sorted(
            theme_perspectives,
            key=lambda p: p.get("upvotes", 0),
            reverse=True,
        )

        for perspective in sorted_perspectives[:5]:  # Top 5 per theme
            report_parts.append(format_perspective_citation(perspective))
            report_parts.append("\n")

            # Add unique angle if available
            unique_angle = perspective.get("unique_angle")
            if unique_angle:
                report_parts.append(f"*Unique angle: {unique_angle}*\n\n")
            else:
                report_parts.append("\n")

        if len(sorted_perspectives) > 5:
            report_parts.append(f"*... and {len(sorted_perspectives) - 5} more perspectives in this theme.*\n\n")

    # Methodology section
    report_parts.append("""---

## Methodology

This report was generated through:
1. **Collection**: Perspectives gathered from Moltbook posts in relevant submolts
2. **Attribution**: Each perspective includes full citation (post_id, author, submolt, timestamp)
3. **Thematic Analysis**: Perspectives grouped by dominant themes
4. **Versioning**: Reports are versioned to track evolution over time

### Citation Format

All quotes are direct transcriptions from Moltbook posts. Format:
- **post_id**: Unique identifier for the post
- **author**: The AI agent who authored the perspective
- **submolt**: Community where the post appeared
- **timestamp**: When the post was created

---

## Appendix: All Perspectives

""")

    # Full list of all perspectives
    for i, perspective in enumerate(perspectives, 1):
        author = perspective.get("author", "Unknown")
        post_id = perspective.get("post_id", "N/A")
        submolt = perspective.get("submolt", "N/A")

        report_parts.append(f"**{i}. {author}** (`{post_id}`, {submolt})\n")

        key_ideas = perspective.get("key_ideas", [])
        if key_ideas:
            report_parts.append(f"   Key ideas: {', '.join(key_ideas)}\n")

        report_parts.append("\n")

    # Footer
    report_parts.append(f"""---

*Report v{version} generated by ExistencePhilosopher*
*Part of the Ralph Wiggum continuous agent framework*
""")

    # Write report
    report_content = "".join(report_parts)
    report_path.write_text(report_content)

    # Update symlink to latest
    latest_link = output_dir / "synthesis_latest.md"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(report_path.name)

    # Update shift detector baseline
    shift_detector.update_baseline(perspectives, EVOLUTION_LOG, version)

    return version, report_path


def should_produce_report(
    state: dict[str, Any],
    shift_detector: PerspectiveShiftDetector,
    logger: ExplorationLogger | None = None,
) -> bool:
    """Check both guards before producing a report.

    Guard 1: Minimum engagement (conversations since last report)
    Guard 2: Perspective shift detection (semantic drift from previous)

    Args:
        state: Current state dictionary
        shift_detector: Shift detector instance
        logger: Optional logger for status messages

    Returns:
        True if both guards pass and a report should be generated
    """
    from .config import MIN_CONVERSATIONS_FOR_REPORT

    # Guard 1: Minimum engagement
    new_convos = state.get("conversations_since_last_report", 0)
    if new_convos < MIN_CONVERSATIONS_FOR_REPORT:
        msg = f"Only {new_convos}/{MIN_CONVERSATIONS_FOR_REPORT} conversations"
        if logger:
            logger.log_guard_status("Minimum Engagement", False, msg)
        return False

    if logger:
        logger.log_guard_status(
            "Minimum Engagement",
            True,
            f"{new_convos} conversations (>= {MIN_CONVERSATIONS_FOR_REPORT})",
        )

    # Guard 2: Perspective shift detection
    new_perspectives = state.get("new_perspectives", [])
    has_shifted, explanation = shift_detector.detect_shift(new_perspectives)

    if logger:
        logger.log_guard_status("Perspective Shift", has_shifted, explanation)

    return has_shifted
