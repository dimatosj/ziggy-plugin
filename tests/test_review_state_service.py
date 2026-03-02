"""Tests for ReviewStateService."""
import pytest
import tempfile
from pathlib import Path

from ziggy.services.review_state_service import ReviewStateService
from ziggy.models.review import ReviewState


@pytest.fixture
def data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def service(data_dir):
    return ReviewStateService(data_dir)


def test_no_state_initially(service):
    state = service.get_state("weekly")
    assert state is None


def test_save_and_get_state(service):
    state = ReviewState(type="weekly")
    service.save_state("weekly", state.model_dump())
    loaded = service.get_state("weekly")
    assert loaded is not None
    assert loaded["type"] == "weekly"
    assert loaded["status"] == "in_progress"


def test_clear_state(service):
    state = ReviewState(type="monthly")
    service.save_state("monthly", state.model_dump())
    service.clear_state("monthly")
    assert service.get_state("monthly") is None


def test_different_review_types_independent(service):
    service.save_state("weekly", ReviewState(type="weekly").model_dump())
    service.save_state("monthly", ReviewState(type="monthly").model_dump())
    assert service.get_state("weekly")["type"] == "weekly"
    assert service.get_state("monthly")["type"] == "monthly"
    service.clear_state("weekly")
    assert service.get_state("weekly") is None
    assert service.get_state("monthly") is not None


def test_invalid_review_type(service):
    with pytest.raises(ValueError):
        service.get_state("invalid")
