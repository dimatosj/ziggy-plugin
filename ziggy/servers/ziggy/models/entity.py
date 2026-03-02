"""Entity data models."""
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """An entity (person, place, organization) in the system."""
    id: str = ""  # Set by EntityService.create_entity() as "{type}-{name-slug}"
    name: str
    type: str  # person | property | organization
    subtype: str = ""
    domain: str = ""
    aliases: list[str] = Field(default_factory=list)
    description: str = ""
    contact_info: dict[str, str] = Field(default_factory=dict)
    relationships: list[dict[str, Any]] = Field(default_factory=list)


class EntityMention(BaseModel):
    """A detected entity mention in text."""
    text: str
    type_hint: Optional[str] = None
    signals: list[str] = Field(default_factory=list)
    triage_score: int = 1
    start: int = 0
    end: int = 0


class ResolutionResult(BaseModel):
    """Result of resolving an entity query."""
    status: str  # resolved | fuzzy_match | ambiguous | unknown
    entity: Optional[Entity] = None
    candidates: list[Entity] = Field(default_factory=list)
    confidence: float = 0.0
