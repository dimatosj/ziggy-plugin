"""Tests for Ziggy plugin data models."""
import pytest
from datetime import datetime
from ziggy.models.task import Task, Draft, AnalysisResult
from ziggy.models.entity import Entity, EntityMention, ResolutionResult
from ziggy.models.review import ReviewState
from ziggy.models.config import ZiggyConfig, Household
from ziggy.models.foundation import PillarName


class TestTaskModels:
    def test_task_creation_defaults(self):
        task = Task(title="buy eggs")
        assert task.title == "buy eggs"
        assert task.status == "inbox"
        assert task.priority == "MEDIUM"
        assert task.domain == "home"
        assert task.id is not None  # auto-generated UUID

    def test_task_status_values(self):
        for status in ["inbox", "active", "completed", "archived"]:
            task = Task(title="test", status=status)
            assert task.status == status

    def test_draft_creation(self):
        draft = Draft(title="renovate kitchen", type="project")
        assert draft.status == "draft"
        assert draft.type == "project"
        assert draft.id is not None

    def test_analysis_result(self):
        result = AnalysisResult(
            is_clear_task=True,
            entity_detection={"type": "task", "confidence": 0.9, "signals": []},
            priority={"level": "HIGH", "score": 0.6, "signals": ["deadline"]},
            domain={"matched": "home", "confidence": "high", "keywords_found": ["faucet"]},
        )
        assert result.is_clear_task is True
        assert result.entity_detection["type"] == "task"


class TestEntityModels:
    def test_entity_creation(self):
        entity = Entity(
            id="person-maria-chen",
            name="Maria Chen",
            type="person",
            subtype="professional",
            domain="finances",
        )
        assert entity.id == "person-maria-chen"
        assert entity.name == "Maria Chen"

    def test_entity_with_aliases(self):
        entity = Entity(
            name="Maria Chen",
            type="person",
            aliases=["Maria", "our accountant"],
        )
        assert len(entity.aliases) == 2

    def test_resolution_result_resolved(self):
        entity = Entity(name="Maria", type="person")
        result = ResolutionResult(status="resolved", entity=entity)
        assert result.status == "resolved"

    def test_resolution_result_unknown(self):
        result = ResolutionResult(status="unknown")
        assert result.entity is None


class TestReviewModels:
    def test_review_state_creation(self):
        state = ReviewState(type="weekly")
        assert state.status == "in_progress"
        assert state.current_step == "reflect"

    def test_review_types(self):
        for rtype in ["weekly", "monthly", "quarterly"]:
            state = ReviewState(type=rtype)
            assert state.type == rtype


class TestConfigModels:
    def test_single_user_config(self):
        config = ZiggyConfig(user_name="Alice")
        assert config.user_name == "Alice"
        assert config.household.members == ["Alice"]

    def test_household_config(self):
        config = ZiggyConfig(
            user_name="John",
            household=Household(
                members=["John", "Kristen"],
                domain_owners={"home": "Both", "finances": "John"},
            ),
        )
        assert len(config.household.members) == 2


class TestFoundationModels:
    def test_pillar_names(self):
        assert PillarName.REALITY == "reality"
        assert PillarName.FAMILY == "family"
        assert PillarName.CONTEXT == "context"
        assert PillarName.CAPABILITY == "capability"
        assert PillarName.VISION == "vision"

    def test_all_pillar_names(self):
        assert len(PillarName) == 5
