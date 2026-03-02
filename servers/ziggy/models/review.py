"""Review state data models."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ReviewState(BaseModel):
    """State for an in-progress review."""
    type: str  # weekly | monthly | quarterly
    status: str = "in_progress"  # in_progress | completed
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    current_step: str = "reflect"  # reflect | assess | plan
    data: dict[str, Any] = Field(default_factory=dict)
