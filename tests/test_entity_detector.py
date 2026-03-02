"""Tests for EntityDetector."""
import pytest

from ziggy.services.entity_detector import EntityDetector


@pytest.fixture
def detector():
    return EntityDetector()


class TestEntityTypeDetection:
    def test_simple_task(self, detector):
        result = detector.detect_entity_type("buy milk")
        assert result.entity_type == "task"

    def test_project_detection(self, detector):
        result = detector.detect_entity_type("renovate the kitchen over 3 weeks")
        assert result.entity_type == "project"

    def test_commitment_detection(self, detector):
        result = detector.detect_entity_type("exercise 3x per week")
        assert result.entity_type == "commitment"

    def test_goal_detection(self, detector):
        result = detector.detect_entity_type("set Q1 goal to improve fitness")
        assert result.entity_type == "goal"


class TestMentionDetection:
    def test_detect_person(self, detector):
        mentions = detector.detect_mentions("Call Maria about the project")
        names = [m["text"] for m in mentions]
        assert "Maria" in names

    def test_no_false_positive_common_words(self, detector):
        mentions = detector.detect_mentions("buy eggs and milk")
        assert len(mentions) == 0

    def test_detect_multiple_mentions(self, detector):
        mentions = detector.detect_mentions("Email Avi about the contract, then call Avi again")
        avi_mentions = [m for m in mentions if m["text"] == "Avi"]
        assert len(avi_mentions) >= 1
        assert avi_mentions[0]["triage_score"] >= 3  # Multiple mentions + action verb
