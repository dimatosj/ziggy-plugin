"""Tests for LocalTaskService."""
import json
import pytest
import tempfile
from pathlib import Path

from ziggy.services.local_task_service import LocalTaskService
from ziggy.models.task import Task, Draft


@pytest.fixture
def data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def service(data_dir):
    return LocalTaskService(data_dir)


class TestTaskCRUD:
    def test_store_task(self, service):
        task = service.store_task(title="buy eggs", analysis={"entity_type": "task"})
        assert task.title == "buy eggs"
        assert task.status == "inbox"
        assert task.id is not None

    def test_list_tasks_empty(self, service):
        tasks = service.list_tasks()
        assert tasks == []

    def test_list_tasks_with_filter(self, service):
        service.store_task(title="task1", analysis={"priority": {"level": "HIGH"}})
        service.store_task(title="task2", analysis={"priority": {"level": "LOW"}})
        # Update task1 to active
        tasks = service.list_tasks()
        assert len(tasks) == 2

    def test_list_tasks_by_status(self, service):
        service.store_task(title="inbox task", analysis={})
        t = service.store_task(title="active task", analysis={})
        service.update_task(t.id, status="active")
        inbox = service.list_tasks(status="inbox")
        active = service.list_tasks(status="active")
        assert len(inbox) == 1
        assert len(active) == 1

    def test_update_task(self, service):
        task = service.store_task(title="original", analysis={})
        updated = service.update_task(task.id, status="active", priority="HIGH")
        assert updated.status == "active"
        assert updated.priority == "HIGH"

    def test_update_nonexistent_raises(self, service):
        with pytest.raises(KeyError):
            service.update_task("nonexistent-id", status="active")

    def test_get_task(self, service):
        task = service.store_task(title="find me", analysis={})
        found = service.get_task(task.id)
        assert found.title == "find me"

    def test_persistence(self, data_dir):
        svc1 = LocalTaskService(data_dir)
        svc1.store_task(title="persistent", analysis={})
        svc2 = LocalTaskService(data_dir)
        tasks = svc2.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "persistent"


class TestDraftCRUD:
    def test_store_draft(self, service):
        draft = service.store_draft(title="renovate kitchen", type="project", analysis={})
        assert draft.title == "renovate kitchen"
        assert draft.type == "project"
        assert draft.status == "draft"

    def test_list_drafts(self, service):
        service.store_draft(title="p1", type="project", analysis={})
        service.store_draft(title="g1", type="goal", analysis={})
        all_drafts = service.list_drafts()
        assert len(all_drafts) == 2
        projects = service.list_drafts(type="project")
        assert len(projects) == 1

    def test_list_drafts_empty(self, service):
        drafts = service.list_drafts()
        assert drafts == []


class TestTaskStats:
    def test_get_stats(self, service):
        service.store_task(title="t1", analysis={"priority": {"level": "URGENT"}})
        service.store_task(title="t2", analysis={"priority": {"level": "HIGH"}})
        t3 = service.store_task(title="t3", analysis={})
        service.update_task(t3.id, status="active")
        stats = service.get_stats()
        assert stats["total"] == 3
        assert stats["by_status"]["inbox"] == 2
        assert stats["by_status"]["active"] == 1
