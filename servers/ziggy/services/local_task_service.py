"""Local task and draft storage service using JSON files."""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ziggy.models.task import Task, Draft


class LocalTaskService:
    """CRUD service for tasks and drafts stored in local JSON files."""

    def __init__(self, data_dir: Path):
        self.tasks_dir = data_dir / "tasks"
        self.tasks_file = self.tasks_dir / "tasks.json"
        self.drafts_file = self.tasks_dir / "drafts.json"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    # ── Task operations ──

    def store_task(
        self,
        title: str,
        analysis: dict[str, Any],
        description: str = "",
        domain: str = "home",
        priority: str = "MEDIUM",
        entity_mentions: list[str] | None = None,
        due_date: str | None = None,
    ) -> Task:
        """Create and store a new task."""
        priority = analysis.get("priority", {}).get("level", priority)
        domain = analysis.get("domain", {}).get("matched", domain)
        mentions = entity_mentions or [
            m.get("text", "") for m in analysis.get("entity_mentions", [])
        ]

        task = Task(
            title=title,
            description=description,
            status="inbox",
            priority=priority,
            domain=domain,
            entity_mentions=mentions,
            due_date=due_date,
            analysis=analysis,
        )
        tasks = self._load_tasks()
        tasks.append(task)
        self._save_tasks(tasks)
        return task

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID. Raises KeyError if not found."""
        tasks = self._load_tasks()
        for task in tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"Task not found: {task_id}")

    def list_tasks(
        self,
        status: Optional[str] = None,
        domain: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> list[Task]:
        """List tasks with optional filters."""
        tasks = self._load_tasks()
        if status:
            tasks = [t for t in tasks if t.status == status]
        if domain:
            tasks = [t for t in tasks if t.domain == domain]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        return tasks

    def update_task(self, task_id: str, **kwargs: Any) -> Task:
        """Update task fields. Raises KeyError if not found."""
        tasks = self._load_tasks()
        for i, task in enumerate(tasks):
            if task.id == task_id:
                data = task.model_dump()
                for key, value in kwargs.items():
                    if key in data:
                        data[key] = value
                if kwargs.get("status") == "completed" and not data.get("completed_at"):
                    data["completed_at"] = datetime.now()
                tasks[i] = Task(**data)
                self._save_tasks(tasks)
                return tasks[i]
        raise KeyError(f"Task not found: {task_id}")

    def get_stats(self) -> dict[str, Any]:
        """Get task statistics."""
        tasks = self._load_tasks()
        status_counts = Counter(t.status for t in tasks)
        priority_counts = Counter(t.priority for t in tasks if t.status in ("inbox", "active"))
        return {
            "total": len(tasks),
            "by_status": dict(status_counts),
            "by_priority": dict(priority_counts),
        }

    # ── Draft operations ──

    def store_draft(
        self,
        title: str,
        type: str,
        analysis: dict[str, Any],
        description: str = "",
        domain: str = "home",
    ) -> Draft:
        """Create and store a new draft."""
        domain = analysis.get("domain", {}).get("matched", domain)
        draft = Draft(
            title=title,
            type=type,
            description=description,
            domain=domain,
        )
        drafts = self._load_drafts()
        drafts.append(draft)
        self._save_drafts(drafts)
        return draft

    def update_draft(self, draft_id: str, **kwargs: Any) -> Draft:
        """Update draft fields. Raises KeyError if not found."""
        drafts = self._load_drafts()
        for i, draft in enumerate(drafts):
            if draft.id == draft_id:
                data = draft.model_dump()
                for key, value in kwargs.items():
                    if key in data:
                        data[key] = value
                drafts[i] = Draft(**data)
                self._save_drafts(drafts)
                return drafts[i]
        raise KeyError(f"Draft not found: {draft_id}")

    def delete_draft(self, draft_id: str) -> None:
        """Delete a draft by ID. Raises KeyError if not found."""
        drafts = self._load_drafts()
        for i, draft in enumerate(drafts):
            if draft.id == draft_id:
                drafts.pop(i)
                self._save_drafts(drafts)
                return
        raise KeyError(f"Draft not found: {draft_id}")

    def list_drafts(self, type: Optional[str] = None) -> list[Draft]:
        """List drafts with optional type filter."""
        drafts = self._load_drafts()
        if type:
            drafts = [d for d in drafts if d.type == type]
        return drafts

    # ── File I/O ──

    def _load_tasks(self) -> list[Task]:
        if not self.tasks_file.exists():
            return []
        data = json.loads(self.tasks_file.read_text())
        return [Task(**t) for t in data]

    def _save_tasks(self, tasks: list[Task]) -> None:
        self.tasks_file.write_text(
            json.dumps([t.model_dump(mode="json") for t in tasks], indent=2, default=str)
        )

    def _load_drafts(self) -> list[Draft]:
        if not self.drafts_file.exists():
            return []
        data = json.loads(self.drafts_file.read_text())
        return [Draft(**d) for d in data]

    def _save_drafts(self, drafts: list[Draft]) -> None:
        self.drafts_file.write_text(
            json.dumps([d.model_dump(mode="json") for d in drafts], indent=2, default=str)
        )
