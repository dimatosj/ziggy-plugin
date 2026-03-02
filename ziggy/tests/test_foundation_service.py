"""Tests for FoundationService."""
import pytest
import tempfile
from pathlib import Path

from ziggy.services.foundation_service import FoundationService
from ziggy.models.foundation import PillarName


@pytest.fixture
def data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def service(data_dir):
    return FoundationService(data_dir)


def test_write_and_read_pillar(service):
    service.write_pillar(PillarName.REALITY, "# Life Reality\n\nWe live in Atlanta.")
    content = service.read_pillar(PillarName.REALITY)
    assert "Atlanta" in content


def test_read_nonexistent_returns_none(service):
    content = service.read_pillar(PillarName.FAMILY)
    assert content is None


def test_read_all_pillars(service):
    service.write_pillar(PillarName.REALITY, "reality content")
    service.write_pillar(PillarName.VISION, "vision content")
    all_pillars = service.read_all()
    assert "reality" in all_pillars
    assert "vision" in all_pillars
    assert all_pillars["reality"] == "reality content"
    assert all_pillars["family"] is None


def test_has_foundation(service):
    assert service.has_foundation() is False
    service.write_pillar(PillarName.REALITY, "content")
    assert service.has_foundation() is True
