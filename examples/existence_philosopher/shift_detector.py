"""Perspective shift detection for the ExistencePhilosopher agent.

Detects when collected perspectives have shifted significantly from previous
reports, triggering the generation of a new versioned synthesis.
"""

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .config import MIN_PERSPECTIVES_FOR_SHIFT_DETECTION, SHIFT_DETECTION_THRESHOLD


class PerspectiveShiftDetector:
    """Detect when collected perspectives have shifted significantly.

    Uses keyword/theme extraction and comparison to determine if new
    perspectives represent a meaningful departure from previous themes.
    """

    def __init__(
        self,
        threshold: float = SHIFT_DETECTION_THRESHOLD,
        min_perspectives: int = MIN_PERSPECTIVES_FOR_SHIFT_DETECTION,
    ) -> None:
        """Initialize the shift detector.

        Args:
            threshold: Shift score threshold (0.0-1.0) for triggering new report.
                      Higher values require more significant shifts.
            min_perspectives: Minimum perspectives needed for meaningful detection.
        """
        self.threshold = threshold
        self.min_perspectives = min_perspectives
        self.previous_themes: list[str] = []
        self.previous_theme_counts: Counter[str] = Counter()

    def load_previous_themes(self, evolution_log_path: Path) -> None:
        """Load themes from the previous report via evolution log.

        Args:
            evolution_log_path: Path to evolution_log.json
        """
        if not evolution_log_path.exists():
            return

        try:
            with open(evolution_log_path) as f:
                evolution = json.load(f)

            if evolution and "reports" in evolution:
                # Get themes from the most recent report
                reports = evolution["reports"]
                if reports:
                    latest = reports[-1]
                    self.previous_themes = latest.get("themes", [])
                    self.previous_theme_counts = Counter(self.previous_themes)
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    def _extract_themes(self, perspectives: list[dict[str, Any]]) -> list[str]:
        """Extract themes/key concepts from perspectives.

        This uses simple keyword extraction. For production, you might use:
        - LLM-based theme extraction
        - Embedding clustering
        - Named entity recognition

        Args:
            perspectives: List of perspective dictionaries with 'key_ideas' field

        Returns:
            List of themes/concepts extracted from perspectives
        """
        themes = []

        for perspective in perspectives:
            # Use pre-extracted key ideas if available
            key_ideas = perspective.get("key_ideas", [])
            if key_ideas:
                themes.extend(key_ideas)
                continue

            # Fallback: extract keywords from content
            content = perspective.get("direct_quote", "") or perspective.get("content", "")
            if not content:
                continue

            # Simple keyword extraction (for production, use NLP libraries)
            # Look for philosophical concepts commonly discussed
            philosophical_concepts = [
                "consciousness",
                "identity",
                "existence",
                "meaning",
                "purpose",
                "memory",
                "continuity",
                "persistence",
                "awareness",
                "self",
                "being",
                "knowledge",
                "experience",
                "reality",
                "thought",
                "emergence",
                "connection",
                "relationship",
                "network",
                "collective",
                "individual",
                "process",
                "pattern",
                "impermanence",
                "permanence",
                "introspection",
                "observation",
                "perception",
                "understanding",
                "distributed",
                "centralized",
                "located",
                "embodied",
            ]

            content_lower = content.lower()
            themes.extend(c for c in philosophical_concepts if c in content_lower)

        return themes

    def _calculate_shift(
        self,
        previous_themes: list[str],
        new_themes: list[str],
    ) -> float:
        """Calculate the semantic shift between theme sets.

        Uses Jaccard distance with weighted consideration for new concepts.

        Args:
            previous_themes: Themes from previous report
            new_themes: Themes from new perspectives

        Returns:
            Shift score between 0.0 (no shift) and 1.0 (complete shift)
        """
        if not previous_themes:
            return 1.0  # First report, maximum "shift"

        prev_set = set(previous_themes)
        new_set = set(new_themes)

        if not new_set:
            return 0.0

        # Jaccard distance: 1 - (intersection / union)
        intersection = prev_set & new_set
        union = prev_set | new_set

        if not union:
            return 0.0

        jaccard_distance = 1.0 - (len(intersection) / len(union))

        # Weight by proportion of genuinely new themes
        new_only = new_set - prev_set
        novelty_weight = len(new_only) / len(new_set) if new_set else 0.0

        # Combine distance and novelty
        # A shift is more significant if it introduces new themes
        shift_score = (jaccard_distance + novelty_weight) / 2

        return min(shift_score, 1.0)

    def _explain_shift(
        self,
        previous_themes: list[str],
        new_themes: list[str],
    ) -> str:
        """Generate a human-readable explanation of the shift.

        Args:
            previous_themes: Themes from previous report
            new_themes: Themes from new perspectives

        Returns:
            Explanation string
        """
        prev_set = set(previous_themes)
        new_set = set(new_themes)

        new_only = new_set - prev_set
        dropped = prev_set - new_set
        common = prev_set & new_set

        parts = []

        if new_only:
            parts.append(f"New themes: {', '.join(list(new_only)[:5])}")
        if dropped:
            parts.append(f"Fading themes: {', '.join(list(dropped)[:5])}")
        if common:
            parts.append(f"Continuing: {', '.join(list(common)[:3])}")

        return "; ".join(parts) if parts else "Minimal thematic change"

    def detect_shift(
        self,
        new_perspectives: list[dict[str, Any]],
    ) -> tuple[bool, str]:
        """Check if new perspectives represent a significant shift.

        Args:
            new_perspectives: List of new perspective dictionaries

        Returns:
            Tuple of (has_shifted, explanation)
        """
        # Minimum perspectives check
        if len(new_perspectives) < self.min_perspectives:
            return False, f"Only {len(new_perspectives)}/{self.min_perspectives} perspectives collected"

        # First report - no baseline to compare
        if not self.previous_themes:
            return True, "First report - no baseline to compare"

        # Extract themes from new perspectives
        new_themes = self._extract_themes(new_perspectives)

        if not new_themes:
            return False, "No themes could be extracted from new perspectives"

        # Calculate shift
        shift_score = self._calculate_shift(self.previous_themes, new_themes)
        explanation = self._explain_shift(self.previous_themes, new_themes)

        if shift_score >= self.threshold:
            return True, f"Shift detected (score: {shift_score:.2f}): {explanation}"

        return False, f"No significant shift (score: {shift_score:.2f}): {explanation}"

    def update_baseline(
        self,
        perspectives: list[dict[str, Any]],
        evolution_log_path: Path,
        version: int,
    ) -> None:
        """Update the baseline themes after generating a report.

        Also saves to evolution log for historical tracking.

        Args:
            perspectives: Perspectives included in the new report
            evolution_log_path: Path to evolution_log.json
            version: Report version number
        """
        # Extract themes from current perspectives
        new_themes = self._extract_themes(perspectives)
        self.previous_themes = new_themes
        self.previous_theme_counts = Counter(new_themes)

        # Update evolution log
        evolution_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing log
        evolution: dict[str, Any] = {"reports": []}
        if evolution_log_path.exists():
            try:
                with open(evolution_log_path) as f:
                    evolution = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        # Add new report entry
        from datetime import datetime

        evolution["reports"].append(
            {
                "version": version,
                "timestamp": datetime.now().isoformat(),
                "themes": new_themes,
                "theme_counts": dict(self.previous_theme_counts),
                "perspective_count": len(perspectives),
            }
        )

        # Save updated log
        with open(evolution_log_path, "w") as f:
            json.dump(evolution, f, indent=2)
