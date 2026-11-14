"""Top-K selector for article ranking."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml

from news_feed.scorers.weighted_scorer import Candidate, Query


class TopKSelector:
    """Select top K candidates by score.

    Sorts by score descending and keeps top K.
    Ties are stable (original order preserved).
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Load K from config file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "scoring.yaml"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.top_k = config.get("selection", {}).get("top_k", 20)

    def select(self, q: Query, cands: List[Candidate], k: Optional[int] = None) -> List[Candidate]:
        """Select top K candidates by score.

        Args:
            q: Query context (unused but kept for interface consistency).
            cands: List of scored candidates.
            k: Override for top_k (optional).

        Returns:
            Top K candidates sorted by score (descending).
        """
        if k is None:
            k = self.top_k

        # Sort by score descending, stable (preserve order for ties)
        # Python's sort is stable, so equal scores keep original order
        sorted_cands = sorted(cands, key=lambda c: c.score, reverse=True)

        # Return top K
        return sorted_cands[:k]
