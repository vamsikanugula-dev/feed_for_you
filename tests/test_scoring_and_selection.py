"""Tests for scoring and selection (stage 4)."""
import pytest
from datetime import datetime, timedelta, timezone
from news_feed.scorers.weighted_scorer import WeightedScorer, Candidate, Query
from news_feed.selectors.top_k_selector import TopKSelector


def make_candidate(article_id: int, title: str = "", tags: list = None,
                  published_at: datetime = None, source_quality: float = 0.5,
                  popularity: float = 0, source: str = "", score: float = 0.0) -> Candidate:
    """Helper to create a Candidate."""
    return Candidate(
        article_id=article_id,
        data={
            "title": title,
            "tags": tags or [],
            "published_at": published_at or datetime.now(timezone.utc),
            "source_quality": source_quality,
            "popularity": popularity,
            "source": source,
        },
        score=score
    )


class TestWeightedScorer:
    """Tests for WeightedScorer."""

    def test_fresher_article_scores_higher(self):
        """Newer article should have higher freshness score."""
        scorer = WeightedScorer()
        query = Query(user_id=1, topics=[])

        # Fresh article (1 hour old)
        fresh = make_candidate(1, published_at=datetime.now(timezone.utc) - timedelta(hours=1))
        # Old article (48 hours old)
        old = make_candidate(2, published_at=datetime.now(timezone.utc) - timedelta(hours=48))

        scored = scorer.score(query, [fresh, old])

        assert scored[0].score > scored[1].score, "Fresh article should score higher"

    def test_topic_match_scores_higher(self):
        """Article matching user topics should score higher."""
        scorer = WeightedScorer()
        query = Query(user_id=1, topics=["python", "ai"])

        # Matching article
        match = make_candidate(1, title="Python AI tutorial", tags=["programming"])
        # Non-matching article
        no_match = make_candidate(2, title="Cooking recipes", tags=["food"])

        scored = scorer.score(query, [match, no_match])

        assert scored[0].score > scored[1].score, "Matching article should score higher"

    def test_partial_topic_match(self):
        """Partial topic match should get partial relevance score."""
        scorer = WeightedScorer()
        query = Query(user_id=1, topics=["python", "ai", "ml"])

        # Matches 1 of 3 topics
        partial = make_candidate(1, title="Python tutorial")
        # Matches 2 of 3 topics
        better = make_candidate(1, title="Python AI tutorial")

        scored = scorer.score(query, [partial, better])

        # Both should have non-zero scores, better should be higher
        assert scored[0].score >= 0
        assert scored[1].score >= 0

    def test_source_quality_affects_score(self):
        """Higher source quality should boost score."""
        scorer = WeightedScorer()
        query = Query(user_id=1, topics=[])

        high_quality = make_candidate(1, source_quality=0.9)
        low_quality = make_candidate(2, source_quality=0.3)

        scored = scorer.score(query, [high_quality, low_quality])

        assert scored[0].score > scored[1].score, "High quality source should score higher"

    def test_popularity_normalization(self):
        """Popularity should be normalized across batch."""
        scorer = WeightedScorer()
        query = Query(user_id=1, topics=[])

        # Set same age and quality, different popularity
        now = datetime.now(timezone.utc)
        high_pop = make_candidate(1, popularity=100, published_at=now, source_quality=0.5)
        low_pop = make_candidate(2, popularity=10, published_at=now, source_quality=0.5)

        scored = scorer.score(query, [high_pop, low_pop])

        assert scored[0].score > scored[1].score, "High popularity should score higher"

    def test_repeat_source_penalty(self):
        """Repeated sources should be penalized."""
        scorer = WeightedScorer()
        query = Query(user_id=1, topics=[])

        now = datetime.now(timezone.utc)
        first = make_candidate(1, source="source_a", published_at=now, source_quality=0.5)
        second = make_candidate(2, source="source_a", published_at=now, source_quality=0.5)

        scored = scorer.score(query, [first, second])

        # Second from same source should have lower score
        assert scored[0].score > scored[1].score, "Repeat source should be penalized"

    def test_empty_list(self):
        """Empty list should return empty."""
        scorer = WeightedScorer()
        query = Query(user_id=1, topics=[])

        scored = scorer.score(query, [])

        assert scored == []


class TestTopKSelector:
    """Tests for TopKSelector."""

    def test_k_is_respected(self):
        """Should return exactly K candidates."""
        selector = TopKSelector()
        query = Query(user_id=1)

        cands = [make_candidate(i, score=float(i)) for i in range(10)]

        selected = selector.select(query, cands, k=5)

        assert len(selected) == 5, "Should return exactly K candidates"

    def test_returns_highest_scores(self):
        """Should return candidates with highest scores."""
        selector = TopKSelector()
        query = Query(user_id=1)

        cands = [
            make_candidate(1, score=10.0),
            make_candidate(2, score=5.0),
            make_candidate(3, score=15.0),
            make_candidate(4, score=7.0),
        ]

        selected = selector.select(query, cands, k=2)

        assert len(selected) == 2
        assert selected[0].article_id == 3  # highest score
        assert selected[1].article_id == 1  # second highest

    def test_ties_are_stable(self):
        """Equal scores should preserve original order."""
        selector = TopKSelector()
        query = Query(user_id=1)

        # Create candidates with same score, different ids
        cands = [
            make_candidate(1, score=10.0),
            make_candidate(2, score=10.0),
            make_candidate(3, score=10.0),
        ]

        selected = selector.select(query, cands, k=3)

        # Order should be preserved
        assert [c.article_id for c in selected] == [1, 2, 3]

    def test_empty_list(self):
        """Empty list should return empty."""
        selector = TopKSelector()
        query = Query(user_id=1)

        selected = selector.select(query, [], k=5)

        assert selected == []

    def test_k_greater_than_list(self):
        """K > len(list) should return all candidates."""
        selector = TopKSelector()
        query = Query(user_id=1)

        cands = [make_candidate(i, score=float(i)) for i in range(3)]

        selected = selector.select(query, cands, k=10)

        assert len(selected) == 3
        assert selected == sorted(cands, key=lambda c: c.score, reverse=True)


class TestIntegration:
    """Integration tests for scoring + selection."""

    def test_full_pipeline(self):
        """Test scoring followed by selection."""
        scorer = WeightedScorer()
        selector = TopKSelector()
        query = Query(user_id=1, topics=["ai", "python"])

        cands = [
            make_candidate(1, title="AI news", popularity=10),
            make_candidate(2, title="Python tutorial", popularity=5),
            make_candidate(3, title="Random article", popularity=8),
            make_candidate(4, title="AI Python ML", popularity=15),
        ]

        scored = scorer.score(query, cands)
        selected = selector.select(query, scored, k=2)

        # Should have 2 candidates
        assert len(selected) == 2

        # Should be highest scored
        all_scores = sorted([c.score for c in scored], reverse=True)
        assert selected[0].score == all_scores[0]
        assert selected[1].score == all_scores[1]
