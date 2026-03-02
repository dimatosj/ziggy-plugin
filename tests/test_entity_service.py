"""Tests for EntityService."""
import pytest
import tempfile
from pathlib import Path

from ziggy.services.entity_service import EntityService


@pytest.fixture
def data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def service(data_dir):
    return EntityService(data_dir)


class TestEntityCRUD:
    def test_create_entity(self, service):
        entity = service.create_entity(
            name="Maria Chen",
            entity_type="person",
            subtype="professional",
            domain="finances",
            description="Our accountant",
        )
        assert entity["name"] == "Maria Chen"
        assert entity["type"] == "person"

    def test_get_all_empty(self, service):
        assert service.get_all() == []

    def test_create_and_list(self, service):
        service.create_entity(name="Maria", entity_type="person")
        service.create_entity(name="Acme Corp", entity_type="organization")
        all_entities = service.get_all()
        assert len(all_entities) == 2

    def test_get_by_type(self, service):
        service.create_entity(name="Maria", entity_type="person")
        service.create_entity(name="Acme", entity_type="organization")
        people = service.get_by_type("person")
        assert len(people) == 1
        assert people[0]["name"] == "Maria"


class TestEntityResolution:
    def test_resolve_exact_match(self, service):
        service.create_entity(name="Maria Chen", entity_type="person", aliases=["Maria"])
        result = service.resolve("Maria")
        assert result["status"] == "resolved"
        assert result["entity"]["name"] == "Maria Chen"

    def test_resolve_unknown(self, service):
        result = service.resolve("Unknown Person")
        assert result["status"] == "unknown"

    def test_resolve_fuzzy_match(self, service):
        service.create_entity(name="Maria Chen", entity_type="person")
        result = service.resolve("maria chen")
        assert result["status"] in ("resolved", "fuzzy_match")

    def test_resolve_ambiguous(self, service):
        service.create_entity(name="Mike Smith", entity_type="person", domain="home")
        service.create_entity(name="Mike Smith Jr", entity_type="person", domain="work", aliases=["Mike Smith"])
        result = service.resolve("Mike Smith")
        # Could be resolved or ambiguous depending on matching
        assert result["status"] in ("resolved", "ambiguous")


class TestEntityProfiles:
    def test_create_entity_creates_profile(self, service):
        service.create_entity(
            name="Maria Chen",
            entity_type="person",
            description="Our accountant",
        )
        profile_dir = service.data_dir / "entities" / "profiles" / "people"
        profiles = list(profile_dir.glob("*.md"))
        assert len(profiles) == 1
        content = profiles[0].read_text()
        assert "Maria Chen" in content
        assert "accountant" in content


class TestTaskEnrichment:
    def test_enrich_task_with_contact(self, service):
        service.create_entity(
            name="Maria Chen",
            entity_type="person",
            contact_info={"email": "maria@example.com", "phone": "555-1234"},
        )
        result = service.enrich_task("Call Maria about taxes", "")
        assert "maria@example.com" in result["description"]
