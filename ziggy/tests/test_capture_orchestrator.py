"""Tests for CaptureOrchestrator."""
import pytest

from ziggy.orchestrators.capture_orchestrator import CaptureOrchestrator


@pytest.fixture
def orchestrator():
    return CaptureOrchestrator()


class TestPriorityScoring:
    def test_deadline_is_urgent(self, orchestrator):
        result = orchestrator.calculate_priority("finish report by tomorrow")
        assert result["level"] == "URGENT"

    def test_blocking_increases_priority(self, orchestrator):
        result = orchestrator.calculate_priority("this is blocking the release")
        assert result["level"] in ("URGENT", "HIGH")

    def test_normal_task_is_medium(self, orchestrator):
        result = orchestrator.calculate_priority("buy groceries")
        assert result["level"] == "MEDIUM"


class TestDomainMatching:
    def test_home_keywords(self, orchestrator):
        result = orchestrator.match_domain("fix the leaky faucet")
        assert result["matched"] == "home"

    def test_health_keywords(self, orchestrator):
        result = orchestrator.match_domain("schedule doctor appointment")
        assert result["matched"] == "health"

    def test_no_match_defaults_to_home(self, orchestrator):
        result = orchestrator.match_domain("do the thing")
        assert result["matched"] == "home"


class TestAnalyze:
    def test_clear_task(self, orchestrator):
        result = orchestrator.analyze("buy milk")
        assert result["is_clear_task"] is True
        assert result["entity_detection"]["type"] == "task"

    def test_project_detection(self, orchestrator):
        result = orchestrator.analyze("renovate the kitchen over 3 weeks")
        assert result["is_clear_task"] is False
        assert result["entity_detection"]["type"] == "project"

    def test_analyze_includes_all_fields(self, orchestrator):
        result = orchestrator.analyze("fix the faucet tomorrow")
        assert "is_clear_task" in result
        assert "entity_detection" in result
        assert "priority" in result
        assert "domain" in result
        assert "owner" in result


class TestOwnerSuggestion:
    def test_default_owner(self, orchestrator):
        owner = orchestrator.suggest_owner("home")
        # Without config, returns None
        assert owner is None or isinstance(owner, str)

    def test_with_config(self):
        config = {
            "household": {
                "domain_owners": {"home": "Both", "finances": "John"}
            }
        }
        orch = CaptureOrchestrator(config=config)
        assert orch.suggest_owner("finances") == "John"
