"""Weighted scorer for article ranking."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml
import math
from datetime import datetime, timezone


@dataclass
class Query:
    """Query context for scoring."""
    user_id: int
    topics: List[str] = field(default_factory=list)
    interest_vec: Optional[List[float]] = None
    hidden: Dict[str, Any] = field(default_factory=dict)
    seen_ids: set = field(default_factory=set)


@dataclass
class Candidate:
    """One article moving through the pipeline."""
    article_id: int
    origin: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


class WeightedScorer:
    """Score articles using configurable weights.

    score = w1*relevance + w2*freshness + w3*source_quality + w4*popularity + w5*cluster_size - penalties
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Load weights from config file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "scoring.yaml"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.weights = config["weights"]
        self.penalties = config.get("penalties", {})
        self.freshness_params = config.get("freshness", {})

    def _compute_relevance(self, q: Query, c: Candidate) -> float:
        """Compute relevance score (0-1).

        For now: fraction of user's topics that appear in article's tags or title.
        TODO: Add embedding similarity once embeddings are implemented.
        """
        if not q.topics:
            return 0.5  # neutral score if no topics

        topics_lower = [t.lower() for t in q.topics]

        # Get article's tags and title from data
        tags = c.data.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        tags_lower = [t.lower() for t in tags]

        title = c.data.get("title", "").lower()

        # Count matches
        matches = 0
        for topic in topics_lower:
            if topic in tags_lower or topic in title:
                matches += 1

        return matches / len(topics_lower) if topics_lower else 0.0

    def _compute_freshness(self, c: Candidate) -> float:
        """Compute freshness score using exponential decay.

        Decays exponentially with article age.
        """
        published_at = c.data.get("published_at")
        if not published_at:
            return 0.5  # neutral if no timestamp

        # Parse timestamp if needed
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return 0.5
        elif isinstance(published_at, datetime):
            pass
        else:
            return 0.5

        # Ensure timezone-aware
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_hours = (now - published_at).total_seconds() / 3600

        # Exponential decay
        half_life = self.freshness_params.get("half_life_hours", 24)
        freshness = math.exp(-age_hours * math.log(2) / half_life)

        return max(0.0, min(1.0, freshness))

    def _compute_source_quality(self, c: Candidate) -> float:
        """Compute source quality (0-1)."""
        return c.data.get("source_quality", 0.5)

    def _compute_popularity(self, c: Candidate, all_cands: List[Candidate]) -> float:
        """Compute normalized popularity (0-1) across batch."""
        popularity = c.data.get("popularity", 0)

        if not all_cands:
            return 0.5

        # Normalize across batch
        pops = [cand.data.get("popularity", 0) for cand in all_cands]
        min_pop = min(pops)
        max_pop = max(pops)

        if max_pop == min_pop:
            return 0.5  # all same popularity

        return (popularity - min_pop) / (max_pop - min_pop)

    def _compute_cluster_size(self, c: Candidate) -> float:
        """Compute cluster size score (0-1).

        For now: return 0 (cluster_size not implemented yet).
        """
        # TODO: Implement once clustering is available
        return 0.0

    def score(self, q: Query, cands: List[Candidate]) -> List[Candidate]:
        """Score all candidates and return them with scores.

        Args:
            q: Query context with user topics.
            cands: List of candidates to score.

        Returns:
            Candidates with updated scores (higher is better).
        """
        if not cands:
            return cands

        # Track source occurrences for repeat penalty
        source_counts: Dict[str, int] = {}

        # Compute base scores
        for c in cands:
            relevance = self._compute_relevance(q, c)
            freshness = self._compute_freshness(c)
            source_quality = self._compute_source_quality(c)
            popularity = self._compute_popularity(c, cands)
            cluster_size = self._compute_cluster_size(c)

            c.score = (
                self.weights.get("relevance", 0.35) * relevance +
                self.weights.get("freshness", 0.25) * freshness +
                self.weights.get("source_quality", 0.20) * source_quality +
                self.weights.get("popularity", 0.15) * popularity +
                self.weights.get("cluster_size", 0.05) * cluster_size
            )

            # Track source
            source = c.data.get("source", "")
            source_counts[source] = source_counts.get(source, 0) + 1

        # Apply repeat source penalty (after first occurrence)
        seen_sources: Dict[str, int] = {}
        for c in cands:
            source = c.data.get("source", "")
            if source in seen_sources:
                # Apply penalty for repeat
                penalty = self.penalties.get("repeat_source", 0.1)
                c.score -= penalty * seen_sources[source]
            seen_sources[source] = seen_sources.get(source, 0) + 1

        return cands
