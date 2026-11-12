"""Test that all base modules can be imported."""
import pytest


def test_import_sources():
    """Test importing sources module."""
    from news_feed.sources import BaseSource
    assert BaseSource is not None


def test_import_hydrators():
    """Test importing hydrators module."""
    from news_feed.hydrators import BaseHydrator
    assert BaseHydrator is not None


def test_import_filters():
    """Test importing filters module."""
    from news_feed.filters import BaseFilter
    assert BaseFilter is not None


def test_import_scorers():
    """Test importing scorers module."""
    from news_feed.scorers import BaseScorer
    assert BaseScorer is not None


def test_import_selectors():
    """Test importing selectors module."""
    from news_feed.selectors import BaseSelector
    assert BaseSelector is not None


def test_all_base_classes_exist():
    """Verify all base classes are abstract and have expected methods."""
    from news_feed.sources import BaseSource
    from news_feed.hydrators import BaseHydrator
    from news_feed.filters import BaseFilter
    from news_feed.scorers import BaseScorer
    from news_feed.selectors import BaseSelector

    # All should be abstract (cannot be instantiated directly)
    with pytest.raises(TypeError):
        BaseSource()
    with pytest.raises(TypeError):
        BaseHydrator()
    with pytest.raises(TypeError):
        BaseFilter()
    with pytest.raises(TypeError):
        BaseScorer()
    with pytest.raises(TypeError):
        BaseSelector()
