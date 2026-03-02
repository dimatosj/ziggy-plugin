"""Task and Draft data models."""
import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    """A task in the Ziggy system."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    status: str = "inbox"  # inbox | active | completed | archived
    priority: str = "MEDIUM"  # URGENT | HIGH | MEDIUM | LOW
    domain: str = "home"  # home | health | personal | family | work | finances | social
    entity_mentions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    due_date: Optional[str] = None
    analysis: dict[str, Any] = Field(default_factory=dict)


class Draft(BaseModel):
    """A draft entity (project, goal, commitment, initiative)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    type: str  # project | goal | commitment | initiative
    description: str = ""
    domain: str = "home"
    status: str = "draft"  # draft | promoted | declined
    created_at: datetime = Field(default_factory=datetime.now)
    promoted_at: Optional[datetime] = None


class AnalysisResult(BaseModel):
    """Result of analyzing captured text (matches CaptureOrchestrator.analyze() output)."""
    is_clear_task: bool
    entity_detection: dict[str, Any] = Field(default_factory=dict)  # {"type": ..., "confidence": ..., "signals": ...}
    priority: dict[str, Any] = Field(default_factory=dict)  # {"level": ..., "score": ..., "signals": ...}
    domain: dict[str, Any] = Field(default_factory=dict)  # {"matched": ..., "confidence": ..., "keywords_found": ...}
    owner: dict[str, Any] = Field(default_factory=dict)  # {"suggested": ..., "reason": ...}
    duration: Optional[dict[str, Any]] = None
    entity_mentions: list[dict[str, Any]] = Field(default_factory=list)
